from pydantic import BaseModel, Field

from app.schemas.common import Recommendation


class MatchRequest(BaseModel):
    resume_text: str = Field(min_length=20)
    job_description: str = Field(min_length=20)
    target_role: str | None = None


class MatchSectionScores(BaseModel):
    technical_skills: int
    experience: int
    education: int
    projects: int
    semantic_similarity: int


class MatchResponse(BaseModel):
    match_score: int = Field(ge=0, le=100)
    normalized_role: str | None = None
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    additional_resume_skills: list[str] = Field(default_factory=list)
    section_scores: MatchSectionScores
    explanation: str
    recommendations: list[Recommendation] = Field(default_factory=list)
    parser_mode: str
    embeddings_mode: str
