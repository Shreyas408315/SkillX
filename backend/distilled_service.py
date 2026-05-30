#!/usr/bin/env python3
"""
Service integration layer replacing Gemini calls with fine-tuned model.

This module provides drop-in replacements for:
  - resume_parser_service.parse_resume()
  - matching_service.score_match()
  - gap_service.analyze_gap()

Deploy this to replace expensive Gemini API calls with fine-tuned models.

Configuration:
  Set FINE_TUNED_MODEL_TYPE env var: 'ollama' or 'huggingface'
  Set FINE_TUNED_MODEL_PATH: path to HF model (if using huggingface)
"""

import os
import json
from typing import Optional, Dict, Any, List
from fine_tuned_inference import FineTunedResumePipeline


class DistilledResumePipeline:
    """Unified interface replacing all resume analysis services."""
    
    def __init__(
        self,
        model_type: Optional[str] = None,
        model_path: Optional[str] = None,
        use_gemini_fallback: bool = True,
    ):
        """
        Initialize distilled pipeline.
        
        Args:
            model_type: 'ollama' or 'huggingface' (from env if not provided)
            model_path: Path to HF model (from env if not provided)
            use_gemini_fallback: Fall back to Gemini if inference fails
        """
        self.model_type = model_type or os.getenv('FINE_TUNED_MODEL_TYPE', 'ollama')
        self.model_path = model_path or os.getenv('FINE_TUNED_MODEL_PATH', './resume_distiller_model')
        self.use_gemini_fallback = use_gemini_fallback
        
        # Try to initialize fine-tuned model
        self.fine_tuned = None
        self._init_fine_tuned()
        
        # Initialize fallback (Gemini)
        self.gemini_available = False
        self._init_gemini()
    
    def _init_fine_tuned(self):
        """Initialize fine-tuned model."""
        try:
            print(f"Initializing {self.model_type} model...")
            self.fine_tuned = FineTunedResumePipeline(
                model_type=self.model_type,
                model_path=self.model_path,
            )
            print(f"✓ Fine-tuned model ready")
        except Exception as e:
            print(f"⚠ Fine-tuned model unavailable: {e}")
            if not self.use_gemini_fallback:
                raise
    
    def _init_gemini(self):
        """Initialize Gemini fallback."""
        try:
            from app.services.llm_service import analyze_with_gemini
            self.analyze_with_gemini = analyze_with_gemini
            self.gemini_available = True
            print("✓ Gemini fallback available")
        except ImportError:
            print("⚠ Gemini fallback not available")
    
    # ========== RESUME PARSING ==========
    
    def parse_resume(self, resume_text: str, target_role: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse resume and extract information.
        
        DROP-IN REPLACEMENT for:
            resume_parser_service.parse_resume()
        
        Returns:
            {
                "normalized_role": str,
                "summary": str,
                "top_skills": [str],
                "experience": str,
                "education": [str],
                "certifications": [str]
            }
        """
        if self.fine_tuned:
            try:
                result = self.fine_tuned.parse_resume(resume_text, target_role)
                return result
            except Exception as e:
                print(f"Fine-tuned inference failed: {e}")
                if not self.use_gemini_fallback:
                    return self._fallback_parse_resume(resume_text)
        
        # Fallback to Gemini
        if self.gemini_available:
            prompt = f"""Parse this resume and extract:
- normalized_role: Primary job role
- summary: Professional summary
- top_skills: Top 10 technical skills
- experience: Years of experience
- education: Degrees
- certifications: Certifications

Resume:
{resume_text}

Return JSON only."""
            
            try:
                response = self.analyze_with_gemini(prompt)
                return json.loads(response)
            except:
                return self._fallback_parse_resume(resume_text)
        
        return self._fallback_parse_resume(resume_text)
    
    def _fallback_parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """Fallback parsing without external services."""
        return {
            'normalized_role': 'Unknown',
            'summary': resume_text[:300],
            'top_skills': [],
            'experience': 'Unknown',
            'education': [],
            'certifications': [],
        }
    
    # ========== MATCHING ==========
    
    def score_match(
        self,
        resume_text: str,
        job_description: str,
        target_role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Score resume vs job match.
        
        DROP-IN REPLACEMENT for:
            matching_service.score_match()
        
        Returns:
            {
                "match_score": 0-100,
                "matched_skills": [str],
                "missing_skills": [str],
                "recommendations": [str]
            }
        """
        if self.fine_tuned:
            try:
                result = self.fine_tuned.score_match(resume_text, job_description, target_role)
                return result
            except Exception as e:
                print(f"Fine-tuned matching failed: {e}")
                if not self.use_gemini_fallback:
                    return self._fallback_match()
        
        # Fallback to Gemini
        if self.gemini_available:
            prompt = f"""Score resume vs job match.

Resume:
{resume_text}

Job:
{job_description}

Return JSON:
- match_score: 0-100
- matched_skills: []
- missing_skills: []
- recommendations: []"""
            
            try:
                response = self.analyze_with_gemini(prompt)
                return json.loads(response)
            except:
                return self._fallback_match()
        
        return self._fallback_match()
    
    def _fallback_match(self) -> Dict[str, Any]:
        """Fallback matching without external services."""
        return {
            'match_score': 50,
            'matched_skills': [],
            'missing_skills': [],
            'recommendations': [],
        }
    
    # ========== GAP ANALYSIS ==========
    
    def analyze_gap(
        self,
        target_role: str,
        current_skills: List[str],
    ) -> Dict[str, Any]:
        """
        Analyze skill gaps for target role.
        
        DROP-IN REPLACEMENT for:
            gap_service.analyze_gap()
        
        Returns:
            {
                "gap_readiness": 0-100,
                "missing_skills": [str],
                "stretch_skills": [str],
                "learning_path": [str]
            }
        """
        if self.fine_tuned:
            try:
                result = self.fine_tuned.analyze_gap(target_role, current_skills)
                return result
            except Exception as e:
                print(f"Fine-tuned gap analysis failed: {e}")
                if not self.use_gemini_fallback:
                    return self._fallback_gap(target_role)
        
        # Fallback to Gemini
        if self.gemini_available:
            skills_str = ', '.join(current_skills)
            prompt = f"""Analyze skill gaps for {target_role}.

Current skills: {skills_str}

Return JSON:
- gap_readiness: 0-100
- missing_skills: []
- stretch_skills: []
- learning_path: []"""
            
            try:
                response = self.analyze_with_gemini(prompt)
                return json.loads(response)
            except:
                return self._fallback_gap(target_role)
        
        return self._fallback_gap(target_role)
    
    def _fallback_gap(self, target_role: str) -> Dict[str, Any]:
        """Fallback gap analysis without external services."""
        return {
            'gap_readiness': 50,
            'missing_skills': [],
            'stretch_skills': [],
            'learning_path': [],
        }


# Singleton instance for use in routes
_pipeline_instance = None


def get_distilled_pipeline(
    model_type: Optional[str] = None,
    model_path: Optional[str] = None,
) -> DistilledResumePipeline:
    """Get or create singleton pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = DistilledResumePipeline(
            model_type=model_type,
            model_path=model_path,
        )
    return _pipeline_instance


# ========== EXAMPLE INTEGRATION ==========

if __name__ == '__main__':
    """
    Example integration in FastAPI route:
    
    from distilled_service import get_distilled_pipeline
    
    @app.post('/api/resume/parse-distilled')
    async def parse_resume_distilled(resume_text: str):
        pipeline = get_distilled_pipeline()
        result = pipeline.parse_resume(resume_text)
        return result
    
    @app.post('/api/matching/score-distilled')
    async def score_match_distilled(resume: str, job: str):
        pipeline = get_distilled_pipeline()
        result = pipeline.score_match(resume, job)
        return result
    
    @app.post('/api/gap/analyze-distilled')
    async def analyze_gap_distilled(target_role: str, skills: List[str]):
        pipeline = get_distilled_pipeline()
        result = pipeline.analyze_gap(target_role, skills)
        return result
    """
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Test distilled service integration")
    parser.add_argument('--model', default='ollama', choices=['ollama', 'huggingface'])
    parser.add_argument('--test-parse', action='store_true')
    parser.add_argument('--test-match', action='store_true')
    parser.add_argument('--test-gap', action='store_true')
    
    args = parser.parse_args()
    
    print("\n🚀 Initializing distilled pipeline...")
    pipeline = get_distilled_pipeline(model_type=args.model)
    
    # Test data
    sample_resume = """
    Senior Backend Developer
    - 5 years experience building REST APIs
    - Proficient in Python, Go, TypeScript
    - Experience with Docker, Kubernetes, PostgreSQL
    - Strong in system design and databases
    """
    
    sample_job = """
    Backend Developer (5+ years)
    Required: Python, REST APIs, SQL
    Nice to have: Go, Kubernetes, Docker
    """
    
    if args.test_parse or not any([args.test_match, args.test_gap]):
        print("\n📋 Testing parse_resume...")
        result = pipeline.parse_resume(sample_resume)
        print("Result:", json.dumps(result, indent=2))
    
    if args.test_match:
        print("\n🎯 Testing score_match...")
        result = pipeline.score_match(sample_resume, sample_job)
        print("Result:", json.dumps(result, indent=2))
    
    if args.test_gap:
        print("\n📈 Testing analyze_gap...")
        result = pipeline.analyze_gap("Senior Backend Engineer", ["Python", "Docker"])
        print("Result:", json.dumps(result, indent=2))
