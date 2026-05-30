import re

from app.schemas.resume import (
    EducationItem,
    ExperienceItem,
    ProjectItem,
    ResumeParseRequest,
    ResumeParseResponse,
)
from app.services.llm_service import llm_service
from app.services.text_utils import (
    extract_bullets,
    extract_known_skills,
    normalized_role_name,
    normalize_skill,
    normalize_text,
    sentence_chunks,
)


TITLE_PATTERNS = [
    "frontend developer",
    "frontend engineer",
    "backend developer",
    "backend engineer",
    "full stack developer",
    "data scientist",
    "machine learning engineer",
    "devops engineer",
    "python developer",
    "software engineer",
]

EDUCATION_TOKENS = ["b.tech", "bachelor", "master", "mca", "bca", "phd", "degree", "university", "college"]
CERT_TOKENS = ["certified", "certification", "aws certified", "google cloud", "azure"]


class ResumeParserService:
    def parse_resume(self, payload: ResumeParseRequest) -> ResumeParseResponse:
        llm_result = llm_service.parse_resume_structured(
            resume_text=payload.resume_text,
            target_role=payload.target_role,
        )
        if llm_result:
            return self._from_llm_result(llm_result)

        text = normalize_text(payload.resume_text)
        lines = [line.strip() for line in payload.resume_text.splitlines() if line.strip()]
        text_lower = text.lower()

        skills = extract_known_skills(text)
        summary = self._build_summary(text)
        normalized_role = None
        if payload.target_role:
            normalized_role = normalized_role_name(payload.target_role)
        if not normalized_role:
            normalized_role = self._infer_role(text_lower)
        experience = self._extract_experience(lines)
        education = self._extract_education(lines)
        projects = self._extract_projects(lines, skills)
        certifications = self._extract_certifications(lines)

        total_experience_months = sum(
            item.duration_months or 0 for item in experience
        )

        return ResumeParseResponse(
            summary=summary,
            normalized_role=normalized_role,
            skills=skills,
            experience=experience,
            education=education,
            projects=projects,
            certifications=certifications,
            total_experience_months=total_experience_months,
            parser_mode=llm_service.mode,
        )

    def _from_llm_result(self, result: dict) -> ResumeParseResponse:
        return ResumeParseResponse(
            summary=result.get("summary") or "",
            normalized_role=result.get("normalized_role"),
            skills=[
                normalize_skill(skill)
                for skill in (result.get("skills") or [])
                if isinstance(skill, str)
            ],
            experience=[
                ExperienceItem(**item) for item in (result.get("experience") or [])
                if isinstance(item, dict)
            ],
            education=[
                EducationItem(**item) for item in (result.get("education") or [])
                if isinstance(item, dict)
            ],
            projects=[
                ProjectItem(
                    name=item.get("name"),
                    description=item.get("description"),
                    technologies=[
                        normalize_skill(skill)
                        for skill in (item.get("technologies") or [])
                        if isinstance(skill, str)
                    ],
                )
                for item in (result.get("projects") or [])
                if isinstance(item, dict)
            ],
            certifications=[
                normalize_skill(cert)
                for cert in (result.get("certifications") or [])
                if isinstance(cert, str)
            ],
            total_experience_months=result.get("total_experience_months") or 0,
            parser_mode=llm_service.mode,
        )

    def _build_summary(self, text: str) -> str:
        chunks = sentence_chunks(text)
        if chunks:
            return " ".join(chunks[:2])[:400]
        return text[:400]

    def _infer_role(self, text_lower: str) -> str | None:
        for title in TITLE_PATTERNS:
            if title in text_lower:
                return normalized_role_name(title)
        return None

    def _extract_experience(self, lines: list[str]) -> list[ExperienceItem]:
        bullets = extract_bullets("\n".join(lines))
        months = self._estimate_experience_months("\n".join(lines))
        if not bullets:
            return []
        return [
            ExperienceItem(
                title=None,
                company=None,
                duration_text=f"Estimated from resume text",
                duration_months=months,
                responsibilities=bullets[:5],
            )
        ]

    def _extract_education(self, lines: list[str]) -> list[EducationItem]:
        education_lines = [line for line in lines if any(token in line.lower() for token in EDUCATION_TOKENS)]
        items = []
        for line in education_lines[:3]:
            items.append(EducationItem(degree=line, field=None, institution=None, graduation_date=None))
        return items

    def _extract_projects(self, lines: list[str], skills: list[str]) -> list[ProjectItem]:
        project_lines = [line for line in lines if "project" in line.lower() or "built" in line.lower() or "developed" in line.lower()]
        if not project_lines:
            return []
        return [
            ProjectItem(
                name="Highlighted Project",
                description=project_lines[0][:240],
                technologies=skills[:5],
            )
        ]

    def _extract_certifications(self, lines: list[str]) -> list[str]:
        return [line for line in lines if any(token in line.lower() for token in CERT_TOKENS)][:5]

    def _estimate_experience_months(self, text: str) -> int:
        matches = re.findall(r"(\d+)\+?\s*(?:years|year)", text.lower())
        if matches:
            return max(int(value) for value in matches) * 12
        month_matches = re.findall(r"(\d+)\s*(?:months|month)", text.lower())
        if month_matches:
            return max(int(value) for value in month_matches)
        return 0


resume_parser_service = ResumeParserService()
