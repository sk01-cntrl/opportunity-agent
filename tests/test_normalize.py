from src.normalize import (
    normalize_tag,
    normalize_tags,
    normalize_format,
    normalize_category,
    normalize_title,
    extract_domains,
    extract_skills,
    extract_experience_level,
    clean_prize_html,
)


def test_normalize_tag_lowercase():
    assert normalize_tag("Machine Learning") == "machine-learning"


def test_normalize_tag_slash():
    assert normalize_tag("ML/AI") == "ml-ai"


def test_normalize_tag_synonyms():
    assert normalize_tag("AI") == "artificial-intelligence"
    assert normalize_tag("ML") == "machine-learning"
    assert normalize_tag("JS") == "javascript"
    assert normalize_tag("Full Stack") == "full-stack"
    assert normalize_tag("Open Source") == "open-source"


def test_normalize_tag_dedup():
    result = normalize_tags(["AI", "Artificial Intelligence", "ai"])
    assert result == ["artificial-intelligence"]


def test_normalize_tag_data_synonyms():
    assert normalize_tag("Data Science") == "data-science"
    assert normalize_tag("Data Scientist") == "data-science"
    assert normalize_tag("Data Analytics") == "data-analytics"
    assert normalize_tag("Data Analysis") == "data-analytics"
    assert normalize_tag("Data Engineering") == "data-engineering"
    assert normalize_tag("Python 3") == "python"
    assert normalize_tag("SQL") == "sql"


def test_normalize_tag_new_synonyms():
    assert normalize_tag("Gen AI") == "generative-ai"
    assert normalize_tag("GenAI") == "generative-ai"
    assert normalize_tag("NLP") == "nlp"
    assert normalize_tag("Computer Vision") == "computer-vision"
    assert normalize_tag("LLM") == "llm"
    assert normalize_tag("IoT") == "iot"
    assert normalize_tag("Web3") == "web3"
    assert normalize_tag("Climate Tech") == "climate-tech"


def test_normalize_format():
    assert normalize_format("digital") == "online"
    assert normalize_format("In-Person") == "in-person"
    assert normalize_format("hybrid_physical") == "hybrid"
    assert normalize_format("remote") == "online"


def test_normalize_category():
    assert normalize_category("fellowship") == "internship"
    assert normalize_category("challenge") == "competition"
    assert normalize_category("hackathon") == "hackathon"


def test_normalize_title():
    assert normalize_title("HackPrix Season 3") == "hackprix"
    assert normalize_title("Test Hack 2026") == "test hack"
    assert normalize_title("AI YES v2") == "ai yes"


def test_extract_domains_ml():
    tags = ["Machine Learning/AI", "Web", "Social Good"]
    domains = extract_domains(tags)
    assert "machine-learning" in domains
    assert "web" in domains
    assert "social-good" in domains


def test_extract_domains_data():
    tags = ["Data Science", "Python", "SQL"]
    domains = extract_domains(tags)
    assert "data" in domains


def test_extract_domains_cloud():
    tags = ["AWS", "Docker", "Kubernetes"]
    domains = extract_domains(tags)
    assert "cloud" in domains


def test_extract_skills():
    tags = ["Python", "JavaScript", "React", "SQL"]
    skills = extract_skills(tags)
    assert "python" in skills
    assert "javascript" in skills
    assert "react" in skills
    assert "sql" in skills


def test_extract_skills_no_tech():
    tags = ["Social Good", "Beginner Friendly"]
    skills = extract_skills(tags)
    assert skills == []


def test_extract_experience_level_beginner():
    assert extract_experience_level(["Beginner Friendly"]) == "beginner"
    assert extract_experience_level(["Beginners Welcome"]) == "beginner"


def test_extract_experience_level_advanced():
    assert extract_experience_level(["Advanced"]) == "advanced"


def test_extract_experience_level_none():
    assert extract_experience_level(["Web", "Mobile"]) == ""


def test_clean_prize_html():
    assert clean_prize_html("$<span>10,000</span>") == "10000"
    assert clean_prize_html("$740,000") == "740000"
    assert clean_prize_html("") == ""
    assert clean_prize_html(None) == ""
