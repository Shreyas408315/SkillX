import re

from app.schemas.common import Recommendation
from app.schemas.matching import MatchRequest, MatchResponse, MatchSectionScores
from app.schemas.resume import ResumeParseRequest
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service
from app.services.resume_parser import resume_parser_service
from app.services.text_utils import extract_known_skills, normalize_skill


class MatchingService:
    def score_match(self, payload: MatchRequest) -> MatchResponse:
        parsed_resume = resume_parser_service.parse_resume(
            ResumeParseRequest(resume_text=payload.resume_text, target_role=payload.target_role)
        )
        resume_skills = {normalize_skill(skill) for skill in parsed_resume.skills}
        jd_skills = {normalize_skill(skill) for skill in extract_known_skills(payload.job_description)}

        matched_skills = sorted(resume_skills & jd_skills)
        missing_skills = sorted(jd_skills - resume_skills)
        additional_resume_skills = sorted(resume_skills - jd_skills)

        technical_score = self._weighted_overlap(resume_skills, jd_skills, max_points=50)
        experience_score = self._experience_score(payload.resume_text, max_points=25)
        education_score = self._education_score(payload.resume_text, max_points=10)
        projects_score = self._projects_score(payload.resume_text, max_points=15)
        similarity_score = round(embedding_service.similarity(payload.resume_text, payload.job_description) * 100)

        raw_score = technical_score + experience_score + education_score + projects_score
        match_score = round((raw_score * 0.7) + (similarity_score * 0.3))
        match_score = max(0, min(match_score, 100))

        explanation = llm_service.summarize_match(
            role=payload.target_role or parsed_resume.normalized_role,
            match_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
        )

        recommendations = self._recommendations(missing_skills)

        return MatchResponse(
            match_score=match_score,
            normalized_role=parsed_resume.normalized_role,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            additional_resume_skills=additional_resume_skills[:10],
            section_scores=MatchSectionScores(
                technical_skills=technical_score,
                experience=experience_score,
                education=education_score,
                projects=projects_score,
                semantic_similarity=similarity_score,
            ),
            explanation=explanation,
            recommendations=recommendations,
            parser_mode=parsed_resume.parser_mode,
            embeddings_mode=embedding_service.mode,
        )

    def _weighted_overlap(self, resume_skills: set[str], jd_skills: set[str], *, max_points: int) -> int:
        if not jd_skills:
            return 0
        return round((len(resume_skills & jd_skills) / len(jd_skills)) * max_points)

    def _experience_score(self, resume_text: str, *, max_points: int) -> int:
        text = resume_text.lower()
        matches = [int(value) for value in re.findall(r"(\d+)\+?\s*(?:years|year)", text)]
        if matches:
            years = max(matches)
            return min(max_points, round((years / 5) * max_points))
        if "experience" in text or "built" in text or "developed" in text:
            return round(max_points * 0.4)
        return round(max_points * 0.2)

    def _education_score(self, resume_text: str, *, max_points: int) -> int:
        text = resume_text.lower()
        if any(token in text for token in ["master", "m.tech", "mca", "mba"]):
            return max_points
        if any(token in text for token in ["bachelor", "b.tech", "b.e", "bca", "degree"]):
            return round(max_points * 0.8)
        return round(max_points * 0.3)

    def _projects_score(self, resume_text: str, *, max_points: int) -> int:
        text = resume_text.lower()
        indicators = sum(1 for token in ["project", "built", "developed", "implemented", "deployed"] if token in text)
        return min(max_points, indicators * 3)

    def _recommendations(self, missing_skills: list[str]) -> list[Recommendation]:
        recommendations = []
        for skill in missing_skills[:3]:
            recommendations.append(
                Recommendation(
                    title=f"Strengthen {skill}",
                    detail=f"Add a project or measurable experience that demonstrates {skill}.",
                    priority="high",
                )
            )
        if not recommendations:
            recommendations.append(
                Recommendation(
                    title="Refine resume targeting",
                    detail="Your skill overlap is already strong. Tailor the summary and projects to the job description.",
                    priority="medium",
                )
            )
        return recommendations


matching_service = MatchingService()
