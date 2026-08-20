# Opportunity Scout

A personalized opportunity scouting agent that finds hackathons, internships, and competitions from multiple websites, then ranks them against your profile using a weighted scoring system.

## Architecture

```
profiles/default.json    # User skills, interests, preferences
        |
        v
    main.py              # CLI entry point
        |
        v
    Scanner              # Orchestrates all scrapers, filters expired, deduplicates
        |
        v
    Scrapers (6)         # Fetch raw data from each source
        |
        v
    Normalizer           # Tag/skill/category normalization (128 synonyms)
        |
        v
    Scorer               # Weighted 6-factor relevance scoring
        |
        v
    Output JSON          # Timestamped results with scores + reasons
```

### Scoring Formula

| Factor | Weight | Description |
|--------|--------|-------------|
| Tags/Skills match | 35% | Direct + partial overlap between user skills/interests and opportunity tags/skills/domain |
| Category match | 20% | hackathon, internship, competition, other |
| Format match | 15% | online, in-person, hybrid |
| Deadline urgency | 15% | Graduated: >30d=1.0, <30d=0.8, <7d=0.5, <3d=0.2 |
| Location match | 10% | Special handling for india-or-online, online-only preferences |
| Experience level | 5% | Beginner/intermediate/advanced compatibility |

Missing information is treated as neutral (0.5), not penalized.

## Sources

| Source | Status | Data |
|--------|--------|------|
| [Devpost](https://devpost.com) | Working | Hackathons via public JSON API |
| [MLH](https://mlh.io) | Working | Events via embedded Inertia.js JSON |
| [Luma](https://lu.ma) | Working | Tech events via `__NEXT_DATA__` |
| [Internshala](https://internshala.com) | Working | Internships via HTML parsing |
| [Unstop](https://unstop.com) | Stub | Angular SPA, no public API |
| [HackCulture](https://hackculture.com) | Stub | B2B platform, no public listings |

## Installation

```bash
git clone https://github.com/yourusername/opportunity-agent.git
cd opportunity-agent
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

### Requirements

- Python 3.10+
- `requests` - HTTP client
- `beautifulsoup4` - HTML parsing (used by Internshala scraper)
- `pytest` - Test framework

## Usage

```bash
# Run with default profile
python3 main.py

# Run with custom profile
python3 main.py profiles/my_profile.json
```

### Profile Format

Create a JSON file in `profiles/`:

```json
{
  "skills": ["python", "sql", "machine learning"],
  "interests": ["artificial intelligence", "data science"],
  "experience_level": "beginner",
  "preferred_formats": ["online", "in-person"],
  "preferred_categories": ["hackathon", "internship"],
  "location_preference": "india-or-online",
  "excluded_tags": ["paid-entry"]
}
```

### Location Preferences

- `any` - No location filtering
- `online-only` - Only online/digital opportunities
- `india-or-online` - Indian cities or online (uses 22-city keyword matching)

## Running Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_scorer.py -v

# Run with coverage
python3 -m pytest tests/ --cov=src --cov-report=term-missing
```

**Test count: 126 tests** across 6 test files, all using mocked HTTP requests.

## Output

Results are saved to `output/opportunities_YYYYMMDD_HHMMSS.json` with:
- All opportunity fields
- Score (0.0 - 1.0)
- Matched skills/interests
- Unmatched profile items
- Fee status (free, paid, stipend, invite-only, unknown)
- Scoring reasons breakdown

## Limitations

1. **Rate limiting** - No built-in rate limiting; relies on respectful scraping delays
2. **No authentication** - Cannot access private/login-required listings
3. **Static scraping** - Some sites (Unstop, HackCulture) require JavaScript rendering
4. **No caching** - Re-running fetches fresh data each time
5. **English only** - Tag normalization is English-centric
6. **No deduplication across time** - Same opportunity in different runs treated separately
7. **Stub sources** - Unstop and HackCulture are placeholders (require headless browser)

## GitHub Actions Plan

Future CI/CD improvements:

- [ ] Run tests on push/PR
- [ ] Lint with flake8/ruff
- [ ] Type checking with mypy
- [ ] Scheduled daily runs (cron)
- [ ] Telegram/Discord notifications for high-score opportunities
- [ ] Deploy to cloud (AWS Lambda / Railway)

## Project Structure

```
opportunity-agent/
├── main.py                  # CLI entry point
├── requirements.txt         # Python dependencies
├── profiles/
│   └── default.json         # Default user profile
├── src/
│   ├── models.py           # Data models (Opportunity, Category, Source)
│   ├── scanner.py          # Orchestrator
│   ├── normalize.py        # Tag normalization (128 synonyms)
│   ├── profile.py          # Profile loading/validation
│   ├── scorer.py           # Relevance scoring engine
│   ├── deduper.py          # Cross-source deduplication
│   └── scrapers/
│       ├── base.py         # Abstract base scraper
│       ├── devpost.py      # Devpost hackathons
│       ├── mlh.py          # MLH events
│       ├── luma.py         # Luma tech events
│       ├── internshala.py  # Internshala internships
│       ├── unstop.py       # Stub (unavailable)
│       └── hackculture.py  # Stub (unavailable)
├── tests/
│   ├── test_models.py
│   ├── test_scrapers.py
│   ├── test_normalize.py
│   ├── test_profile.py
│   ├── test_scorer.py
│   └── test_deduper.py
└── output/                  # Generated JSON results (gitignored)
```

## License

MIT
