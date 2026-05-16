import pytest
from unittest.mock import patch

from app import app, extract_date


MOCK_REPORTS = [
    {
        "filename": "Intel-2026-05-16-AM.md",
        "filepath": "/fake/Intel-2026-05-16-AM.md",
        "size": 1024,
        "modified": "2026-05-16T08:00:00",
        "version": "v1",
        "period": "AM",
        "date": "2026-05-16",
    },
    {
        "filename": "Intel-v2-2026-05-15-PM.md",
        "filepath": "/fake/Intel-v2-2026-05-15-PM.md",
        "size": 2048,
        "modified": "2026-05-15T18:00:00",
        "version": "v2",
        "period": "PM",
        "date": "2026-05-15",
    },
]

MOCK_SOURCES = [
    {"category": "security", "url": "https://krebsonsecurity.com", "domain": "krebsonsecurity.com"},
    {"category": "cve", "url": "https://www.cisa.gov/alerts", "domain": "cisa.gov"},
]


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestRoutes:
    def test_index(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    @patch("app.get_reports", return_value=MOCK_REPORTS)
    def test_api_reports_returns_list(self, _mock, client):
        resp = client.get("/api/reports")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 2

    @patch("app.get_reports", return_value=MOCK_REPORTS)
    def test_api_reports_version_filter(self, _mock, client):
        resp = client.get("/api/reports?version=v2")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["version"] == "v2"

    @patch("app.get_reports", return_value=MOCK_REPORTS)
    def test_api_reports_period_filter(self, _mock, client):
        resp = client.get("/api/reports?version=v1")
        data = resp.get_json()
        assert all(r["version"] == "v1" for r in data)

    @patch("app.get_reports", return_value=MOCK_REPORTS)
    def test_api_report_not_found(self, _mock, client):
        resp = client.get("/api/reports/nonexistent.md")
        assert resp.status_code == 404

    @patch("app.get_reports", return_value=MOCK_REPORTS)
    @patch("app.read_report", return_value="<p>content</p>")
    def test_api_report_content(self, _mock_read, _mock_get, client):
        resp = client.get("/api/reports/Intel-2026-05-16-AM.md")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["filename"] == "Intel-2026-05-16-AM.md"
        assert "content" in data
        assert data["version"] == "v1"

    @patch("app.get_source_status", return_value=MOCK_SOURCES)
    def test_api_sources(self, _mock, client):
        resp = client.get("/api/sources")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    @patch("app.get_reports", return_value=MOCK_REPORTS)
    @patch("app.get_source_status", return_value=MOCK_SOURCES)
    def test_api_stats_shape(self, _mock_src, _mock_rep, client):
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_reports"] == 2
        assert data["v1_reports"] == 1
        assert data["v2_reports"] == 1
        assert data["total_sources"] == 2
        assert "categories" in data

    @patch("app.get_reports", return_value=[])
    @patch("app.get_source_status", return_value=[])
    def test_api_stats_empty(self, _mock_src, _mock_rep, client):
        resp = client.get("/api/stats")
        data = resp.get_json()
        assert data["total_reports"] == 0
        assert data["latest_report"] is None


class TestExtractDate:
    def test_v1_am(self):
        assert extract_date("Intel-2026-05-16-AM.md") == "2026-05-16"

    def test_v2_pm(self):
        assert extract_date("Intel-v2-2026-05-15-PM.md") == "2026-05-15"

    def test_v1_pm(self):
        assert extract_date("Intel-2026-01-01-PM.md") == "2026-01-01"

    def test_malformed_returns_string(self):
        result = extract_date("bad.md")
        assert isinstance(result, str)
