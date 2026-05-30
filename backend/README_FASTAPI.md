# FastAPI AI Backend Scaffold

This project now includes a Python `FastAPI` scaffold for the AI features while leaving the existing Node backend untouched.

## Run

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Optional Gemini configuration

Set these environment variables before starting the API if you want hosted Gemini calls instead of heuristic fallbacks:

```powershell
$env:GEMINI_API_KEY="your_new_key"
$env:GEMINI_CHAT_MODEL="gemini-2.5-flash"
$env:GEMINI_EMBEDDING_MODEL="gemini-embedding-001"
```

## Included endpoints

- `GET /api/health`
- `POST /api/resume/parse`
- `POST /api/match/score`
- `POST /api/gap/analyze`
- `POST /api/roadmap/generate` (second-wave placeholder)
- `POST /api/courses/recommend` (second-wave placeholder)

## Evaluation runner

Run the built-in evaluation script from the backend directory:

```powershell
cd backend
.venv\Scripts\python.exe evaluate_backend.py
```

The script exercises the core resume parse, match score, and gap analysis endpoints against seed evaluation examples.

## Notes

- `frontend/index.html` was intentionally left untouched.
- The current implementation uses deterministic heuristics as a safe fallback.
- `LLM` and embeddings provider hooks are isolated in `app/services/llm_service.py` and `app/services/embedding_service.py`.
- Evaluation seed files are available in:
  - [eval_resume_parse_samples.json](/c:/Users/shrey/OneDrive/Desktop/DTI/backend/eval_resume_parse_samples.json)
  - [eval_match_samples.json](/c:/Users/shrey/OneDrive/Desktop/DTI/backend/eval_match_samples.json)
  - [eval_gap_analysis_samples.json](/c:/Users/shrey/OneDrive/Desktop/DTI/backend/eval_gap_analysis_samples.json)
