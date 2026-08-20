from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Tuple

from src.models import Opportunity
from src.normalize import normalize_tag, normalize_tags, normalize_format
from src.profile import Profile


INDIA_KEYWORDS = {
    "india", "bangalore", "bengaluru", "mumbai", "pune", "hyderabad",
    "chennai", "delhi", "jaipur", "ahmedabad", "kolkata", "lucknow",
    "noida", "gurgaon", "gurugram", "coimbatore", "kochi", "indore",
    "bhopal", "chandigarh", "visakhapatnam", "nagpur", "patna",
    "work from home",
}


@dataclass
class ScoredOpportunity:
    opportunity: Opportunity
    score: float
    reasons: List[str] = field(default_factory=list)
    fee_status: str = "unknown"


def score(opportunities: List[Opportunity], profile: Profile) -> List[ScoredOpportunity]:
    filtered = _apply_excluded_tags(opportunities, profile)
    scored = []
    for opp in filtered:
        s = _score_one(opp, profile)
        scored.append(s)
    scored.sort(key=lambda s: (-s.score, s.opportunity.deadline or datetime.max))
    return scored


def _apply_excluded_tags(
    opportunities: List[Opportunity], profile: Profile
) -> List[Opportunity]:
    if not profile.excluded_tags:
        return opportunities
    excluded = set(normalize_tags(profile.excluded_tags))
    result = []
    for opp in opportunities:
        opp_opp_tags = set(normalize_tags(opp.tags))
        opp_elig = normalize_tag(opp.eligibility) if opp.eligibility else ""
        opp_skills = set(normalize_tags(opp.skills_required))
        opp_domain = set(opp.domain)
        opp_desc = opp.description.lower()
        all_opp = opp_opp_tags | opp_skills | opp_domain
        is_excluded = False
        for ex in excluded:
            if ex in all_opp:
                is_excluded = True
                break
            if ex == "paid-entry" and (
                opp_elig == "paid-event"
                or "paid" in opp_elig
                or "fee" in opp_desc
            ):
                is_excluded = True
                break
        if not is_excluded:
            result.append(opp)
    return result


def _score_one(opp: Opportunity, profile: Profile) -> ScoredOpportunity:
    total = 0.0
    reasons = []

    tag_score, tag_reasons = _score_tags(opp, profile)
    total += tag_score * 0.35
    reasons.extend(tag_reasons)

    cat_score, cat_reason = _score_category(opp, profile)
    total += cat_score * 0.20
    if cat_reason:
        reasons.append(cat_reason)

    fmt_score, fmt_reason = _score_format(opp, profile)
    total += fmt_score * 0.15
    if fmt_reason:
        reasons.append(fmt_reason)

    dl_score, dl_reason = _score_deadline(opp)
    total += dl_score * 0.15
    if dl_reason:
        reasons.append(dl_reason)

    loc_score, loc_reason = _score_location(opp, profile)
    total += loc_score * 0.10
    if loc_reason:
        reasons.append(loc_reason)

    exp_score, exp_reason = _score_experience(opp, profile)
    total += exp_score * 0.05
    if exp_reason:
        reasons.append(exp_reason)

    total = max(0.0, min(1.0, total))
    fee_status = _detect_fee_status(opp)
    return ScoredOpportunity(
        opportunity=opp, score=round(total, 3), reasons=reasons, fee_status=fee_status
    )


def _score_tags(opp: Opportunity, profile: Profile) -> Tuple[float, List[str]]:
    user_tags = set()
    for s in profile.skills:
        user_tags.add(normalize_tag(s))
    for i in profile.interests:
        user_tags.add(normalize_tag(i))
    user_tags -= {""}
    if not user_tags:
        return 0.0, []

    opp_tags = set(normalize_tags(opp.tags))
    opp_skills = set(normalize_tags(opp.skills_required))
    opp_domain = set(opp.domain)
    all_opp = opp_tags | opp_skills | opp_domain

    if not all_opp:
        return 0.0, []

    direct_overlap = user_tags & all_opp
    partial_overlap = set()
    for ut in user_tags:
        if ut in direct_overlap:
            continue
        for ot in all_opp:
            if len(ut) >= 4 and ut in ot:
                partial_overlap.add(ot)
                break

    matched = direct_overlap | partial_overlap
    if not matched:
        return 0.0, []

    score_val = len(matched) / len(user_tags)
    score_val = min(1.0, score_val)
    matched_names = sorted(matched)[:5]
    return score_val, [f"Matches: {', '.join(matched_names)}"]


def _score_category(opp: Opportunity, profile: Profile) -> Tuple[float, str]:
    cat = opp.category.value
    if cat in profile.preferred_categories:
        return 1.0, f"Category: {cat}"
    return 0.0, ""


KNOWN_FORMATS = {"online", "in-person", "hybrid"}


def _score_format(opp: Opportunity, profile: Profile) -> Tuple[float, str]:
    fmt = opp.format or normalize_format(opp.location)
    if not fmt:
        for tag in opp.tags:
            fmt = normalize_format(tag)
            if fmt in KNOWN_FORMATS:
                break
    if not fmt or fmt not in KNOWN_FORMATS:
        return 0.5, ""
    if fmt in profile.preferred_formats:
        return 1.0, f"Format: {fmt}"
    return 0.0, ""


def _score_deadline(opp: Opportunity) -> Tuple[float, str]:
    if not opp.deadline:
        return 0.5, "No deadline set"
    now = datetime.now(tz=timezone.utc)
    dl = opp.deadline
    if dl.tzinfo is None:
        dl = dl.replace(tzinfo=timezone.utc)
    days_left = (dl - now).total_seconds() / 86400
    if days_left < 0:
        return 0.0, ""
    if days_left < 3:
        return 0.2, f"{int(days_left)}d left"
    if days_left < 7:
        return 0.5, f"{int(days_left)}d left"
    if days_left < 30:
        return 0.8, f"{int(days_left)}d left"
    return 1.0, f"{int(days_left)}d left"


def _score_location(opp: Opportunity, profile: Profile) -> Tuple[float, str]:
    pref = profile.location_preference
    if pref == "any":
        return 1.0, ""

    loc = opp.location.lower().strip()
    fmt = opp.format or normalize_format(opp.location)

    if not loc and not fmt:
        return 0.5, ""

    if pref == "online-only":
        if "online" in loc or "digital" in loc or fmt == "online":
            return 1.0, "Online"
        for tag in opp.tags:
            if normalize_format(tag) == "online":
                return 1.0, "Online"
        return 0.2, ""

    if pref == "india-or-online":
        is_online = (
            "online" in loc
            or "work from home" in loc
            or "remote" in loc
            or fmt == "online"
        )
        if is_online:
            return 1.0, "Online"
        for tag in opp.tags:
            if normalize_format(tag) == "online":
                return 1.0, "Online"
        is_india = any(kw in loc for kw in INDIA_KEYWORDS)
        if is_india:
            return 1.0, f"Location: {opp.location}"
        return 0.2, ""

    if pref in loc:
        return 1.0, f"Location: {opp.location}"
    return 0.5, ""


def _score_experience(opp: Opportunity, profile: Profile) -> Tuple[float, str]:
    if profile.experience_level == "all":
        return 1.0, ""
    opp_level = opp.experience_level.lower()
    if not opp_level or opp_level == "all":
        return 0.8, ""
    levels = ["beginner", "intermediate", "advanced"]
    try:
        user_idx = levels.index(profile.experience_level)
        opp_idx = levels.index(opp_level)
    except ValueError:
        return 0.5, ""
    if opp_idx <= user_idx:
        return 1.0, f"Level: {opp_level}"
    if opp_idx == user_idx + 1:
        return 0.5, f"Level: {opp_level} (stretch)"
    return 0.2, f"Level: {opp_level} (advanced)"


def _detect_fee_status(opp: Opportunity) -> str:
    elig = opp.eligibility.lower() if opp.eligibility else ""
    if "paid" in elig:
        return "paid"
    if "invite" in elig:
        return "invite-only"
    desc = opp.description.lower()
    if "fee" in desc and ("application" in desc or "entry" in desc or "registration" in desc):
        return "paid"
    if "stipend" in desc:
        return "stipend"
    if opp.prize_info:
        return "free (prizes)"
    if opp.source.value == "internshala":
        return "free (internship)"
    return "unknown"
