from abc import ABC, abstractmethod
from typing import List

import requests

from src.models import Opportunity


class BaseScraper(ABC):
    """Abstract base class for all opportunity scrapers."""

    BASE_URL: str = ""
    TIMEOUT: int = 15
    HEADERS: dict = {
        "User-Agent": "OpportunityScout/1.0 (respectful-scraper)"
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def fetch(self, url: str) -> requests.Response:
        response = self.session.get(url, timeout=self.TIMEOUT)
        response.raise_for_status()
        return response

    @abstractmethod
    def scrape(self) -> List[Opportunity]:
        """Return a list of opportunities from this source."""
        ...
