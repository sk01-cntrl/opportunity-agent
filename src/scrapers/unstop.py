from typing import List

from src.models import Opportunity
from src.scrapers.base import BaseScraper


class UnstopScraper(BaseScraper):
    """Stub: Unstop requires JavaScript rendering and blocks scrapers.

    Unstop is a single-page Angular application. All API calls return 404 or
    require browser cookies/JS. robots.txt explicitly disallows scraper bots.
    No public data source is available without a headless browser.
    """

    def scrape(self) -> List[Opportunity]:
        raise RuntimeError(
            "Unstop is unavailable: Angular SPA with no public API, "
            "robots.txt blocks scrapers, requires headless browser"
        )
