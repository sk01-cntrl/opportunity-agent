from datetime import datetime, timedelta, timezone

from src.models import Category, Opportunity, Source
from src.profile import Profile
from src.scorer import (
    score,
    _score_tags,
    _score_category,
    _score_format,
    _score_deadline,
    _score_location,
    _score_experience,
    _detect_fee_status,
    _apply_excluded_tags,
)


def _make_opp(**kwargs):
    defaults = {
        "title": "Test Hack",
        "url": "https://example.com",
        "source": Source.DEVPOST,
        "category": Category.HACKATHON,
        "tags": [],
        "format": "",
        "experience_level": "",
    }
    defaults.update(kwargs)
    return Opportunity(**defaults)


def _make_profile(**kwargs):
    defaults = {
        "skills": [],
        "interests": [],
        "experience_level": "beginner",
        "preferred_formats": ["online"],
        "preferred_categories": ["hackathon"],
        "location_preference": "any",
        "excluded_tags": [],
    }
    defaults.update(kwargs)
    return Profile(**defaults)


def test_scoring_empty_profile():
    opp = _make_opp(tags=["python", "web"])
    profile = _make_profile(preferred_categories=["competition"])
    tag_score, _ = _score_tags(opp, profile)
    assert tag_score == 0.0


def test_scoring_tag_match():
    opp = _make_opp(tags=["python", "web"])
    profile = _make_profile(skills=["python"], interests=["web"])
    result = score([opp], profile)
    assert result[0].score > 0.0
    assert any("python" in r for r in result[0].reasons)


def test_scoring_category_match():
    opp = _make_opp(category=Category.HACKATHON)
    profile = _make_profile(preferred_categories=["hackathon"])
    _, reason = _score_category(opp, profile)
    assert reason == "Category: hackathon"


def test_scoring_category_no_match():
    opp = _make_opp(category=Category.COMPETITION)
    profile = _make_profile(preferred_categories=["hackathon"])
    s, _ = _score_category(opp, profile)
    assert s == 0.0


def test_scoring_format_match():
    opp = _make_opp(format="online")
    profile = _make_profile(preferred_formats=["online"])
    s, reason = _score_format(opp, profile)
    assert s == 1.0
    assert "online" in reason


def test_scoring_format_no_match():
    opp = _make_opp(format="in-person")
    profile = _make_profile(preferred_formats=["online"])
    s, _ = _score_format(opp, profile)
    assert s == 0.0


def test_scoring_deadline_far_future():
    opp = _make_opp(deadline=datetime.now(tz=timezone.utc) + timedelta(days=60))
    s, reason = _score_deadline(opp)
    assert s == 1.0
    assert "d left" in reason


def test_scoring_deadline_soon():
    opp = _make_opp(deadline=datetime.now(tz=timezone.utc) + timedelta(days=2))
    s, _ = _score_deadline(opp)
    assert s == 0.2


def test_scoring_deadline_none():
    opp = _make_opp(deadline=None)
    s, reason = _score_deadline(opp)
    assert s == 0.5


def test_scoring_sorted_by_score_desc():
    opp_high = _make_opp(title="Match", tags=["python"], format="online")
    opp_low = _make_opp(title="No Match", tags=["rust"], format="in-person")
    profile = _make_profile(
        skills=["python"], preferred_formats=["online"]
    )
    result = score([opp_low, opp_high], profile)
    assert result[0].opportunity.title == "Match"
    assert result[1].opportunity.title == "No Match"


def test_score_bounded_0_to_1():
    opp = _make_opp(
        tags=["python", "ai", "web", "social-good"],
        category=Category.HACKATHON,
        format="online",
        deadline=datetime.now(tz=timezone.utc) + timedelta(days=15),
    )
    profile = _make_profile(
        skills=["python", "ai", "web", "social-good"],
        preferred_categories=["hackathon"],
        preferred_formats=["online"],
        location_preference="any",
    )
    result = score([opp], profile)
    assert 0.0 <= result[0].score <= 1.0


def test_ai_opportunities_score_higher_for_ai_profile():
    ai_opp = _make_opp(
        title="AI Hack", tags=["machine-learning", "ai"],
        category=Category.HACKATHON, format="online",
    )
    non_ai_opp = _make_opp(
        title="Design Hack", tags=["design", "ui"],
        category=Category.HACKATHON, format="online",
    )
    profile = _make_profile(
        skills=["ai", "machine-learning"],
        interests=["artificial-intelligence", "machine-learning"],
        preferred_formats=["online"],
        preferred_categories=["hackathon"],
    )
    result = score([non_ai_opp, ai_opp], profile)
    ai_scored = [s for s in result if s.opportunity.title == "AI Hack"][0]
    non_ai_scored = [s for s in result if s.opportunity.title == "Design Hack"][0]
    assert ai_scored.score > non_ai_scored.score


def test_ml_opportunities_score_higher_for_ml_profile():
    ml_opp = _make_opp(
        title="ML Hack", tags=["Machine Learning/AI"],
        category=Category.HACKATHON, format="online",
    )
    web_opp = _make_opp(
        title="Web Hack", tags=["Web", "JavaScript"],
        category=Category.HACKATHON, format="online",
    )
    profile = _make_profile(
        skills=["machine-learning"],
        interests=["machine-learning"],
        preferred_formats=["online"],
        preferred_categories=["hackathon"],
    )
    result = score([web_opp, ml_opp], profile)
    ml_scored = [s for s in result if s.opportunity.title == "ML Hack"][0]
    web_scored = [s for s in result if s.opportunity.title == "Web Hack"][0]
    assert ml_scored.score > web_scored.score


def test_data_science_opportunities_score_higher():
    ds_opp = _make_opp(
        title="DS Hack", tags=["data-science", "python"],
        category=Category.HACKATHON, format="online",
    )
    web_opp = _make_opp(
        title="Web Hack", tags=["web", "javascript"],
        category=Category.HACKATHON, format="online",
    )
    profile = _make_profile(
        skills=["data-science", "python"],
        interests=["data-science"],
        preferred_formats=["online"],
        preferred_categories=["hackathon"],
    )
    result = score([web_opp, ds_opp], profile)
    ds_scored = [s for s in result if s.opportunity.title == "DS Hack"][0]
    web_scored = [s for s in result if s.opportunity.title == "Web Hack"][0]
    assert ds_scored.score > web_scored.score


def test_data_analytics_opportunities_score_higher():
    da_opp = _make_opp(
        title="DA Hack", tags=["data-analytics", "sql"],
        category=Category.HACKATHON, format="online",
    )
    web_opp = _make_opp(
        title="Web Hack", tags=["web"],
        category=Category.HACKATHON, format="online",
    )
    profile = _make_profile(
        skills=["data-analytics", "sql"],
        interests=["data-analytics"],
        preferred_formats=["online"],
        preferred_categories=["hackathon"],
    )
    result = score([web_opp, da_opp], profile)
    da_scored = [s for s in result if s.opportunity.title == "DA Hack"][0]
    web_scored = [s for s in result if s.opportunity.title == "Web Hack"][0]
    assert da_scored.score > web_scored.score


def test_data_engineering_opportunities_score_higher():
    de_opp = _make_opp(
        title="DE Hack", tags=["data-engineering", "python", "sql"],
        category=Category.HACKATHON, format="online",
    )
    web_opp = _make_opp(
        title="Web Hack", tags=["web"],
        category=Category.HACKATHON, format="online",
    )
    profile = _make_profile(
        skills=["data-engineering", "python", "sql"],
        interests=["data-engineering"],
        preferred_formats=["online"],
        preferred_categories=["hackathon"],
    )
    result = score([web_opp, de_opp], profile)
    de_scored = [s for s in result if s.opportunity.title == "DE Hack"][0]
    web_scored = [s for s in result if s.opportunity.title == "Web Hack"][0]
    assert de_scored.score > web_scored.score


def test_python_skills_required_matches():
    opp = _make_opp(
        title="Python Intern",
        skills_required=["Python", "SQL"],
        tags=["internship"],
        category=Category.INTERNSHIP,
        format="online",
    )
    profile = _make_profile(
        skills=["python", "sql"],
        preferred_categories=["internship"],
        preferred_formats=["online"],
    )
    result = score([opp], profile)
    assert result[0].score > 0.4
    assert any("python" in r for r in result[0].reasons)


def test_domain_matching_boosts_score():
    opp_with_domain = _make_opp(
        title="ML Hack", tags=["ai"],
        domain=["machine-learning"],
        category=Category.HACKATHON, format="online",
    )
    opp_without = _make_opp(
        title="Design Hack", tags=["design"],
        category=Category.HACKATHON, format="online",
    )
    profile = _make_profile(
        skills=["machine-learning"],
        interests=["machine-learning"],
        preferred_formats=["online"],
        preferred_categories=["hackathon"],
    )
    result = score([opp_without, opp_with_domain], profile)
    ml = [s for s in result if s.opportunity.title == "ML Hack"][0]
    no_ml = [s for s in result if s.opportunity.title == "Design Hack"][0]
    assert ml.score > no_ml.score


def test_beginner_opportunities_preferred_for_beginner_user():
    beg_opp = _make_opp(
        title="Beginner Hack", experience_level="beginner",
        category=Category.HACKATHON, format="online",
    )
    adv_opp = _make_opp(
        title="Advanced Hack", experience_level="advanced",
        category=Category.HACKATHON, format="online",
    )
    profile = _make_profile(
        experience_level="beginner",
        preferred_formats=["online"],
        preferred_categories=["hackathon"],
    )
    result = score([adv_opp, beg_opp], profile)
    beg_scored = [s for s in result if s.opportunity.title == "Beginner Hack"][0]
    adv_scored = [s for s in result if s.opportunity.title == "Advanced Hack"][0]
    assert beg_scored.score > adv_scored.score


def test_india_or_online_online_location_scores_high():
    opp = _make_opp(location="Online", format="online")
    profile = _make_profile(location_preference="india-or-online")
    s, reason = _score_location(opp, profile)
    assert s == 1.0
    assert "Online" in reason


def test_india_or_online_india_location_scores_high():
    opp = _make_opp(location="Bangalore, India")
    profile = _make_profile(location_preference="india-or-online")
    s, reason = _score_location(opp, profile)
    assert s == 1.0
    assert "Bangalore" in reason


def test_india_or_online_indian_city_scores_high():
    for city in ["Mumbai", "Pune", "Hyderabad", "Chennai", "Delhi", "Jaipur"]:
        opp = _make_opp(location=city)
        profile = _make_profile(location_preference="india-or-online")
        s, _ = _score_location(opp, profile)
        assert s == 1.0, f"{city} should score 1.0"


def test_india_or_online_work_from_home_scores_high():
    opp = _make_opp(location="Work from home", format="online")
    profile = _make_profile(location_preference="india-or-online")
    s, reason = _score_location(opp, profile)
    assert s == 1.0
    assert "Online" in reason


def test_india_or_online_us_location_scores_low():
    opp = _make_opp(location="New York, NY")
    profile = _make_profile(location_preference="india-or-online")
    s, _ = _score_location(opp, profile)
    assert s == 0.2


def test_paid_entry_excluded_by_tags():
    opp = _make_opp(
        title="Paid Hack", tags=["paid-entry"],
        category=Category.HACKATHON, format="online",
    )
    profile = _make_profile(
        excluded_tags=["paid-entry"],
        preferred_formats=["online"],
        preferred_categories=["hackathon"],
    )
    result = score([opp], profile)
    assert len(result) == 0


def test_paid_entry_in_eligibility_excluded():
    opp = _make_opp(
        title="Paid Event",
        eligibility="Paid event",
        category=Category.HACKATHON, format="online",
    )
    profile = _make_profile(
        excluded_tags=["paid-entry"],
        preferred_formats=["online"],
        preferred_categories=["hackathon"],
    )
    result = score([opp], profile)
    assert len(result) == 0


def test_free_opportunities_not_excluded():
    opp = _make_opp(
        title="Free Hack", tags=["python"],
        category=Category.HACKATHON, format="online",
    )
    profile = _make_profile(
        skills=["python"],
        excluded_tags=["paid-entry"],
        preferred_formats=["online"],
        preferred_categories=["hackathon"],
    )
    result = score([opp], profile)
    assert len(result) == 1


def test_unknown_fee_not_treated_as_free():
    opp = _make_opp(
        title="Unknown Fee Hack",
        category=Category.HACKATHON, format="online",
    )
    fee = _detect_fee_status(opp)
    assert fee == "unknown"


def test_expired_opportunities_excluded_by_scanner():
    from src.scanner import Scanner

    expired = _make_opp(
        title="Expired Hack",
        deadline=datetime.now(tz=timezone.utc) - timedelta(days=1),
    )
    alive = _make_opp(
        title="Alive Hack",
        deadline=datetime.now(tz=timezone.utc) + timedelta(days=30),
    )
    scanner = Scanner()
    filtered = scanner._filter_expired([expired, alive])
    assert len(filtered) == 1
    assert filtered[0].title == "Alive Hack"


def test_no_deadline_opportunities_not_excluded():
    from src.scanner import Scanner

    no_dl = _make_opp(title="No Deadline", deadline=None)
    scanner = Scanner()
    filtered = scanner._filter_expired([no_dl])
    assert len(filtered) == 1


def test_fee_status_detects_stipend():
    opp = _make_opp(description="Company: X; Stipend: 25000 /month")
    assert _detect_fee_status(opp) == "stipend"


def test_fee_status_detects_invite_only():
    opp = _make_opp(eligibility="Invite only")
    assert _detect_fee_status(opp) == "invite-only"


def test_fee_status_free_with_prizes():
    opp = _make_opp(prize_info="$10000, 2 cash prizes")
    assert _detect_fee_status(opp) == "free (prizes)"


def test_fee_status_internship_is_free():
    opp = _make_opp(source=Source.INTERNSHALA, category=Category.INTERNSHIP)
    assert _detect_fee_status(opp) == "free (internship)"


def test_online_opportunities_preferred_over_non_online_for_online_profile():
    online = _make_opp(
        title="Online Hack", format="online",
        category=Category.HACKATHON,
    )
    offline = _make_opp(
        title="Offline Hack", format="in-person",
        category=Category.HACKATHON,
    )
    profile = _make_profile(
        preferred_formats=["online"],
        preferred_categories=["hackathon"],
        location_preference="any",
    )
    result = score([offline, online], profile)
    assert result[0].opportunity.title == "Online Hack"
    assert result[0].score > result[1].score


def test_india_or_online_online_beats_us_location():
    online = _make_opp(title="Online", format="online", location="Online")
    us = _make_opp(title="US Event", location="San Francisco, CA")
    profile = _make_profile(
        location_preference="india-or-online",
        preferred_formats=["online"],
        preferred_categories=["hackathon"],
    )
    result = score([us, online], profile)
    online_s = [s for s in result if s.opportunity.title == "Online"][0]
    us_s = [s for s in result if s.opportunity.title == "US Event"][0]
    assert online_s.score > us_s.score


def test_partial_tag_match_works():
    opp = _make_opp(
        title="Data Hack",
        tags=["data-science", "python"],
        category=Category.HACKATHON, format="online",
    )
    profile = _make_profile(
        skills=["python", "data"],
        interests=["data-science"],
        preferred_formats=["online"],
        preferred_categories=["hackathon"],
    )
    result = score([opp], profile)
    assert result[0].score > 0.4
    assert any("Match" in r for r in result[0].reasons)


def test_missing_format_not_penalized():
    opp_no_fmt = _make_opp(
        title="Internship No Format",
        tags=["python", "sql"],
        skills_required=["Python", "SQL"],
        category=Category.INTERNSHIP,
        format="",
        location="",
    )
    opp_online = _make_opp(
        title="Internship Online",
        tags=["python", "sql"],
        skills_required=["Python", "SQL"],
        category=Category.INTERNSHIP,
        format="online",
        location="",
    )
    profile = _make_profile(
        skills=["python", "sql"],
        preferred_categories=["internship"],
        preferred_formats=["online"],
        location_preference="any",
    )
    result = score([opp_no_fmt, opp_online], profile)
    no_fmt = [s for s in result if s.opportunity.title == "Internship No Format"][0]
    online = [s for s in result if s.opportunity.title == "Internship Online"][0]
    assert no_fmt.score > 0.4
    assert online.score > no_fmt.score


def test_missing_format_scores_neutral():
    opp = _make_opp(format="", location="")
    profile = _make_profile(preferred_formats=["online"])
    s, _ = _score_format(opp, profile)
    assert s == 0.5


def test_missing_deadline_not_penalized():
    opp_no_dl = _make_opp(
        title="No Deadline",
        tags=["python"],
        skills_required=["Python"],
        category=Category.INTERNSHIP,
        deadline=None,
    )
    opp_far = _make_opp(
        title="Far Deadline",
        tags=["python"],
        skills_required=["Python"],
        category=Category.INTERNSHIP,
        deadline=datetime.now(tz=timezone.utc) + timedelta(days=60),
    )
    profile = _make_profile(
        skills=["python"],
        preferred_categories=["internship"],
        preferred_formats=["online"],
        location_preference="any",
    )
    result = score([opp_no_dl, opp_far], profile)
    no_dl = [s for s in result if s.opportunity.title == "No Deadline"][0]
    far = [s for s in result if s.opportunity.title == "Far Deadline"][0]
    assert no_dl.score > 0.4
    assert far.score > no_dl.score


def test_empty_location_neutral_for_india_or_online():
    opp = _make_opp(location="", format="")
    profile = _make_profile(location_preference="india-or-online")
    s, _ = _score_location(opp, profile)
    assert s == 0.5


def test_empty_location_neutral_for_online_only():
    opp = _make_opp(location="", format="")
    profile = _make_profile(location_preference="online-only")
    s, _ = _score_location(opp, profile)
    assert s == 0.5


def test_conflicting_location_still_penalized():
    opp = _make_opp(location="New York, NY", format="")
    profile = _make_profile(location_preference="india-or-online")
    s, _ = _score_location(opp, profile)
    assert s == 0.2


def test_missing_skills_no_penalty():
    opp = _make_opp(tags=[], skills_required=[], domain=[])
    profile = _make_profile(skills=["python"])
    s, _ = _score_tags(opp, profile)
    assert s == 0.0


def test_unknown_fee_not_treated_as_paid():
    opp = _make_opp(description="No fee information available")
    fee = _detect_fee_status(opp)
    assert fee == "unknown"


def test_internship_with_strong_matches_but_missing_format():
    opp = _make_opp(
        title="Python Data Analytics Intern",
        tags=["Python", "SQL", "Data Analytics"],
        skills_required=["Python", "SQL", "Data Analytics"],
        category=Category.INTERNSHIP,
        format="",
        location="Hyderabad",
    )
    profile = _make_profile(
        skills=["python", "sql", "data-analytics"],
        interests=["data-analytics"],
        preferred_categories=["internship"],
        preferred_formats=["online"],
        location_preference="india-or-online",
    )
    result = score([opp], profile)
    assert result[0].score > 0.45
