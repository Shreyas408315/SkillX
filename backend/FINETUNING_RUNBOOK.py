#!/usr/bin/env python3
"""
FINE-TUNING IMPLEMENTATION RUNBOOK

Complete end-to-end guide for fine-tuning your LLM and integrating
into the DTI backend, replacing expensive Gemini API calls.

🎯 GOALS:
  ✓ Reduce API costs (eliminate Gemini calls)
  ✓ Improve latency (local inference)
  ✓ Fine-tune on your specific data
  ✓ Deploy in 4 different ways

📋 4-PATH IMPLEMENTATION STRATEGY
=====================================

PATH 1: QUICK LOCAL TESTING (Ollama/LM Studio)
  │
  ├─ Install Ollama
  ├─ Run ollama_quickstart.py
  ├─ Test inference locally
  └─ Iterate on training data
  
  TIMELINE: 15 mins | HARDWARE: CPU ok | COST: Free

PATH 2: PRODUCTION FINE-TUNING (HuggingFace)
  │
  ├─ Load real data (load_training_data_real.py)
  ├─ Fine-tune (finetune_huggingface.py)
  ├─ Save model to disk
  └─ Test inference (fine_tuned_inference.py)
  
  TIMELINE: 1-2 hours | HARDWARE: GPU recommended | COST: Free

PATH 3: BACKEND INTEGRATION
  │
  ├─ Use distilled_service.py
  ├─ Update API routes
  ├─ Add fallback to Gemini
  └─ A/B test results
  
  TIMELINE: 30 mins | HARDWARE: Depends on model | COST: Reduced

PATH 4: REAL DATA LOADING
  │
  ├─ Configure HuggingFace auth
  ├─ Run load_training_data_real.py --from-hf
  ├─ Validate output JSONL
  └─ Use for fine-tuning
  
  TIMELINE: Varies | HARDWARE: None | COST: Free

═══════════════════════════════════════════════════════════════════

QUICK START (Path 1 + 2)
========================

STEP 1: Install Required Packages
──────────────────────────────────

pip install transformers datasets torch
# GPU (if available):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For Ollama integration:
pip install ollama

STEP 2: Prepare Training Data (Local)
──────────────────────────────────────

# Uses existing local data (processed_resumes.cleaned.jsonl + job_descriptions.csv)
cd backend
python run_loader.py

# Output: fine_tuning/training_pairs_distillation.jsonl (5-600 pairs)

STEP 3: Quick Test with Ollama (Path 1)
────────────────────────────────────────

# Install Ollama: https://ollama.ai
# Then pull a model:
ollama pull neural-chat

# Run quickstart:
python ollama_quickstart.py

# Or use LM Studio GUI for visual interface

STEP 4: Train with HuggingFace (Path 2)
────────────────────────────────────────

# Small model (2.7B, CPU-friendly):
python finetune_huggingface.py \\
    --model microsoft/phi-2 \\
    --epochs 3 \\
    --batch-size 1

# Medium model (7B, GPU recommended):
python finetune_huggingface.py \\
    --model mistralai/Mistral-7B-Instruct-v0.1 \\
    --epochs 5

# Output: resume_distiller_model/

STEP 5: Test Fine-Tuned Model
──────────────────────────────

python fine_tuned_inference.py \\
    --model huggingface \\
    --model-path ./resume_distiller_model

STEP 6: Integrate with Backend (Path 3)
───────────────────────────────────────

# See BACKEND INTEGRATION section below

═══════════════════════════════════════════════════════════════════

DETAILED PATH DESCRIPTIONS
==========================

PATH 1: QUICK LOCAL TESTING (Ollama/LM Studio)
───────────────────────────────────────────────

PURPOSE: Test the pipeline quickly without GPU costs

STEPS:
1. Install Ollama (https://ollama.ai) or LM Studio (https://lmstudio.ai)

2. For Ollama (CLI):
   ollama pull neural-chat
   python ollama_quickstart.py
   
3. For LM Studio:
   - Download and install
   - Load model in GUI
   - Run inference examples

MODELS TO TEST:
  ♦ neural-chat (7B): Fast, good quality
  ♦ mistral (7B): Better reasoning
  ♦ llama2 (7B-13B): Production-grade
  ♦ tinyllama (1.1B): Minimal resources

OUTPUT:
  - Test prompts → JSON responses
  - Latency measurements
  - Response quality assessment

COST: Free (just compute time)
TIME: 15-30 minutes

PATH 2: PRODUCTION FINE-TUNING (HuggingFace)
─────────────────────────────────────────────

PURPOSE: Create a fine-tuned model optimized for your data

STEPS:
1. Prepare training data:
   python load_training_data_real.py --output fine_tuning/train_real.jsonl
   
   OR use synthetic data from run_loader.py (faster for testing)

2. Choose a base model:
   
   FOR CPU/RAM LIMITED:
     microsoft/phi-2 (2.7B)
     TinyLlama/TinyLlama-1.1B (1.1B)
   
   FOR BALANCED:
     mistralai/Mistral-7B-Instruct-v0.1 (7B, ~14GB VRAM)
   
   FOR BEST QUALITY (GPU required):
     meta-llama/Llama-2-7b-chat (7B, ~15GB VRAM)
     meta-llama/Llama-2-13b-chat (13B, ~27GB VRAM)

3. Fine-tune:
   python finetune_huggingface.py \\
       --model microsoft/phi-2 \\
       --training-file fine_tuning/training_pairs_distillation.jsonl \\
       --output-dir ./resume_distiller_model \\
       --epochs 3 \\
       --batch-size 1

4. Monitor training:
   - Loss should decrease
   - Check checkpoints in resume_distiller_model/
   - Early stop if validation loss plateaus

5. Test inference:
   python fine_tuned_inference.py \\
       --model huggingface \\
       --model-path ./resume_distiller_model

OUTPUT:
  - resume_distiller_model/model/ (trained weights)
  - resume_distiller_model/tokenizer/ (vocabulary)
  - Can be deployed anywhere

COST: Free (HuggingFace, transformer, torch are open source)
TIME: 30 mins - 2 hours (depends on model size + data size)
HARDWARE: GPU recommended (RTX 3060+ or 4060), CPU ok for small models

PATH 3: BACKEND INTEGRATION
───────────────────────────

PURPOSE: Replace Gemini API calls with fine-tuned model

CURRENT FLOW:
  Route → resume_parser_service (Gemini API) → Response

NEW FLOW:
  Route → distilled_service (Local model) → Response
                         ↓ (fallback if needed)
                    Gemini API

IMPLEMENTATION:

1. Update routes to use distilled_service:

   # app/api/routes/resume.py
   from distilled_service import get_distilled_pipeline
   
   @app.post('/api/resume/parse')
   async def parse_resume(resume_text: str):
       pipeline = get_distilled_pipeline()
       return pipeline.parse_resume(resume_text)
   
   @app.post('/api/resume/parse-legacy')  # For A/B testing
   async def parse_resume_legacy(resume_text: str):
       # Keep old Gemini version for comparison
       ...

2. Configure model source:
   
   .env file:
   FINE_TUNED_MODEL_TYPE=ollama  # or 'huggingface'
   FINE_TUNED_MODEL_PATH=./resume_distiller_model

3. Initialize on startup:
   
   # app/main.py
   from distilled_service import get_distilled_pipeline
   
   @app.on_event('startup')
   async def startup():
       pipeline = get_distilled_pipeline()
       logger.info("Distilled pipeline loaded")

4. A/B Testing:
   
   # Maintain both routes for comparison
   /api/resume/parse (uses distilled)
   /api/resume/parse-legacy (uses Gemini)
   
   # Compare:
   - Latency
   - Output quality
   - Cost savings
   - User satisfaction

5. Monitoring:
   
   # Track metrics
   - Inference time per request
   - Error rate
   - API cost savings
   - Model accuracy vs Gemini

COST: Reduced (replaces Gemini API)
TIME: 30 minutes
RISK: Low (fallback to Gemini available)

PATH 4: REAL DATA LOADING
──────────────────────────

PURPOSE: Use actual HuggingFace dataset for fine-tuning

DATA SOURCES:
  1. HuggingFace: gautamsabba/training_data_llama2_resume_distiller
     - 1000s of resume-job pairs
     - Pre-labeled with analyses
     - Streaming support for large datasets

  2. Local: processed_resumes.cleaned.jsonl
     - 2457 real resumes
     - Cleaned and deduplicated

  3. Local: job_descriptions.csv
     - 200 job descriptions
     - Various roles and industries

USAGE:

# Option 1: Local data only (fastest)
python load_training_data_real.py \\
    --local-only \\
    --output fine_tuning/train_local.jsonl

# Option 2: Local + HuggingFace (comprehensive)
python load_training_data_real.py \\
    --from-hf \\
    --output fine_tuning/train_all.jsonl

# Option 3: HuggingFace only (detailed labels)
python load_training_data_real.py \\
    --from-hf \\
    --local-only false \\
    --output fine_tuning/train_hf.jsonl

# Limit for quick testing
python load_training_data_real.py \\
    --max-pairs 500 \\
    --output fine_tuning/train_sample.jsonl

OUTPUT:
  - JSONL with prompt-completion pairs
  - Ready for HuggingFace fine-tuning
  - Can be split into train/val sets

REQUIREMENTS:
  # For HuggingFace access:
  pip install datasets
  
  # (Optional) HF auth for gated datasets:
  huggingface-cli login

COST: Free
TIME: 5 mins (local) to 30+ mins (with HF)
NETWORK: Required for HuggingFace streaming

═══════════════════════════════════════════════════════════════════

CRITICAL FILES REFERENCE
========================

1. ollama_quickstart.py
   └─ Quick test with Ollama
   └─ No training, just inference
   
2. finetune_huggingface.py
   └─ Main fine-tuning script
   └─ Trains model on your data
   
3. fine_tuned_inference.py
   └─ Load + inference wrapper
   └─ For testing trained models
   
4. distilled_service.py
   └─ Drop-in replacement for Gemini
   └─ For backend integration
   
5. load_training_data_real.py
   └─ Load from HF + local sources
   └─ Prepare training data
   
6. run_loader.py
   └─ Quick data prep (uses mock data)
   └─ For fast testing

═══════════════════════════════════════════════════════════════════

TROUBLESHOOTING
===============

Q: "transformers not found"
A: pip install transformers datasets torch

Q: "CUDA out of memory"
A: Reduce batch size: --batch-size 1
   Or use smaller model: --model microsoft/phi-2
   Or use CPU: pip install torch --cpu

Q: "Ollama not found"
A: Install: https://ollama.ai
   Then: ollama pull neural-chat

Q: "HuggingFace dataset too large"
A: Use streaming: load_training_data_real.py (built-in)
   Or limit: --max-pairs 1000

Q: "Inference is slow"
A: Check hardware (CPU vs GPU)
   Monitor memory usage
   Use smaller model if needed

Q: "Responses are garbage"
A: Need more training data (increase pairs)
   Adjust hyperparameters (--epochs, --learning-rate)
   Use bigger base model

═══════════════════════════════════════════════════════════════════

RECOMMENDED SEQUENCE
====================

WEEK 1: VALIDATION & QUICK TEST
  Day 1: Run PATH 1 (Ollama quickstart)
    - Install Ollama
    - Run ollama_quickstart.py
    - Verify pipeline works
  
  Day 2: Run PATH 2 (Quick fine-tune)
    - Use synthetic data from run_loader.py
    - Fine-tune phi-2 (small, fast)
    - Test inference
  
  Day 3: Prepare PATH 3 (Integration)
    - Create distilled_service integration code
    - Update one route as test
    - A/B test with users

WEEK 2: PRODUCTION & SCALING
  Day 1: Real data (PATH 4)
    - Load local resumes + jobs
    - Generate 1000s of pairs
  
  Day 2-3: Production fine-tune
    - Fine-tune Mistral-7B or better
    - Full training pipeline
  
  Day 4: Full integration
    - Replace all Gemini calls
    - Monitor costs and quality
  
  Day 5: Optimization
    - A/B test results
    - Fine-tune hyperparameters
    - Deploy to production

═══════════════════════════════════════════════════════════════════

COST ANALYSIS
=============

BEFORE (Using Gemini API):
  Per request: ~$0.01-0.05
  1000 requests: ~$10-50
  Monthly (10k requests): ~$100-500

AFTER (Fine-tuned model):
  Training cost: $0 (free models, your compute)
  Per request: ~$0 (local inference)
  1000 requests: $0 (just electricity)
  Monthly (10k requests): ~$5-20 (compute cost)
  
  SAVINGS: 90-95% reduction in API costs

═══════════════════════════════════════════════════════════════════

NEXT STEPS
==========

1. Install packages:
   pip install transformers datasets torch

2. Run Path 1 (Quick test):
   python ollama_quickstart.py

3. Run Path 2 (Fine-tune):
   python finetune_huggingface.py --model microsoft/phi-2

4. Run Path 3 (Integrate):
   Update app/api/routes/resume.py (see example above)

5. Run Path 4 (Real data):
   python load_training_data_real.py --from-hf

"""

if __name__ == '__main__':
    import subprocess
    import sys
    
    # Print the guide
    # This entire module is the guide when viewed/printed
    
    # Interactive menu
    print(__doc__)
    
    print("\n" + "="*70)
    print("LAUNCH WIZARD")
    print("="*70)
    
    while True:
        print("\nSelect an option:")
        print("1. Run Path 1 (Ollama Quick Test)")
        print("2. Run Path 2 (HuggingFace Fine-tune)")
        print("3. Run Path 3 Backend Integration Guide")
        print("4. Run Path 4 (Real Data Loading)")
        print("0. Exit")
        
        choice = input("\nChoice (0-4): ").strip()
        
        if choice == '1':
            print("\n🚀 Launching Path 1...")
            subprocess.run([sys.executable, 'ollama_quickstart.py'])
        
        elif choice == '2':
            print("\n🚀 Launching Path 2...")
            model = input("Model (default: microsoft/phi-2): ").strip() or 'microsoft/phi-2'
            subprocess.run([\n                sys.executable,\n                'finetune_huggingface.py',\n                '--model', model\n            ])\n        
        elif choice == '4':
            print("\n🚀 Launching Path 4...")
            subprocess.run([sys.executable, 'load_training_data_real.py'])\n        
        elif choice == '0':
            print("\\nGoodbye!")
            break
        
        else:
            print("Invalid choice")
