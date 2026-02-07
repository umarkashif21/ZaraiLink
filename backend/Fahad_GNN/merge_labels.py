"""
merge_labels.py

Merges new labels with existing human_labels.json
"""

import json
import os

def merge_labels(new_labels_file='model_guided_labeling_template.json', 
                 existing_labels_file='human_labels.json',
                 output_file='human_labels.json'):
    """
    Merge new labels with existing ones.
    Only adds traders that have class_id filled in.
    """
    
    # Load existing labels
    if os.path.exists(existing_labels_file):
        with open(existing_labels_file, 'r') as f:
            existing = json.load(f)
        print(f"[INFO] Loaded {len(existing)} existing labels")
    else:
        existing = {}
        print("[INFO] No existing labels found, starting fresh")
    
    # Load new labels
    with open(new_labels_file, 'r') as f:
        new_labels = json.load(f)
    
    # Count valid new labels (those with class_id filled in)
    valid_new = {k: v for k, v in new_labels.items() 
                 if v.get('class_id') is not None}
    
    print(f"[INFO] Found {len(valid_new)} new labeled traders")
    
    if len(valid_new) == 0:
        print("\n⚠️  No new labels found!")
        print("Make sure you've filled in 'class_id' for traders you want to add.")
        return
    
    # Merge (new labels overwrite existing if same trader)
    merged = {**existing, **valid_new}
    
    # Save
    with open(output_file, 'w') as f:
        json.dump(merged, f, indent=2)
    
    print(f"\n[SUCCESS] Merged labels saved to: {output_file}")
    print(f"  Total labels: {len(merged)}")
    print(f"  Previous: {len(existing)}")
    print(f"  Added: {len(valid_new)}")
    print(f"  Updated: {len([k for k in valid_new if k in existing])}")
    
    # Show class distribution
    class_counts = {}
    for trader, info in merged.items():
        class_id = info.get('class_id')
        class_counts[class_id] = class_counts.get(class_id, 0) + 1
    
    print(f"\n📊 Final class distribution:")
    for class_id in sorted(class_counts.keys()):
        print(f"  Class {class_id}: {class_counts[class_id]} traders")
    
    print(f"\n✅ Ready to retrain! Run: python gnn_core.py\n")


if __name__ == "__main__":
    merge_labels()