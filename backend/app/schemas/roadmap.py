from pydantic import BaseModel, Field


class RoadmapRequest(BaseModel):
    target_role: str
    current_skills: list[str] = Field(default_factory=list)


class RoadmapResponse(BaseModel):
    message: str
