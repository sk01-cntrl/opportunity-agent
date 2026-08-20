import json
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Profile:
    skills: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    experience_level: str = "beginner"
    preferred_formats: List[str] = field(default_factory=lambda: ["online"])
    preferred_categories: List[str] = field(
        default_factory=lambda: ["hackathon", "internship"]
    )
    location_preference: str = "any"
    excluded_tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.skills = [s.lower().strip() for s in self.skills]
        self.interests = [i.lower().strip() for i in self.interests]
        self.experience_level = self.experience_level.lower().strip()
        self.preferred_formats = [f.lower().strip() for f in self.preferred_formats]
        self.preferred_categories = [
            c.lower().strip() for c in self.preferred_categories
        ]
        self.location_preference = self.location_preference.lower().strip()
        self.excluded_tags = [t.lower().strip() for t in self.excluded_tags]


VALID_EXPERIENCE_LEVELS = {"beginner", "intermediate", "advanced", "all"}


def load_profile(path: str | None = None) -> Profile:
    if path is None:
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "profiles",
            "default.json",
        )
    if not os.path.exists(path):
        raise FileNotFoundError(f"Profile not found: {path}")
    with open(path) as f:
        data = json.load(f)
    return _build(data)


def load_profile_from_dict(data: dict) -> Profile:
    return _build(data)


def _build(data: dict) -> Profile:
    level = data.get("experience_level", "beginner")
    if level not in VALID_EXPERIENCE_LEVELS:
        raise ValueError(
            f"Invalid experience_level '{level}'. "
            f"Must be one of: {', '.join(sorted(VALID_EXPERIENCE_LEVELS))}"
        )
    return Profile(
        skills=data.get("skills", []),
        interests=data.get("interests", []),
        experience_level=level,
        preferred_formats=data.get("preferred_formats", ["online"]),
        preferred_categories=data.get("preferred_categories", ["hackathon"]),
        location_preference=data.get("location_preference", "any"),
        excluded_tags=data.get("excluded_tags", []),
    )
