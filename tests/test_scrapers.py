import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from src.models import Category, Source
from src.scrapers.devpost import DevpostScraper
from src.scrapers.mlh import MLHScraper
from src.scrapers.luma import LumaScraper
from src.scrapers.internshala import InternshalaScraper
from src.scrapers.unstop import UnstopScraper
from src.scrapers.hackculture import HackCultureScraper
from src.scanner import Scanner


SAMPLE_DEVPOST_RESPONSE = {
    "hackathons": [
        {
            "id": 12345,
            "title": "Test Hackathon 2026",
            "url": "https://test-hackathon-2026.devpost.com",
            "displayed_location": {"icon": "globe", "location": "Online"},
            "open_state": "open",
            "themes": [{"name": "Machine Learning/AI"}, {"name": "Web"}],
            "prize_amount": "$<span data-currency-value>10,000</span>",
            "prizes_counts": {"cash": 2, "other": 1},
            "registrations_count": 5432,
            "organization_name": "TechCorp",
            "invite_only": False,
            "submission_period_dates": "Jul 1 - Jul 30, 2026",
        },
        {
            "id": 12346,
            "title": "Ended Hackathon",
            "url": "https://ended.devpost.com",
            "displayed_location": {"location": "New York, NY"},
            "open_state": "ended",
            "themes": [],
            "prize_amount": "",
            "prizes_counts": {},
            "registrations_count": 0,
            "organization_name": "",
            "invite_only": False,
            "submission_period_dates": "",
        },
        {
            "id": 12347,
            "title": "Upcoming Hack",
            "url": "https://upcoming.devpost.com",
            "displayed_location": {"location": "San Francisco, CA"},
            "open_state": "upcoming",
            "themes": [{"name": "Health"}, {"name": "Beginner Friendly"}],
            "prize_amount": "$5,000",
            "prizes_counts": {"cash": 1, "other": 0},
            "registrations_count": 800,
            "organization_name": "HealthTech Inc",
            "invite_only": True,
            "submission_period_dates": "Aug 15 - Sep 15, 2026",
        },
    ]
}

SAMPLE_MLH_PAGE = {
    "component": "EventsListing",
    "props": {
        "pastEvents": [
            {
                "id": "evt-1",
                "name": "MLH Past Hackathon",
                "status": "ended",
                "startsAt": "2026-06-13T12:00:00Z",
                "endsAt": "2026-06-14T23:59:59Z",
                "dateRange": "JUN 13 - 14",
                "url": "/events/mlh-past/prizes",
                "location": "Toronto, Canada",
                "formatType": "physical",
                "region": "AMER",
                "websiteUrl": "https://mlh-past.example.com",
                "venueAddress": {"city": "Toronto", "state": "Ontario", "country": "CA"},
                "customFields": {"underserved_types": []},
            }
        ],
        "upcomingEvents": [
            {
                "id": "evt-2",
                "name": "MLH Upcoming Hackathon",
                "status": "pending",
                "startsAt": "2026-09-20T10:00:00Z",
                "endsAt": "2026-09-21T22:00:00Z",
                "dateRange": "SEP 20 - 21",
                "url": "/events/mlh-upcoming/prizes",
                "location": "San Francisco, CA",
                "formatType": "digital",
                "region": "AMER",
                "websiteUrl": "https://mlh-upcoming.example.com",
                "venueAddress": {"city": "San Francisco", "state": "CA", "country": "US"},
                "customFields": {"underserved_types": ["Women Only"]},
            }
        ],
    },
}


def _build_mlh_html(page_data: dict) -> str:
    json_str = json.dumps(page_data)
    return f"""
<html><body>
<script data-page="app" type="application/json">{json_str}</script>
</body></html>
"""


class TestDevpostScraper:
    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_returns_open_hackathons(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_DEVPOST_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = DevpostScraper()
        results = scraper.scrape(max_pages=1)

        assert len(results) == 2
        titles = [r.title for r in results]
        assert "Test Hackathon 2026" in titles
        assert "Upcoming Hack" in titles
        assert "Ended Hackathon" not in titles

    @patch("src.scrapers.base.requests.Session.get")
    def test_devpost_parses_correct_fields(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_DEVPOST_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = DevpostScraper()
        results = scraper.scrape(max_pages=1)

        first = results[0]
        assert first.source == Source.DEVPOST
        assert first.category == Category.HACKATHON
        assert first.location == "Online"
        assert "Machine Learning/AI" in first.tags
        assert first.deadline == datetime(2026, 7, 30)

    @patch("src.scrapers.base.requests.Session.get")
    def test_devpost_extracts_prize_info(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_DEVPOST_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = DevpostScraper()
        results = scraper.scrape(max_pages=1)

        first = results[0]
        assert "10000" in first.prize_info
        assert "2 cash prizes" in first.prize_info
        assert "1 other prize" in first.prize_info

    @patch("src.scrapers.base.requests.Session.get")
    def test_devpost_extracts_registrations(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_DEVPOST_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = DevpostScraper()
        results = scraper.scrape(max_pages=1)

        first = results[0]
        assert first.registrations_count == 5432
        assert "5,432 registered" in first.description

    @patch("src.scrapers.base.requests.Session.get")
    def test_devpost_extracts_organizer(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_DEVPOST_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = DevpostScraper()
        results = scraper.scrape(max_pages=1)

        first = results[0]
        assert first.organizer == "TechCorp"

    @patch("src.scrapers.base.requests.Session.get")
    def test_devpost_extracts_domain(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_DEVPOST_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = DevpostScraper()
        results = scraper.scrape(max_pages=1)

        first = results[0]
        assert "machine-learning" in first.domain
        assert "web" in first.domain

    @patch("src.scrapers.base.requests.Session.get")
    def test_devpost_extracts_experience_level(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_DEVPOST_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = DevpostScraper()
        results = scraper.scrape(max_pages=1)

        beginner_hack = [r for r in results if r.title == "Upcoming Hack"][0]
        assert beginner_hack.experience_level == "beginner"

    @patch("src.scrapers.base.requests.Session.get")
    def test_devpost_extracts_invite_only(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_DEVPOST_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = DevpostScraper()
        results = scraper.scrape(max_pages=1)

        invite_hack = [r for r in results if r.title == "Upcoming Hack"][0]
        assert "Invite only" in invite_hack.eligibility


class TestMLHScraper:
    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_filters_ended_events(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = _build_mlh_html(SAMPLE_MLH_PAGE)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = MLHScraper()
        results = scraper.scrape()

        assert len(results) == 1
        assert results[0].title == "MLH Upcoming Hackathon"
        assert results[0].source == Source.MLH

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_parses_upcoming_fields(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = _build_mlh_html(SAMPLE_MLH_PAGE)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = MLHScraper()
        results = scraper.scrape()

        opp = results[0]
        assert opp.url == "https://mlh-upcoming.example.com"
        assert opp.category == Category.HACKATHON
        assert "digital" in opp.tags
        assert "AMER" in opp.tags
        assert "Women Only" in opp.tags
        assert opp.deadline.replace(tzinfo=None) == datetime(2026, 9, 21, 22, 0, 0)

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_extracts_venue_address(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = _build_mlh_html(SAMPLE_MLH_PAGE)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = MLHScraper()
        results = scraper.scrape()

        opp = results[0]
        assert opp.location == "San Francisco, US"

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_extracts_format(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = _build_mlh_html(SAMPLE_MLH_PAGE)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = MLHScraper()
        results = scraper.scrape()

        opp = results[0]
        assert opp.format == "online"

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_extracts_eligibility(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = _build_mlh_html(SAMPLE_MLH_PAGE)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = MLHScraper()
        results = scraper.scrape()

        opp = results[0]
        assert "Women Only" in opp.eligibility

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_returns_empty_when_all_ended(self, mock_get):
        page = {"props": {"pastEvents": [{"status": "ended", "name": "X"}], "upcomingEvents": []}}
        mock_resp = MagicMock()
        mock_resp.text = _build_mlh_html(page)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = MLHScraper()
        results = scraper.scrape()
        assert results == []

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_excludes_expired_pending_event(self, mock_get):
        page = {
            "props": {
                "pastEvents": [
                    {
                        "id": "expired-pending",
                        "name": "Aston Hack 11",
                        "status": "pending",
                        "startsAt": "2026-02-07T14:00:00Z",
                        "endsAt": "2026-02-08T23:59:59Z",
                        "dateRange": "FEB 07 - 08",
                        "url": "/events/aston-hack-11/prizes",
                        "location": "Birmingham, Birmingham",
                        "formatType": "physical",
                        "region": "EMEA",
                        "websiteUrl": "https://www.astonhack.co.uk",
                        "venueAddress": {},
                        "customFields": {"underserved_types": []},
                    }
                ],
                "upcomingEvents": [],
            }
        }
        mock_resp = MagicMock()
        mock_resp.text = _build_mlh_html(page)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = MLHScraper()
        results = scraper.scrape()
        assert results == [], (
            "Event with status 'pending' but ended date should be excluded"
        )


class TestScanner:
    @patch("src.scanner.HackCultureScraper.scrape")
    @patch("src.scanner.UnstopScraper.scrape")
    @patch("src.scanner.InternshalaScraper.scrape")
    @patch("src.scanner.LumaScraper.scrape")
    @patch("src.scanner.MLHScraper.scrape")
    @patch("src.scanner.DevpostScraper.scrape")
    def test_deduplicates(self, mock_devpost, mock_mlh, mock_luma, mock_intern, mock_unstop, mock_hack):
        from src.models import Opportunity

        opp = Opportunity(
            title="Same Hack", url="https://x.com", source=Source.DEVPOST
        )
        mock_devpost.return_value = [opp, opp]
        mock_mlh.return_value = []
        mock_luma.return_value = []
        mock_intern.return_value = []
        mock_unstop.return_value = []
        mock_hack.return_value = []

        scanner = Scanner()
        results = scanner.scan()
        assert len(results) == 1

    def test_save_creates_file(self, tmp_path):
        from src.models import Opportunity

        opp = Opportunity(
            title="Saved Hack",
            url="https://x.com",
            source=Source.DEVPOST,
        )
        scanner = Scanner(output_dir=str(tmp_path))
        path = scanner.save([opp])
        import os

        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["title"] == "Saved Hack"


class TestScannerSourceStatus:
    @patch("src.scanner.HackCultureScraper.scrape")
    @patch("src.scanner.UnstopScraper.scrape")
    @patch("src.scanner.InternshalaScraper.scrape")
    @patch("src.scanner.LumaScraper.scrape")
    @patch("src.scanner.MLHScraper.scrape")
    @patch("src.scanner.DevpostScraper.scrape")
    def test_success_with_opportunities(self, mock_devpost, mock_mlh, mock_luma, mock_intern, mock_unstop, mock_hack):
        from src.models import Opportunity

        opp = Opportunity(
            title="Hack One", url="https://hack1.com", source=Source.DEVPOST
        )
        mock_devpost.return_value = [opp]
        mock_mlh.return_value = []
        mock_luma.return_value = []
        mock_intern.return_value = []
        mock_unstop.return_value = []
        mock_hack.return_value = []

        scanner = Scanner()
        results = scanner.scan()

        assert len(results) == 1
        assert scanner.source_statuses["DevpostScraper"].ok
        assert scanner.source_statuses["DevpostScraper"].count == 1
        assert scanner.source_statuses["MLHScraper"].ok
        assert scanner.source_statuses["MLHScraper"].count == 0

    @patch("src.scanner.HackCultureScraper.scrape")
    @patch("src.scanner.UnstopScraper.scrape")
    @patch("src.scanner.InternshalaScraper.scrape")
    @patch("src.scanner.LumaScraper.scrape")
    @patch("src.scanner.MLHScraper.scrape")
    @patch("src.scanner.DevpostScraper.scrape")
    def test_success_with_zero(self, mock_devpost, mock_mlh, mock_luma, mock_intern, mock_unstop, mock_hack):
        mock_devpost.return_value = []
        mock_mlh.return_value = []
        mock_luma.return_value = []
        mock_intern.return_value = []
        mock_unstop.return_value = []
        mock_hack.return_value = []

        scanner = Scanner()
        results = scanner.scan()

        assert results == []
        assert scanner.source_statuses["DevpostScraper"].ok
        assert scanner.source_statuses["DevpostScraper"].count == 0
        assert scanner.source_statuses["MLHScraper"].ok
        assert scanner.source_statuses["MLHScraper"].count == 0

    @patch("src.scanner.HackCultureScraper.scrape")
    @patch("src.scanner.UnstopScraper.scrape")
    @patch("src.scanner.InternshalaScraper.scrape")
    @patch("src.scanner.LumaScraper.scrape")
    @patch("src.scanner.MLHScraper.scrape")
    @patch("src.scanner.DevpostScraper.scrape")
    def test_network_failure(self, mock_devpost, mock_mlh, mock_luma, mock_intern, mock_unstop, mock_hack):
        import requests as req_lib

        mock_devpost.return_value = []
        mock_mlh.side_effect = req_lib.exceptions.ConnectionError(
            "[Errno -2] Name or service not known"
        )
        mock_luma.return_value = []
        mock_intern.return_value = []
        mock_unstop.return_value = []
        mock_hack.return_value = []

        scanner = Scanner()
        results = scanner.scan()

        assert results == []
        assert scanner.source_statuses["DevpostScraper"].ok
        assert scanner.source_statuses["DevpostScraper"].count == 0
        assert not scanner.source_statuses["MLHScraper"].ok
        assert "Name or service not known" in scanner.source_statuses["MLHScraper"].error

    @patch("src.scanner.HackCultureScraper.scrape")
    @patch("src.scanner.UnstopScraper.scrape")
    @patch("src.scanner.InternshalaScraper.scrape")
    @patch("src.scanner.LumaScraper.scrape")
    @patch("src.scanner.MLHScraper.scrape")
    @patch("src.scanner.DevpostScraper.scrape")
    def test_http_failure(self, mock_devpost, mock_mlh, mock_luma, mock_intern, mock_unstop, mock_hack):
        import requests as req_lib

        mock_devpost.return_value = []
        mock_mlh.side_effect = req_lib.exceptions.HTTPError(
            "403 Forbidden", response=MagicMock(status_code=403)
        )
        mock_luma.return_value = []
        mock_intern.return_value = []
        mock_unstop.return_value = []
        mock_hack.return_value = []

        scanner = Scanner()
        results = scanner.scan()

        assert results == []
        assert scanner.source_statuses["DevpostScraper"].ok
        assert not scanner.source_statuses["MLHScraper"].ok
        assert "403" in scanner.source_statuses["MLHScraper"].error

    @patch("src.scanner.HackCultureScraper.scrape")
    @patch("src.scanner.UnstopScraper.scrape")
    @patch("src.scanner.InternshalaScraper.scrape")
    @patch("src.scanner.LumaScraper.scrape")
    @patch("src.scanner.MLHScraper.scrape")
    @patch("src.scanner.DevpostScraper.scrape")
    def test_partial_failure_still_returns_other_sources(self, mock_devpost, mock_mlh, mock_luma, mock_intern, mock_unstop, mock_hack):
        from src.models import Opportunity

        opp = Opportunity(
            title="Devpost Hack", url="https://d.com", source=Source.DEVPOST
        )
        mock_devpost.return_value = [opp]
        mock_mlh.side_effect = ConnectionError("unreachable")
        mock_luma.return_value = []
        mock_intern.return_value = []
        mock_unstop.return_value = []
        mock_hack.return_value = []

        scanner = Scanner()
        results = scanner.scan()

        assert len(results) == 1
        assert results[0].title == "Devpost Hack"
        assert scanner.source_statuses["DevpostScraper"].ok
        assert not scanner.source_statuses["MLHScraper"].ok


SAMPLE_LUMA_PAGE = {
    "props": {
        "pageProps": {
            "featuredEvents": [
                {
                    "name": "AI Builder Night SF",
                    "slug": "ai-builder-night-sf",
                    "start_at": "2026-09-15T18:00:00Z",
                    "end_at": "2026-09-15T22:00:00Z",
                    "location_type": "in-person",
                    "geo_address_json": {"address": "San Francisco, CA"},
                    "calendar": {"name": "Luma"},
                    "paid_ticket": False,
                    "description": "<p>Build AI projects</p>",
                    "topics": [{"name": "AI"}, {"name": "Machine Learning"}],
                },
                {
                    "name": "Crypto Hack Week",
                    "slug": "crypto-hack-week",
                    "start_at": "2026-09-01T10:00:00Z",
                    "end_at": "2026-09-07T18:00:00Z",
                    "location_type": "online",
                    "geo_address_json": {},
                    "calendar": {"name": "CryptoDAO"},
                    "paid_ticket": True,
                    "description": "",
                    "topics": ["blockchain", "web3"],
                },
                {
                    "name": "Past Event",
                    "slug": "past-event",
                    "start_at": "2026-01-01T10:00:00Z",
                    "end_at": "2026-01-02T10:00:00Z",
                    "location_type": "in-person",
                    "geo_address_json": {"address": "New York, NY"},
                    "calendar": {"name": "OldOrg"},
                    "paid_ticket": False,
                    "description": "",
                    "topics": [],
                },
            ]
        }
    }
}

SAMPLE_INTERNSHALA_PAGE = """
<html><body>
<div class="container-fluid individual_internship logged_out_jd_summary" id="individual_internship_12345" internshipId="12345" data-href='/internship/detail/software-development-intern-12345'>
    <div class="internship_meta duration_meta">
        <div class="internship-heading-container">
            <div class="company generic_company">
                <div class='generic_container'>
                    <h2 class="job-internship-name">
                        <a class="job-title-href" href="/internship/detail/software-development-intern-12345">Software Development Intern</a>
                    </h2>
                </div>
                <p class="company-name">Google India</p>
            </div>
        </div>
        <div class="individual_internship_details individual_internship_internship">
            <div class="detail-row-1">
                <div class="row-1-item locations">
                    <span><a>Bangalore</a></span>
                </div>
                <div class="row-1-item">
                    <span class='stipend'>INR 25000 /month</span>
                </div>
                <div class="row-1-item">
                    <span>6 Months</span>
                </div>
            </div>
            <div class="job_skills">
                <div class='skill_container'><div class='job_skill'>Python</div></div>
                <div class='skill_container'><div class='job_skill'>SQL</div></div>
            </div>
        </div>
    </div>
</div>
<div class="container-fluid individual_internship logged_out_jd_summary" id="individual_internship_67890" internshipId="67890" data-href='/internship/detail/data-science-intern-67890'>
    <div class="internship_meta duration_meta">
        <div class="internship-heading-container">
            <div class="company generic_company">
                <div class='generic_container'>
                    <h2 class="job-internship-name">
                        <a class="job-title-href" href="/internship/detail/data-science-intern-67890">Data Science Intern</a>
                    </h2>
                </div>
                <p class="company-name">StartupXYZ</p>
            </div>
        </div>
        <div class="individual_internship_details individual_internship_internship">
            <div class="detail-row-1">
                <div class="row-1-item locations">
                    <span><a>Work From Home</a></span>
                </div>
                <div class="row-1-item">
                    <span class='stipend'>INR 15000 /month</span>
                </div>
                <div class="row-1-item">
                    <span>3 Months</span>
                </div>
            </div>
            <div class="job_skills">
                <div class='skill_container'><div class='job_skill'>Python</div></div>
                <div class='skill_container'><div class='job_skill'>Machine Learning</div></div>
            </div>
        </div>
    </div>
</div>
</body></html>
"""


def _build_luma_html(page_data):
    import json as _json
    json_str = _json.dumps(page_data)
    return f"""
<html><head>
<script id="__NEXT_DATA__" type="application/json">{json_str}</script>
</head><body></body></html>
"""


class TestLumaScraper:
    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_returns_non_expired_events(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = _build_luma_html(SAMPLE_LUMA_PAGE)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = LumaScraper()
        results = scraper.scrape()

        assert len(results) == 2
        titles = [r.title for r in results]
        assert "AI Builder Night SF" in titles
        assert "Crypto Hack Week" in titles
        assert "Past Event" not in titles

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_parses_correct_fields(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = _build_luma_html(SAMPLE_LUMA_PAGE)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = LumaScraper()
        results = scraper.scrape()

        sf_event = [r for r in results if r.title == "AI Builder Night SF"][0]
        assert sf_event.source == Source.LUMA
        assert sf_event.category == Category.OTHER
        assert sf_event.url == "https://lu.ma/ai-builder-night-sf"
        assert sf_event.location == "San Francisco, CA"
        assert sf_event.format == "in-person"
        assert sf_event.organizer == "Luma"

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_extracts_tags(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = _build_luma_html(SAMPLE_LUMA_PAGE)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = LumaScraper()
        results = scraper.scrape()

        sf_event = [r for r in results if r.title == "AI Builder Night SF"][0]
        assert "AI" in sf_event.tags
        assert "Machine Learning" in sf_event.tags

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_extracts_domain(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = _build_luma_html(SAMPLE_LUMA_PAGE)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = LumaScraper()
        results = scraper.scrape()

        sf_event = [r for r in results if r.title == "AI Builder Night SF"][0]
        assert "machine-learning" in sf_event.domain

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_marks_paid_events(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = _build_luma_html(SAMPLE_LUMA_PAGE)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = LumaScraper()
        results = scraper.scrape()

        crypto = [r for r in results if r.title == "Crypto Hack Week"][0]
        assert "Paid event" in crypto.eligibility

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_parses_description_html(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = _build_luma_html(SAMPLE_LUMA_PAGE)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = LumaScraper()
        results = scraper.scrape()

        sf_event = [r for r in results if r.title == "AI Builder Night SF"][0]
        assert "Build AI projects" in sf_event.description

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_returns_empty_when_no_next_data(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = "<html><body>no data</body></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = LumaScraper()
        results = scraper.scrape()
        assert results == []

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_handles_malformed_json(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = '<script id="__NEXT_DATA__">NOT JSON</script>'
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = LumaScraper()
        results = scraper.scrape()
        assert results == []

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_skips_events_without_name(self, mock_get):
        page = {
            "props": {
                "pageProps": {
                    "featuredEvents": [
                        {"name": "", "slug": "x", "end_at": "2026-12-01T00:00:00Z"},
                        {"slug": "y", "end_at": "2026-12-01T00:00:00Z"},
                    ]
                }
            }
        }
        mock_resp = MagicMock()
        mock_resp.text = _build_luma_html(page)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = LumaScraper()
        results = scraper.scrape()
        assert results == []


class TestInternshalaScraper:
    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_returns_internships(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_INTERNSHALA_PAGE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = InternshalaScraper()
        results = scraper.scrape()

        assert len(results) == 2
        titles = [r.title for r in results]
        assert "Software Development Intern" in titles
        assert "Data Science Intern" in titles

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_parses_correct_fields(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_INTERNSHALA_PAGE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = InternshalaScraper()
        results = scraper.scrape()

        sw_intern = [r for r in results if r.title == "Software Development Intern"][0]
        assert sw_intern.source == Source.INTERNSHALA
        assert sw_intern.category == Category.INTERNSHIP
        assert sw_intern.location == "Bangalore"
        assert "Google India" in sw_intern.description

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_extracts_skills(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_INTERNSHALA_PAGE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = InternshalaScraper()
        results = scraper.scrape()

        sw_intern = [r for r in results if r.title == "Software Development Intern"][0]
        assert "Python" in sw_intern.skills_required
        assert "SQL" in sw_intern.skills_required

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_infers_online_from_work_from_home(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_INTERNSHALA_PAGE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = InternshalaScraper()
        results = scraper.scrape()

        ds_intern = [r for r in results if r.title == "Data Science Intern"][0]
        assert ds_intern.format == "online"
        assert "online" in ds_intern.tags

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_extracts_domain(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_INTERNSHALA_PAGE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = InternshalaScraper()
        results = scraper.scrape()

        ds_intern = [r for r in results if r.title == "Data Science Intern"][0]
        assert "machine-learning" in ds_intern.domain

    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_handles_empty_page(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = "<html><body></body></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        scraper = InternshalaScraper()
        results = scraper.scrape()
        assert results == []


class TestUnstopScraper:
    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_raises_runtime_error(self, mock_get):
        scraper = UnstopScraper()
        try:
            scraper.scrape()
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "Angular SPA" in str(e)


class TestHackCultureScraper:
    @patch("src.scrapers.base.requests.Session.get")
    def test_scrape_raises_runtime_error(self, mock_get):
        scraper = HackCultureScraper()
        try:
            scraper.scrape()
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "B2B" in str(e)


class TestScannerNewSources:
    @patch("src.scanner.HackCultureScraper.scrape")
    @patch("src.scanner.UnstopScraper.scrape")
    @patch("src.scanner.InternshalaScraper.scrape")
    @patch("src.scanner.LumaScraper.scrape")
    @patch("src.scanner.MLHScraper.scrape")
    @patch("src.scanner.DevpostScraper.scrape")
    def test_all_six_sources_called(self, mock_devpost, mock_mlh, mock_luma, mock_intern, mock_unstop, mock_hack):
        mock_devpost.return_value = []
        mock_mlh.return_value = []
        mock_luma.return_value = []
        mock_intern.return_value = []
        mock_unstop.side_effect = RuntimeError("unavailable")
        mock_hack.side_effect = RuntimeError("unavailable")

        scanner = Scanner()
        results = scanner.scan()

        assert results == []
        assert mock_devpost.called
        assert mock_mlh.called
        assert mock_luma.called
        assert mock_intern.called
        assert mock_unstop.called
        assert mock_hack.called

    @patch("src.scanner.HackCultureScraper.scrape")
    @patch("src.scanner.UnstopScraper.scrape")
    @patch("src.scanner.InternshalaScraper.scrape")
    @patch("src.scanner.LumaScraper.scrape")
    @patch("src.scanner.MLHScraper.scrape")
    @patch("src.scanner.DevpostScraper.scrape")
    def test_stub_failures_recorded_as_errors(self, mock_devpost, mock_mlh, mock_luma, mock_intern, mock_unstop, mock_hack):
        mock_devpost.return_value = []
        mock_mlh.return_value = []
        mock_luma.return_value = []
        mock_intern.return_value = []
        mock_unstop.side_effect = RuntimeError("Angular SPA")
        mock_hack.side_effect = RuntimeError("B2B")

        scanner = Scanner()
        scanner.scan()

        assert not scanner.source_statuses["UnstopScraper"].ok
        assert "Angular SPA" in scanner.source_statuses["UnstopScraper"].error
        assert not scanner.source_statuses["HackCultureScraper"].ok
        assert "B2B" in scanner.source_statuses["HackCultureScraper"].error

    @patch("src.scanner.HackCultureScraper.scrape")
    @patch("src.scanner.UnstopScraper.scrape")
    @patch("src.scanner.InternshalaScraper.scrape")
    @patch("src.scanner.LumaScraper.scrape")
    @patch("src.scanner.MLHScraper.scrape")
    @patch("src.scanner.DevpostScraper.scrape")
    def test_merges_opps_from_all_working_sources(self, mock_devpost, mock_mlh, mock_luma, mock_intern, mock_unstop, mock_hack):
        from src.models import Opportunity

        opp1 = Opportunity(title="Devpost Hack", url="https://d.com", source=Source.DEVPOST)
        opp2 = Opportunity(title="Luma Event", url="https://lu.ma/x", source=Source.LUMA)
        opp3 = Opportunity(title="Internship", url="https://i.com", source=Source.INTERNSHALA)
        mock_devpost.return_value = [opp1]
        mock_mlh.return_value = []
        mock_luma.return_value = [opp2]
        mock_intern.return_value = [opp3]
        mock_unstop.side_effect = RuntimeError("unavailable")
        mock_hack.side_effect = RuntimeError("unavailable")

        scanner = Scanner()
        results = scanner.scan()

        titles = [r.title for r in results]
        assert "Devpost Hack" in titles
        assert "Luma Event" in titles
        assert "Internship" in titles
        assert len(results) == 3
