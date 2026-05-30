from fastapi import APIRouter, Query
from typing import Optional

from app.schemas.gap_analysis import GapAnalysisRequest, GapAnalysisResponse
from app.services.gap_service import gap_service

# Optional: Use distilled model for cheaper inference
try:
    from distilled_service import get_distilled_pipeline
    DISTILLED_AVAILABLE = True
except ImportError:
    DISTILLED_AVAILABLE = False

router = APIRouter()


@router.post("/analyze", response_model=GapAnalysisResponse)
def analyze_gap(payload: GapAnalysisRequest, use_distilled: bool = Query(False)):
    """
    Analyze skill gaps for target role.
    
    Set use_distilled=true to use fine-tuned model instead of Gemini API.
    Falls back to Gemini if distilled model unavailable.
    """
    if use_distilled and DISTILLED_AVAILABLE:
        try:
            # Use fine-tuned model
            pipeline = get_distilled_pipeline()
            skills = payload.resume_skills if payload.resume_skills else []
            result = pipeline.analyze_gap(payload.target_role, skills)
            
            # Convert to response format
            readiness = result.get('gap_readiness', 50)
            return GapAnalysisResponse(
                target_role=payload.target_role,
                normalized_role=payload.target_role,
                readiness_score=int(readiness) if 0 <= int(readiness) <= 100 else 50,
                matched_skills=payload.resume_skills if payload.resume_skills else [],
                missing_skills=result.get('missing_skills', []),
                stretch_skills=result.get('stretch_skills', []),
                learning_path=result.get('learning_path', []),
                recommendations=[],
            )
        except Exception as e:
            # Fallback to Gemini on error
            print(f"Distilled service failed: {e}, falling back to Gemini")
            return gap_service.analyze_gap(payload)
    
    # Default: use Gemini
    return gap_service.analyze_gap(payload)
