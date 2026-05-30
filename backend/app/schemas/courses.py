from pydantic import BaseModel, Field


class CourseRecommendationRequest(BaseModel):
    missing_skills: list[str] = Field(default_factory=list)
    target_role: str | None = None


class CourseRecommendationResponse(BaseModel):
    message: str
