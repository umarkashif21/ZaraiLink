"""
create_truly_balanced_labels.py

Creates genuinely balanced labels by sampling across the ENTIRE volume distribution,
not just high-priority traders.
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


def calculate_trader_features(trader):
    """Calculate comprehensive features for a trader"""
    txs_as_buyer = Transaction.objects.filter(buyer=trader)
    txs_as_seller = Transaction.objects.filter(seller=trader)
    all_txs = txs_as_buyer | txs_as_seller
    
    if all_txs.count() == 0:
        return None
    
    total_usd = float(all_txs.aggregate(sum_usd=Sum('usd'))['sum_usd'] or 0)
    total_tx = all_txs.count()
    
    # Consistency
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


def assign_class_by_percentile(trader_stats, volume_percentiles):
    """
    Assign class based on volume percentile ONLY.
    This ensures true representation of data distribution.
    """
    total_usd = trader_stats['total_usd']
    
    # Determine percentile
    if total_usd >= volume_percentiles[95]:
        return 0, f"Top 5% by volume (${total_usd:,.0f})"
    elif total_usd >= volume_percentiles[80]:
        return 1, f"Top 20% by volume (${total_usd:,.0f})"
    elif total_usd >= volume_percentiles[50]:
        return 2, f"Top 50% by volume (${total_usd:,.0f})"
    else:
        return 3, f"Bottom 50% by volume (${total_usd:,.0f})"


def create_balanced_percentile_labels(samples_per_class=12, output_file='human_labels.json'):
    """
    Create balanced labels by sampling from each volume quartile.
    """
    print("="*80)
    print("CREATING TRULY BALANCED LABELS (PERCENTILE-BASED)")
    print("="*80)
    
    buyers = Transaction.objects.values_list('buyer', flat=True).distinct()
    sellers = Transaction.objects.values_list('seller', flat=True).distinct()
    all_traders = list(set(list(buyers) + list(sellers)))
    
    print(f"\n[INFO] Found {len(all_traders)} unique traders")
    
    # Calculate features for all
    trader_stats = []
    for trader in all_traders:
        features = calculate_trader_features(trader)
        if features:
            trader_stats.append(features)
    
    # Calculate volume percentiles
    volumes = [t['total_usd'] for t in trader_stats]
    volume_percentiles = {
        50: np.percentile(volumes, 50),
        80: np.percentile(volumes, 80),
        95: np.percentile(volumes, 95)
    }
    
    print(f"\n[INFO] Volume percentiles:")
    print(f"  50th percentile: ${volume_percentiles[50]:,.2f}")
    print(f"  80th percentile: ${volume_percentiles[80]:,.2f}")
    print(f"  95th percentile: ${volume_percentiles[95]:,.2f}")
    
    # Classify all traders
    classified = {0: [], 1: [], 2: [], 3: []}
    for stats in trader_stats:
        class_id, reason = assign_class_by_percentile(stats, volume_percentiles)
        classified[class_id].append({**stats, 'reason': reason})
    
    print(f"\n[INFO] Natural distribution:")
    for class_id in range(4):
        print(f"  Class {class_id}: {len(classified[class_id])} traders ({len(classified[class_id])/len(trader_stats)*100:.1f}%)")
    
    # Sample evenly from each class
    labels = {}
    
    for class_id in range(4):
        candidates = classified[class_id]
        
        if len(candidates) == 0:
            print(f"\n⚠️  Class {class_id} has no candidates!")
            continue
        
        # Sample diverse traders (spread across the range)
        n_samples = min(samples_per_class, len(candidates))
        
        if len(candidates) <= n_samples:
            selected = candidates
        else:
            # Sample evenly across the sorted list
            indices = np.linspace(0, len(candidates)-1, n_samples, dtype=int)
            selected = [candidates[i] for i in indices]
        
        for trader_info in selected:
            labels[trader_info['name']] = {
                'class_id': class_id,
                'confidence': 1.0,
                'reason': trader_info['reason'],
                'method': 'percentile_balanced',
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
    
    class_dist = {}
    for trader, info in labels.items():
        class_id = info['class_id']
        class_dist[class_id] = class_dist.get(class_id, 0) + 1
    
    print(f"\n📊 Final label distribution:")
    for class_id in sorted(class_dist.keys()):
        print(f"  Class {class_id}: {class_dist[class_id]} samples")
    
    print(f"\n  Saved to: {output_path}")
    print("\n✅ Ready to train! Run: python gnn_core.py")
    
    return labels


if __name__ == "__main__":
    # Create 48 balanced labels (12 per class)
    create_balanced_percentile_labels(samples_per_class=12, output_file='human_labels.json')