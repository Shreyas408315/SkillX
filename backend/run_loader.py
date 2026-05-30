#!/usr/bin/env python3
"""Run the training data loader with reduced data for quick validation."""
import sys
from pathlib import Path
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("Step 1: Loading local datasets...")
    import load_training_data
    
    local_data = load_training_data.load_local_datasets()
    print(f"  Local data loaded: {list(local_data.keys())}")
    
    print("\nStep 2: Creating mock HF dataset structure...")
    # Create a simple mock dataset to avoid downloading HF data
    class MockDataset:
        def __init__(self):
            self.data = [
                {'text': 'Senior Software Engineer with 10 years of Python experience.'},
                {'text': 'Full Stack Developer proficient in React and Node.js.'},
                {'text': 'DevOps Engineer with Kubernetes and AWS expertise.'},
            ]
        def __getitem__(self, key):
            return self.data
        def __len__(self):
            return len(self.data)
        def __iter__(self):
            return iter(self.data)
    
    mock_hf_dataset = {'train': MockDataset(), 'test': MockDataset()}
    
    print(f"  Mock dataset created with {len(mock_hf_dataset['train'])} examples")
    
    print("\nStep 3: Creating training pairs...")
    training_pairs = load_training_data.create_training_pairs(mock_hf_dataset, local_data)
    print(f"  Created {len(training_pairs)} training pairs")
    
    if training_pairs:
        print("\nStep 4: Saving training pairs...")
        output_file = Path(__file__).parent / "training_pairs.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(training_pairs[:100], f, indent=2, ensure_ascii=False)  # Save first 100
        print(f"  Saved to {output_file}")
        
        print("\nStep 5: Creating distillation examples (limited to 5 for testing)...")
        try:
            distillation_examples = load_training_data.create_distillation_examples(training_pairs, max_examples=5)
            distillation_file = Path(__file__).parent / "fine_tuning" / "training_pairs_distillation.jsonl"
            load_training_data.save_jsonl(distillation_examples, distillation_file)
            print(f"  Saved distillation examples to {distillation_file}")
        except Exception as e:
            print(f"  Note: Distillation failed (this requires Backend services): {e}")
        
        print("\nStep 6: Saving raw HF dataset...")
        try:
            fine_tune_dir = Path(__file__).parent / "fine_tuning"
            load_training_data.save_hf_raw_dataset(mock_hf_dataset, fine_tune_dir)
            print(f"  Saved HF raw datasets")
        except Exception as e:
            print(f"  Note: HF raw save failed: {e}")
    
    print("\n✓ Dataset loading complete!")
    
except Exception as e:
    import traceback
    print(f"\n✗ Error: {e}")
    traceback.print_exc()
