#!/usr/bin/env python3
"""
Quick test to verify model loading works.
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

print("Testing facebook/opt-125m model loading...")

try:
    tokenizer = AutoTokenizer.from_pretrained("facebook/opt-125m", trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        "facebook/opt-125m",
        torch_dtype=torch.float32,
        trust_remote_code=True,
    )
    print("✅ Model loaded successfully!")
    print(f"Model parameters: {model.num_parameters():,}")
    print(f"Tokenizer vocab size: {tokenizer.vocab_size}")

except Exception as e:
    print(f"❌ Error: {e}")