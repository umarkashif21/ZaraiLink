"""
create_balanced_test_labels.py

Generate BALANCED test labels with at least 5 samples per class.
This ensures proper train/val splitting.
"""

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zarailink.settings")
django.setup()

from django.db.models import Sum, Count, StdDev
from django.db.models.functions import TruncMonth
from trade_data.models import Transaction
import numpy as np


def calculate_trader_features(trader):
    """Calculate comprehensive features for a trader"""
    txs_as_buyer = Transaction.objects.filter(buyer=trader)
    txs_as_seller = Transaction.objects.filter(seller=trader)
    all_txs = txs_as_buyer | txs_as_seller
    
    if all_txs.count() == 0:
        return None
    
    total_usd = float(all_txs.aggregate(sum_usd=Sum('usd'))['sum_usd'] or 0)
    avg_usd = float(all_txs.aggregate(avg_usd=Sum('usd'))['avg_usd'] or 0)
    
    num_as_buyer = txs_as_buyer.count()
    num_as_seller = txs_as_seller.count()
    total_tx = num_as_buyer + num_as_seller
    
    # Consistency score
    monthly_stats = all_txs.annotate(
        month=TruncMonth('reporting_date')
    ).values('month').annotate(
        monthly_usd=Sum('usd')
    )
    
    months_active = len(monthly_stats)
    
    if months_active > 1:
        monthly_volumes = [float(m['monthly_usd']) for m in monthly_stats if m['monthly_usd']]
        mean_monthly = np.mean(monthly_volumes) if monthly_volumes else 0
        std_monthly = np.std(monthly_volumes) if monthly_volumes else 0
        consistency_score = 1.0 / (1.0 + (std_monthly / mean_monthly)) if mean_monthly > 0 else 0
    else:
        consistency_score = 0.5 if months_active == 1 else 0
    
    partners_as_buyer = txs_as_buyer.values('seller').distinct().count()
    partners_as_seller = txs_as_seller.values('buyer').distinct().count()
    num_partners = partners_as_buyer + partners_as_seller
    
    product_diversity = all_txs.values('product_item').distinct().count()
    
    return {
        'name': trader,
        'total_usd': total_usd,
        'total_tx': total_tx,
        'avg_tx_size': total_usd / total_tx if total_tx > 0 else 0,
        'consistency_score': consistency_score,
        'num_partners': num_partners,
        'product_diversity': product_diversity,
        'months_active': months_active
    }


def assign_class_robust(stats):
    """
    Improved classification with better separation.
    Ensures we get balanced classes.
    """
    total_usd = stats['total_usd']
    avg_tx = stats['avg_tx_size']
    consistency = stats['consistency_score']
    num_partners = stats['num_partners']
    total_tx = stats['total_tx']
    
    # Class 0: Major strategic players
    # High volume + consistent + diverse
    if (total_usd > 5_000_000 and 
        consistency > 0.6 and 
        num_partners >= 3 and
        total_tx >= 10):
        return 0, "Major strategic trader"
    
    # Class 1: Opportunistic/Spot traders
    # High value per transaction but infrequent
    if (avg_tx > 1_000_000 and 
        total_tx < 10):
        return 1, "Opportunistic spot trader"
    
    # Class 2: Regular/Established traders
    # Medium volume, consistent activity
    if (total_usd > 100_000 and
        total_tx >= 10 and
        consistency > 0.4):
        return 2, "Regular established trader"
    
    # Class 3: Small/Irregular traders
    # Everything else
    return 3, "Small/irregular trader"


def create_balanced_labels(target_per_class=5, output_file='human_labels.json'):
    """
    Create balanced test labels with equal samples per class.
    """
    print("="*80)
    print("CREATING BALANCED TEST LABELS")
    print("="*80)
    
    buyers = Transaction.objects.values_list('buyer', flat=True).distinct()
    sellers = Transaction.objects.values_list('seller', flat=True).distinct()
    all_traders = list(set(list(buyers) + list(sellers)))
    
    print(f"\n[INFO] Found {len(all_traders)} unique traders")
    
    # Calculate features for all traders
    trader_stats = []
    for trader in all_traders:
        features = calculate_trader_features(trader)
        if features:
            trader_stats.append(features)
    
    # Sort by total volume
    trader_stats.sort(key=lambda x: x['total_usd'], reverse=True)
    
    # Classify all traders
    classified_traders = {0: [], 1: [], 2: [], 3: []}
    
    for stats in trader_stats:
        class_id, reason = assign_class_robust(stats)
        classified_traders[class_id].append({**stats, 'reason': reason})
    
    print(f"\n[INFO] Natural class distribution:")
    for class_id in range(4):
        print(f"  Class {class_id}: {len(classified_traders[class_id])} traders")
    
    # Select balanced samples
    labels = {}
    
    for class_id in range(4):
        candidates = classified_traders[class_id]
        
        if len(candidates) < target_per_class:
            print(f"\n⚠️  Warning: Class {class_id} has only {len(candidates)} candidates")
            selected = candidates  # Take all
        else:
            # Select diverse samples (top, middle, bottom of volume range)
            indices = np.linspace(0, len(candidates)-1, target_per_class, dtype=int)
            selected = [candidates[i] for i in indices]
        
        for trader_info in selected:
            labels[trader_info['name']] = {
                'class_id': class_id,
                'confidence': 1.0,
                'reason': trader_info['reason'],
                'method': 'heuristic_balanced',
                'stats': {
                    'total_usd': f"${trader_info['total_usd']:,.2f}",
                    'total_tx': trader_info['total_tx'],
                    'avg_tx_size': f"${trader_info['avg_tx_size']:,.2f}",
                    'consistency': f"{trader_info['consistency_score']:.2f}",
                    'partners': trader_info['num_partners']
                }
            }
    
    # Save
    output_path = output_file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(labels, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SUCCESS] Created {len(labels)} balanced labels")
    print(f"  Class distribution:")
    class_dist = {}
    for trader, info in labels.items():
        class_id = info['class_id']
        class_dist[class_id] = class_dist.get(class_id, 0) + 1
    
    for class_id in sorted(class_dist.keys()):
        print(f"    Class {class_id}: {class_dist[class_id]} samples")
    
    print(f"\n  Saved to: {output_path}")
    print("\n✅ Ready to train! Run: python gnn_core.py")
    
    return labels


if __name__ == "__main__":
    create_balanced_labels(target_per_class=5)