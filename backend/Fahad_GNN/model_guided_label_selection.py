"""
model_guided_label_selection.py

Uses the trained GNN's predictions to intelligently select next traders to label.
Prioritizes:
1. High-impact traders (high volume/connectivity)
2. Uncertain predictions (low confidence)
3. Representative samples from predicted classes
4. Diversity (different products, countries, patterns)
"""

import sys
import os
import json
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zarailink.settings")
django.setup()

from django.db.models import Sum, Avg, Count, StdDev
from django.db.models.functions import TruncMonth
from trade_data.models import Transaction


def load_predictions():
    """Load model predictions from previous run"""
    with open('prediction_analysis.json', 'r') as f:
        return json.load(f)


def load_existing_labels():
    """Load already labeled traders"""
    try:
        with open('human_labels.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def calculate_trader_importance(trader):
    """Calculate importance metrics for a trader"""
    txs_as_buyer = Transaction.objects.filter(buyer=trader)
    txs_as_seller = Transaction.objects.filter(seller=trader)
    all_txs = txs_as_buyer | txs_as_seller
    
    if all_txs.count() == 0:
        return None
    
    total_usd = float(all_txs.aggregate(sum_usd=Sum('usd'))['sum_usd'] or 0)
    total_tx = all_txs.count()
    
    # Network metrics
    num_partners = (
        txs_as_buyer.values('seller').distinct().count() +
        txs_as_seller.values('buyer').distinct().count()
    )
    
    # Diversity metrics
    product_diversity = all_txs.values('product_item').distinct().count()
    country_diversity = all_txs.values('country').distinct().count()
    
    # Temporal spread
    monthly_stats = all_txs.annotate(
        month=TruncMonth('reporting_date')
    ).values('month').distinct().count()
    
    return {
        'total_usd': total_usd,
        'total_tx': total_tx,
        'avg_tx_size': total_usd / total_tx if total_tx > 0 else 0,
        'num_partners': num_partners,
        'product_diversity': product_diversity,
        'country_diversity': country_diversity,
        'months_active': monthly_stats
    }


def prioritize_next_labels(target_count=50):
    """
    Select next traders to label based on model predictions and importance.
    """
    print("="*80)
    print("MODEL-GUIDED LABEL SELECTION")
    print("="*80)
    
    # Load data
    predictions = load_predictions()
    existing_labels = load_existing_labels()
    
    print(f"\n[INFO] Loaded {len(existing_labels)} existing labels")
    print(f"[INFO] Analyzing model predictions...")
    
    # Flatten predictions with metadata
    all_predictions = []
    for confidence_level in ['high_confidence', 'low_confidence']:
        for pred in predictions.get(confidence_level, []):
            if not pred['is_labeled']:  # Skip already labeled
                all_predictions.append(pred)
    
    # Add remaining predictions from by_class
    for class_id in range(4):
        for pred in predictions['by_class'].get(str(class_id), []):
            if not pred['is_labeled'] and pred not in all_predictions:
                all_predictions.append(pred)
    
    print(f"[INFO] Found {len(all_predictions)} unlabeled traders")
    
    # Calculate importance for each trader
    candidates = []
    for i, pred in enumerate(all_predictions):
        if (i + 1) % 100 == 0:
            print(f"  Processing {i+1}/{len(all_predictions)}...")
        
        trader_name = pred['name']
        importance = calculate_trader_importance(trader_name)
        
        if importance is None:
            continue
        
        # Calculate priority score
        priority_score = 0.0
        
        # 1. Volume importance (0-30 points)
        volume_score = min(30, (importance['total_usd'] / 1_000_000) * 2)
        priority_score += volume_score
        
        # 2. Uncertainty importance (0-30 points)
        confidence = pred['confidence']
        uncertainty_score = (1 - confidence) * 30
        priority_score += uncertainty_score
        
        # 3. Network importance (0-20 points)
        network_score = min(20, importance['num_partners'] * 2)
        priority_score += network_score
        
        # 4. Diversity importance (0-10 points)
        diversity_score = min(10, importance['product_diversity'] * 2)
        priority_score += diversity_score
        
        # 5. Activity breadth (0-10 points)
        activity_score = min(10, importance['months_active'])
        priority_score += activity_score
        
        candidates.append({
            'name': trader_name,
            'predicted_class': pred['predicted_class'],
            'confidence': confidence,
            'priority_score': priority_score,
            'volume_score': volume_score,
            'uncertainty_score': uncertainty_score,
            'network_score': network_score,
            'diversity_score': diversity_score,
            **importance
        })
    
    # Sort by priority score
    candidates.sort(key=lambda x: x['priority_score'], reverse=True)
    
    # Select top candidates with diversity
    selected = []
    class_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    
    # First pass: Ensure at least 5 from each predicted class
    for class_id in range(4):
        class_candidates = [c for c in candidates if c['predicted_class'] == class_id]
        for candidate in class_candidates[:5]:
            if candidate not in selected:
                selected.append(candidate)
                class_counts[class_id] += 1
    
    # Second pass: Fill remaining slots with highest priority
    for candidate in candidates:
        if len(selected) >= target_count:
            break
        if candidate not in selected:
            selected.append(candidate)
            class_counts[candidate['predicted_class']] += 1
    
    # Generate labeling template
    template = {}
    for rank, candidate in enumerate(selected, 1):
        template[candidate['name']] = {
            'class_id': None,  # To be filled by human
            'class_name': None,
            'confidence': 1.0,
            'annotator': 'YOUR_NAME_HERE',
            'notes': '',
            'model_suggestion': {
                'predicted_class': candidate['predicted_class'],
                'model_confidence': f"{candidate['confidence']:.3f}",
                'priority_rank': rank,
                'priority_score': f"{candidate['priority_score']:.1f}"
            },
            'reference_stats': {
                'total_usd': f"${candidate['total_usd']:,.2f}",
                'total_transactions': candidate['total_tx'],
                'avg_transaction_size': f"${candidate['avg_tx_size']:,.2f}",
                'num_partners': candidate['num_partners'],
                'product_diversity': candidate['product_diversity'],
                'months_active': candidate['months_active']
            },
            'priority_breakdown': {
                'volume': f"{candidate['volume_score']:.1f}/30",
                'uncertainty': f"{candidate['uncertainty_score']:.1f}/30",
                'network': f"{candidate['network_score']:.1f}/20",
                'diversity': f"{candidate['diversity_score']:.1f}/10",
                'total': f"{candidate['priority_score']:.1f}/100"
            }
        }
    
    # Save template
    output_path = 'model_guided_labeling_template.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"[SUCCESS] Selected {len(selected)} traders for labeling")
    print(f"{'='*80}")
    print(f"\nDistribution by predicted class:")
    for class_id in range(4):
        print(f"  Class {class_id}: {class_counts[class_id]} traders")
    
    print(f"\nTop 10 priority traders:")
    for i, candidate in enumerate(selected[:10], 1):
        print(f"  {i}. {candidate['name']}")
        print(f"     Priority: {candidate['priority_score']:.1f} | "
              f"Model predicts: Class {candidate['predicted_class']} "
              f"(conf: {candidate['confidence']:.2f})")
        print(f"     Volume: ${candidate['total_usd']:,.0f} | "
              f"Partners: {candidate['num_partners']}")
    
    print(f"\n{'='*80}")
    print(f"📋 LABELING INSTRUCTIONS")
    print(f"{'='*80}")
    print(f"\n1. Open: {output_path}")
    print(f"2. For each trader:")
    print(f"   - Review 'reference_stats' and 'model_suggestion'")
    print(f"   - Assign 'class_id' (0, 1, 2, or 3)")
    print(f"   - Optionally add 'notes' about your reasoning")
    print(f"3. Run: python merge_labels.py")
    print(f"4. Run: python gnn_core.py")
    print(f"\n{'='*80}\n")
    
    # Save summary statistics
    summary = {
        'total_candidates': len(candidates),
        'selected_count': len(selected),
        'class_distribution': class_counts,
        'top_10_names': [c['name'] for c in selected[:10]],
        'priority_score_range': {
            'min': min(c['priority_score'] for c in selected),
            'max': max(c['priority_score'] for c in selected),
            'mean': np.mean([c['priority_score'] for c in selected])
        }
    }
    
    with open('labeling_selection_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"💾 Summary saved to: labeling_selection_summary.json\n")
    
    return selected


if __name__ == "__main__":
    try:
        prioritize_next_labels(target_count=50)
    except FileNotFoundError:
        print("\n⚠️  ERROR: prediction_analysis.json not found!")
        print("Please run 'python gnn_core.py' first to generate predictions.")
        print("="*80 + "\n")