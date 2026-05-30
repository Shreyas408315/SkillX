from fastapi import APIRouter, Query
from typing import Optional

from app.schemas.resume import ResumeParseRequest, ResumeParseResponse
from app.services.resume_parser import resume_parser_service

# Optional: Use distilled model for cheaper inference
try:
    from distilled_service import get_distilled_pipeline
    DISTILLED_AVAILABLE = True
except ImportError:
    DISTILLED_AVAILABLE = False

router = APIRouter()


@router.post("/parse", response_model=ResumeParseResponse)
def parse_resume(payload: ResumeParseRequest, use_distilled: bool = Query(False)):
    """
    Parse resume.
    
    Set use_distilled=true to use fine-tuned model instead of Gemini API.
    Falls back to Gemini if distilled model unavailable.
    """
    if use_distilled and DISTILLED_AVAILABLE:
        try:
            # Use fine-tuned model
            pipeline = get_distilled_pipeline()
            result = pipeline.parse_resume(payload.resume_text, payload.target_role)
            # Convert to response format
            return ResumeParseResponse(
                normalized_role=result.get('normalized_role', 'Unknown'),
                summary=result.get('summary', ''),
                top_skills=result.get('top_skills', []),
                experience_items=[],  # Distilled model doesn't return detailed items
                education_items=[],
                projects=[],
                certifications=result.get('certifications', []),
            )
        except Exception as e:
            # Fallback to Gemini on error
            print(f"Distilled service failed: {e}, falling back to Gemini")
            return resume_parser_service.parse_resume(payload)
    
    # Default: use Gemini
    return resume_parser_service.parse_resume(payload)
