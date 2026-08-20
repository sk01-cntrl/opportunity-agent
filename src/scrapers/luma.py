import json
import re
from datetime import datetime, timezone
from typing import List

from src.models import Category, Opportunity, Source
from src.normalize import extract_domains, normalize_format
from src.scrapers.base import BaseScraper


class LumaScraper(BaseScraper):
    """Scrapes tech events from Luma via __NEXT_DATA__ JSON on category pages."""

    BASE_URL = "https://lu.ma/tech"

    def scrape(self) -> List[Opportunity]:
        resp = self.fetch(self.BASE_URL)
        events = self._extract_events(resp.text)
        now = datetime.now(tz=timezone.utc)
        return [opp for opp in (self._parse(e, now) for e in events) if opp]

    def _extract_events(self, html: str) -> list:
        match = re.search(
            r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        )
        if not match:
            return []
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []
        props = data.get("props", {}).get("pageProps", {})
        return props.get("featuredEvents", [])

    def _parse(self, event: dict, now: datetime) -> Opportunity | None:
        name = event.get("name", "").strip()
        if not name:
            return None

        slug = event.get("slug", "")
        url = f"https://lu.ma/{slug}" if slug else ""

        ends_at = event.get("end_at", "")
        deadline = None
        if ends_at:
            try:
                deadline = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        if deadline and deadline < now:
            return None

        location = ""
        geo = event.get("geo_address_json", {})
        if isinstance(geo, dict):
            location = geo.get("address", "") or ""
        if not location:
            geo_type = event.get("location_type", "")
            if geo_type == "online":
                location = "Online"
            else:
                location = ""

        tags = []
        for topic in event.get("topics", []):
            if isinstance(topic, dict):
                tags.append(topic.get("name", ""))
            elif isinstance(topic, str):
                tags.append(topic)
        tags = [t for t in tags if t]

        geo_type = event.get("location_type", "")
        if geo_type:
            tags.append(geo_type)

        fmt = normalize_format(geo_type) if geo_type else ""

        organizer = ""
        cal = event.get("calendar", {})
        if isinstance(cal, dict):
            organizer = cal.get("name", "")

        domain = extract_domains(tags)

        paid = event.get("paid_ticket", False)
        eligibility = "Paid event" if paid else ""

        description = ""
        if event.get("description"):
            raw = event["description"]
            cleaned = re.sub(r"<[^>]+>", "", raw)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            if len(cleaned) > 300:
                cleaned = cleaned[:300] + "..."
            description = cleaned

        return Opportunity(
            title=name,
            url=url,
            source=Source.LUMA,
            category=Category.OTHER,
            description=description,
            deadline=deadline,
            location=location,
            tags=tags,
            format=fmt,
            domain=domain,
            organizer=organizer,
            eligibility=eligibility,
        )
