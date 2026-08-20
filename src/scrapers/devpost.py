import re
from datetime import datetime
from typing import List

from src.models import Category, Opportunity, Source
from src.normalize import (
    extract_domains,
    extract_experience_level,
    extract_skills,
    normalize_format,
    clean_prize_html,
)
from src.scrapers.base import BaseScraper


def _try_parse_date(s: str) -> datetime | None:
    for fmt in ("%b %d %Y", "%B %d %Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


class DevpostScraper(BaseScraper):
    """Scrapes hackathons from Devpost's public JSON API."""

    BASE_URL = "https://devpost.com/api/hackathons"

    def scrape(self, max_pages: int = 3) -> List[Opportunity]:
        opportunities = []
        for page in range(1, max_pages + 1):
            url = f"{self.BASE_URL}?page={page}"
            data = self.fetch(url).json()
            hackathons = data.get("hackathons", [])
            if not hackathons:
                break
            for h in hackathons:
                opp = self._parse(h)
                if opp:
                    opportunities.append(opp)
        return opportunities

    def _parse(self, h: dict) -> Opportunity | None:
        title = h.get("title", "").strip()
        if not title:
            return None

        url = h.get("url", "")
        location = ""
        displayed = h.get("displayed_location", {})
        if isinstance(displayed, dict):
            location = displayed.get("location", "")

        open_state = h.get("open_state", "")
        if open_state == "ended":
            return None

        tags = []
        for theme in h.get("themes", []):
            if isinstance(theme, dict):
                tags.append(theme.get("name", ""))
            elif isinstance(theme, str):
                tags.append(theme)
        tags = [t for t in tags if t]

        deadline = self._parse_deadline(h)

        prize_raw = h.get("prize_amount", "")
        prize_clean = clean_prize_html(prize_raw)
        prizes_counts = h.get("prizes_counts", {})
        cash_count = prizes_counts.get("cash", 0) if isinstance(prizes_counts, dict) else 0
        other_count = prizes_counts.get("other", 0) if isinstance(prizes_counts, dict) else 0
        prize_parts = []
        if prize_clean:
            prize_parts.append(f"${prize_clean}")
        if cash_count:
            prize_parts.append(f"{cash_count} cash prize{'s' if cash_count > 1 else ''}")
        if other_count:
            prize_parts.append(f"{other_count} other prize{'s' if other_count > 1 else ''}")
        prize_info = ", ".join(prize_parts)

        registrations = h.get("registrations_count", 0)
        if not isinstance(registrations, int):
            registrations = 0

        organizer = h.get("organization_name", "")
        if not isinstance(organizer, str):
            organizer = ""

        invite_only = h.get("invite_only", False)
        eligibility_parts = []
        if invite_only:
            eligibility_parts.append("Invite only")
        eligibility = "; ".join(eligibility_parts)

        fmt = normalize_format(location)
        domain = extract_domains(tags)
        skills = extract_skills(tags)
        exp_level = extract_experience_level(tags)

        description_parts = []
        if prize_info:
            description_parts.append(f"Prizes: {prize_info}")
        if registrations:
            description_parts.append(f"{registrations:,} registered")

        return Opportunity(
            title=title,
            url=url,
            source=Source.DEVPOST,
            category=Category.HACKATHON,
            description="; ".join(description_parts),
            deadline=deadline,
            location=location,
            tags=tags,
            skills_required=skills,
            experience_level=exp_level,
            format=fmt,
            domain=domain,
            prize_info=prize_info,
            eligibility=eligibility,
            organizer=organizer,
            registrations_count=registrations,
        )

    def _parse_deadline(self, h: dict) -> datetime | None:
        submission = h.get("submission_period_dates", "")
        if not submission:
            return None
        match = re.search(r"(\w+ \d{1,2}),?\s*(\d{4})", submission)
        if match:
            result = _try_parse_date(f"{match.group(1)} {match.group(2)}")
            if result:
                return result
        match = re.search(r"(\w+ \d{1,2})\s*-\s*(\w+ \d{1,2}),?\s*(\d{4})", submission)
        if match:
            result = _try_parse_date(f"{match.group(2)} {match.group(3)}")
            if result:
                return result
        return None
