from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class Category(Enum):
    HACKATHON = "hackathon"
    INTERNSHIP = "internship"
    COMPETITION = "competition"
    OTHER = "other"


class Source(Enum):
    DEVPOST = "devpost"
    MLH = "mlh"
    LUMA = "luma"
    INTERNSHALA = "internshala"
    UNSTOP = "unstop"
    HACKCULTURE = "hackculture"
    UNKNOWN = "unknown"


@dataclass
class Opportunity:
    title: str
    url: str
    source: Source
    category: Category = Category.OTHER
    description: str = ""
    deadline: Optional[datetime] = None
    location: str = ""
    tags: List[str] = None
    skills_required: List[str] = None
    team_size_range: str = ""
    experience_level: str = ""
    format: str = ""
    domain: List[str] = None
    prize_info: str = ""
    eligibility: str = ""
    organizer: str = ""
    registrations_count: int = 0

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.skills_required is None:
            self.skills_required = []
        if self.domain is None:
            self.domain = []

    def to_dict(self) -> dict:
        d = asdict(self)
        d["source"] = self.source.value
        d["category"] = self.category.value
        if self.deadline:
            d["deadline"] = self.deadline.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Opportunity":
        data["source"] = Source(data["source"])
        data["category"] = Category(data["category"])
        if data.get("deadline"):
            data["deadline"] = datetime.fromisoformat(data["deadline"])
        else:
            data["deadline"] = None
        return cls(**data)
