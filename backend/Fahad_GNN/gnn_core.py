import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from graph_builder import build_graph
import json
import numpy as np

def attach_labels_to_data(data, node_id_mapping, label_file="human_labels.json"):
    """
    Attach labels to data.y
    Unlabeled nodes get label = -1
    """
    with open(label_file, "r") as f:
        label_dict = json.load(f)

    num_nodes = data.num_nodes
    y = torch.full((num_nodes,), -1, dtype=torch.long)

    for trader, info in label_dict.items():
        if trader in node_id_mapping:
            idx = node_id_mapping[trader]
            y[idx] = info["class_id"]

    data.y = y
    print(f"[INFO] Labeled traders: {(y != -1).sum().item()} / {num_nodes}")
    return data

# -----------------------------
# Model
# -----------------------------
class SimplerGraphSAGE(nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.dropout = nn.Dropout(0.5)
        self.lin = nn.Linear(hidden_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.dropout(x)
        return self.lin(x)

# -----------------------------
# FIXED: Better Train / Val Split
# -----------------------------
def create_train_val_masks(data, val_ratio=0.2, min_val_per_class=1):
    """
    Create train/val split with safety checks.
    Falls back to random split if stratified split creates empty classes.
    """
    labeled_mask = data.y != -1
    labeled_indices = torch.where(labeled_mask)[0]
    labels = data.y[labeled_mask]
    
    # Check class distribution
    unique_classes = labels.unique()
    class_counts = torch.bincount(labels)
    
    print(f"\n[LABEL DISTRIBUTION CHECK]")
    for class_id in unique_classes:
        count = (labels == class_id).sum().item()
        print(f"  Class {class_id}: {count} samples")
    
    # Attempt stratified split
    train_indices = []
    val_indices = []
    can_stratify = True
    
    for class_id in unique_classes:
        class_indices = labeled_indices[labels == class_id]
        n_class = len(class_indices)
        
        # Check if we have enough samples for this class
        if n_class < 2:
            print(f"  ⚠️  Class {class_id} has only {n_class} sample(s) - cannot split")
            can_stratify = False
            break
        
        # Random permutation
        perm = torch.randperm(n_class)
        n_val = max(1, int(n_class * val_ratio))
        
        # Ensure at least 1 in training
        if n_class - n_val < 1:
            n_val = n_class - 1
        
        val_indices.extend(class_indices[perm[:n_val]].tolist())
        train_indices.extend(class_indices[perm[n_val:]].tolist())
    
    # Fallback to random split if stratified fails
    if not can_stratify:
        print("  ⚠️  Using random split instead of stratified split")
        num_labeled = len(labeled_indices)
        perm = torch.randperm(num_labeled)
        n_val = max(2, int(num_labeled * val_ratio))  # At least 2 in validation
        
        val_indices = labeled_indices[perm[:n_val]].tolist()
        train_indices = labeled_indices[perm[n_val:]].tolist()
    
    train_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
    val_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
    
    train_mask[train_indices] = True
    val_mask[val_indices] = True
    
    return train_mask, val_mask

# -----------------------------
# Evaluation
# -----------------------------
@torch.no_grad()
def evaluate(model, data, mask):
    model.eval()
    out = model(data.x, data.edge_index)
    pred = out[mask].argmax(dim=1)
    acc = (pred == data.y[mask]).float().mean()
    return acc.item()

# -----------------------------
# Training (Single Run) - FIXED
# -----------------------------
def train_gnn_single_run(data, num_classes, run_id=1):
    """Train GNN once with a specific train/val split"""
    train_mask, val_mask = create_train_val_masks(data)

    # Print split analysis
    print(f"\n[SPLIT ANALYSIS - Run {run_id}]")
    train_classes = data.y[train_mask]
    val_classes = data.y[val_mask]
    
    # Safe bincount (handle missing classes)
    train_counts = torch.zeros(num_classes, dtype=torch.long)
    val_counts = torch.zeros(num_classes, dtype=torch.long)
    
    for class_id in range(num_classes):
        train_counts[class_id] = (train_classes == class_id).sum()
        val_counts[class_id] = (val_classes == class_id).sum()
    
    print(f"Training set class distribution: {train_counts}")
    print(f"Validation set class distribution: {val_counts}")
    print(f"Training nodes: {train_mask.sum()}")
    print(f"Validation nodes: {val_mask.sum()}")
    
    # SAFETY CHECK: Ensure all classes present in training
    if (train_counts == 0).any():
        print(f"  ⚠️  WARNING: Some classes missing in training set!")
        print(f"  Missing classes: {torch.where(train_counts == 0)[0].tolist()}")
    
    # Compute class weights SAFELY
    train_class_counts = torch.bincount(train_classes)
    
    # Add small epsilon to avoid division by zero
    class_weights = 1.0 / (train_class_counts.float() + 1e-6)
    class_weights = class_weights / class_weights.sum()
    
    # Handle NaN in weights
    if torch.isnan(class_weights).any() or torch.isinf(class_weights).any():
        print("  ⚠️  WARNING: Invalid class weights detected, using uniform weights")
        class_weights = torch.ones(num_classes) / num_classes

    loss_fn = nn.CrossEntropyLoss(weight=class_weights)

    model = SimplerGraphSAGE(
        in_channels=data.x.size(1),
        hidden_channels=64,
        out_channels=num_classes
    )

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=0.01,
        weight_decay=5e-4
    )

    best_val_loss = float('inf')
    best_val_acc = 0.0
    patience = 20
    patience_counter = 0
    best_epoch = 0

    for epoch in range(200):
        model.train()
        optimizer.zero_grad()

        out = model(data.x, data.edge_index)
        loss = loss_fn(out[train_mask], data.y[train_mask])
        
        # Check for NaN loss
        if torch.isnan(loss) or torch.isinf(loss):
            print(f"  ⚠️  NaN/Inf loss detected at epoch {epoch}! Skipping training.")
            return model, 0.0, float('inf')
        
        loss.backward()
        
        # Gradient clipping to prevent explosion
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()

        # Validation
        model.eval()
        with torch.no_grad():
            val_out = model(data.x, data.edge_index)
            val_loss = loss_fn(val_out[val_mask], data.y[val_mask])
            val_acc = evaluate(model, data, val_mask)

        if epoch % 10 == 0:
            print(
                f"Epoch {epoch:03d} | "
                f"Train Loss: {loss:.4f} | "
                f"Val Loss: {val_loss:.4f} | "
                f"Val Acc: {val_acc:.4f}"
            )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_val_acc = val_acc
            best_epoch = epoch
            patience_counter = 0
            torch.save(model.state_dict(), f"best_model_run{run_id}.pt")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch} (best was epoch {best_epoch})")
                break

    return model, best_val_acc, best_val_loss

# -----------------------------
# Multi-Run Stability Test
# -----------------------------
def train_multiple_runs(data, num_classes, num_runs=5):
    """Train with different random splits to measure stability"""
    val_accs = []
    val_losses = []
    successful_runs = 0
    
    for run in range(num_runs):
        print(f"\n{'='*60}")
        print(f"RUN {run + 1}/{num_runs}")
        print(f"{'='*60}")
        
        model, val_acc, val_loss = train_gnn_single_run(data, num_classes, run_id=run+1)
        
        # Only count successful runs
        if val_loss != float('inf'):
            val_accs.append(val_acc)
            val_losses.append(val_loss)
            successful_runs += 1
        
        print(f"\nRun {run + 1} Best Val Accuracy: {val_acc:.4f}")
        print(f"Run {run + 1} Best Val Loss: {val_loss:.4f}")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY ACROSS {num_runs} RUNS ({successful_runs} successful)")
    print(f"{'='*60}")
    
    if len(val_accs) > 0:
        print(f"Mean Val Accuracy: {np.mean(val_accs):.4f} ± {np.std(val_accs):.4f}")
        print(f"Mean Val Loss: {np.mean(val_losses):.4f} ± {np.std(val_losses):.4f}")
        print(f"Val Acc Range: [{min(val_accs):.4f}, {max(val_accs):.4f}]")
    else:
        print("⚠️  All runs failed - cannot compute statistics")
    print(f"{'='*60}\n")
    
    return val_accs, val_losses

# -----------------------------
# Prediction Analysis
# -----------------------------
@torch.no_grad()
def analyze_predictions(model, data, node_id_mapping):
    """Analyze what the model predicts for all traders"""
    model.eval()
    out = model(data.x, data.edge_index)
    probs = F.softmax(out, dim=1)
    preds = out.argmax(dim=1)
    
    # Get confidence scores
    max_probs, _ = probs.max(dim=1)
    
    # Reverse mapping
    id_to_trader = {v: k for k, v in node_id_mapping.items()}
    
    # Analyze predictions
    results = {
        'high_confidence': [],
        'low_confidence': [],
        'by_class': {0: [], 1: [], 2: [], 3: []}
    }
    
    for idx in range(data.num_nodes):
        trader_name = id_to_trader[idx]
        pred_class = preds[idx].item()
        confidence = max_probs[idx].item()
        
        trader_info = {
            'name': trader_name,
            'predicted_class': pred_class,
            'confidence': confidence,
            'is_labeled': data.y[idx].item() != -1
        }
        
        results['by_class'][pred_class].append(trader_info)
        
        if confidence > 0.9:
            results['high_confidence'].append(trader_info)
        elif confidence < 0.6:
            results['low_confidence'].append(trader_info)
    
    # Print summary
    print("\n" + "="*60)
    print("PREDICTION ANALYSIS")
    print("="*60)
    
    for class_id in range(4):
        count = len(results['by_class'][class_id])
        labeled_count = sum(1 for t in results['by_class'][class_id] if t['is_labeled'])
        print(f"Class {class_id}: {count} traders ({labeled_count} labeled)")
    
    print(f"\nHigh confidence predictions (>0.9): {len(results['high_confidence'])}")
    print(f"Low confidence predictions (<0.6): {len(results['low_confidence'])}")
    
    # Show some high confidence unlabeled predictions
    print("\n📊 Top 10 high-confidence unlabeled predictions:")
    unlabeled_high_conf = [t for t in results['high_confidence'] if not t['is_labeled']]
    unlabeled_high_conf.sort(key=lambda x: x['confidence'], reverse=True)
    
    for i, t in enumerate(unlabeled_high_conf[:10], 1):
        print(f"  {i}. {t['name']}: Class {t['predicted_class']} (confidence: {t['confidence']:.3f})")
    
    # Show some low confidence predictions (need manual review)
    print("\n⚠️  Top 10 low-confidence predictions (uncertain cases):")
    low_conf_list = sorted(results['low_confidence'], key=lambda x: x['confidence'])
    
    for i, t in enumerate(low_conf_list[:10], 1):
        labeled_str = "LABELED" if t['is_labeled'] else "unlabeled"
        print(f"  {i}. {t['name']}: Class {t['predicted_class']} (confidence: {t['confidence']:.3f}) [{labeled_str}]")
    
    print("="*60 + "\n")
    
    # Save detailed results to JSON
    output_file = "prediction_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"💾 Detailed prediction analysis saved to: {output_file}\n")
    
    return results


# =====================================================
# 🚀 MAIN
# =====================================================
if __name__ == "__main__":
    print("="*60)
    print("GNN TRADER CLASSIFICATION - ENHANCED ANALYSIS")
    print("="*60)
    
    print("\n[STEP 1] Building graph...")
    data, node_id_mapping, stats = build_graph()
    data = attach_labels_to_data(data, node_id_mapping)

    print(f"\n[STEP 2] Graph loaded:")
    print(f"  - Nodes: {data.num_nodes}")
    print(f"  - Edges: {data.edge_index.size(1)}")
    print(f"  - Labeled traders: {(data.y != -1).sum().item()}")

    NUM_CLASSES = 4

    # ===== STABILITY TEST (5 RUNS) =====
    print("\n" + "="*60)
    print("RUNNING STABILITY TEST (5 different train/val splits)")
    print("="*60)
    val_accs, val_losses = train_multiple_runs(data, NUM_CLASSES, num_runs=5)

    # ===== TRAIN FINAL MODEL =====
    print("\n" + "="*60)
    print("TRAINING FINAL MODEL (for prediction analysis)")
    print("="*60)
    final_model, final_val_acc, final_val_loss = train_gnn_single_run(data, NUM_CLASSES, run_id="final")
    
    # Only load and analyze if training was successful
    if final_val_loss != float('inf'):
        # Load best model
        try:
            final_model.load_state_dict(torch.load("best_model_runfinal.pt"))
            
            # ===== PREDICTION ANALYSIS =====
            prediction_results = analyze_predictions(final_model, data, node_id_mapping)
        except FileNotFoundError:
            print("⚠️  No saved model found - training may have failed")
            prediction_results = None
    else:
        print("⚠️  Training failed - skipping prediction analysis")
        prediction_results = None

    print("\n" + "="*60)
    print("✅ ANALYSIS COMPLETE")
    print("="*60)
    
    if len(val_accs) > 0:
        print("\n📋 Summary:")
        print(f"  - Successful runs: {len(val_accs)}/5")
        print(f"  - Mean validation accuracy: {np.mean(val_accs):.4f}")
        print(f"  - Validation accuracy range: [{min(val_accs):.4f}, {max(val_accs):.4f}]")
        
        if prediction_results:
            print(f"  - Prediction analysis saved: prediction_analysis.json")
        
        print("\n💡 Next steps:")
        print("  - Review prediction_analysis.json for patterns")
        print("  - Use smart_label_collector.py to select next traders")
        print("  - Add 30-50 more labels and retrain")
    else:
        print("\n⚠️  ISSUE DETECTED:")
        print("  - All training runs failed (NaN loss)")
        print("  - This is likely due to Class 0 having only 1 sample")
        print("\n💡 RECOMMENDED FIX:")
        print("  - Add more labels to Class 0 (high-volume consistent traders)")
        print("  - Or merge Class 0 with Class 1 temporarily")
        print("  - Minimum 2 samples per class needed for train/val split")
    
    print("="*60 + "\n")