"""
backend/training_scripts/finetune_embeddings.py

Phase 4-C: Fine-tune nomic-embed-text-v1 on Zarailink trade-domain triplets.

Uses sentence-transformers MultipleNegativesRankingLoss (MNRL) which treats
all other batch positives as in-batch negatives — one hard negative per sample
is included for additional signal.

Input:  backend/training_data/embedding_pairs.jsonl
Output: backend/search/models/nomic_finetuned/

Usage:
    cd backend
    python training_scripts/finetune_embeddings.py [--epochs 1] [--batch-size 16]

Requirements:
    pip install sentence-transformers datasets torch
"""

import os
import sys
import json
import argparse
import logging

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

PAIRS_PATH = os.path.join(BACKEND_DIR, 'training_data', 'embedding_pairs.jsonl')
OUTPUT_DIR = os.path.join(BACKEND_DIR, 'search', 'models', 'nomic_finetuned')
BASE_MODEL = 'nomic-ai/nomic-embed-text-v1'
RANDOM_SEED = 42


def _load_pairs(path: str):
    pairs = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    return pairs


def run(num_epochs: int = 1, batch_size: int = 16, warmup_steps: int = 10):
    if not os.path.exists(PAIRS_PATH):
        logger.error(
            f"Pairs file not found: {PAIRS_PATH}. "
            "Run generate_embedding_pairs.py first."
        )
        sys.exit(1)

    try:
        from sentence_transformers import SentenceTransformer, InputExample
        from sentence_transformers.losses import MultipleNegativesRankingLoss
        from torch.utils.data import DataLoader
    except ImportError as e:
        logger.error(f"Missing dependency: {e}. Run: pip install sentence-transformers torch")
        sys.exit(1)

    pairs = _load_pairs(PAIRS_PATH)
    logger.info(f"Loaded {len(pairs)} training triplets from {PAIRS_PATH}")

    # Build InputExample list
    # MNRL: each example = (anchor, positive[, negative])
    # When negative is provided it becomes the first hard negative in the batch.
    examples = []
    for p in pairs:
        texts = [p['query'], p['positive']]
        if 'negative' in p:
            texts.append(p['negative'])
        examples.append(InputExample(texts=texts))

    # 80/20 split
    split = max(1, int(len(examples) * 0.8))
    train_examples = examples[:split]
    eval_examples = examples[split:]
    logger.info(f"Train: {len(train_examples)}, Eval: {len(eval_examples)}")

    # Load base model
    logger.info(f"Loading base model: {BASE_MODEL}")
    model = SentenceTransformer(BASE_MODEL, trust_remote_code=True)

    # DataLoader
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)

    # Loss
    loss = MultipleNegativesRankingLoss(model=model)

    # Training steps
    total_steps = len(train_dataloader) * num_epochs
    logger.info(
        f"Training for {num_epochs} epoch(s), "
        f"batch_size={batch_size}, total_steps={total_steps}"
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    model.fit(
        train_objectives=[(train_dataloader, loss)],
        epochs=num_epochs,
        warmup_steps=warmup_steps,
        output_path=OUTPUT_DIR,
        show_progress_bar=True,
        checkpoint_path=OUTPUT_DIR,
        checkpoint_save_steps=max(1, total_steps // 2),
    )

    logger.info(f"Fine-tuned model saved to {OUTPUT_DIR}")

    # Quick sanity check — encode a sample query
    test_query = "search_query: find dextrose suppliers"
    test_doc   = "search_document: Dextrose Anhydrous - pharmaceutical grade glucose"
    q_vec = model.encode([test_query])[0]
    d_vec = model.encode([test_doc])[0]
    import numpy as np
    cos_sim = float(np.dot(q_vec, d_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(d_vec)))
    logger.info(f"Sanity check cosine similarity (dextrose query/doc): {cos_sim:.4f}")

    # Save metadata
    metadata = {
        'base_model': BASE_MODEL,
        'output_dir': OUTPUT_DIR,
        'num_epochs': num_epochs,
        'batch_size': batch_size,
        'num_train_examples': len(train_examples),
        'num_eval_examples': len(eval_examples),
        'sanity_cos_sim': cos_sim,
    }
    with open(os.path.join(OUTPUT_DIR, 'finetune_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info("Done.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fine-tune nomic-embed-text-v1')
    parser.add_argument('--epochs', type=int, default=1)
    parser.add_argument('--batch-size', type=int, default=16)
    parser.add_argument('--warmup-steps', type=int, default=10)
    args = parser.parse_args()
    run(num_epochs=args.epochs, batch_size=args.batch_size, warmup_steps=args.warmup_steps)
