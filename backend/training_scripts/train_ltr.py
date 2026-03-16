"""
backend/training_scripts/train_ltr.py

Trains LightGBM LambdaRank model v2 on labeled (query, supplier) pairs.

Input:  backend/training_data/ltr_labels.json
Output: backend/search/models/lgbm_ltr_v2.txt

Usage:
    cd backend
    python training_scripts/train_ltr.py
    python training_scripts/train_ltr.py --labels-path /path/to/labels.json
"""

import os
import sys
import json
import logging
import argparse
import random
import numpy as np

# Add backend dir to path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

LABELS_PATH = os.path.join(BACKEND_DIR, 'training_data', 'ltr_labels.json')
MODEL_OUTPUT_PATH = os.path.join(BACKEND_DIR, 'search', 'models', 'lgbm_ltr_v2.txt')

RANDOM_SEED = 42
TRAIN_SPLIT = 0.8
NDCG_EVAL_AT = [5, 10]


def _load_labels(path: str) -> list:
    with open(path, 'r') as f:
        return json.load(f)


def _build_lgbm_dataset(records: list):
    """
    Convert records list to LightGBM training format.

    Returns:
        X: np.ndarray (n_samples, n_features)
        y: np.ndarray (n_samples,) — relevance labels 0-3
        groups: list of ints — number of samples per query group
    """
    from collections import defaultdict
    query_groups = defaultdict(list)
    for r in records:
        query_groups[r['query_id']].append(r)

    X, y, groups = [], [], []
    for qid, group_records in sorted(query_groups.items()):
        for r in group_records:
            features = r.get('features', [])
            if not features:
                continue
            X.append(features)
            y.append(r['relevance'])
        groups.append(len(group_records))

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32), groups


def _train_test_split(records: list, train_frac: float = 0.8, seed: int = 42):
    """Stratified split by query_id."""
    from collections import defaultdict
    query_groups = defaultdict(list)
    for r in records:
        query_groups[r['query_id']].append(r)

    query_ids = sorted(query_groups.keys())
    random.seed(seed)
    random.shuffle(query_ids)

    split_idx = int(len(query_ids) * train_frac)
    train_qids = set(query_ids[:split_idx])
    holdout_qids = set(query_ids[split_idx:])

    train_records = [r for r in records if r['query_id'] in train_qids]
    holdout_records = [r for r in records if r['query_id'] in holdout_qids]

    return train_records, holdout_records


def run(labels_path: str = LABELS_PATH, output_path: str = MODEL_OUTPUT_PATH):
    try:
        import lightgbm as lgb
    except ImportError:
        logger.error("lightgbm not installed. Run: pip install lightgbm")
        sys.exit(1)

    if not os.path.exists(labels_path):
        logger.error(
            f"Labels file not found: {labels_path}\n"
            f"Run: python training_scripts/generate_ltr_labels.py"
        )
        sys.exit(1)

    records = _load_labels(labels_path)
    logger.info(f"Loaded {len(records)} labeled records from {labels_path}")

    # Split
    train_records, holdout_records = _train_test_split(records, TRAIN_SPLIT, RANDOM_SEED)
    logger.info(f"Train: {len(train_records)} | Holdout: {len(holdout_records)}")

    # Build datasets
    X_train, y_train, groups_train = _build_lgbm_dataset(train_records)
    X_holdout, y_holdout, groups_holdout = _build_lgbm_dataset(holdout_records)

    if len(X_train) == 0:
        logger.error("No training samples — labels may be empty or malformed")
        sys.exit(1)

    n_features = X_train.shape[1]
    logger.info(f"Features: {n_features}, train samples: {len(X_train)}, holdout: {len(X_holdout)}")

    # LightGBM datasets
    from search.services.ranking_ltr import FeatureExtractor
    feature_names = FeatureExtractor.FEATURE_NAMES[:n_features]

    lgb_train = lgb.Dataset(
        X_train, label=y_train,
        group=groups_train,
        feature_name=feature_names,
    )
    lgb_holdout = lgb.Dataset(
        X_holdout, label=y_holdout,
        group=groups_holdout,
        feature_name=feature_names,
        reference=lgb_train,
    )

    # Training params
    params = {
        'objective': 'lambdarank',
        'metric': 'ndcg',
        'ndcg_eval_at': NDCG_EVAL_AT,
        'learning_rate': 0.05,
        'num_leaves': 31,
        'min_data_in_leaf': 5,
        'n_estimators': 200,
        'verbose': -1,
        'seed': RANDOM_SEED,
    }

    logger.info("Training LightGBM LambdaRank model...")
    callbacks = [lgb.early_stopping(stopping_rounds=20, verbose=False),
                 lgb.log_evaluation(period=50)]

    model = lgb.train(
        params,
        lgb_train,
        valid_sets=[lgb_holdout],
        valid_names=['holdout'],
        num_boost_round=params['n_estimators'],
        callbacks=callbacks,
    )

    # Evaluate on holdout
    holdout_preds = model.predict(X_holdout)

    # Compute NDCG manually per query
    ndcg_at_5_list, ndcg_at_10_list = [], []

    from collections import defaultdict
    holdout_groups = defaultdict(list)
    for r in holdout_records:
        holdout_groups[r['query_id']].append(r)

    pred_idx = 0
    for qid, group_records in sorted(holdout_groups.items()):
        n = len(group_records)
        preds = holdout_preds[pred_idx:pred_idx + n]
        labels = np.array([r['relevance'] for r in group_records], dtype=float)
        pred_idx += n

        order = np.argsort(preds)[::-1]
        labels_ranked = labels[order]

        def _dcg(labels_sorted, k):
            k = min(k, len(labels_sorted))
            gains = labels_sorted[:k]
            discounts = np.log2(np.arange(2, k + 2))
            return np.sum((2 ** gains - 1) / discounts)

        ideal_order = np.argsort(labels)[::-1]
        ideal_labels = labels[ideal_order]

        for k, ndcg_list in [(5, ndcg_at_5_list), (10, ndcg_at_10_list)]:
            dcg = _dcg(labels_ranked, k)
            idcg = _dcg(ideal_labels, k)
            ndcg_list.append(dcg / idcg if idcg > 0 else 0.0)

    ndcg5 = np.mean(ndcg_at_5_list) if ndcg_at_5_list else 0.0
    ndcg10 = np.mean(ndcg_at_10_list) if ndcg_at_10_list else 0.0

    logger.info(f"\n{'='*50}")
    logger.info(f"Holdout NDCG@5  = {ndcg5:.4f}")
    logger.info(f"Holdout NDCG@10 = {ndcg10:.4f}")
    logger.info(f"Best iteration  = {model.best_iteration}")
    logger.info(f"{'='*50}")

    # Feature importances
    importances = dict(zip(model.feature_name(), model.feature_importance(importance_type='gain')))
    top_features = sorted(importances.items(), key=lambda x: -x[1])[:10]
    logger.info("\nTop 10 features by gain:")
    for name, gain in top_features:
        logger.info(f"  {name:30s} {gain:.1f}")

    # Save model
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    model.save_model(output_path)
    logger.info(f"\nModel saved to {output_path}")

    return model, ndcg5, ndcg10


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train LTR v2 model')
    parser.add_argument('--labels-path', default=LABELS_PATH)
    parser.add_argument('--output-path', default=MODEL_OUTPUT_PATH)
    args = parser.parse_args()
    run(args.labels_path, args.output_path)
