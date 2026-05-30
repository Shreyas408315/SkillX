from app.schemas.common import Recommendation
from app.schemas.gap_analysis import GapAnalysisRequest, GapAnalysisResponse, GapComparisonItem
from app.schemas.resume import ResumeParseRequest
from app.services.resume_parser import resume_parser_service
from app.services.skill_catalog import ROLE_SKILLS
from app.services.text_utils import normalized_role_name, normalize_skill


class GapService:
    def analyze_gap(self, payload: GapAnalysisRequest) -> GapAnalysisResponse:
        normalized_role = (normalized_role_name(payload.target_role) or payload.target_role).strip().lower()
        role_profile = ROLE_SKILLS.get(normalized_role)
        if not role_profile:
            role_profile = {"required": [], "optional": []}

        resume_skills = {
            normalize_skill(skill)
            for skill in payload.resume_skills
            if isinstance(skill, str) and skill.strip()
        }
        if not resume_skills and payload.resume_text:
            parsed = resume_parser_service.parse_resume(
                ResumeParseRequest(resume_text=payload.resume_text, target_role=payload.target_role)
            )
            resume_skills = set(parsed.skills)

        skill_levels = {
            item.name.lower().strip(): item.proficiency for item in payload.skill_levels
        }
        required = set(role_profile["required"])
        optional = set(role_profile["optional"])
        matched = sorted(resume_skills & required)
        missing = sorted(required - resume_skills)
        stretch = sorted((optional - resume_skills))[:5]
        comparison = []
        for skill in sorted(required):
            current = skill_levels.get(skill.lower(), 70 if skill in resume_skills else 0)
            required_score = 85
            comparison.append(
                GapComparisonItem(
                    skill=skill,
                    current=current,
                    required=required_score,
                    gap=max(0, required_score - current),
                )
            )
        comparison.sort(key=lambda item: item.gap, reverse=True)

        readiness_score = round((len(matched) / len(required)) * 100) if required else 0
        recommendations = self._recommendations(missing, stretch)

        return GapAnalysisResponse(
            target_role=payload.target_role,
            normalized_role=normalized_role.title() if normalized_role != "devops engineer" else "DevOps Engineer",
            readiness_score=readiness_score,
            matched_skills=matched,
            missing_skills=missing,
            stretch_skills=stretch,
            comparison=comparison,
            recommendations=recommendations,
        )

    def _recommendations(self, missing: list[str], stretch: list[str]) -> list[Recommendation]:
        items = []
        for skill in missing[:4]:
            items.append(
                Recommendation(
                    title=f"Prioritize {skill}",
                    detail=f"Focus on {skill} first because it is a required capability for the target role.",
                    priority="high",
                )
            )
        for skill in stretch[:2]:
            items.append(
                Recommendation(
                    title=f"Add {skill} later",
                    detail=f"{skill} is a good second-wave skill once the core gaps are closed.",
                    priority="medium",
                )
            )
        if not items:
            items.append(
                Recommendation(
                    title="You are on track",
                    detail="Your current skills already align well with the selected role. Focus on projects and interview readiness.",
                    priority="low",
                )
            )
        return items


gap_service = GapService()
