from typing import List

from src.models import Opportunity
from src.scrapers.base import BaseScraper


class HackCultureScraper(BaseScraper):
    """Stub: HackCulture is a B2B corporate innovation platform.

    HackCulture runs private, invite-only innovation programs for enterprises.
    There are no public event listings or scrapable data. The public-facing
    site only describes their B2B services.
    """

    def scrape(self) -> List[Opportunity]:
        raise RuntimeError(
            "HackCulture is unavailable: B2B corporate innovation platform "
            "with no public event listings"
        )
