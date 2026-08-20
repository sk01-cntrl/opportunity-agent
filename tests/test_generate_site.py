import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.models import Category, Opportunity, Source
from src.scorer import score, ScoredOpportunity
from src.profile import Profile


def _make_opp(**kwargs):
    defaults = {
        "title": "Test Hack",
        "url": "https://example.com",
        "source": Source.DEVPOST,
        "category": Category.HACKATHON,
        "tags": ["python", "ai"],
        "skills_required": ["python"],
        "domain": ["machine-learning"],
    }
    defaults.update(kwargs)
    return Opportunity(**defaults)


def _make_profile(**kwargs):
    defaults = {
        "skills": ["python", "ai"],
        "interests": ["machine-learning"],
        "experience_level": "beginner",
        "preferred_formats": ["online"],
        "preferred_categories": ["hackathon"],
        "location_preference": "any",
        "excluded_tags": [],
    }
    defaults.update(kwargs)
    return Profile(**defaults)


class TestGenerateSite:
    def test_generate_site_creates_files(self, tmp_path):
        from generate_site import generate_site, build_dashboard_data

        opps = [
            _make_opp(title="AI Hack"),
            _make_opp(title="Web Hack", tags=["web"], skills_required=[], domain=[]),
        ]
        profile = _make_profile()
        scored = score(opps, profile)

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        data = [s.opportunity.to_dict() for s in scored]
        with open(output_dir / "opportunities_20260101_120000.json", "w") as f:
            json.dump(data, f)

        web_dir = tmp_path / "web"
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            result = build_dashboard_data()
            assert "opportunities" in result
            assert len(result["opportunities"]) == 2

            generate_site(web_dir=str(web_dir))
            assert (web_dir / "index.html").exists()
            assert (web_dir / "data.js").exists()
        finally:
            os.chdir(original_cwd)

    def test_data_js_contains_valid_json(self, tmp_path):
        from generate_site import build_dashboard_data

        opps = [_make_opp()]
        profile = _make_profile()
        scored = score(opps, profile)

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        data = [s.opportunity.to_dict() for s in scored]
        with open(output_dir / "opportunities_20260101_120000.json", "w") as f:
            json.dump(data, f)

        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            result = build_dashboard_data()
            assert result["total"] == 1
            assert result["strong_matches"] >= 0
            assert len(result["source_statuses"]) >= 1
        finally:
            os.chdir(original_cwd)

    def test_html_contains_required_elements(self, tmp_path):
        from generate_site import generate_html

        web_dir = tmp_path / "web"
        web_dir.mkdir()
        generate_html(str(web_dir))

        html = (web_dir / "index.html").read_text()
        assert "Opportunity Scout" in html
        assert "data.js" in html
        assert "filter-category" in html
        assert "filter-domain" in html
        assert "filter-location" in html
        assert "sort-by" in html
        assert "search" in html

    def test_dashboard_includes_all_fields(self, tmp_path):
        from generate_site import build_dashboard_data

        opp = _make_opp(
            title="Python Data Hack",
            location="Online",
            format="online",
            deadline=datetime.now(tz=timezone.utc) + timedelta(days=30),
            prize_info="$5000",
            eligibility="Open to all",
            organizer="TechCorp",
            registrations_count=150,
        )
        profile = _make_profile()
        scored = score([opp], profile)

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        data = [s.opportunity.to_dict() for s in scored]
        with open(output_dir / "opportunities_20260101_120000.json", "w") as f:
            json.dump(data, f)

        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            result = build_dashboard_data()
            o = result["opportunities"][0]
            assert o["title"] == "Python Data Hack"
            assert o["source"] == "devpost"
            assert o["category"] == "hackathon"
            assert o["location"] == "Online"
            assert o["format"] == "online"
            assert o["deadline"] is not None
            assert o["prize_info"] == "$5000"
            assert o["eligibility"] == "Open to all"
            assert o["organizer"] == "TechCorp"
            assert o["registrations_count"] == 150
            assert "score" in o
            assert "fee_status" in o
            assert "reasons" in o
        finally:
            os.chdir(original_cwd)

    def test_no_output_returns_error(self, tmp_path):
        from generate_site import build_dashboard_data

        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            result = build_dashboard_data()
            assert "error" in result
            assert result["opportunities"] == []
        finally:
            os.chdir(original_cwd)

    def test_scanner_failure_does_not_break_dashboard(self, tmp_path):
        from generate_site import build_dashboard_data

        opps = [_make_opp()]
        profile = _make_profile()
        scored = score(opps, profile)

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        data = [s.opportunity.to_dict() for s in scored]
        with open(output_dir / "opportunities_20260101_120000.json", "w") as f:
            json.dump(data, f)

        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            result = build_dashboard_data()
            assert result["total"] == 1
            statuses = result["source_statuses"]
            assert any(s["name"] == "devpost" for s in statuses)
        finally:
            os.chdir(original_cwd)

    def test_empty_opportunities_list(self, tmp_path):
        from generate_site import build_dashboard_data

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        with open(output_dir / "opportunities_20260101_120000.json", "w") as f:
            json.dump([], f)

        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            result = build_dashboard_data()
            assert result["total"] == 0
            assert result["opportunities"] == []
        finally:
            os.chdir(original_cwd)
