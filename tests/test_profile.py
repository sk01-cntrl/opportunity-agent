import json
import os
import pytest
from src.profile import Profile, load_profile, load_profile_from_dict


def test_load_default_profile():
    p = load_profile()
    assert "python" in p.skills
    assert "sql" in p.skills
    assert "artificial intelligence" in p.interests
    assert p.experience_level == "beginner"
    assert "online" in p.preferred_formats
    assert "hackathon" in p.preferred_categories
    assert p.location_preference == "india-or-online"
    assert "paid-entry" in p.excluded_tags


def test_load_from_dict():
    p = load_profile_from_dict({
        "skills": ["python", "ML"],
        "interests": ["ai", "social good"],
        "experience_level": "intermediate",
        "preferred_formats": ["online", "in-person"],
        "preferred_categories": ["hackathon"],
        "location_preference": "any",
        "excluded_tags": ["blockchain"],
    })
    assert p.skills == ["python", "ml"]
    assert p.interests == ["ai", "social good"]
    assert p.experience_level == "intermediate"
    assert p.preferred_formats == ["online", "in-person"]
    assert p.excluded_tags == ["blockchain"]


def test_load_from_file(tmp_path):
    data = {
        "skills": ["rust"],
        "interests": ["web"],
        "experience_level": "beginner",
        "preferred_formats": ["online"],
        "preferred_categories": ["hackathon"],
        "location_preference": "online-only",
        "excluded_tags": [],
    }
    path = tmp_path / "test_profile.json"
    path.write_text(json.dumps(data))
    p = load_profile(str(path))
    assert p.skills == ["rust"]
    assert p.location_preference == "online-only"


def test_invalid_experience_level():
    with pytest.raises(ValueError, match="Invalid experience_level"):
        load_profile_from_dict({"experience_level": "expert"})


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_profile("/nonexistent/path.json")


def test_profile_normalizes_lowercase():
    p = load_profile_from_dict({
        "skills": ["Python", "TypeScript"],
        "interests": ["AI", "Web3"],
        "preferred_formats": ["Online"],
    })
    assert p.skills == ["python", "typescript"]
    assert p.interests == ["ai", "web3"]
    assert p.preferred_formats == ["online"]
