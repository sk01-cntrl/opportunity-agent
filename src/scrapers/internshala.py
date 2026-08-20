import re
from typing import List

from src.models import Category, Opportunity, Source
from src.normalize import extract_domains, normalize_format
from src.scrapers.base import BaseScraper


class InternshalaScraper(BaseScraper):
    """Scrapes internship listings from Internshala's HTML pages."""

    BASE_URL = "https://internshala.com/internships"

    def scrape(self) -> List[Opportunity]:
        opps = []
        url = self.BASE_URL
        for _ in range(3):
            resp = self.fetch(url)
            page_opps = self._parse_list_page(resp.text)
            opps.extend(page_opps)
            next_url = self._find_next_page(resp.text)
            if not next_url:
                break
            url = next_url
        return opps

    def _parse_list_page(self, html: str) -> List[Opportunity]:
        opps = []
        parts = re.split(r'(?=id="individual_internship_\d+")', html)
        for part in parts:
            if not re.match(r'id="individual_internship_\d+"', part):
                continue
            opp = self._parse_card(part)
            if opp:
                opps.append(opp)
        return opps

    def _parse_card(self, card_html: str) -> Opportunity | None:
        title_match = re.search(
            r'<a\s+class="job-title-href"[^>]*href="([^"]*)"[^>]*>\s*(.*?)\s*</a>',
            card_html,
            re.DOTALL,
        )
        if not title_match:
            return None
        href = title_match.group(1)
        title = re.sub(r"<[^>]+>", "", title_match.group(2)).strip()
        if not title:
            return None

        url = href if href.startswith("http") else f"https://internshala.com{href}"

        company_match = re.search(
            r'<p\s+class="company-name">\s*(.*?)\s*</p>',
            card_html,
            re.DOTALL,
        )
        company = re.sub(r"<[^>]+>", "", company_match.group(1)).strip() if company_match else ""

        location_match = re.search(
            r'<div\s+class="[^"]*locations[^"]*"[^>]*>.*?<a>(.*?)</a>',
            card_html,
            re.DOTALL,
        )
        location = re.sub(r"<[^>]+>", "", location_match.group(1)).strip() if location_match else ""

        stipend = ""
        stipend_match = re.search(
            r"<span\s+class='stipend'>(.*?)</span>",
            card_html,
            re.DOTALL,
        )
        if stipend_match:
            stipend = re.sub(r"<[^>]+>", "", stipend_match.group(1)).strip()

        duration = ""
        duration_match = re.search(
            r'<div\s+class="row-1-item">\s*<i[^>]*ic-16-calendar[^>]*></i>\s*<span>(.*?)</span>',
            card_html,
            re.DOTALL,
        )
        if duration_match:
            duration = re.sub(r"<[^>]+>", "", duration_match.group(1)).strip()

        skills = []
        for skill_match in re.finditer(
            r"<div\s+class='job_skill'>(.*?)</div>",
            card_html,
            re.DOTALL,
        ):
            skill = re.sub(r"<[^>]+>", "", skill_match.group(1)).strip()
            if skill:
                skills.append(skill)

        tags = skills[:]
        if "work from home" in location.lower() or "remote" in location.lower():
            tags.append("online")
            fmt = "online"
        else:
            fmt = normalize_format(location) if location else ""

        domain = extract_domains(tags)

        description_parts = []
        if company:
            description_parts.append(f"Company: {company}")
        if stipend:
            description_parts.append(f"Stipend: {stipend}")
        if duration:
            description_parts.append(f"Duration: {duration}")

        category = self._infer_category(title, tags)

        return Opportunity(
            title=title,
            url=url,
            source=Source.INTERNSHALA,
            category=category,
            description="; ".join(description_parts),
            location=location,
            tags=tags,
            skills_required=skills,
            format=fmt,
            domain=domain,
        )

    def _infer_category(self, title: str, tags: List[str]) -> Category:
        combined = (title + " " + " ".join(tags)).lower()
        if any(w in combined for w in ["hackathon", "hack"]):
            return Category.HACKATHON
        if any(w in combined for w in ["internship", "intern"]):
            return Category.INTERNSHIP
        if any(w in combined for w in ["competition", "contest", "challenge"]):
            return Category.COMPETITION
        return Category.INTERNSHIP

    def _find_next_page(self, html: str) -> str | None:
        match = re.search(r'"next_url"\s*:\s*"([^"]+)"', html)
        if match:
            url = match.group(1)
            if url.startswith("/"):
                return f"https://internshala.com{url}"
            return url
        return None
