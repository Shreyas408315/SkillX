from pathlib import Path
import json
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.services.text_utils import normalized_role_name

BASE_DIR = Path(__file__).resolve().parent
client = TestClient(app)


def load_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def contains_all(expected: list[str], actual: list[str]) -> bool:
    actual_set = {item.strip().lower() for item in actual}
    return all(item.strip().lower() in actual_set for item in expected)


def normalize_text_for_check(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().lower()


def evaluate_resume_parse() -> int:
    samples = load_json_file(BASE_DIR / "eval_resume_parse_samples.json")
    passed = 0
    print("=== Resume Parse Evaluation ===")

    for sample in samples:
        name = sample["name"]
        request = sample["request"]
        expected = sample["expected"]
        response = client.post("/api/resume/parse", json=request)

        if response.status_code != 200:
            print(f"{name}: FAILED (status={response.status_code})")
            print(response.text)
            continue

        payload = response.json()
        result_ok = True

        if expected_role := expected.get("normalized_role"):
            actual_role = normalized_role_name(payload.get("normalized_role")) or payload.get("normalized_role")
            if normalize_text_for_check(actual_role) != normalize_text_for_check(expected_role):
                print(f"{name}: role mismatch -> expected {expected_role}, got {payload.get('normalized_role')}")
                result_ok = False

        if skills := expected.get("skills_include"):
            if not contains_all(skills, payload.get("skills", [])):
                print(f"{name}: missing skills -> expected at least {skills}, got {payload.get('skills', [])}")
                result_ok = False

        if education := expected.get("education_mentions"):
            text = " ".join([payload.get("summary", ""), " ".join(item.get("degree", "") or "" for item in payload.get("education", [])), " ".join(item.get("field", "") or "" for item in payload.get("education", []))]).lower()
            if not all(item.lower() in text for item in education):
                print(f"{name}: education mentions missing -> expected {education}, got {text}")
                result_ok = False

        if result_ok:
            passed += 1
            print(f"{name}: PASS")
    return passed


def evaluate_match() -> int:
    samples = load_json_file(BASE_DIR / "eval_match_samples.json")
    passed = 0
    print("=== Match Score Evaluation ===")

    for sample in samples:
        name = sample["name"]
        request = sample["request"]
        expected = sample["expected"]
        response = client.post("/api/match/score", json=request)

        if response.status_code != 200:
            print(f"{name}: FAILED (status={response.status_code})")
            print(response.text)
            continue

        payload = response.json()
        result_ok = True

        if min_score := expected.get("min_match_score"):
            if payload.get("match_score", 0) < min_score:
                print(f"{name}: score too low -> expected >= {min_score}, got {payload.get('match_score')}")
                result_ok = False

        if matched := expected.get("matched_skills_include"):
            if not contains_all(matched, payload.get("matched_skills", [])):
                print(f"{name}: matched skills missing -> expected {matched}, got {payload.get('matched_skills', [])}")
                result_ok = False

        if missing := expected.get("missing_skills_include"):
            if not contains_all(missing, payload.get("missing_skills", [])):
                print(f"{name}: missing skills mismatch -> expected {missing}, got {payload.get('missing_skills', [])}")
                result_ok = False

        if result_ok:
            passed += 1
            print(f"{name}: PASS")
    return passed


def evaluate_gap_analysis() -> int:
    samples = load_json_file(BASE_DIR / "eval_gap_analysis_samples.json")
    passed = 0
    print("=== Gap Analysis Evaluation ===")

    for sample in samples:
        name = sample["name"]
        request = sample["request"]
        expected = sample["expected"]
        response = client.post("/api/gap/analyze", json=request)

        if response.status_code != 200:
            print(f"{name}: FAILED (status={response.status_code})")
            print(response.text)
            continue

        payload = response.json()
        result_ok = True

        if readiness := expected.get("readiness_min"):
            if payload.get("readiness_score", 0) < readiness:
                print(f"{name}: readiness too low -> expected >= {readiness}, got {payload.get('readiness_score')}")
                result_ok = False

        if missing := expected.get("missing_skills_include"):
            if not contains_all(missing, payload.get("missing_skills", [])):
                print(f"{name}: missing skills mismatch -> expected {missing}, got {payload.get('missing_skills', [])}")
                result_ok = False

        if result_ok:
            passed += 1
            print(f"{name}: PASS")
    return passed


def main() -> None:
    total_passed = 0
    total_tests = 0

    total_passed += evaluate_resume_parse()
    total_tests += len(load_json_file(BASE_DIR / "eval_resume_parse_samples.json"))
    print()

    total_passed += evaluate_match()
    total_tests += len(load_json_file(BASE_DIR / "eval_match_samples.json"))
    print()

    total_passed += evaluate_gap_analysis()
    total_tests += len(load_json_file(BASE_DIR / "eval_gap_analysis_samples.json"))
    print()

    print(f"Summary: {total_passed}/{total_tests} tests passed.")
    if total_passed != total_tests:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
