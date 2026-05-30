from pydantic import BaseModel, Field


class ResumeParseRequest(BaseModel):
    resume_text: str = Field(min_length=20)
    target_role: str | None = None


class ExperienceItem(BaseModel):
    title: str | None = None
    company: str | None = None
    duration_text: str | None = None
    duration_months: int | None = None
    responsibilities: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    degree: str | None = None
    field: str | None = None
    institution: str | None = None
    graduation_date: str | None = None


class ProjectItem(BaseModel):
    name: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class ResumeParseResponse(BaseModel):
    summary: str
    normalized_role: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    total_experience_months: int = 0
    parser_mode: str
