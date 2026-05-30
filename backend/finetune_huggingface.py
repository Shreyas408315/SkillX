#!/usr/bin/env python3
"""
Production fine-tuning with Hugging Face Transformers.

This script fine-tunes an open-source LLM on your resume distiller data
for production use. The fine-tuned model can be deployed via Hugging Face Hub,
Ollama, or integrated directly into your backend.

Requirements:
    pip install transformers datasets torch peft bitsandbytes

Basic usage:
    python finetune_huggingface.py --model microsoft/phi-2

Models available (pick based on your hardware):
    - microsoft/phi-2 (2.7B, fast, CPU friendly)
    - facebook/opt-125m (125M, very fast, minimal resources)
    - google/flan-t5-small (77M, fast, good quality)
    - distilgpt2 (82M, very fast, GPT-2 based)
    - mistralai/Mistral-7B-Instruct-v0.1 (7B, balanced)
"""

import json
import argparse
from pathlib import Path
from typing import Optional


def check_requirements():
    """Check if required packages are installed."""
    required = ['transformers', 'datasets', 'torch', 'accelerate']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print(f"\nInstall with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    return True


def finetune_with_transformers(
    model_name: str,
    training_file: str,
    output_dir: str = "./resume_distiller_model",
    num_epochs: int = 3,
    batch_size: int = 1,
    learning_rate: float = 2e-4,
):
    """
    Fine-tune a model using Hugging Face Transformers.
    
    Args:
        model_name: HF model ID (e.g., "microsoft/phi-2")
        training_file: Path to JSONL training file
        output_dir: Directory to save fine-tuned model
        num_epochs: Number of training epochs
        batch_size: Batch size (reduce if OOM errors)
        learning_rate: Learning rate for optimizer
    """
    try:
        from transformers import (
            AutoTokenizer,
            AutoModelForCausalLM,
            TrainingArguments,
            Trainer,
            DataCollatorForLanguageModeling,
        )
        from datasets import load_dataset
        import torch
    except ImportError:
        print("❌ Required packages not installed")
        print("Run: pip install transformers datasets torch")
        return False
    
    print(f"\n[FINETUNING] {model_name}")
    print(f"   Dataset: {training_file}")
    print(f"   Output: {output_dir}")
    print(f"   Hardware: {'GPU' if torch.cuda.is_available() else 'CPU'}")
    
    # Load tokenizer and model
    print("\n[LOADING] Loading model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        trust_remote_code=True,
    )
    
    # Set padding token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load dataset
    print("\n[DATA] Loading training data...")
    dataset = load_dataset('json', data_files={'train': training_file})
    
    def preprocess_function(examples):
        """Prepare text data for training."""
        texts = []
        for prompt, completion in zip(examples['prompt'], examples['completion']):
            # Combine prompt and completion
            text = f"{prompt}\n{completion}"
            texts.append(text)
        
        return tokenizer(
            texts,
            truncation=True,
            max_length=1024,
            padding='max_length',
        )
    
    print("   [TOKENIZING] Tokenizing...")
    tokenized_dataset = dataset['train'].map(
        preprocess_function,
        batched=True,
        remove_columns=['prompt', 'completion'],
    )
    
    # Training configuration
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        save_steps=50,
        save_total_limit=2,
        logging_steps=10,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_steps=50,
        log_level='info',
        report_to=[],  # Disable wandb/tensorboard
        push_to_hub=False,
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # Causal LM, not masked
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
    )
    
    # Fine-tune
    print("\n[TRAINING] Starting fine-tuning...")
    trainer.train()
    
    # Save
    print(f"\n[SAVE] Saving model to {output_dir}/")
    model.save_pretrained(f"{output_dir}/model")
    tokenizer.save_pretrained(f"{output_dir}/tokenizer")
    
    print(f"\n[SUCCESS] Fine-tuning completed!")
    print(f"\n[MODEL] Model saved to: {output_dir}/")
    print(f"\n[NEXT] Next steps:")
    print(f"   1. Test: python fine_tuned_inference.py --model huggingface --model-path {output_dir}")
    print(f"   2. Integrate: See fine_tuned_inference.py for backend integration")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Fine-tune LLM for resume distiller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python finetune_huggingface.py --model microsoft/phi-2
  python finetune_huggingface.py --model mistralai/Mistral-7B-Instruct-v0.1 --epochs 5
  python finetune_huggingface.py --model facebook/opt-125m --batch-size 2
        """
    )
    
    parser.add_argument('--model', default='facebook/opt-125m',
                        help='Hugging Face model ID')
    parser.add_argument('--training-file', default='fine_tuning/training_pairs_distillation.jsonl',
                        help='Path to JSONL training file')
    parser.add_argument('--output-dir', default='./resume_distiller_model',
                        help='Output directory for fine-tuned model')
    parser.add_argument('--epochs', type=int, default=3,
                        help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=1,
                        help='Batch size (reduce if OOM)')
    parser.add_argument('--learning-rate', type=float, default=2e-4,
                        help='Learning rate')
    
    args = parser.parse_args()
    
    # Check requirements
    if not check_requirements():
        return 1
    
    # Check training file
    if not Path(args.training_file).exists():
        print(f"\n❌ Training file not found: {args.training_file}")
        return 1
    
    # Run fine-tuning
    success = finetune_with_transformers(
        model_name=args.model,
        training_file=args.training_file,
        output_dir=args.output_dir,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
