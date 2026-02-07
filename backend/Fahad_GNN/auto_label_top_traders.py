"""
auto_label_top_traders.py

Automatically labels the top priority traders from model_guided_labeling_template.json
using enhanced heuristics. This saves you from manually labeling 30+ traders.
"""

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zarailink.settings")
django.setup()

from django.db.models import Sum, Avg, Count, StdDev
from django.db.models.functions import TruncMonth
from trade_data.models import Transaction
import numpy as np


def calculate_enhanced_features(trader_name):
    """Calculate detailed features for classification"""
    txs_as_buyer = Transaction.objects.filter(buyer=trader_name)
    txs_as_seller = Transaction.objects.filter(seller=trader_name)
    all_txs = txs_as_buyer | txs_as_seller
    
    if all_txs.count() == 0:
        return None
    
    total_usd = float(all_txs.aggregate(sum_usd=Sum('usd'))['sum_usd'] or 0)
    avg_usd = float(all_txs.aggregate(avg_usd=Avg('usd'))['avg_usd'] or 0)
    std_usd = float(all_txs.aggregate(std_usd=StdDev('usd'))['std_usd'] or 0)
    
    num_as_buyer = txs_as_buyer.count()
    num_as_seller = txs_as_seller.count()
    total_tx = all_txs.count()
    
    # Partners
    partners_as_buyer = txs_as_buyer.values('seller').distinct().count()
    partners_as_seller = txs_as_seller.values('buyer').distinct().count()
    num_partners = partners_as_buyer + partners_as_seller
    
    # Diversity
    product_diversity = all_txs.values('product_item').distinct().count()
    country_diversity = all_txs.values('country').distinct().count()
    
    # Temporal consistency
    monthly_stats = all_txs.annotate(
        month=TruncMonth('reporting_date')
    ).values('month').annotate(
        monthly_usd=Sum('usd')
    ).order_by('month')
    
    months_active = len(monthly_stats)
    
    if months_active > 1:
        monthly_volumes = [float(m['monthly_usd']) for m in monthly_stats if m['monthly_usd']]
        if len(monthly_volumes) > 1:
            mean_monthly = np.mean(monthly_volumes)
            std_monthly = np.std(monthly_volumes)
            consistency_score = 1.0 / (1.0 + (std_monthly / mean_monthly)) if mean_monthly > 0 else 0
        else:
            consistency_score = 0.5
    else:
        consistency_score = 0.5 if months_active == 1 else 0
    
    return {
        'total_usd': total_usd,
        'avg_usd': avg_usd,
        'std_usd': std_usd,
        'total_tx': total_tx,
        'avg_tx_size': total_usd / total_tx if total_tx > 0 else 0,
        'num_partners': num_partners,
        'product_diversity': product_diversity,
        'country_diversity': country_diversity,
        'months_active': months_active,
        'consistency_score': consistency_score,
        'num_as_buyer': num_as_buyer,
        'num_as_seller': num_as_seller
    }


def assign_class_intelligent(features, model_suggestion):
    """
    Enhanced classification logic that considers both features and model suggestion.
    
    Class 0: Major Strategic Traders
    - Very high volume (>$10M)
    - Consistent activity (consistency > 0.6)
    - Many partners (>5)
    - Diverse products
    
    Class 1: Opportunistic/Spot Traders
    - High average transaction size (>$500K)
    - Low frequency (<10 transactions)
    - Can be high total volume but sporadic
    
    Class 2: Regular/Established Traders
    - Medium to high volume ($100K - $10M)
    - Consistent activity
    - Regular transaction pattern (10+ transactions)
    
    Class 3: Small/Irregular Traders
    - Low volume (<$100K)
    - Sporadic or inconsistent
    - Few partners
    """
    
    total_usd = features['total_usd']
    avg_tx_size = features['avg_tx_size']
    total_tx = features['total_tx']
    consistency = features['consistency_score']
    num_partners = features['num_partners']
    product_diversity = features['product_diversity']
    
    # Decision tree with confidence scores
    scores = {0: 0, 1: 0, 2: 0, 3: 0}
    
    # --- Class 0: Major Strategic Traders ---
    if total_usd > 10_000_000:
        scores[0] += 30
    elif total_usd > 5_000_000:
        scores[0] += 15
    
    if consistency > 0.7:
        scores[0] += 20
    elif consistency > 0.5:
        scores[0] += 10
    
    if num_partners >= 10:
        scores[0] += 20
    elif num_partners >= 5:
        scores[0] += 10
    
    if total_tx >= 20:
        scores[0] += 15
    elif total_tx >= 10:
        scores[0] += 5
    
    if product_diversity >= 5:
        scores[0] += 15
    
    # --- Class 1: Opportunistic Traders ---
    if avg_tx_size > 1_000_000:
        scores[1] += 40
    elif avg_tx_size > 500_000:
        scores[1] += 20
    
    if total_tx < 10:
        scores[1] += 30
    elif total_tx < 20:
        scores[1] += 15
    
    if consistency < 0.5:
        scores[1] += 20
    
    if num_partners < 5:
        scores[1] += 10
    
    # --- Class 2: Regular Traders ---
    if 100_000 < total_usd < 10_000_000:
        scores[2] += 25
    
    if total_tx >= 20:
        scores[2] += 25
    elif total_tx >= 10:
        scores[2] += 15
    
    if 0.5 < consistency < 0.8:
        scores[2] += 20
    
    if 3 <= num_partners < 10:
        scores[2] += 15
    
    if 2 <= product_diversity < 5:
        scores[2] += 15
    
    # --- Class 3: Small/Irregular ---
    if total_usd < 100_000:
        scores[3] += 40
    elif total_usd < 500_000:
        scores[3] += 20
    
    if total_tx < 10:
        scores[3] += 20
    
    if consistency < 0.4:
        scores[3] += 20
    
    if num_partners < 3:
        scores[3] += 15
    
    if product_diversity == 1:
        scores[3] += 5
    
    # Consider model suggestion (bonus points)
    model_class = model_suggestion['predicted_class']
    model_conf = float(model_suggestion['model_confidence'])
    
    if model_conf > 0.7:
        scores[model_class] += 20
    elif model_conf > 0.5:
        scores[model_class] += 10
    
    # Select class with highest score
    predicted_class = max(scores, key=scores.get)
    confidence_score = scores[predicted_class] / 100.0
    
    # Generate reasoning
    reasons = []
    if total_usd > 10_000_000:
        reasons.append(f"Very high volume (${total_usd:,.0f})")
    elif total_usd > 1_000_000:
        reasons.append(f"High volume (${total_usd:,.0f})")
    elif total_usd < 100_000:
        reasons.append(f"Low volume (${total_usd:,.0f})")
    
    if avg_tx_size > 1_000_000:
        reasons.append(f"High avg tx (${avg_tx_size:,.0f})")
    
    if total_tx >= 20:
        reasons.append(f"Many transactions ({total_tx})")
    elif total_tx < 10:
        reasons.append(f"Few transactions ({total_tx})")
    
    if consistency > 0.7:
        reasons.append(f"Very consistent ({consistency:.2f})")
    elif consistency < 0.4:
        reasons.append(f"Inconsistent ({consistency:.2f})")
    
    if num_partners >= 10:
        reasons.append(f"Many partners ({num_partners})")
    elif num_partners < 3:
        reasons.append(f"Few partners ({num_partners})")
    
    reasoning = "; ".join(reasons)
    
    return predicted_class, confidence_score, reasoning


def auto_label_traders(input_file='model_guided_labeling_template.json', 
                       output_file='model_guided_labeling_template.json',
                       num_to_label=30):
    """
    Automatically label top N traders from the template.
    """
    print("="*80)
    print("AUTO-LABELING TOP PRIORITY TRADERS")
    print("="*80)
    
    # Load template
    if not os.path.exists(input_file):
        print(f"\n⚠️  ERROR: {input_file} not found!")
        print("Run 'python model_guided_label_selection.py' first.")
        return
    
    with open(input_file, 'r') as f:
        template = json.load(f)
    
    print(f"\n[INFO] Loaded {len(template)} traders from template")
    print(f"[INFO] Will auto-label top {num_to_label} traders")
    
    # Get traders sorted by priority
    traders_with_priority = []
    for trader_name, info in template.items():
        priority_score = float(info['model_suggestion']['priority_score'])
        traders_with_priority.append((trader_name, priority_score, info))
    
    traders_with_priority.sort(key=lambda x: x[1], reverse=True)
    
    # Auto-label top N
    labeled_count = 0
    class_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    
    for i, (trader_name, priority_score, info) in enumerate(traders_with_priority[:num_to_label]):
        print(f"\n  Processing {i+1}/{num_to_label}: {trader_name}")
        
        # Get enhanced features
        features = calculate_enhanced_features(trader_name)
        
        if features is None:
            print(f"    ⚠️  No transaction data found, skipping")
            continue
        
        # Classify
        predicted_class, conf_score, reasoning = assign_class_intelligent(
            features, 
            info['model_suggestion']
        )
        
        # Update template
        template[trader_name]['class_id'] = predicted_class
        template[trader_name]['confidence'] = conf_score
        template[trader_name]['annotator'] = 'AUTO_LABELER'
        template[trader_name]['notes'] = f"Auto-labeled: {reasoning}"
        
        class_counts[predicted_class] += 1
        labeled_count += 1
        
        print(f"    ✅ Assigned Class {predicted_class} (confidence: {conf_score:.2f})")
        print(f"    Reasoning: {reasoning}")
    
    # Save updated template
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"[SUCCESS] Auto-labeled {labeled_count} traders")
    print(f"{'='*80}")
    print(f"\nClass distribution:")
    for class_id in range(4):
        print(f"  Class {class_id}: {class_counts[class_id]} traders")
    
    print(f"\n💾 Saved to: {output_file}")
    print(f"\n📋 Next steps:")
    print(f"  1. Review {output_file} (optional - check if labels look reasonable)")
    print(f"  2. Run: python merge_labels.py")
    print(f"  3. Run: python gnn_core.py")
    print(f"{'='*80}\n")
    
    return labeled_count


if __name__ == "__main__":
    auto_label_traders(num_to_label=30)