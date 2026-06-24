import os
import re
from datetime import datetime

import markdown
import nh3
import yaml
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)

# Fail closed: a missing secret must stop startup, not silently fall back to a
# known default that would make Flask session cookies forgeable.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required (set it in .env)")
app.config["SECRET_KEY"] = SECRET_KEY

REPORTS_PATH = os.path.expanduser(
    os.getenv('INTEL_REPORTS_PATH', '~/Documents/Projects/intel-pipeline/reports')
)
OBSIDIAN_PATH = os.path.expanduser(
    os.getenv('INTEL_OBSIDIAN_PATH', '~/Documents/MyVault/Inbox')
)
PIPELINE_PATH = os.path.expanduser(
    os.getenv('INTEL_PIPELINE_PATH', '~/Documents/Projects/intel-pipeline')
)

# Report markdown originates from external OSINT feeds and is therefore
# untrusted. After markdown->HTML conversion we strip everything except this
# allowlist, so a feed item carrying <script> or an onerror handler cannot
# execute in an analyst's browser when the HTML is injected into the DOM.
ALLOWED_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "hr",
    "ul", "ol", "li", "blockquote",
    "table", "thead", "tbody", "tr", "th", "td",
    "code", "pre", "em", "strong", "a",
}
ALLOWED_ATTRS = {"a": {"href", "title"}}

# Query-string filter constraints (schema validation on inputs).
VALID_VERSIONS = ("", "v1", "v2")
CATEGORY_RE = re.compile(r"[a-z_]{0,32}")


def get_reports() -> list:
    """Get all intel reports sorted by date descending"""
    reports = []

    for path in [REPORTS_PATH, OBSIDIAN_PATH]:
        if not os.path.exists(path):
            continue
        for filename in os.listdir(path):
            if filename.startswith("Intel-") and filename.endswith(".md"):
                filepath = os.path.join(path, filename)
                stat = os.stat(filepath)
                reports.append({
                    "filename": filename,
                    "filepath": filepath,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "version": "v2" if "v2" in filename else "v1",
                    "period": "PM" if "PM" in filename else "AM",
                    "date": extract_date(filename)
                })

    # Deduplicate by filename
    seen = set()
    unique = []
    for r in reports:
        if r["filename"] not in seen:
            seen.add(r["filename"])
            unique.append(r)

    return sorted(unique, key=lambda x: x["modified"], reverse=True)


def extract_date(filename: str) -> str:
    """Extract date from filename like Intel-2026-04-18-AM.md"""
    try:
        parts = filename.replace("Intel-v2-", "").replace("Intel-", "").replace(".md", "")
        date_part = "-".join(parts.split("-")[:3])
        return date_part
    except Exception:
        return "Unknown"


def read_report(filepath: str) -> str:
    """Read a markdown report and convert it to sanitised HTML."""
    try:
        with open(filepath) as f:
            content = f.read()
    except Exception:
        return "<p>Error reading report</p>"
    html = markdown.markdown(content, extensions=["tables", "fenced_code"])
    return nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)


def get_source_status() -> list:
    """Read configured feed sources from the pipeline's sources.yaml.

    Reads the YAML config directly rather than importing pipeline code via
    sys.path injection — no foreign-module execution and no cross-repo path
    coupling. Degrades to an empty list if the config is missing or unreadable.
    """
    config_path = os.path.join(PIPELINE_PATH, "config", "sources.yaml")
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
        feeds = config.get("feeds", {})
        sources = []
        for category, urls in feeds.items():
            for url in urls:
                sources.append({
                    "category": category,
                    "url": url,
                    "domain": url.split("/")[2].replace("www.", "")
                })
        return sources
    except Exception:
        return []


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/reports')
def api_reports():
    """Get list of all reports"""
    category = request.args.get('category', '')
    version = request.args.get('version', '')

    if version not in VALID_VERSIONS:
        abort(400, description="invalid version filter")
    if not CATEGORY_RE.fullmatch(category):
        abort(400, description="invalid category filter")

    reports = get_reports()

    if category:
        reports = [r for r in reports if category.lower() in r['filename'].lower()]
    if version:
        reports = [r for r in reports if r['version'] == version]

    return jsonify(reports)


@app.route('/api/reports/<path:filename>')
def api_report_content(filename):
    """Get content of a specific report"""
    reports = get_reports()
    report = next((r for r in reports if r['filename'] == filename), None)

    if not report:
        return jsonify({"error": "Report not found"}), 404

    html_content = read_report(report['filepath'])
    return jsonify({
        **report,
        "content": html_content
    })


@app.route('/api/sources')
def api_sources():
    """Get configured sources"""
    return jsonify(get_source_status())


@app.route('/api/stats')
def api_stats():
    """Dashboard statistics"""
    reports = get_reports()
    sources = get_source_status()

    return jsonify({
        "total_reports": len(reports),
        "v1_reports": sum(1 for r in reports if r['version'] == 'v1'),
        "v2_reports": sum(1 for r in reports if r['version'] == 'v2'),
        "total_sources": len(sources),
        "latest_report": reports[0]['filename'] if reports else None,
        "categories": list(set(s['category'] for s in sources))
    })


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5004)
