# CLAUDE.md — Intel Dashboard

## What This Is
A Flask web dashboard for viewing and browsing LeightonSec intel pipeline
reports in the browser. Renders markdown reports as HTML, provides search
and filtering, and shows active source status pulled from the pipeline
config. Companion tool to the intel-pipeline project.

## SOC Toolkit Position
- **Layer:** Visibility (Intelligence)
- **Reads from:** intel-pipeline reports folder (configurable via `INTEL_REPORTS_PATH`), Obsidian inbox (`INTEL_OBSIDIAN_PATH`)
- **Reads config from:** intel-pipeline config/sources.yaml via config_loader (`INTEL_PIPELINE_PATH`)
- **Gap it fills:** Browser-based report viewer, replaces opening Obsidian manually

## Architecture
- `app.py` — Flask server, report reader, source status, API endpoints
- `templates/index.html` — Two-panel UI, sidebar with filters, main report viewer

## Report Paths
- Local: `~/Documents/Projects/intel-pipeline/reports/`
- Obsidian: `~/Documents/MyVault/Inbox/`
- Deduplicates across both paths by filename

## Current Status
✅ Complete and live — LeightonSec/intel-dashboard
✅ Report listing with v1/v2 badges
✅ Markdown to HTML rendering
✅ Version and period filtering
✅ Search by filename
✅ Source status from pipeline config
✅ Category colour coding — security, ai_research, crypto, cve
✅ Stats overview — total reports, v1/v2 counts, source count
✅ Auto-refresh every 60 seconds
✅ Path traversal protection — reports validated against known list

## API Endpoints
- `GET /api/reports` — list reports, ?version=v1/v2, ?category=
- `GET /api/reports/<filename>` — report content as HTML
- `GET /api/sources` — configured sources from pipeline config
- `GET /api/stats` — dashboard statistics

## Security Notes
- SECRET_KEY fails closed — app raises and refuses to start if unset (no forgeable default). Kept in .env, never committed
- HTML sanitisation — markdown report output sanitised with nh3 (tight tag/attr allowlist) before it reaches the browser DOM. Report content originates from untrusted external OSINT feeds (stored-XSS defence)
- Input validation — version/category query filters constrained, 400 on invalid
- Read-only — dashboard never writes to pipeline or reports
- Path traversal protection — filename validated against known reports list
- Source config read via yaml.safe_load on the pipeline's config/sources.yaml — no sys.path injection, no foreign-module execution
- Server on 127.0.0.1 port 5004

## Known Issues / Tech Debt
- No full text search across report content yet
- No persistent storage — reads files fresh on every request

## Next Steps
- [ ] Full text search across report content
- [ ] Severity badges per report — HIGH/MEDIUM/LOW count
- [ ] Historical charts — detections over time
- [ ] Database backend for structured report storage
- [ ] Source reputation scoring
- [ ] Trending topics across reports
- [ ] Integration with Unified Dashboard

## Tech Stack
- Python, Flask
- markdown (pip) — converts report markdown to HTML
- pyyaml — reads pipeline config
- python-dotenv

## Conventions
- Reports always read from REPORTS_PATH and OBSIDIAN_PATH
- Never write to pipeline folders — read only
- Filename validation before serving any report content
- All config read from intel-pipeline — never duplicate config here
