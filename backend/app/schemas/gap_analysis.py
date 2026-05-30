from pydantic import BaseModel, Field

from app.schemas.common import Recommendation


class SkillLevel(BaseModel):
    name: str
    proficiency: int = Field(ge=0, le=100)


class GapComparisonItem(BaseModel):
    skill: str
    current: int = Field(ge=0, le=100)
    required: int = Field(ge=0, le=100)
    gap: int = Field(ge=0, le=100)


class GapAnalysisRequest(BaseModel):
    target_role: str
    resume_skills: list[str] = Field(default_factory=list)
    resume_text: str | None = None
    skill_levels: list[SkillLevel] = Field(default_factory=list)


class GapAnalysisResponse(BaseModel):
    target_role: str
    normalized_role: str
    readiness_score: int = Field(ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    stretch_skills: list[str] = Field(default_factory=list)
    comparison: list[GapComparisonItem] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
