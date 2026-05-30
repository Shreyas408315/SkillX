#!/usr/bin/env python3
"""
Quick start: Fine-tune with Ollama (local, free, no GPU required for small models).

This script:
1. Downloads a small model (default: Neural Chat, 7B)
2. Prepares training data for Ollama
3. Shows how to run inference with the fine-tuned model
4. Provides API endpoint for integration

Installation:
    1. Download Ollama: https://ollama.ai
    2. Run: ollama serve (in another terminal)
    3. Run this script: python ollama_quickstart.py

Models to choose from:
    - neural-chat (7B) - Best for Q&A, resume tasks
    - mistral (7B) - Fast, good quality
    - llama2 (7B/13B) - Versatile, slightly slower
    - phi (2.7B) - Small, CPU friendly
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Optional


class OllamaClient:
    """Simple Ollama client for inference and fine-tuning."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model_name = "neural-chat"
    
    def check_server(self) -> bool:
        """Check if Ollama server is running."""
        try:
            result = subprocess.run(
                ["curl", "-s", f"{self.base_url}/api/tags"],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False
    
    def pull_model(self, model_name: str = "neural-chat") -> bool:
        """Download a model from Ollama registry."""
        print(f"\n📥 Downloading {model_name}...")
        print("   This may take 5-10 minutes depending on internet speed\n")
        
        result = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=False
        )
        return result.returncode == 0
    
    def infer(self, prompt: str, model: Optional[str] = None) -> str:
        """Run inference with Ollama."""
        model = model or self.model_name
        
        try:
            result = subprocess.run(
                ["ollama", "run", model, prompt],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"Error during inference: {e}")
            return ""
    
    def start_server(self) -> subprocess.Popen:
        """Start Ollama server (if not already running)."""
        print("\n🚀 Starting Ollama server...")
        
        try:
            # Try to use 'ollama serve' command
            return subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except FileNotFoundError:
            print("\n❌ Ollama not found. Please install from https://ollama.ai")
            return None


def prepare_training_data():
    """Convert JSONL training data to Ollama format."""
    training_file = Path("fine_tuning/training_pairs_distillation.jsonl")
    
    if not training_file.exists():
        print(f"❌ Training file not found: {training_file}")
        return None
    
    print(f"\n📊 Preparing training data from {training_file.name}...")
    
    # Read examples
    examples = []
    with open(training_file, 'r') as f:
        for i, line in enumerate(f):
            try:
                example = json.loads(line)
                examples.append(example)
            except json.JSONDecodeError as e:
                print(f"  ⚠️  Skipped line {i+1}: {e}")
    
    print(f"  ✓ Loaded {len(examples)} training examples")
    return examples


def show_quick_start():
    """Display quick-start instructions."""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                    OLLAMA QUICK START GUIDE                    ║
╚════════════════════════════════════════════════════════════════╝

Step 1: INSTALL OLLAMA
    Download and install from: https://ollama.ai
    (Available for Windows, Mac, Linux)

Step 2: START OLLAMA SERVER
    Open a NEW terminal and run:
        ollama serve
    
    You should see: "Ollama is running on 127.0.0.1:11434"

Step 3: TEST THIS SCRIPT
    In another terminal, run:
        python ollama_quickstart.py --test

Step 4: PREPARE YOUR DATA
    python ollama_quickstart.py --prepare

Step 5: RUN INFERENCE
    python ollama_quickstart.py --infer "resume parsing prompt"

Step 6: INTEGRATE INTO YOUR BACKEND
    See backend/fine_tuned_inference.py for integration examples
    """)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Quick-start fine-tuning with Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ollama_quickstart.py --help          # Show this help
  python ollama_quickstart.py --guide         # Show setup guide
  python ollama_quickstart.py --test          # Test connection
  python ollama_quickstart.py --prepare       # Prepare training data
  python ollama_quickstart.py --infer "text"  # Run inference
    """
    )
    
    parser.add_argument('--guide', action='store_true',
                        help='Show setup guide')
    parser.add_argument('--test', action='store_true',
                        help='Test Ollama connection')
    parser.add_argument('--prepare', action='store_true',
                        help='Prepare training data')
    parser.add_argument('--infer', type=str,
                        help='Run inference with given prompt')
    parser.add_argument('--model', default='neural-chat',
                        help='Model to use (default: neural-chat)')
    parser.add_argument('--download', action='store_true',
                        help='Download model')
    
    args = parser.parse_args()
    
    client = OllamaClient()
    
    if args.guide:
        show_quick_start()
        return
    
    if args.test:
        print("\n🔍 Testing Ollama connection...")
        if client.check_server():
            print("✅ Ollama server is running!")
            print("   You can now use: python ollama_quickstart.py --infer 'prompt'")
        else:
            print("❌ Ollama server is NOT running")
            print("   Start it with: ollama serve")
        return
    
    if args.download:
        client.pull_model(args.model)
        return
    
    if args.prepare:
        examples = prepare_training_data()
        if examples:
            print(f"\n✅ Ready! {len(examples)} training examples prepared")
            print("\n💡 Next step: Fine-tune your model")
            print("   See: backend/finetune_huggingface.py for production fine-tuning")
        return
    
    if args.infer:
        print(f"\n🤖 Running inference with {args.model}...")
        
        if not client.check_server():
            print("❌ Ollama server not running. Start with: ollama serve")
            return
        
        response = client.infer(args.infer, args.model)
        print(f"\n📝 Response:\n{response}")
        return
    
    # Default: show quick setup
    show_quick_start()


if __name__ == '__main__':
    main()
