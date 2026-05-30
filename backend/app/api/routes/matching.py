from fastapi import APIRouter, Query
from typing import Optional

from app.schemas.matching import MatchRequest, MatchResponse, MatchSectionScores
from app.schemas.common import Recommendation
from app.services.matching_service import matching_service

# Optional: Use distilled model for cheaper inference
try:
    from distilled_service import get_distilled_pipeline
    DISTILLED_AVAILABLE = True
except ImportError:
    DISTILLED_AVAILABLE = False

router = APIRouter()


@router.post("/score", response_model=MatchResponse)
def score_match(payload: MatchRequest, use_distilled: bool = Query(False)):
    """
    Score resume vs job match.
    
    Set use_distilled=true to use fine-tuned model instead of Gemini API.
    Falls back to Gemini if distilled model unavailable.
    """
    if use_distilled and DISTILLED_AVAILABLE:
        try:
            # Use fine-tuned model
            pipeline = get_distilled_pipeline()
            result = pipeline.score_match(payload.resume_text, payload.job_description, payload.target_role)
            
            # Convert to response format
            match_score = result.get('match_score', 50)
            return MatchResponse(
                match_score=int(match_score) if 0 <= int(match_score) <= 100 else 50,
                normalized_role=payload.target_role,
                matched_skills=result.get('matched_skills', []),
                missing_skills=result.get('missing_skills', []),
                additional_resume_skills=[],
                section_scores=MatchSectionScores(
                    technical_skills=int(match_score * 0.4) if 0 <= int(match_score * 0.4) <= 100 else 50,
                    experience=int(match_score * 0.25) if 0 <= int(match_score * 0.25) <= 100 else 50,
                    education=int(match_score * 0.15) if 0 <= int(match_score * 0.15) <= 100 else 50,
                    projects=int(match_score * 0.1) if 0 <= int(match_score * 0.1) <= 100 else 50,
                    semantic_similarity=int(match_score) if 0 <= int(match_score) <= 100 else 50,
                ),
                explanation=f"Distilled model assessment: {match_score}% match",
                recommendations=[
                    Recommendation(category="skill", content=skill) 
                    for skill in result.get('recommendations', [])
                ],
                parser_mode="distilled",
                embeddings_mode="distilled",
            )
        except Exception as e:
            # Fallback to Gemini on error
            print(f"Distilled service failed: {e}, falling back to Gemini")
            return matching_service.score_match(payload)
    
    # Default: use Gemini
    return matching_service.score_match(payload)
