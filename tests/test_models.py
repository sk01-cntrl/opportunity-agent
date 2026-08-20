from datetime import datetime

from src.models import Category, Opportunity, Source


def test_opportunity_creation():
    opp = Opportunity(
        title="Test Hackathon",
        url="https://example.com",
        source=Source.DEVPOST,
        category=Category.HACKATHON,
    )
    assert opp.title == "Test Hackathon"
    assert opp.source == Source.DEVPOST
    assert opp.category == Category.HACKATHON
    assert opp.tags == []


def test_opportunity_to_dict():
    opp = Opportunity(
        title="Test",
        url="https://example.com",
        source=Source.MLH,
        deadline=datetime(2026, 6, 15),
    )
    d = opp.to_dict()
    assert d["title"] == "Test"
    assert d["source"] == "mlh"
    assert d["deadline"] == "2026-06-15T00:00:00"
    assert isinstance(d["tags"], list)


def test_opportunity_from_dict():
    data = {
        "title": "HackIt",
        "url": "https://hackit.dev",
        "source": "devpost",
        "category": "competition",
        "description": "",
        "deadline": "2026-03-01T00:00:00",
        "location": "Online",
        "tags": ["AI"],
    }
    opp = Opportunity.from_dict(data)
    assert opp.title == "HackIt"
    assert opp.source == Source.DEVPOST
    assert opp.category == Category.COMPETITION
    assert opp.deadline == datetime(2026, 3, 1)
    assert opp.location == "Online"


def test_opportunity_roundtrip():
    opp = Opportunity(
        title="Roundtrip",
        url="https://rt.dev",
        source=Source.DEVPOST,
        category=Category.HACKATHON,
        deadline=datetime(2026, 9, 1),
        tags=["web", "AI"],
    )
    d = opp.to_dict()
    opp2 = Opportunity.from_dict(d)
    assert opp2.title == opp.title
    assert opp2.source == opp.source
    assert opp2.deadline == opp.deadline
    assert opp2.tags == opp.tags
