from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Resume Screening API"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    llm_mode: str = "heuristic"
    embeddings_mode: str = "heuristic"
    gemini_api_key: str | None = None
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    processed_resumes_path: Path = ROOT_DIR / "data" / "processed_resumes.cleaned.jsonl"
    job_descriptions_path: Path = ROOT_DIR / "job_descriptions.csv"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
