from pydantic import BaseModel, Field


class SkillScore(BaseModel):
    skill: str
    score: float = Field(ge=0, le=1)


class Recommendation(BaseModel):
    title: str
    detail: str
    priority: str = "medium"
