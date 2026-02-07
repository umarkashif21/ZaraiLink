import sys
import os
import django
import torch
from torch_geometric.data import Data
from django.db.models import Sum, Avg, Count, StdDev
from django.db.models.functions import TruncMonth
import numpy as np

# Add backend folder to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Correct Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zarailink.settings")

# Initialize Django
django.setup()

from trade_data.models import Transaction
from sklearn.preprocessing import StandardScaler


def build_graph():
    """
    Build a corrected trader graph with node features and edge attributes.
    
    Returns:
        data (torch_geometric.data.Data): PyG Data object
        node_id_mapping (dict): mapping from trader name -> node ID
        stats (dict): graph statistics for validation
    """

    # -------------------------------
    # Step 1: Collect unique traders
    # -------------------------------
    buyers = list(Transaction.objects.values_list('buyer', flat=True).distinct())
    sellers = list(Transaction.objects.values_list('seller', flat=True).distinct())
    traders = list(set(buyers + sellers))
    
    if len(traders) == 0:
        raise ValueError("[ERROR] No traders found in database!")
    
    node_id_mapping = {trader: idx for idx, trader in enumerate(traders)}

    print(f"[INFO] Total unique traders: {len(traders)}")
    print(f"  - Unique buyers: {len(buyers)}")
    print(f"  - Unique sellers: {len(sellers)}")

    # -------------------------------
    # Step 2: Build edges (seller → buyer)
    # -------------------------------
    edge_index = [[], []]  # PyG format [2, num_edges]
    edge_attrs = []

    # Aggregate transactions for each seller-buyer pair
    pair_agg = Transaction.objects.values('buyer', 'seller').annotate(
        total_usd=Sum('usd'),
        total_qty=Sum('qty_mt'),
        tx_count=Count('id')
    )

    for pair in pair_agg:
        buyer = pair['buyer']
        seller = pair['seller']
        
        # Skip if buyer or seller not in mapping (safety check)
        if buyer not in node_id_mapping or seller not in node_id_mapping:
            continue

        src = node_id_mapping[seller]  # seller → buyer (goods flow)
        dst = node_id_mapping[buyer]

        edge_index[0].append(src)
        edge_index[1].append(dst)

        # Edge features: total_usd, total_qty, number of transactions
        edge_attrs.append([
            float(pair['total_usd'] or 0),
            float(pair['total_qty'] or 0),
            float(pair['tx_count'])
        ])

    if len(edge_index[0]) == 0:
        raise ValueError("[ERROR] No edges found in graph!")

    # Convert to numpy for normalization
    edge_attrs_array = np.array(edge_attrs)
    
    # Normalize edge features
    print(f"[INFO] Normalizing edge features...")
    edge_scaler = StandardScaler()
    edge_attrs_normalized = edge_scaler.fit_transform(edge_attrs_array)
    
    edge_index = torch.tensor(edge_index, dtype=torch.long)
    edge_attrs = torch.tensor(edge_attrs_normalized, dtype=torch.float)

    # Check for isolated nodes
    print(f"[INFO] Checking graph connectivity...")
    nodes_with_edges = set()
    for i in range(len(edge_index[0])):
        nodes_with_edges.add(int(edge_index[0][i]))
        nodes_with_edges.add(int(edge_index[1][i]))
    
    isolated_nodes = set(range(len(traders))) - nodes_with_edges
    if isolated_nodes:
        print(f"[WARNING] Found {len(isolated_nodes)} isolated nodes (no connections)")
        isolated_traders = [traders[i] for i in isolated_nodes]
        print(f"  Isolated traders: {isolated_traders[:5]}...")  # Show first 5

    # -------------------------------
    # Step 3: Build node features
    # -------------------------------
    node_features = []
    
    print(f"[INFO] Building node features for {len(traders)} traders...")

    for idx, trader in enumerate(traders):
        if (idx + 1) % 100 == 0:
            print(f"  Progress: {idx + 1}/{len(traders)} traders processed")
        
        # Transactions as buyer and seller
        txs_as_buyer = Transaction.objects.filter(buyer=trader)
        txs_as_seller = Transaction.objects.filter(seller=trader)
        all_txs = txs_as_buyer | txs_as_seller

        tx_count = all_txs.count()
        if tx_count == 0:
            print(f"[WARNING] Trader '{trader}' has no transactions!")
            # Assign default/zero features for traders with no transactions
            node_features.append([0.0] * 12)
            continue

        # Volume statistics
        total_usd = float(all_txs.aggregate(sum_usd=Sum('usd'))['sum_usd'] or 0)
        avg_usd = float(all_txs.aggregate(avg_usd=Avg('usd'))['avg_usd'] or 0)
        std_usd = float(all_txs.aggregate(std_usd=StdDev('usd'))['std_usd'] or 0)

        # Number of transactions
        num_as_buyer = txs_as_buyer.count()
        num_as_seller = txs_as_seller.count()
        total_transactions = num_as_buyer + num_as_seller

        # Number of unique trading partners (CORRECTED)
        partners_as_buyer = txs_as_buyer.values('seller').distinct().count()
        partners_as_seller = txs_as_seller.values('buyer').distinct().count()
        num_partners = partners_as_buyer + partners_as_seller

        # Product diversity
        product_diversity = all_txs.values('product_item').distinct().count()

        # Country diversity
        country_diversity = all_txs.values('country').distinct().count()

        # Temporal stats using reporting_date
        monthly_stats = all_txs.annotate(
            month=TruncMonth('reporting_date')
        ).values('month').annotate(
            monthly_usd=Sum('usd'),
            monthly_count=Count('id')
        ).order_by('month')

        months_active = len(monthly_stats)

        # Consistency score (CORRECTED formula)
        if months_active > 1:
            monthly_volumes = [float(m['monthly_usd']) for m in monthly_stats if m['monthly_usd']]
            if len(monthly_volumes) > 1:
                mean_monthly = np.mean(monthly_volumes)
                std_monthly = np.std(monthly_volumes)
                
                if mean_monthly > 0:
                    cv_monthly = std_monthly / mean_monthly
                    consistency_score = 1.0 / (1.0 + cv_monthly)  # Range: 0 to 1
                else:
                    consistency_score = 0.0
            else:
                consistency_score = 0.5
        elif months_active == 1:
            consistency_score = 0.5  # single month = medium consistency
        else:
            consistency_score = 0.0

        # Coefficient of variation for transaction sizes
        cv = (std_usd / avg_usd) if avg_usd > 0 else 0.0

        # Average transaction size
        avg_transaction_size = total_usd / total_transactions if total_transactions > 0 else 0.0

        # Node feature vector (12 features)
        node_features.append([
            total_usd,
            avg_usd,
            std_usd,
            num_partners,
            product_diversity,
            consistency_score,
            cv,
            num_as_buyer,
            num_as_seller,
            months_active,
            country_diversity,
            avg_transaction_size
        ])

    # Normalize node features
    print(f"[INFO] Normalizing node features...")
    node_features_array = np.array(node_features)
    
    # Check for NaN or Inf values
    if np.any(np.isnan(node_features_array)) or np.any(np.isinf(node_features_array)):
        print("[WARNING] Found NaN or Inf values in node features. Replacing with 0...")
        node_features_array = np.nan_to_num(node_features_array, nan=0.0, posinf=0.0, neginf=0.0)
    
    scaler = StandardScaler()
    node_features_normalized = scaler.fit_transform(node_features_array)
    x = torch.tensor(node_features_normalized, dtype=torch.float)

    # -------------------------------
    # Step 4: Create PyG Data object
    # -------------------------------
    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attrs
    )

    # Compute graph statistics
    stats = {
        'num_nodes': data.num_nodes,
        'num_edges': data.num_edges,
        'num_isolated_nodes': len(isolated_nodes),
        'avg_degree': (2 * data.num_edges) / data.num_nodes if data.num_nodes > 0 else 0,
        'node_feature_dim': data.x.shape[1],
        'edge_feature_dim': data.edge_attr.shape[1]
    }

    print("\n" + "="*60)
    print("[INFO] Graph construction complete")
    print("="*60)
    print(f"Nodes: {stats['num_nodes']}")
    print(f"Edges: {stats['num_edges']}")
    print(f"Isolated nodes: {stats['num_isolated_nodes']}")
    print(f"Average degree: {stats['avg_degree']:.2f}")
    print(f"Node features shape: {data.x.shape}")
    print(f"Edge features shape: {data.edge_attr.shape}")
    print("="*60)

    return data, node_id_mapping, stats


# Optional test run
if __name__ == "__main__":
    try:
        data, mapping, stats = build_graph()
        
        # Additional validation
        print("\n[VALIDATION CHECKS]")
        print(f"✓ Node features contain no NaN: {not torch.isnan(data.x).any()}")
        print(f"✓ Edge features contain no NaN: {not torch.isnan(data.edge_attr).any()}")
        print(f"✓ Edge indices valid: {data.edge_index.max() < data.num_nodes}")
        
        # Sample statistics
        print(f"\nNode feature statistics:")
        print(f"  Mean: {data.x.mean(dim=0)}")
        print(f"  Std: {data.x.std(dim=0)}")
        
    except Exception as e:
        print(f"\n[ERROR] Graph construction failed: {e}")
        import traceback
        traceback.print_exc()