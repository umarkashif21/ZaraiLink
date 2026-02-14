import numpy as np
from sklearn.metrics import ndcg_score

def compute_ndcg_at_k(y_true, y_pred, k=5):
    """
    Computes NDCG@k for a single query result list.
    y_true: correct relevance labels
    y_pred: predicted scores
    """
    # sklearn expects shape (n_samples, n_labelsargs)
    # But here we pass one query at a time usually
    if len(y_true) < 2: 
        return 1.0 if len(y_true) == 0 else (1.0 if y_true[0] > 0 else 0.0) # Trivial
        
    return ndcg_score([y_true], [y_pred], k=k)

def compute_mrr(y_true, y_pred):
    """
    Computes MRR for a single query.
    Assumes binary relevance (>=1 is relevant) for MRR calculation.
    """
    # Sort predictions
    sorted_indices = np.argsort(y_pred)[::-1]
    
    for i, idx in enumerate(sorted_indices):
        if y_true[idx] > 0: # Found a relevant item
            return 1.0 / (i + 1)
            
    return 0.0

def evaluate_model(model, X_val, y_val, group_val):
    """
    Evaluates model on validation set grouped by query.
    Performs grouping logic to iterate query-by-query.
    """
    preds = model.predict(X_val)
    
    ndcg_scores = []
    mrr_scores = []
    
    cursor = 0
    for g_size in group_val:
        # Slice the batch
        y_g = y_val[cursor : cursor + g_size]
        p_g = preds[cursor : cursor + g_size]
        
        ndcg_scores.append(compute_ndcg_at_k(y_g, p_g, k=5))
        mrr_scores.append(compute_mrr(y_g, p_g))
        
        cursor += g_size
        
    return {
        "ndcg@5": np.mean(ndcg_scores),
        "mrr": np.mean(mrr_scores)
    }
