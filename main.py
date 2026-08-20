import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.profile import load_profile
from src.scanner import Scanner
from src.scorer import score


def main():
    profile_path = sys.argv[1] if len(sys.argv) > 1 else None
    print("Loading profile...")
    profile = load_profile(profile_path)
    print(f"  Skills: {profile.skills or '(none)'}")
    print(f"  Interests: {profile.interests or '(none)'}")
    print(f"  Experience: {profile.experience_level}")
    print(f"  Preferred formats: {profile.preferred_formats}")
    print(f"  Preferred categories: {profile.preferred_categories}")
    print(f"  Location preference: {profile.location_preference}")
    print(f"  Excluded tags: {profile.excluded_tags}")
    print()

    print("Scanning sources...")
    scanner = Scanner()
    raw_opps = scanner.scan()

    failed_sources = [s for s in scanner.source_statuses.values() if not s.ok]
    if failed_sources:
        print(f"\n  WARNING: {len(failed_sources)} source(s) failed:")
        for s in failed_sources:
            print(f"    {s}")
    print()

    if not raw_opps:
        print("No opportunities found.")
        return

    print(f"After filtering expired and dedup: {len(raw_opps)}")

    print("Scoring opportunities...")
    scored = score(raw_opps, profile)

    filtered_count = len(raw_opps) - len(scored)
    if filtered_count > 0:
        print(f"  Excluded by excluded_tags: {filtered_count}")

    print(f"\n{'='*70}")
    print(f" Top {min(20, len(scored))} Opportunities (personalized)")
    print(f"{'='*70}\n")

    for i, s in enumerate(scored[:20], 1):
        opp = s.opportunity
        deadline_str = opp.deadline.strftime("%Y-%m-%d") if opp.deadline else "N/A"

        matched = []
        if s.reasons:
            for r in s.reasons:
                if r.startswith("Matches:"):
                    matched.extend(r.replace("Matches: ", "").split(", "))

        all_user_skills = set(profile.skills) | set(profile.interests)
        opp_all = set(opp.tags) | set(opp.skills_required) | set(opp.domain)
        from src.normalize import normalize_tag, normalize_tags
        opp_all_norm = set(normalize_tags(list(opp_all)))
        user_norm = {normalize_tag(s) for s in all_user_skills}
        matched_norm = opp_all_norm & user_norm
        unmatched = sorted(all_user_skills - {
            s for s in all_user_skills if normalize_tag(s) in matched_norm
        })

        why_parts = []
        for r in s.reasons:
            why_parts.append(r)

        print(f"{i:2d}. [{s.score:.3f}] {opp.title}")
        print(f"    Category: {opp.category.value} | Source: {opp.source.value}")
        print(f"    Deadline: {deadline_str} | Location: {opp.location or 'N/A'}")
        print(f"    Fee: {s.fee_status}")
        print(f"    Score: {s.score:.3f}")
        if matched_norm:
            print(f"    Matched skills/interests: {', '.join(sorted(matched_norm))}")
        else:
            print(f"    Matched skills/interests: (none)")
        if unmatched:
            print(f"    Unmatched profile items: {', '.join(unmatched[:5])}")
        if why_parts:
            print(f"    Why: {'; '.join(why_parts)}")
        print(f"    URL: {opp.url}")
        print()

    scanner.save([s.opportunity for s in scored])


if __name__ == "__main__":
    main()
