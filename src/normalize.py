import re
from typing import List


SYNONYMS = {
    "ml": "machine-learning",
    "machine learning": "machine-learning",
    "machine-learning/ai": "machine-learning",
    "machine-learning-ai": "machine-learning",
    "ai": "artificial-intelligence",
    "artificial intelligence": "artificial-intelligence",
    "data sci": "data-science",
    "data science": "data-science",
    "data scientist": "data-science",
    "data scientist/analyst": "data-science",
    "data-scientist": "data-science",
    "data-analytics": "data-analytics",
    "data-analysis": "data-analytics",
    "data analysis": "data-analytics",
    "data-analyst": "data-analytics",
    "data-engineering": "data-engineering",
    "data engineer": "data-engineering",
    "data engineer/scientist": "data-engineering",
    "web-dev": "web",
    "web dev": "web",
    "web development": "web",
    "front-end": "front-end",
    "frontend": "front-end",
    "front end": "front-end",
    "back-end": "back-end",
    "backend": "back-end",
    "back end": "back-end",
    "full-stack": "full-stack",
    "fullstack": "full-stack",
    "full stack": "full-stack",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "python-3": "python",
    "python 3": "python",
    "rust lang": "rust",
    "golang": "go",
    "devops": "dev-ops",
    "block chain": "blockchain",
    "open-source": "open-source",
    "open source": "open-source",
    "social-good": "social-good",
    "social good": "social-good",
    "social impact": "social-good",
    "low-code": "low-code",
    "low code": "low-code",
    "no-code": "no-code",
    "no code": "no-code",
    "fintech": "fintech",
    "fin-tech": "fintech",
    "fin tech": "fintech",
    "health-tech": "health-tech",
    "healthtech": "health-tech",
    "health tech": "health-tech",
    "education-tech": "education-tech",
    "edtech": "education-tech",
    "education tech": "education-tech",
    "climate-tech": "climate-tech",
    "climate tech": "climate-tech",
    "cleantech": "climate-tech",
    "agriculture-tech": "agriculture-tech",
    "agri tech": "agriculture-tech",
    "agritech": "agriculture-tech",
    "iot": "iot",
    "internet-of-things": "iot",
    "internet of things": "iot",
    "nlp": "nlp",
    "natural-language-processing": "nlp",
    "natural language processing": "nlp",
    "computer-vision": "computer-vision",
    "cv": "computer-vision",
    "computer vision": "computer-vision",
    "llm": "llm",
    "large-language-model": "llm",
    "large language model": "llm",
    "generative-ai": "generative-ai",
    "generative ai": "generative-ai",
    "gen-ai": "generative-ai",
    "gen ai": "generative-ai",
    "genai": "generative-ai",
    "blockchain": "blockchain",
    "web3": "web3",
    "web 3": "web3",
    "cloud": "cloud",
    "aws": "aws",
    "azure": "azure",
    "gcp": "gcp",
    "google-cloud": "gcp",
    "google cloud": "gcp",
    "react": "react",
    "reactjs": "react",
    "react.js": "react",
    "node": "node",
    "nodejs": "node",
    "node.js": "node",
    "java": "java",
    "c++": "c++",
    "c#": "csharp",
    "ruby": "ruby",
    "php": "php",
    "swift": "swift",
    "kotlin": "kotlin",
    "go ": "go",
    "rust": "rust",
    "sql": "sql",
    "nosql": "nosql",
    "mongodb": "mongodb",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mysql": "mysql",
    "firebase": "firebase",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "git": "git",
    "github": "github",
    "beginner-friendly": "beginner-friendly",
    "beginner friendly": "beginner-friendly",
    "beginners-welcome": "beginner-friendly",
    "beginners welcome": "beginner-friendly",
    "beginners-friendly": "beginner-friendly",
    "beginners friendly": "beginner-friendly",
}

FORMAT_MAP = {
    "online": "online",
    "digital": "online",
    "remote": "online",
    "everywhere": "online",
    "worldwide": "online",
    "in-person": "in-person",
    "in person": "in-person",
    "onsite": "in-person",
    "physical": "in-person",
    "hybrid": "hybrid",
    "hybrid_physical": "hybrid",
}

CATEGORY_MAP = {
    "hackathon": "hackathon",
    "internship": "internship",
    "competition": "competition",
    "fellowship": "internship",
    "challenge": "competition",
}

DOMAIN_KEYWORDS = {
    "machine-learning": ["machine-learning", "artificial-intelligence", "ai", "ml",
                         "data-science", "nlp", "computer-vision", "llm",
                         "generative-ai", "deep-learning"],
    "web": ["web", "frontend", "front-end", "backend", "back-end", "full-stack",
            "react", "node", "javascript", "html", "css"],
    "mobile": ["mobile", "ios", "android", "swift", "kotlin", "react-native",
               "flutter"],
    "data": ["data-science", "data-analytics", "data-engineering", "sql",
             "analytics", "visualization"],
    "cloud": ["cloud", "aws", "azure", "gcp", "devops", "docker", "kubernetes"],
    "blockchain": ["blockchain", "web3", "crypto", "defi"],
    "gaming": ["gaming", "game", "unity", "unreal"],
    "iot": ["iot", "hardware", "robotics", "embedded"],
    "security": ["security", "cybersecurity", "privacy"],
    "fintech": ["fintech", "finance", "banking", "payments"],
    "health": ["health", "healthcare", "medical", "biotech"],
    "social-good": ["social-good", "social-impact", "education", "sustainability",
                    "environment", "climate"],
}


def normalize_tag(tag: str) -> str:
    t = tag.lower().strip()
    t = re.sub(r"[/\\]+", "-", t)
    t = re.sub(r"[^a-z0-9\-]+", " ", t)
    t = re.sub(r"\s+", "-", t).strip("-")
    return SYNONYMS.get(t, t)


def normalize_tags(tags: List[str]) -> List[str]:
    seen = set()
    result = []
    for tag in tags:
        n = normalize_tag(tag)
        if n and n not in seen:
            seen.add(n)
            result.append(n)
    return result


def normalize_format(raw: str) -> str:
    return FORMAT_MAP.get(raw.lower().strip(), raw.lower().strip())


def normalize_category(raw: str) -> str:
    return CATEGORY_MAP.get(raw.lower().strip(), raw.lower().strip())


def normalize_title(title: str) -> str:
    t = title.lower().strip()
    t = re.sub(r"\b(v\d+|season\s*\d+|\d{4})\b", "", t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_domains(tags: List[str]) -> List[str]:
    normalized = normalize_tags(tags)
    domains = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for tag in normalized:
            if tag in keywords:
                if domain not in domains:
                    domains.append(domain)
                break
    return domains


def extract_skills(tags: List[str]) -> List[str]:
    normalized = normalize_tags(tags)
    tech_skills = {
        "python", "javascript", "typescript", "java", "c++", "csharp",
        "ruby", "php", "swift", "kotlin", "go", "rust", "sql", "nosql",
        "react", "node", "html", "css", "mongodb", "postgresql", "mysql",
        "firebase", "docker", "kubernetes", "git", "github", "aws", "azure",
        "gcp",
    }
    skills = []
    for tag in normalized:
        if tag in tech_skills and tag not in skills:
            skills.append(tag)
    return skills


def extract_experience_level(tags: List[str]) -> str:
    normalized = normalize_tags(tags)
    if "beginner-friendly" in normalized or "beginner" in normalized:
        return "beginner"
    if "advanced" in normalized:
        return "advanced"
    if "intermediate" in normalized:
        return "intermediate"
    return ""


def clean_prize_html(raw: str) -> str:
    if not raw:
        return ""
    cleaned = re.sub(r"<[^>]+>", "", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned.replace("$", "").replace(",", "")
    cleaned = cleaned.strip()
    return cleaned
