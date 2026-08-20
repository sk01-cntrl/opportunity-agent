import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.models import Opportunity
from src.deduper import deduplicate
from src.scrapers.devpost import DevpostScraper
from src.scrapers.mlh import MLHScraper
from src.scrapers.luma import LumaScraper
from src.scrapers.internshala import InternshalaScraper
from src.scrapers.unstop import UnstopScraper
from src.scrapers.hackculture import HackCultureScraper


@dataclass
class SourceStatus:
    name: str
    count: int = 0
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return not self.error

    def __str__(self) -> str:
        if self.error:
            return f"{self.name}: ERROR - {self.error}"
        return f"{self.name}: {self.count} found"


class Scanner:
    """Runs all scrapers, filters expired, and deduplicates results."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.source_statuses: Dict[str, SourceStatus] = {}
        os.makedirs(self.output_dir, exist_ok=True)

    def scan(self) -> List[Opportunity]:
        all_opps = []
        for ScraperClass in [DevpostScraper, MLHScraper, LumaScraper, InternshalaScraper, UnstopScraper, HackCultureScraper]:
            name = ScraperClass.__name__
            try:
                scraper = ScraperClass()
                results = scraper.scrape()
                status = SourceStatus(name=name, count=len(results))
                print(f"  {status}")
                all_opps.extend(results)
            except Exception as e:
                status = SourceStatus(name=name, error=str(e))
                print(f"  {status}")
            self.source_statuses[name] = status
        alive = self._filter_expired(all_opps)
        deduped = deduplicate(alive)
        return deduped

    def _filter_expired(self, opps: List[Opportunity]) -> List[Opportunity]:
        now = datetime.now(tz=timezone.utc)
        result = []
        for opp in opps:
            if opp.deadline:
                dl = opp.deadline
                if dl.tzinfo is None:
                    dl = dl.replace(tzinfo=timezone.utc)
                if dl < now:
                    continue
            result.append(opp)
        return result

    def save(self, opportunities: List[Opportunity]) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"opportunities_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        data = [opp.to_dict() for opp in opportunities]
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nSaved {len(data)} opportunities to {filepath}")
        return filepath
