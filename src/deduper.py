import re
from typing import List
from urllib.parse import urlparse

from src.models import Opportunity
from src.normalize import normalize_title


def deduplicate(opportunities: List[Opportunity]) -> List[Opportunity]:
    seen_titles = {}
    seen_urls = {}
    result = []
    for opp in opportunities:
        key_title = normalize_title(opp.title)
        key_url = _normalize_url(opp.url)
        if key_title in seen_titles or key_url in seen_urls:
            existing = seen_titles.get(key_title) or seen_urls.get(key_url)
            if existing and _prefer(opp, existing):
                result = [o for o in result if o is not existing]
                result.append(opp)
                if key_title:
                    seen_titles[key_title] = opp
                if key_url:
                    seen_urls[key_url] = opp
            continue
        result.append(opp)
        if key_title:
            seen_titles[key_title] = opp
        if key_url:
            seen_urls[key_url] = opp
    return result


def _normalize_url(url: str) -> str:
    try:
        p = urlparse(url)
        path = p.path.rstrip("/")
        return f"{p.netloc}{path}".lower()
    except Exception:
        return url.lower().strip()


def _prefer(a: Opportunity, b: Opportunity) -> bool:
    a_score = _richness(a)
    b_score = _richness(b)
    if a_score != b_score:
        return a_score > b_score
    return False


def _richness(opp: Opportunity) -> int:
    score = 0
    if opp.description:
        score += 2
    if opp.skills_required:
        score += 2
    if opp.location:
        score += 1
    if len(opp.tags) > 1:
        score += 1
    if opp.deadline:
        score += 1
    return score
