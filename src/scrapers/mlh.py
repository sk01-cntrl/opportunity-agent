import json
import re
from datetime import datetime, timezone
from typing import List

from src.models import Category, Opportunity, Source
from src.normalize import normalize_format, extract_domains
from src.scrapers.base import BaseScraper


class MLHScraper(BaseScraper):
    """Scrapes hackathons from MLH's public season page via embedded JSON."""

    BASE_URL = "https://www.mlh.io/seasons/2026/events"

    def scrape(self) -> List[Opportunity]:
        resp = self.fetch(self.BASE_URL)
        events_data = self._extract_json(resp.text)
        now = datetime.now(tz=timezone.utc)
        opportunities = []
        for event in events_data:
            opp = self._parse(event, now)
            if opp:
                opportunities.append(opp)
        return opportunities

    def _extract_json(self, html: str) -> list:
        match = re.search(
            r'<script[^>]*data-page="app"[^>]*type="application/json"[^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        )
        if not match:
            return []
        try:
            page = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []
        props = page.get("props", {})
        past = props.get("pastEvents", [])
        upcoming = props.get("upcomingEvents", [])
        return past + upcoming

    def _parse(self, event: dict, now: datetime) -> Opportunity | None:
        name = event.get("name", "").strip()
        if not name:
            return None

        status = event.get("status", "")
        if status == "ended":
            return None

        deadline = None
        ends_at = event.get("endsAt")
        if ends_at:
            try:
                deadline = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        if deadline and deadline < now:
            return None

        url = event.get("websiteUrl") or event.get("url", "")
        if url and not url.startswith("http"):
            url = f"https://www.mlh.io{url}"

        location = event.get("location", "")
        venue = event.get("venueAddress", {})
        if isinstance(venue, dict):
            city = venue.get("city", "")
            country = venue.get("country", "")
            if city and country:
                location = f"{city}, {country}"
            elif city:
                location = city

        tags = []
        format_type = event.get("formatType", "")
        if format_type == "digital":
            tags.append("digital")
        elif format_type == "hybrid_physical":
            tags.append("hybrid")
        else:
            tags.append("in-person")

        region = event.get("region")
        if region:
            tags.append(region)

        custom = event.get("customFields", {})
        underserved = custom.get("underserved_types", [])
        for ut in underserved:
            tags.append(ut)

        fmt = normalize_format(format_type) if format_type else ""
        domain = extract_domains(tags)

        eligibility_parts = []
        for ut in underserved:
            eligibility_parts.append(ut)
        eligibility = "; ".join(eligibility_parts)

        return Opportunity(
            title=name,
            url=url,
            source=Source.MLH,
            category=Category.HACKATHON,
            location=location,
            deadline=deadline,
            tags=tags,
            format=fmt,
            domain=domain,
            eligibility=eligibility,
        )
