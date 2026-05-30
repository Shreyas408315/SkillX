from fastapi import APIRouter, HTTPException

from app.schemas.courses import CourseRecommendationRequest, CourseRecommendationResponse


router = APIRouter()


@router.post("/recommend", response_model=CourseRecommendationResponse)
def recommend_courses(_: CourseRecommendationRequest):
    raise HTTPException(
        status_code=501,
        detail="Course recommendation is planned for the second wave of AI features.",
    )
