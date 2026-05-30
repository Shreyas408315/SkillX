#!/usr/bin/env python3
"""
Fine-tuning setup for resume distiller.

This script demonstrates how to fine-tune smaller models using the generated
training JSONL. Multiple fine-tuning options are provided:

1. Hugging Face: Fine-tune open-source models (Mistral, Llama, Phi)
2. OpenAI: Fine-tune via API (requires paid account)
3. Ollama: Local LLM fine-tuning (free, GPU optional)
"""

from pathlib import Path
import json
import argparse


def option_1_huggingface_finetuning():
    """
    Fine-tune using Hugging Face Transformers.
    Requires: pip install transformers datasets torch
    """
    print("\n" + "="*60)
    print("OPTION 1: Hugging Face Fine-tuning")
    print("="*60)
    
    print("""
Models available (pick one based on your GPU/CPU):
- mistralai/Mistral-7B-Instruct-v0.1 (7B params, fast)
- meta-llama/Llama-2-7b-chat (7B params)
- microsoft/phi-2 (2.7B params, very fast, CPU friendly)
- TinyLlama/TinyLlama-1.1B (1.1B params, minimal requirements)

Installation:
  pip install transformers datasets torch bitsandbytes peft

Quick start script:
"'
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import TrainingArguments, Trainer
from datasets import load_dataset

# Load model and tokenizer
model_name = "microsoft/phi-2"  # Change this for other models
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", trust_remote_code=True)

# Load training dataset
dataset = load_dataset('json', data_files={
    'train': 'fine_tuning/training_pairs_distillation.jsonl'
})

# Define training arguments
training_args = TrainingArguments(
    output_dir="./resume_distiller_model",
    num_train_epochs=3,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    weight_decay=0.01,
    save_steps=50,
    logging_steps=10,
)

# Create trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset['train'],
)

# Fine-tune
trainer.train()

# Save model
model.save_pretrained("./resume_distiller_fine_tuned")
tokenizer.save_pretrained("./resume_distiller_fine_tuned")
"'
    """)


def option_2_openai_finetuning():
    """
    Fine-tune using OpenAI API.
    Requires: pip install openai
    Costs: ~$0.02-0.05 per 1K tokens (check current pricing)
    """
    print("\n" + "="*60)
    print("OPTION 2: OpenAI Fine-tuning API")
    print("="*60)
    
    print("""
Requirements:
  pip install openai

Setup:
  export OPENAI_API_KEY="your-api-key"

Quick start script:
"'
from openai import OpenAI

client = OpenAI()

# Upload training file
with open('fine_tuning/training_pairs_distillation.jsonl', 'rb') as f:
    response = client.files.create(file=f, purpose='fine-tune')
    file_id = response.id

print(f"File uploaded: {file_id}")

# Create fine-tuning job
fine_tune_job = client.fine_tuning.jobs.create(
    training_file=file_id,
    model="gpt-3.5-turbo",
    hyperparameters={
        "n_epochs": 3,
        "batch_size": 16,
        "learning_rate_multiplier": 0.1,
    }
)

print(f"Fine-tuning job created: {fine_tune_job.id}")
print(f"Status: {fine_tune_job.status}")

# Check status
job_status = client.fine_tuning.jobs.retrieve(fine_tune_job.id)
print(f"Job status: {job_status.status}")

# Once complete, use the fine-tuned model
# model_name = job_status.fine_tuned_model
"'
    """)


def option_3_ollama_local():
    """
    Fine-tune using Ollama (free, runs locally).
    Requires: Ollama installed (https://ollama.ai)
    """
    print("\n" + "="*60)
    print("OPTION 3: Ollama Local Fine-tuning")
    print("="*60)
    
    print("""
Installation:
  1. Download Ollama from https://ollama.ai
  2. Install: ollama pull mistral  (or: llama2, neural-chat, etc.)

Convert JSONL to Ollama format:
  The distillation JSONL is already in compatible format.

Fine-tune locally:
"'
import subprocess
import json

# Convert to Ollama modelfile format
with open('fine_tuning/training_pairs_distillation.jsonl', 'r') as f:
    lines = f.readlines()

# Save as training context for Ollama
training_data = []
for line in lines:
    example = json.loads(line)
    training_data.append(f"Q: {example['prompt']}\\nA: {example['completion']}")

with open('ollama_training.txt', 'w') as f:
    f.write('\\n\\n'.join(training_data))

# Use Ollama CLI (if supported in your version)
# ollama finetune mistral ollama_training.txt
"'

Models to try:
  - ollama pull mistral (fast, 7B)
  - ollama pull neural-chat (resume-friendly)
  - ollama pull llama2 (versatile)
  - ollama pull openhermes (instruction-tuned)

Run locally:
  ollama run mistral "resume parsing prompt"
    """)


def option_4_lm_studio():
    """
    Fine-tune using LM Studio (GUI-based, user-friendly).
    """
    print("\n" + "="*60)
    print("OPTION 4: LM Studio (GUI-based Fine-tuning)")
    print("="*60)
    
    print("""
Installation:
  Download from https://lmstudio.ai

Features:
  - Download models directly from HuggingFace
  - GUI-based fine-tuning (no CLI needed)
  - Local inference
  - HTTP API available

Steps:
  1. Download and install LM Studio
  2. Download a model (Mistral 7B recommended)
  3. Go to "Train" tab
  4. Load fine_tuning/training_pairs_distillation.jsonl
  5. Configure hyperparameters
  6. Start fine-tuning
  7. Use fine-tuned model in "Chat" tab
    """)


def show_file_info():
    """Display training file statistics."""
    print("\n" + "="*60)
    print("TRAINING DATA SUMMARY")
    print("="*60)
    
    distillation_file = Path("fine_tuning/training_pairs_distillation.jsonl")
    
    if distillation_file.exists():
        with open(distillation_file, 'r') as f:
            examples = [json.loads(line) for line in f]
        
        print(f"\n✓ Found {len(examples)} training examples")
        print(f"\nExample structure:")
        if examples:
            ex = examples[0]
            print(f"  - prompt length: {len(ex['prompt'])} chars")
            print(f"  - completion length: {len(ex['completion'])} chars")
            
            # Parse completion to show structure
            try:
                completion = json.loads(ex['completion'])
                print(f"  - completion fields: {list(completion.keys())}")
            except:
                pass
        
        print(f"\nFile size: {distillation_file.stat().st_size / 1024:.1f} KB")
    else:
        print(f"\n✗ Training file not found: {distillation_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Fine-tuning setup for resume distiller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_finetuning.py --info              # Show dataset info
  python setup_finetuning.py --option huggingface # Show HF setup
  python setup_finetuning.py --option openai     # Show OpenAI setup
  python setup_finetuning.py --all               # Show all options
        """
    )
    
    parser.add_argument('--info', action='store_true',
                        help='Show training data information')
    parser.add_argument('--option', choices=['huggingface', 'openai', 'ollama', 'lmstudio'],
                        help='Show specific fine-tuning option')
    parser.add_argument('--all', action='store_true',
                        help='Show all fine-tuning options')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("FINE-TUNING SETUP FOR RESUME DISTILLER")
    print("="*60)
    
    # Show dataset info
    show_file_info()
    
    if args.info or not any([args.option, args.all]):
        return
    
    if args.option == 'huggingface' or args.all:
        option_1_huggingface_finetuning()
    
    if args.option == 'openai' or args.all:
        option_2_openai_finetuning()
    
    if args.option == 'ollama' or args.all:
        option_3_ollama_local()
    
    if args.option == 'lmstudio' or args.all:
        option_4_lm_studio()
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    print("""
For your resume distiller use case, I recommend:

1. START: LM Studio or Ollama
   ✓ Free and open-source
   ✓ No API costs
   ✓ Models run locally on your machine
   ✓ Good for testing and development

2. PRODUCTION: Hugging Face fine-tuning
   ✓ Better performance on custom data
   ✓ Can deploy to Hugging Face Hub
   ✓ Integration with your backend

3. OPTIONAL: OpenAI API
   ✓ High quality results
   ✓ No local GPU needed
   ✗ Ongoing API costs
   ✗ Data sent to OpenAI servers

Next steps:
1. Choose a fine-tuning option above
2. Install required libraries
3. Run the provided script
4. Test the fine-tuned model
5. Integrate into your backend
    """)


if __name__ == '__main__':
    main()
