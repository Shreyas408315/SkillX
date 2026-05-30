#!/usr/bin/env python3
"""
Resume Distiller Training Data Loader
Loads and processes the training_data_llama2_resume_distiller dataset
for NLP experiments and model fine-tuning.
"""

from datasets import load_dataset
import json
import pandas as pd
from pathlib import Path
import sys

from app.schemas.gap_analysis import GapAnalysisRequest
from app.schemas.matching import MatchRequest
from app.schemas.resume import ResumeParseRequest
from app.services.gap_service import gap_service
from app.services.matching_service import matching_service
from app.services.resume_parser import resume_parser_service

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent))

def load_resume_distiller_dataset():
    """Load the training_data_llama2_resume_distiller dataset from Hugging Face."""
    try:
        print("Loading training_data_llama2_resume_distiller dataset...")
        ds = load_dataset("gautamsabba/training_data_llama2_resume_distiller")
        print(f"Dataset loaded successfully. Splits: {list(ds.keys())}")

        # Show dataset info
        for split_name, split_data in ds.items():
            print(f"\n{split_name.upper()} split:")
            print(f"  Number of examples: {len(split_data)}")
            print(f"  Features: {list(split_data.features.keys())}")

            # Show a sample
            if len(split_data) > 0:
                sample = split_data[0]
                print(f"  Sample keys: {list(sample.keys())}")
                for key, value in sample.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"    {key}: {value[:100]}...")
                    else:
                        print(f"    {key}: {value}")

        return ds

    except Exception as e:
        print(f"Error loading dataset: {e}")
        return None

def load_local_datasets():
    """Load local datasets: processed_resumes.cleaned.jsonl and job_descriptions.csv"""
    data_dir = Path(__file__).parent.parent / "data"

    # Load processed resumes
    resumes_file = data_dir / "processed_resumes.cleaned.jsonl"
    if resumes_file.exists():
        print(f"\nLoading processed resumes from {resumes_file}")
        resumes = []
        with open(resumes_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    resumes.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    print(f"Error parsing line: {e}")
        print(f"Loaded {len(resumes)} processed resumes")
    else:
        print(f"Processed resumes file not found: {resumes_file}")
        resumes = []

    # Load job descriptions
    jd_file = data_dir / "job_descriptions.csv"
    if jd_file.exists():
        print(f"\nLoading job descriptions from {jd_file}")
        try:
            job_descriptions = pd.read_csv(jd_file)
            print(f"Loaded {len(job_descriptions)} job descriptions")
            print(f"Columns: {list(job_descriptions.columns)}")
        except Exception as e:
            print(f"Error loading job descriptions: {e}")
            job_descriptions = None
    else:
        print(f"Job descriptions file not found: {jd_file}")
        job_descriptions = None

    # Also check root folder for job_descriptions.csv
    root_jd_file = Path(__file__).parent.parent / "job_descriptions.csv"
    if root_jd_file.exists() and job_descriptions is None:
        print(f"\nLoading job descriptions from root: {root_jd_file}")
        try:
            job_descriptions = pd.read_csv(root_jd_file)
            print(f"Loaded {len(job_descriptions)} job descriptions from root")
        except Exception as e:
            print(f"Error loading job descriptions from root: {e}")
            job_descriptions = None

    return {
        'processed_resumes': resumes,
        'job_descriptions': job_descriptions
    }

def create_training_pairs(hf_dataset, local_data):
    """Create training pairs combining HF dataset with local job descriptions"""
    training_pairs = []

    # Get job descriptions
    jd_df = local_data.get('job_descriptions')
    if jd_df is not None and len(jd_df) > 0:
        job_descriptions = jd_df.to_dict('records')
    else:
        print("No job descriptions available for training pairs")
        return training_pairs

    # Use the train split from HF dataset
    if 'train' in hf_dataset:
        resumes = hf_dataset['train']

        print(f"\nCreating training pairs: {len(resumes)} resumes x {len(job_descriptions)} job descriptions")

        # Create pairs (limit to reasonable size for demo)
        max_pairs = min(1000, len(resumes) * len(job_descriptions))
        pair_count = 0

        for resume in resumes:
            if pair_count >= max_pairs:
                break

            for jd in job_descriptions:
                if pair_count >= max_pairs:
                    break

                pair = {
                    'resume_text': resume.get('text', resume.get('resume', '')),
                    'job_description': jd.get('description', jd.get('text', str(jd))),
                    'resume_id': resume.get('id', f"resume_{pair_count}"),
                    'job_id': jd.get('id', jd.get('role', f"job_{pair_count}"))
                }
                training_pairs.append(pair)
                pair_count += 1

        print(f"Created {len(training_pairs)} training pairs")

    return training_pairs


def save_jsonl(records: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def save_hf_raw_dataset(hf_dataset, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for split in ['train', 'test']:
        output_path = output_dir / f'hf_{split}_raw.jsonl'
        records = [{'text': row['text']} for row in hf_dataset[split]]
        save_jsonl(records, output_path)
        print(f"Saved HF raw {split} dataset to {output_path}")


def create_distillation_examples(training_pairs: list[dict], max_examples: int = 1000) -> list[dict]:
    examples = []
    for idx, pair in enumerate(training_pairs):
        if idx >= max_examples:
            break

        resume_text = pair.get('resume_text', '')
        job_description = pair.get('job_description', '')
        parsed_resume = resume_parser_service.parse_resume(
            ResumeParseRequest(resume_text=resume_text, target_role=None)
        )
        match_response = matching_service.score_match(
            MatchRequest(
                resume_text=resume_text,
                job_description=job_description,
                target_role=parsed_resume.normalized_role,
            )
        )
        gap_response = gap_service.analyze_gap(
            GapAnalysisRequest(
                target_role=parsed_resume.normalized_role or 'Software Engineer',
                resume_skills=parsed_resume.skills,
                skill_levels=[{'name': skill, 'proficiency': 70} for skill in parsed_resume.skills[:10]],
            )
        )

        prompt = (
            "You are a resume distillation assistant. "
            "Given the resume text and the job description below, extract a role-aware summary, top skills, "
            "matched skills, missing skills, readiness, and recommendations. Return only valid JSON.\n\n"
            f"Resume:\n{resume_text}\n\n"
            f"Job Description:\n{job_description}\n\n"
            "Output schema:\n"
            '{"normalized_role": string, "summary": string, "top_skills": [string], "match_score": int, "matched_skills": [string], "missing_skills": [string], "gap_readiness": int, "gap_missing_skills": [string], "recommendations": [string]}'
        )

        completion_obj = {
            'normalized_role': parsed_resume.normalized_role,
            'summary': parsed_resume.summary,
            'top_skills': parsed_resume.skills[:10],
            'match_score': match_response.match_score,
            'matched_skills': match_response.matched_skills,
            'missing_skills': match_response.missing_skills,
            'gap_readiness': gap_response.readiness_score,
            'gap_missing_skills': gap_response.missing_skills,
            'recommendations': [item.detail for item in gap_response.recommendations],
        }

        examples.append({
            'prompt': prompt,
            'completion': json.dumps(completion_obj, ensure_ascii=False),
        })

    return examples


if __name__ == "__main__":
    print("Resume Distiller Dataset Loader")
    print("=" * 40)

    # Load Hugging Face dataset
    hf_dataset = load_resume_distiller_dataset()

    # Load local datasets
    local_data = load_local_datasets()

    # Create training pairs if both are available
    if hf_dataset and local_data.get('job_descriptions') is not None:
        training_pairs = create_training_pairs(hf_dataset, local_data)

        # Save training pairs for later use
        output_file = Path(__file__).parent / "training_pairs.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(training_pairs, f, indent=2, ensure_ascii=False)
        print(f"\nSaved training pairs to {output_file}")

        fine_tune_dir = Path(__file__).parent / "fine_tuning"
        distillation_examples = create_distillation_examples(training_pairs)
        distillation_file = fine_tune_dir / "training_pairs_distillation.jsonl"
        save_jsonl(distillation_examples, distillation_file)
        print(f"Saved distillation dataset to {distillation_file}")

    if hf_dataset:
        fine_tune_dir = Path(__file__).parent / "fine_tuning"
        save_hf_raw_dataset(hf_dataset, fine_tune_dir)

    print("\nDataset loading complete!")