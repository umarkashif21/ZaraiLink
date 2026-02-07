"""
smart_label_collector.py

Creates a prioritized list of traders for human labeling.
Focuses on:
1. High-impact traders (high volume)
2. Uncertain cases (ambiguous patterns)
3. Representative samples from each segment
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
    txs_as_buyer = Transaction.objects.filter(buyer=trader)
    txs_as_seller = Transaction.objects.filter(seller=trader)
    all_txs = txs_as_buyer | txs_as_seller
    
    if all_txs.count() == 0:
        return None
    
    total_usd = float(all_txs.aggregate(sum_usd=Sum('usd'))['sum_usd'] or 0)
    avg_usd = float(all_txs.aggregate(avg_usd=Avg('usd'))['avg_usd'] or 0)
    std_usd = float(all_txs.aggregate(std_usd=StdDev('usd'))['std_usd'] or 0)
    
    num_as_buyer = txs_as_buyer.count()
    num_as_seller = txs_as_seller.count()
    total_tx = num_as_buyer + num_as_seller
    
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
        'avg_usd': avg_usd,
        'std_usd': std_usd,
        'total_tx': total_tx,
        'consistency_score': consistency_score,
        'num_partners': num_partners,
        'product_diversity': product_diversity,
        'months_active': months_active,
        'avg_tx_size': total_usd / total_tx if total_tx > 0 else 0
    }


def prioritize_traders_for_labeling(max_labels=50):
    buyers = Transaction.objects.values_list('buyer', flat=True).distinct()
    sellers = Transaction.objects.values_list('seller', flat=True).distinct()
    all_traders = list(set(list(buyers) + list(sellers)))
    
    trader_features = []
    for i, trader in enumerate(all_traders):
        features = calculate_trader_features(trader)
        if features:
            trader_features.append(features)
    
    trader_features.sort(key=lambda x: x['total_usd'], reverse=True)
    
    volumes = [t['total_usd'] for t in trader_features]
    p25 = np.percentile(volumes, 25)
    p50 = np.percentile(volumes, 50)
    p75 = np.percentile(volumes, 75)
    
    priority_traders = []
    
    # Tier 1: Top 10
    for t in trader_features[:10]:
        priority_traders.append({
            **t,
            'priority': 'high',
            'reason': f'Top volume: ${t["total_usd"]:,.0f}',
            'tier': 1
        })
    
    # Tier 2: representative samples
    high_vol = [t for t in trader_features if t['total_usd'] >= p75 and t not in priority_traders]
    for t in high_vol[:5]:
        priority_traders.append({**t, 'priority': 'medium', 'reason': 'High volume tier representative', 'tier': 2})
    
    med_vol = [t for t in trader_features if p25 <= t['total_usd'] < p75]
    for t in med_vol[:10]:
        priority_traders.append({**t, 'priority': 'medium', 'reason': 'Medium volume tier representative', 'tier': 2})
    
    low_vol = [t for t in trader_features if t['total_usd'] < p25]
    for t in low_vol[:10]:
        priority_traders.append({**t, 'priority': 'medium', 'reason': 'Low volume tier representative', 'tier': 2})
    
    # Tier 3: ambiguous
    opportunistic = [t for t in trader_features 
                     if t['total_tx'] < 5 and t['avg_tx_size'] > p75 and t not in priority_traders][:5]
    for t in opportunistic:
        priority_traders.append({**t, 'priority': 'high', 'reason': f'Ambiguous: Only {t["total_tx"]} tx but high avg (${t["avg_tx_size"]:,.0f})', 'tier': 3})
    
    consistent_small = [t for t in trader_features 
                        if t['total_tx'] >= 20 and t['total_usd'] < p50 and t not in priority_traders][:5]
    for t in consistent_small:
        priority_traders.append({**t, 'priority': 'medium', 'reason': f'Ambiguous: Many tx ({t["total_tx"]}) but low volume', 'tier': 3})
    
    priority_traders = priority_traders[:max_labels]
    
    template = {}
    for t in priority_traders:
        template[t['name']] = {
            'class_id': None,
            'class_name': None,
            'confidence': 1.0,
            'annotator': 'YOUR_NAME_HERE',
            'notes': '',
            'reference_stats': {
                'total_usd': f"${t['total_usd']:,.2f}",
                'total_transactions': t['total_tx'],
                'avg_transaction_size': f"${t['avg_tx_size']:,.2f}",
                'consistency_score': f"{t['consistency_score']:.2f}",
                'months_active': t['months_active'],
                'num_partners': t['num_partners'],
                'product_diversity': t['product_diversity']
            },
            'labeling_priority': t['priority'],
            'selection_reason': t['reason'],
            'tier': t['tier']
        }
    
    output_path = os.path.join('Fahad_GNN', 'labeling_template.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    instructions = """
================================================================================
HUMAN LABELING INSTRUCTIONS
================================================================================
...
Rename labeling_template.json → human_labels.json and run python Fahad_GNN/gnn_core.py
"""
    instructions_path = os.path.join('Fahad_GNN', 'LABELING_INSTRUCTIONS.txt')
    with open(instructions_path, 'w') as f:
        f.write(instructions)
    
    return priority_traders


if __name__ == "__main__":
    prioritize_traders_for_labeling(max_labels=50)
