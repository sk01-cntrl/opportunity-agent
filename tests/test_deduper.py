from src.models import Category, Opportunity, Source
from src.deduper import deduplicate


def _make_opp(title, url="https://example.com", description="", tags=None):
    return Opportunity(
        title=title,
        url=url,
        source=Source.DEVPOST,
        category=Category.HACKATHON,
        description=description,
        tags=tags or [],
    )


def test_dedup_same_title_same_source():
    a = _make_opp("Hack 2026")
    b = _make_opp("Hack 2026")
    result = deduplicate([a, b])
    assert len(result) == 1


def test_dedup_same_title_different_source():
    a = Opportunity(
        title="Hack 2026",
        url="https://devpost.com/hack",
        source=Source.DEVPOST,
        category=Category.HACKATHON,
    )
    b = Opportunity(
        title="Hack 2026",
        url="https://mlh.io/hack",
        source=Source.MLH,
        category=Category.HACKATHON,
    )
    result = deduplicate([a, b])
    assert len(result) == 1


def test_dedup_different_titles():
    a = _make_opp("Hack A", url="https://example.com/a")
    b = _make_opp("Hack B", url="https://example.com/b")
    result = deduplicate([a, b])
    assert len(result) == 2


def test_dedup_same_url():
    a = _make_opp("Hack A", url="https://example.com/event?ref=1")
    b = _make_opp("Hack B", url="https://example.com/event?ref=2")
    result = deduplicate([a, b])
    assert len(result) == 1


def test_dedup_keeps_richer_entry():
    poor = _make_opp("Hack 2026", description="")
    rich = _make_opp("Hack 2026", description="Great prizes!", tags=["ai", "web"])
    result = deduplicate([poor, rich])
    assert len(result) == 1
    assert result[0].description == "Great prizes!"


def test_dedup_preserves_order_of_unique():
    a = _make_opp("Alpha", url="https://example.com/alpha")
    b = _make_opp("Beta", url="https://example.com/beta")
    c = _make_opp("Gamma", url="https://example.com/gamma")
    result = deduplicate([a, b, c])
    assert [r.title for r in result] == ["Alpha", "Beta", "Gamma"]


def test_dedup_title_with_year_variants():
    a = _make_opp("HackPrix Season 3")
    b = _make_opp("HackPrix Season 3 2026")
    result = deduplicate([a, b])
    assert len(result) == 1
