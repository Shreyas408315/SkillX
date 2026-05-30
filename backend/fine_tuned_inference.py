#!/usr/bin/env python3
"""
Inference with fine-tuned models.

This module provides:
1. Local inference (Ollama, HuggingFace)
2. API integration for backend services
3. Drop-in replacement for Gemini services

Usage:
    from fine_tuned_inference import FineTunedResumePipeline
    
    pipeline = FineTunedResumePipeline(model_type='ollama')
    result = pipeline.parse_resume("resume text", target_role="Backend Developer")
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
import sys


class FineTunedResumePipeline:
    """
    Unified inference interface for resume distillation.
    Supports: Ollama, Hugging Face, or other LLM backends.
    """
    
    def __init__(
        self,
        model_type: str = 'ollama',
        model_name: Optional[str] = None,
        model_path: Optional[str] = None,
    ):
        """
        Initialize pipeline.
        
        Args:
            model_type: 'ollama' or 'huggingface'
            model_name: Ollama model name (e.g., 'neural-chat')
            model_path: Path to HF fine-tuned model directory
        """
        self.model_type = model_type
        self.model_name = model_name or 'neural-chat'
        self.model_path = model_path
        
        if model_type == 'huggingface':
            self._init_huggingface()
        elif model_type == 'ollama':
            self._init_ollama()
    
    def _init_ollama(self):
        """Initialize Ollama client."""
        self.client = None
        # Ollama will be called via CLI
        print(f"Configured for Ollama ({self.model_name})")
    
    def _init_huggingface(self):
        """Initialize Hugging Face model."""
        try:
            from transformers import (
                AutoTokenizer,
                AutoModelForCausalLM,
            )
            import torch
            
            model_path = self.model_path or './resume_distiller_model'
            if not Path(model_path).exists():
                print(f"❌ Model path not found: {model_path}")
                print("   Run: python finetune_huggingface.py")
                sys.exit(1)
            
            print(f"Loading model from {model_path}...")
            self.tokenizer = AutoTokenizer.from_pretrained(f"{model_path}/tokenizer")
            self.model = AutoModelForCausalLM.from_pretrained(
                f"{model_path}/model",
                torch_dtype=torch.bfloat16,
                trust_remote_code=True,
            )
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model = self.model.to(self.device)
            print(f"Model loaded on {self.device}")
            
        except ImportError:
            print("❌ Transformers not installed")
            print("   pip install transformers torch")
            sys.exit(1)
    
    def _infer_ollama(self, prompt: str) -> str:
        """Run inference with Ollama."""
        try:
            result = subprocess.run(
                ['ollama', 'run', self.model_name, prompt],
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"Ollama error: {e}")
            return "{}"
    
    def _infer_huggingface(self, prompt: str, max_tokens: int = 512) -> str:
        """Run inference with Hugging Face model."""
        try:
            import torch
            
            inputs = self.tokenizer(
                prompt,
                return_tensors='pt',
                truncation=True,
                max_length=1024,
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                )
            
            generated_tokens = outputs[0][inputs['input_ids'].shape[-1]:]
            response = self.tokenizer.decode(
                generated_tokens,
                skip_special_tokens=True,
            )
            return response.strip()
        except Exception as e:
            print(f"HF inference error: {e}")
            return "{}"
    
    def _infer(self, prompt: str) -> str:
        """Internal inference wrapper."""
        if self.model_type == 'ollama':
            return self._infer_ollama(prompt)
        elif self.model_type == 'huggingface':
            return self._infer_huggingface(prompt)
        return "{}"
    
    def parse_resume(
        self,
        resume_text: str,
        target_role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Parse resume and extract relevant information.
        
        Returns dict with:
            - normalized_role
            - summary
            - top_skills
            - experience
            - education
            - certifications
        """
        resume_text = resume_text.strip()
        prompt = f"""
You are a resume parser that must return valid JSON only.
Do not repeat the instructions or the resume text.
Respond with a single JSON object containing exactly these keys:
- normalized_role
- summary
- top_skills
- experience
- education
- certifications

Resume:
{resume_text}

Return valid JSON only.
"""
        
        response = self._infer(prompt)
        
        # Extract JSON from response
        try:
            # Try direct JSON parse
            return json.loads(response)
        except:
            # Try to find JSON in response
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
            except:
                pass
        
        # Fallback
        return {
            'normalized_role': target_role or 'Unknown',
            'summary': resume_text[:200],
            'top_skills': [],
            'experience': 'Unknown',
            'education': [],
            'certifications': [],
        }
    
    def score_match(
        self,
        resume_text: str,
        job_description: str,
        target_role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Score resume vs job description match.
        
        Returns dict with:
            - match_score (0-100)
            - matched_skills
            - missing_skills
            - recommendations
        """
        prompt = f"""
Score how well this resume matches the job requirements.

Resume:
{resume_text}

Job Description:
{job_description}

Provide in JSON:
- match_score: 0-100
- matched_skills: Array of matching skills
- missing_skills: Array of required but missing skills
- recommendations: Array of improvement suggestions
"""
        
        response = self._infer(prompt)
        
        try:
            # Extract JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        
        # Fallback
        return {
            'match_score': 50,
            'matched_skills': [],
            'missing_skills': [],
            'recommendations': [],
        }
    
    def analyze_gap(
        self,
        target_role: str,
        current_skills: List[str],
    ) -> Dict[str, Any]:
        """
        Analyze skill gaps for a target role.
        
        Returns dict with:
            - gap_readiness (0-100)
            - missing_skills
            - stretch_skills
            - learning_path
        """
        skills_str = ', '.join(current_skills)
        
        prompt = f"""
Analyze readiness for {target_role} role.

Current skills: {skills_str}

Provide in JSON:
- gap_readiness: 0-100 readiness score
- missing_skills: Critical skills to learn
- stretch_skills: Nice-to-have advances skills
- learning_path: Suggested learning order
"""
        
        response = self._infer(prompt)
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        
        # Fallback
        return {
            'gap_readiness': 50,
            'missing_skills': [],
            'stretch_skills': [],
            'learning_path': [],
        }


def main():
    """Test the inference pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test fine-tuned model inference")
    parser.add_argument('--model', default='ollama',
                        choices=['ollama', 'huggingface'])
    parser.add_argument('--model-name', default='neural-chat',
                        help='Ollama model name')
    parser.add_argument('--model-path', default='./resume_distiller_model',
                        help='Path to HF fine-tuned model')
    parser.add_argument('--infer', type=str,
                        help='Test prompt')
    parser.add_argument('--parse-resume', type=str,
                        help='Path to resume file to parse')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    print(f"\nInitializing {args.model} pipeline...")
    pipeline = FineTunedResumePipeline(
        model_type=args.model,
        model_name=args.model_name,
        model_path=args.model_path,
    )
    
    if args.infer:
        print(f"\nPrompt: {args.infer}")
        response = pipeline._infer(args.infer)
        print(f"\nResponse:\n{response}")
    
    elif args.parse_resume:
        print(f"\nParsing: {args.parse_resume}")
        with open(args.parse_resume, 'r') as f:
            resume = f.read()
        result = pipeline.parse_resume(resume)
        print(f"\nResult:")
        print(json.dumps(result, indent=2))
    
    else:
        print("""
Pipeline initialized successfully!

Usage examples:
  python fine_tuned_inference.py --infer "your prompt"
  python fine_tuned_inference.py --parse-resume path/to/resume.txt
  python fine_tuned_inference.py --model huggingface --model-path ./model
        """)


if __name__ == '__main__':
    main()
