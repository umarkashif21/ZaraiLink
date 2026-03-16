"""
backend/training_scripts/train_setfit_intent.py

Trains a SetFit intent classifier for Zarailink query classification.

Classes:
  BUY, SELL, F3_VOLUME, F4_PRICE, F5_TIME, F6_TOPK, F7_COMPARE, F8_EVIDENCE

Base model: sentence-transformers/all-mpnet-base-v2 (ModernBERT-base not stable yet)

Input:  backend/training_data/setfit_intent.csv
Output: backend/search/models/setfit_intent_classifier/

Usage:
    cd backend
    python training_scripts/train_setfit_intent.py
"""

import os
import sys
import csv
import json
import random
import logging
from collections import Counter

# Add backend dir to path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

LABELS_CSV = os.path.join(BACKEND_DIR, 'training_data', 'setfit_intent.csv')
MODEL_OUTPUT_DIR = os.path.join(BACKEND_DIR, 'search', 'models', 'setfit_intent_classifier')
BASE_MODEL = 'sentence-transformers/all-mpnet-base-v2'
RANDOM_SEED = 42
TRAIN_FRAC = 0.8


def _load_csv(path: str):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get('text', '').strip()
            label = row.get('label', '').strip()
            if text and label:
                rows.append((text, label))
    return rows


def _stratified_split(rows, train_frac=0.8, seed=42):
    from collections import defaultdict
    class_rows = defaultdict(list)
    for text, label in rows:
        class_rows[label].append(text)

    train, holdout = [], []
    rng = random.Random(seed)
    for label, texts in class_rows.items():
        texts = texts[:]
        rng.shuffle(texts)
        split = max(1, int(len(texts) * train_frac))
        for t in texts[:split]:
            train.append({'text': t, 'label': label})
        for t in texts[split:]:
            holdout.append({'text': t, 'label': label})

    return train, holdout


def run():
    if not os.path.exists(LABELS_CSV):
        logger.error(f"CSV not found: {LABELS_CSV}")
        sys.exit(1)

    try:
        from setfit import SetFitModel, Trainer, TrainingArguments
        from datasets import Dataset
    except ImportError as e:
        logger.error(f"Missing dependency: {e}. Run: pip install setfit datasets")
        sys.exit(1)

    rows = _load_csv(LABELS_CSV)
    logger.info(f"Loaded {len(rows)} examples")
    label_counts = Counter(label for _, label in rows)
    for label, count in sorted(label_counts.items()):
        logger.info(f"  {label}: {count}")

    # Get unique labels in sorted order
    labels = sorted(set(label for _, label in rows))
    logger.info(f"Classes: {labels}")

    # Split
    train_rows, holdout_rows = _stratified_split(rows, TRAIN_FRAC, RANDOM_SEED)
    logger.info(f"Train: {len(train_rows)}, Holdout: {len(holdout_rows)}")

    # Build HF datasets with integer labels
    label2id = {l: i for i, l in enumerate(labels)}

    train_ds = Dataset.from_dict({
        'text': [r['text'] for r in train_rows],
        'label': [label2id[r['label']] for r in train_rows],
    })
    holdout_ds = Dataset.from_dict({
        'text': [r['text'] for r in holdout_rows],
        'label': [label2id[r['label']] for r in holdout_rows],
    })

    # Load model
    logger.info(f"Loading base model: {BASE_MODEL}")
    model = SetFitModel.from_pretrained(
        BASE_MODEL,
        labels=labels,
    )

    # Training arguments
    args = TrainingArguments(
        output_dir=MODEL_OUTPUT_DIR,
        num_epochs=1,
        batch_size=16,
        seed=RANDOM_SEED,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=holdout_ds,
        metric='accuracy',
    )

    logger.info("Training SetFit model...")
    trainer.train()

    # Evaluate
    metrics = trainer.evaluate()
    logger.info(f"\nHoldout metrics: {metrics}")

    # Per-class accuracy
    preds = model.predict([r['text'] for r in holdout_rows])
    pred_labels = [labels[p] if isinstance(p, int) else p for p in preds]
    true_labels = [r['label'] for r in holdout_rows]

    from collections import defaultdict
    class_correct = defaultdict(int)
    class_total = defaultdict(int)
    for pred, true in zip(pred_labels, true_labels):
        class_total[true] += 1
        if pred == true:
            class_correct[true] += 1

    logger.info("\nPer-class accuracy:")
    for label in sorted(labels):
        n = class_total[label]
        c = class_correct[label]
        acc = c / n if n > 0 else 0.0
        status = "✓" if acc >= 0.85 else "✗"
        logger.info(f"  {label:15s}: {acc:.2%} ({c}/{n}) {status}")

    overall_acc = metrics.get('accuracy', 0.0)
    logger.info(f"\nOverall accuracy: {overall_acc:.2%}")
    if overall_acc >= 0.90:
        logger.info("✓ Target achieved: overall accuracy ≥ 90%")
    else:
        logger.warning(f"✗ Below target (90%): {overall_acc:.2%}")

    # Save model and metadata
    os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)
    model.save_pretrained(MODEL_OUTPUT_DIR)

    metadata = {
        'labels': labels,
        'label2id': label2id,
        'base_model': BASE_MODEL,
        'overall_accuracy': overall_acc,
        'per_class_accuracy': {
            label: class_correct[label] / class_total[label]
            for label in labels if class_total[label] > 0
        },
        'train_size': len(train_rows),
        'holdout_size': len(holdout_rows),
    }
    with open(os.path.join(MODEL_OUTPUT_DIR, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"\nModel saved to {MODEL_OUTPUT_DIR}")
    return model, metrics


if __name__ == '__main__':
    run()
