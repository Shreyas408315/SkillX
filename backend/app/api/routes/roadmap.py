from fastapi import APIRouter, HTTPException

from app.schemas.roadmap import RoadmapRequest, RoadmapResponse


router = APIRouter()


@router.post("/generate", response_model=RoadmapResponse)
def generate_roadmap(_: RoadmapRequest):
    raise HTTPException(
        status_code=501,
        detail="Roadmap generation is planned for the second wave of AI features.",
    )
