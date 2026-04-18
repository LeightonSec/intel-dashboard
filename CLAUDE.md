# CLAUDE.md — Intel Dashboard

## What This Is
A Flask web dashboard for viewing and browsing LeightonSec intel pipeline
reports in the browser. Renders markdown reports as HTML, provides search
and filtering, and shows active source status pulled from the pipeline
config. Companion tool to the intel-pipeline project.

## SOC Toolkit Position
- **Layer:** Visibility (Intelligence)
- **Reads from:** intel-pipeline reports folder, Obsidian inbox
- **Reads config from:** intel-pipeline config/sources.yaml via config_loader
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
✅ Category colour coding — security, ai_research, bsv_bastion, cve
✅ Stats overview — total reports, v1/v2 counts, source count
✅ Auto-refresh every 60 seconds
✅ Path traversal protection — reports validated against known list

## API Endpoints
- `GET /api/reports` — list reports, ?version=v1/v2, ?category=
- `GET /api/reports/<filename>` — report content as HTML
- `GET /api/sources` — configured sources from pipeline config
- `GET /api/stats` — dashboard statistics

## Security Notes
- SECRET_KEY in .env — never committed
- Read-only — dashboard never writes to pipeline or reports
- Path traversal protection — filename validated against known reports list
- sys.path manipulation isolated inside get_source_status() function
- Server on 127.0.0.1 port 5004
- pyyaml required in dashboard venv — not inherited from pipeline venv

## Known Issues / Tech Debt
- Source status requires pyyaml installed in dashboard venv separately
- config_loader imported via sys.path manipulation — fragile if pipeline moves
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
