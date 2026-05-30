from fastapi import APIRouter

from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "llm_mode": llm_service.mode,
        "embeddings_mode": embedding_service.mode,
    }
