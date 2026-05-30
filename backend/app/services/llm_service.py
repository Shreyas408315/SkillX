import json
import re
from typing import Any

from google import genai
from google.genai import types

from app.core.config import settings


class LLMService:
    """LLM provider abstraction for hosted Gemini and safe fallback behavior."""

    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    @property
    def mode(self) -> str:
        return "gemini" if self._client else settings.llm_mode

    def _generate_content(self, *, model: str, contents: str, response_mime_type: str | None = None, temperature: float = 0.2):
        if not self._client:
            return None
        try:
            return self._client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    response_mime_type=response_mime_type,
                ),
            )
        except Exception:
            return None

    def parse_resume_structured(self, *, resume_text: str, target_role: str | None = None) -> dict[str, Any] | None:
        if not self._client:
            return None

        role_hint = f"Target role hint: {target_role}." if target_role else "No explicit target role was provided."
        prompt = f"""
You are a resume parser. Extract the resume information below and return only valid JSON.

Output schema:
{{
  "summary": string,
  "normalized_role": string or null,
  "skills": [string],
  "experience": [{{"title": string or null, "company": string or null, "duration_text": string or null, "duration_months": integer, "responsibilities": [string]}}],
  "education": [{{"degree": string or null, "field": string or null, "institution": string or null, "graduation_date": string or null}}],
  "projects": [{{"name": string or null, "description": string or null, "technologies": [string]}}],
  "certifications": [string],
  "total_experience_months": integer
}}

Rules:
- Return only JSON with no surrounding text, markdown, or explanation.
- Normalize skills to simple, lowercase terms.
- Use null only when the value truly does not exist.
- Use an empty list when a block is missing.
- If duration in months is unclear, use 0.
- {role_hint}

Resume:
{resume_text}
""".strip()

        response = self._generate_content(
            model=settings.gemini_chat_model,
            contents=prompt,
            response_mime_type="application/json",
            temperature=0.1,
        )
        if not response:
            return None

        content = getattr(response, "text", "") or ""
        if not content:
            return None

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                return None
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None

    def summarize_match(self, *, role: str | None, match_score: int, matched_skills: list[str], missing_skills: list[str]) -> str:
        if self._client:
            prompt = f"""
Write a concise recruiter-friendly explanation in 2-3 sentences. Use the skills list and score clearly.
Role: {role or "target role"}
Match score: {match_score}
Matched skills: {matched_skills}
Missing skills: {missing_skills}
""".strip()
            response = self._generate_content(
                model=settings.gemini_chat_model,
                contents=prompt,
                temperature=0.2,
            )
            if response and getattr(response, "text", ""):
                return response.text.strip()

        role_text = role or "the target role"
        if not missing_skills:
            return (
                f"The candidate aligns strongly with {role_text}, with a solid score of {match_score}%. "
                f"Key matched skills include {', '.join(matched_skills[:5]) or 'relevant experience'}."
            )
        return (
            f"The candidate shows a {match_score}% fit for {role_text}. "
            f"Matched skills include {', '.join(matched_skills[:5]) or 'a partial overlap'}, "
            f"while the largest gaps are {', '.join(missing_skills[:5])}."
        )


llm_service = LLMService()
