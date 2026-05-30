import re

from app.services.skill_catalog import ROLE_ALIASES, ROLE_SKILLS, SKILL_ALIASES


WORD_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9.+#/ -]{1,}")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def normalize_skill(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"\s+", " ", lowered)
    return SKILL_ALIASES.get(lowered, lowered)


def known_skills() -> set[str]:
    skills = set(SKILL_ALIASES.values())
    for role_data in ROLE_SKILLS.values():
        skills.update(role_data["required"])
        skills.update(role_data["optional"])
    skills.update(
        {
            "python",
            "java",
            "javascript",
            "react",
            "node.js",
            "sql",
            "docker",
            "aws",
            "machine learning",
            "tensorflow",
            "nlp",
            "mongodb",
            "postgresql",
            "django",
            "flask",
            "express",
            "redis",
            "kubernetes",
            "linux",
            "html",
            "css",
            "typescript",
            "git",
            "pandas",
            "numpy",
            "statistics",
            "pytorch",
            "tableau",
            "data visualization",
            "system design",
            "testing",
            "figma",
            "terraform",
            "monitoring",
            "networking",
            "mlops",
        }
    )
    normalized = {normalize_skill(skill) for skill in skills if skill}
    normalized.update({normalize_skill(alias) for alias in SKILL_ALIASES.keys()})
    return normalized


def extract_known_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found = set()
    for skill in sorted(known_skills(), key=len, reverse=True):
        if skill and skill in text_lower:
            found.add(normalize_skill(skill))
    return sorted(found)


def extract_bullets(text: str) -> list[str]:
    lines = [line.strip(" -\t") for line in text.splitlines()]
    return [line for line in lines if len(line.split()) >= 4][:8]


def sentence_chunks(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+", normalize_text(text))
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def keyword_overlap_score(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def normalized_role_name(raw_role: str | None) -> str | None:
    if not raw_role:
        return None
    raw = raw_role.strip().lower()
    raw = ROLE_ALIASES.get(raw, raw)
    if raw in ROLE_SKILLS:
        return raw.title() if raw != "devops engineer" else "DevOps Engineer"
    return raw_role.strip()
