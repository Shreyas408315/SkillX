import argparse
import json
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path


NON_SKILL_TOKENS = {
    "",
    "advanced",
    "intermediate",
    "beginner",
    "expert",
    "fluent",
    "native",
    "bilingual",
    "english",
    "hindi",
    "marathi",
    "punjabi",
    "tulu",
    "less than 1 year",
    "12 months",
    "24 months",
}

ROLE_NORMALIZATION = {
    "javascript developer": "JavaScript Developer",
    "node.js developer": "Node.js Developer",
    "nodejs developer": "Node.js Developer",
    "devops engineer": "DevOps Engineer",
    "ai engineer": "AI Engineer",
    "mlops engineer": "MLOps Engineer",
    "nlp engineer": "NLP Engineer",
    "ios developer": "iOS Developer",
    "sql developer": "SQL Developer",
    "nosql developer": "NoSQL Developer",
    "full stack developer": "Full Stack Developer",
    "frontend developer": "Frontend Developer",
    "backend developer": "Backend Developer",
    "react native developer": "React Native Developer",
}

SKILL_NORMALIZATION = {
    "nodejs": "node.js",
    "node js": "node.js",
    "react.js": "react",
    "vue.js": "vue",
    "next.js": "next.js",
    "nuxt.js": "nuxt.js",
    "js": "javascript",
    "ts": "typescript",
    "cpp": "c++",
    "csharp": "c#",
    "google cloud platform": "google cloud",
    "gcp": "google cloud",
    "amazon web services": "aws",
}

WEAK_COMPANY_VALUES = {"fresher", "na", "n/a", "none", "nil", "student"}
COMPANYISH_INSTITUTION_PATTERN = re.compile(
    r"\b(llc|inc|corp|corporation|ltd|limited|solutions|technologies|systems|group|sons)\b",
    re.IGNORECASE,
)
RESUME_KEYWORDS = {
    "developer",
    "engineer",
    "scientist",
    "manager",
    "analyst",
    "administrator",
    "experience",
    "experienced",
    "skills",
    "years",
    "project",
    "python",
    "java",
    "react",
    "aws",
    "machine learning",
    "data",
}


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9+#./ ]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_skill(skill: str) -> str | None:
    normalized = slugify(skill)
    if not normalized or normalized in NON_SKILL_TOKENS:
        return None
    normalized = SKILL_NORMALIZATION.get(normalized, normalized)
    if normalized in NON_SKILL_TOKENS:
        return None
    return normalized


def normalize_role(title: str) -> str:
    normalized = slugify(title)
    normalized = ROLE_NORMALIZATION.get(normalized, normalized)
    if not normalized:
        return ""
    if normalized in ROLE_NORMALIZATION.values():
        return normalized
    words = []
    for word in normalized.split():
        if word in {"ai", "mlops", "nlp", "ios", "sql", "nosql"}:
            words.append(word.upper() if word != "ios" else "iOS")
        elif word == "javascript":
            words.append("JavaScript")
        elif word == "node.js":
            words.append("Node.js")
        elif word == "devops":
            words.append("DevOps")
        elif word == "fullstack":
            words.append("Full Stack")
        else:
            words.append(word.capitalize())
    return " ".join(words).replace("Full Stack", "Full Stack")


def parse_year(value):
    if not value:
        return None
    match = re.search(r"(19|20)\d{2}", str(value))
    return int(match.group(0)) if match else None


def collect_titles(record: dict) -> list[str]:
    titles = []
    for item in record.get("experience") or []:
        if isinstance(item, dict):
            title = (item.get("title") or "").strip()
            if title:
                titles.append(title)
    return titles


def infer_domain_from_text(text: str) -> set[str]:
    text = slugify(text)
    domain = set()
    if any(token in text for token in {"data scientist", "machine learning", "deep learning", "nlp", "computer vision", "ai engineer"}):
        domain.add("data_ai")
    if any(token in text for token in {"frontend", "react", "angular", "vue", "javascript", "web developer"}):
        domain.add("frontend")
    if any(token in text for token in {"backend", "node.js", "java developer", "python developer", "api", "database administrator"}):
        domain.add("backend")
    if any(token in text for token in {"project manager", "product manager", "scrum"}):
        domain.add("management")
    if any(token in text for token in {"advocate", "legal", "laws"}):
        domain.add("legal")
    return domain


def flag_record(record: dict) -> list[str]:
    flags = []
    summary = record.get("summary") or ""
    features = record.get("features") or {}
    skills = features.get("primary_skills") or []
    experience = record.get("experience") or []
    education = record.get("education") or []

    titles = collect_titles(record)
    title_domains = set()
    for title in titles:
        title_domains.update(infer_domain_from_text(title))
    summary_domains = infer_domain_from_text(summary)

    if title_domains and summary_domains and title_domains.isdisjoint(summary_domains):
        flags.append("summary_title_domain_mismatch")

    summary_text = slugify(summary)
    if summary_text:
        if not any(keyword in summary_text for keyword in RESUME_KEYWORDS):
            sentence_like_parts = [part.strip() for part in re.split(r"[.!?]+", summary) if part.strip()]
            if len(sentence_like_parts) >= 3:
                flags.append("synthetic_like_summary")

    exp_months = features.get("total_experience_months")
    grad_years = []
    for edu in education:
        if not isinstance(edu, dict):
            continue
        dates = edu.get("dates") or {}
        grad_year = parse_year(dates.get("expected_graduation")) or parse_year(dates.get("end"))
        if grad_year:
            grad_years.append(grad_year)
    if isinstance(exp_months, int) and exp_months >= 120 and grad_years:
        latest_grad_year = max(grad_years)
        if latest_grad_year >= 2020:
            flags.append("high_experience_recent_graduation")

    project_urls = 0
    null_project_fields = 0
    for project in record.get("projects") or []:
        if not isinstance(project, dict):
            continue
        if project.get("url"):
            project_urls += 1
        null_project_fields += sum(1 for value in project.values() if value in (None, [], ""))
    if project_urls >= 3:
        flags.append("many_project_urls")
    if null_project_fields >= 4:
        flags.append("sparse_project_data")

    weak_companies = 0
    for item in experience:
        if not isinstance(item, dict):
            continue
        company = slugify(item.get("company") or "")
        if company in WEAK_COMPANY_VALUES:
            weak_companies += 1
    if weak_companies:
        flags.append("weak_company_placeholder")

    for edu in education:
        if not isinstance(edu, dict):
            continue
        institution_name = ((edu.get("institution") or {}).get("name") or "").strip()
        if institution_name and COMPANYISH_INSTITUTION_PATTERN.search(institution_name):
            flags.append("education_institution_looks_company")
            break

    if len(skills) < 2:
        flags.append("very_few_skills")

    return flags


def is_low_quality(record: dict) -> bool:
    summary = (record.get("summary") or "").strip()
    features = record.get("features") or {}
    experience = record.get("experience") or []
    education = record.get("education") or []
    projects = record.get("projects") or []

    empty_sections = 0
    if not summary:
        empty_sections += 1
    if not experience:
        empty_sections += 1
    if not education:
        empty_sections += 1
    if not projects:
        empty_sections += 1

    primary_skills = features.get("primary_skills") or []
    if len(primary_skills) < 2:
        empty_sections += 1

    flags = set(record.get("quality_flags") or [])
    severe_flags = {
        "synthetic_like_summary",
        "education_institution_looks_company",
    }
    if flags & severe_flags:
        return True

    return empty_sections >= 3


def clean_record(record: dict):
    cleaned = deepcopy(record)
    flags = flag_record(record)

    features = cleaned.setdefault("features", {})
    raw_skills = features.get("primary_skills") or []
    cleaned_skills = []
    seen = set()
    for skill in raw_skills:
        normalized = normalize_skill(str(skill))
        if normalized and normalized not in seen:
            cleaned_skills.append(normalized)
            seen.add(normalized)
    features["primary_skills"] = cleaned_skills

    normalized_titles = []
    for item in cleaned.get("experience") or []:
        if not isinstance(item, dict):
            continue
        title = (item.get("title") or "").strip()
        if title:
            item["title_normalized"] = normalize_role(title)
            normalized_titles.append(item["title_normalized"])

    if normalized_titles:
        cleaned["normalized_role"] = normalized_titles[0]
    elif cleaned_skills:
        cleaned["normalized_role"] = ""

    cleaned["quality_flags"] = flags
    return cleaned


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cleaned_path = output_dir / f"{input_path.stem}.cleaned.jsonl"
    flagged_path = output_dir / f"{input_path.stem}.flagged.jsonl"
    dropped_path = output_dir / f"{input_path.stem}.dropped.jsonl"
    report_path = output_dir / f"{input_path.stem}.report.json"

    stats = Counter()
    flag_counts = Counter()
    role_counts = Counter()

    with input_path.open("r", encoding="utf-8", errors="replace") as src, \
        cleaned_path.open("w", encoding="utf-8") as cleaned_file, \
        flagged_path.open("w", encoding="utf-8") as flagged_file, \
        dropped_path.open("w", encoding="utf-8") as dropped_file:
        for line in src:
            if not line.strip():
                continue
            stats["input_rows"] += 1
            record = json.loads(line)
            cleaned = clean_record(record)

            if is_low_quality(cleaned):
                stats["dropped_rows"] += 1
                dropped_file.write(json.dumps(cleaned, ensure_ascii=True) + "\n")
                continue

            stats["kept_rows"] += 1
            role = cleaned.get("normalized_role") or ""
            if role:
                role_counts[role] += 1

            cleaned_file.write(json.dumps(cleaned, ensure_ascii=True) + "\n")

            if cleaned.get("quality_flags"):
                stats["flagged_rows"] += 1
                for flag in cleaned["quality_flags"]:
                    flag_counts[flag] += 1
                flagged_file.write(json.dumps(cleaned, ensure_ascii=True) + "\n")

    report = {
        "input_file": str(input_path),
        "cleaned_file": str(cleaned_path),
        "flagged_file": str(flagged_path),
        "dropped_file": str(dropped_path),
        "stats": dict(stats),
        "flag_counts": dict(flag_counts),
        "top_normalized_roles": role_counts.most_common(30),
        "non_skill_tokens_removed": sorted(NON_SKILL_TOKENS),
    }

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
