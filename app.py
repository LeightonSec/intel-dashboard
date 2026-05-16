import os
import json
import markdown
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'changeme')

REPORTS_PATH = os.path.expanduser(
    os.getenv('INTEL_REPORTS_PATH', '~/Documents/Projects/intel-pipeline/reports')
)
OBSIDIAN_PATH = os.path.expanduser(
    os.getenv('INTEL_OBSIDIAN_PATH', '~/Documents/MyVault/Inbox')
)
PIPELINE_PATH = os.path.expanduser(
    os.getenv('INTEL_PIPELINE_PATH', '~/Documents/Projects/intel-pipeline')
)

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
    except:
        return "Unknown"

def read_report(filepath: str) -> str:
    """Read and convert markdown report to HTML"""
    try:
        with open(filepath, "r") as f:
            content = f.read()
        return markdown.markdown(content, extensions=["tables", "fenced_code"])
    except:
        return "<p>Error reading report</p>"

def get_source_status() -> list:
    """Check which sources are configured"""
    try:
        import sys
        sys.path.insert(0, PIPELINE_PATH)
        from config_loader import load_config, get_feeds
        config = load_config()
        feeds = get_feeds(config)
        sources = []
        for category, urls in feeds.items():
            for url in urls:
                sources.append({
                    "category": category,
                    "url": url,
                    "domain": url.split("/")[2].replace("www.", "")
                })
        return sources
    except Exception as e:
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/reports')
def api_reports():
    """Get list of all reports"""
    category = request.args.get('category', '')
    version = request.args.get('version', '')
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