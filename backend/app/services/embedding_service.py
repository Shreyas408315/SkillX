from math import sqrt

from google import genai
from google.genai import errors

from app.core.config import settings
from app.services.text_utils import extract_known_skills, keyword_overlap_score


class EmbeddingService:
    """Embedding service abstraction with hosted Gemini fallback support."""

    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    def similarity(self, left_text: str, right_text: str) -> float:
        if self._client:
            try:
                response = self._client.models.embed_content(
                    model=settings.gemini_embedding_model,
                    contents=[left_text, right_text],
                )
                embeddings = getattr(response, "embeddings", None)
                if not embeddings or len(embeddings) < 2:
                    raise ValueError("Unexpected embedding response")

                left_vector = embeddings[0].values
                right_vector = embeddings[1].values
                return round(self._cosine_similarity(left_vector, right_vector), 4)
            except Exception:
                pass

        left_skills = set(extract_known_skills(left_text))
        right_skills = set(extract_known_skills(right_text))
        overlap = keyword_overlap_score(left_skills, right_skills)

        left_words = set(left_text.lower().split())
        right_words = set(right_text.lower().split())
        lexical = keyword_overlap_score(left_words, right_words)

        magnitude_adjustment = 0.0
        if left_words and right_words:
            magnitude_adjustment = min(len(left_words), len(right_words)) / sqrt(len(left_words) * len(right_words))

        score = (0.55 * overlap) + (0.35 * lexical) + (0.10 * magnitude_adjustment)
        return round(min(score, 1.0), 4)

    @property
    def mode(self) -> str:
        return "gemini" if self._client else settings.embeddings_mode

    def _cosine_similarity(self, left_vector: list[float], right_vector: list[float]) -> float:
        numerator = sum(left * right for left, right in zip(left_vector, right_vector))
        left_norm = sqrt(sum(value * value for value in left_vector))
        right_norm = sqrt(sum(value * value for value in right_vector))
        if not left_norm or not right_norm:
            return 0.0
        return max(0.0, min(1.0, numerator / (left_norm * right_norm)))


embedding_service = EmbeddingService()
