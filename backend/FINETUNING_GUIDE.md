# Fine-Tuning LLM Pipeline

Complete guide to fine-tune an open-source LLM on your resume data and integrate with the DTI backend.

## Overview

This fine-tuning pipeline enables you to:
- ✅ Reduce API costs (eliminate Gemini calls)
- ✅ Improve latency (local inference)
- ✅ Custom-tune on your specific data
- ✅ Deploy in multiple ways (Ollama, HuggingFace, integrated backend)

## Quick Start (5 minutes)

```powershell
cd backend

# Install dependencies
pip install transformers datasets torch

# Test with existing mock data
python run_loader.py

# Generate training JSONL (600 pairs)
# Output: fine_tuning/training_pairs_distillation.jsonl
```

## 4-Path Implementation Strategy

### PATH 1: Quick Local Testing (Ollama)
**Best for:** Testing, iteration, no GPU cost
**Time:** 15 minutes | **Hardware:** CPU | **Cost:** Free

```powershell
# Install Ollama: https://ollama.ai
ollama pull neural-chat

# Run quickstart
python ollama_quickstart.py
```

### PATH 2: Production Fine-Tuning (HuggingFace)
**Best for:** Production use, best quality
**Time:** 1-2 hours | **Hardware:** GPU recommended | **Cost:** Free

```powershell
# Fine-tune with small model (CPU-friendly)
python finetune_huggingface.py --model microsoft/phi-2 --epochs 3

# Or larger model (GPU recommended)
python finetune_huggingface.py --model mistralai/Mistral-7B-Instruct-v0.1

# Output: resume_distiller_model/
```

### PATH 3: Backend Integration
**Best for:** Production serving
**Time:** 30 minutes | **Risk:** Low (fallback to Gemini)

```powershell
# Replace Gemini calls with local model
# See distilled_service.py for integration example

# Configure in .env:
# FINE_TUNED_MODEL_TYPE=ollama
# FINE_TUNED_MODEL_PATH=./resume_distiller_model
```

### PATH 4: Real Data Loading
**Best for:** Using actual HuggingFace dataset
**Time:** 5-30 minutes | **Network:** Required

```powershell
# Load local resumes + jobs
python load_training_data_real.py --local-only

# Include HuggingFace dataset
python load_training_data_real.py --from-hf

# Output: fine_tuning/training_data_real.jsonl
```

## File Reference

| File | Purpose | Use Case |
|------|---------|----------|
| `ollama_quickstart.py` | Ollama-based fine-tuning | Quick local testing |
| `finetune_huggingface.py` | HuggingFace fine-tuning | Production training |
| `fine_tuned_inference.py` | Inference wrapper | Testing trained models |
| `distilled_service.py` | Backend integration | Replace Gemini calls |
| `load_training_data_real.py` | Real data loading | Using HF + local data |
| `run_loader.py` | Mock data loading | Fast testing |
| `FINETUNING_RUNBOOK.py` | Complete guide | Reference + wizard |

## Training Data

### Data Sources
1. **HuggingFace** (`gautamsabba/training_data_llama2_resume_distiller`)
   - Pre-labeled resume-job pairs
   - 1000s of examples
   - Streaming support

2. **Local Resumes** (`../data/processed_resumes.cleaned.jsonl`)
   - 2,457 real resumes
   - Cleaned and deduplicated

3. **Local Jobs** (`../job_descriptions.csv`)
   - 200 job descriptions
   - Various roles/industries

## Model Selection Guide

| Model | Size | Speed | Quality | Hardware |
|-------|------|-------|---------|----------|
| TinyLlama | 1.1B | ⚡⚡⚡ | ⭐ | CPU |
| Phi-2 | 2.7B | ⚡⚡ | ⭐⭐ | CPU |
| Mistral-7B | 7B | ⚡ | ⭐⭐⭐ | GPU (14GB) |
| Llama-2-7B | 7B | ⚡ | ⭐⭐⭐ | GPU (15GB) |
| Llama-2-13B | 13B | - | ⭐⭐⭐⭐ | GPU (27GB) |

**Recommended for first-time:**
- CPU: `microsoft/phi-2`
- GPU: `mistralai/Mistral-7B-Instruct-v0.1`

## Installation

```powershell
# Core dependencies
pip install transformers datasets torch

# GPU support (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Ollama (optional, for local testing)
pip install ollama

# HuggingFace (for dataset access)
pip install huggingface-hub

# (Optional) Authenticate with HuggingFace
huggingface-cli login
```

## Usage Examples

### Example 1: Local Testing (Ollama)
```powershell
python ollama_quickstart.py
```

### Example 2: Quick Fine-tine (Phi-2)
```powershell
python finetune_huggingface.py `
    --model microsoft/phi-2 `
    --epochs 3 `
    --batch-size 1
```

### Example 3: Full Fine-tune (Mistral-7B)
```powershell
python finetune_huggingface.py `
    --model mistralai/Mistral-7B-Instruct-v0.1 `
    --epochs 5 `
    --learning-rate 2e-4
```

### Example 4: Test Inference
```powershell
python fine_tuned_inference.py `
    --model huggingface `
    --model-path ./resume_distiller_model `
    --infer "Your test prompt here"
```

### Example 5: Load Real Data
```powershell
python load_training_data_real.py `
    --from-hf `
    --max-pairs 1000 `
    --output fine_tuning/train_1k.jsonl
```

## Backend Integration

### Update Routes

```python
# app/api/routes/resume.py

from distilled_service import get_distilled_pipeline

@app.post('/api/resume/parse')
async def parse_resume(resume_text: str):
    pipeline = get_distilled_pipeline()
    return pipeline.parse_resume(resume_text)

@app.post('/api/match/score')
async def score_match(resume: str, job: str):
    pipeline = get_distilled_pipeline()
    return pipeline.score_match(resume, job)

@app.post('/api/gap/analyze')
async def analyze_gap(target_role: str, skills: List[str]):
    pipeline = get_distilled_pipeline()
    return pipeline.analyze_gap(target_role, skills)
```

### Configuration

```powershell
# .env file
FINE_TUNED_MODEL_TYPE=ollama
FINE_TUNED_MODEL_PATH=./resume_distiller_model
```

### Startup Hook

```python
# app/main.py

from distilled_service import get_distilled_pipeline

@app.on_event('startup')
async def startup():
    pipeline = get_distilled_pipeline()
    logger.info("Distilled pipeline loaded")
```

## Monitoring & Validation

```powershell
# Test inference
python fine_tuned_inference.py --model huggingface

# Parse a resume
python fine_tuned_inference.py --parse-resume path/to/resume.txt

# Benchmark vs Gemini
# (Keep both routes, compare metrics)
```

## Cost Analysis

### Before (Gemini API)
- Per request: $0.01-0.05
- 10k requests/month: $100-500

### After (Fine-tuned Model)
- Per request: $0 (local)
- 10k requests/month: $5-20 (electricity)

**Savings: 90-95% cost reduction**

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `transformers not found` | `pip install transformers datasets torch` |
| CUDA out of memory | `--batch-size 1` or use smaller model |
| `ollama not found` | Install from https://ollama.ai |
| Slow inference | Check GPU usage, monitor memory |
| Poor responses | More training data, adjust epochs |
| HF dataset too large | Use `--max-pairs 1000` or streaming |

## Recommended Sequence

### Week 1: Validation
- **Day 1:** Run Ollama quickstart (PATH 1)
- **Day 2:** Fine-tune Phi-2 on mock data (PATH 2)
- **Day 3:** Integrate with one API route (PATH 3)

### Week 2: Production
- **Day 1:** Load real data (PATH 4)
- **Day 2-3:** Full fine-tune (mistral-7b)
- **Day 4:** Replace all Gemini calls
- **Day 5:** A/B test & optimize

## Next Steps

1. **Install packages:**
   ```powershell
   pip install transformers datasets torch
   ```

2. **Run a quick test:**
   ```powershell
   python run_loader.py
   ```

3. **Try Ollama:**
   ```powershell
   python ollama_quickstart.py
   ```

4. **Fine-tune:**
   ```powershell
   python finetune_huggingface.py --model microsoft/phi-2
   ```

5. **Integrate:**
   See `distilled_service.py` for backend integration example

## References

- [HuggingFace Transformers](https://huggingface.co/docs/transformers/)
- [Ollama](https://ollama.ai)
- [Training Data Dataset](https://huggingface.co/datasets/gautamsabba/training_data_llama2_resume_distiller)
- [PyTorch](https://pytorch.org)

## Support

For issues:
1. Check `FINETUNING_RUNBOOK.py` for detailed guide
2. Review troubleshooting section above
3. Check script's `--help` for all options

---

**Goal:** Fine-tuned model loaded, integrated, and serving requests within 2 weeks.
