"""
Link Prediction Service for Buyer-Seller recommendations.

Implements 5 methods:
1. Node2Vec + Cosine Similarity - Uses pre-computed embeddings
2. Common Neighbors - Nodes sharing common connections
3. Product Co-Trade - Buyers trading same products likely share sellers
4. Jaccard Coefficient - Normalized similarity measure
5. Preferential Attachment - Popular nodes attract more connections
"""

import networkx as nx
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from trade_data.models import Transaction, CompanyEmbedding
from django.db.models import Count






MAX_CONFIDENCE_SCORE = 0.95

def scale_confidence(score, max_val=1.0):
    """
    Scale a score to never exceed MAX_CONFIDENCE_SCORE (95%).
    This prevents misleading 100% predictions.
    """
    if max_val <= 0:
        return 0.0
    normalized = min(1.0, max(0.0, score / max_val))
    
    return normalized * MAX_CONFIDENCE_SCORE


def load_buyer_seller_graph():
    """Load the buyer-seller graph from GraphML or build from transactions."""
    try:
        G = nx.read_graphml("buyer_seller_graph.graphml")
        return G
    except:
        
        G = nx.Graph()
        transactions = Transaction.objects.values('buyer', 'seller', 'qty_mt')
        for tx in transactions:
            buyer = tx['buyer']
            seller = tx['seller']
            weight = float(tx['qty_mt']) if tx['qty_mt'] else 1.0
            
            G.add_node(buyer, type='buyer')
            G.add_node(seller, type='seller')
            
            if G.has_edge(buyer, seller):
                G[buyer][seller]['weight'] += weight
            else:
                G.add_edge(buyer, seller, weight=weight)
        return G


def get_all_buyers():
    """Get all unique buyers from transactions."""
    return list(Transaction.objects.values_list('buyer', flat=True).distinct())


def get_all_sellers():
    """Get all unique sellers from transactions."""
    return list(Transaction.objects.values_list('seller', flat=True).distinct())





def predict_sellers_node2vec(buyer_name, top_k=10):
    """
    Find potential sellers for a buyer using Node2Vec embeddings.
    Uses pre-computed embeddings from CompanyEmbedding model.
    """
    results = []
    
    try:
        
        buyer_emb = CompanyEmbedding.objects.filter(company_name=buyer_name).first()
        if not buyer_emb:
            return {"error": "Buyer not found in embeddings", "results": []}
        
        buyer_vector = np.array(buyer_emb.embedding).reshape(1, -1)
        
        
        seller_names = set(Transaction.objects.values_list('seller', flat=True).distinct())
        
        
        existing_partners = set(
            Transaction.objects.filter(buyer=buyer_name)
            .values_list('seller', flat=True).distinct()
        )
        
        seller_embeddings = CompanyEmbedding.objects.filter(company_name__in=seller_names)
        
        for seller_emb in seller_embeddings:
            if seller_emb.company_name in existing_partners:
                continue  
            
            seller_vector = np.array(seller_emb.embedding).reshape(1, -1)
            similarity = cosine_similarity(buyer_vector, seller_vector)[0][0]
            
            results.append({
                "seller": seller_emb.company_name,
                "raw_score": float(similarity),
                "method": "node2vec",
                "segment_tag": seller_emb.cluster_tag
            })
        
        
        results.sort(key=lambda x: x['raw_score'], reverse=True)
        top_results = results[:top_k]
        
        
        for r in top_results:
            r['score'] = scale_confidence(r['raw_score'], max_val=1.0)
            del r['raw_score']
        
        return {"results": top_results}
    
    except Exception as e:
        return {"error": str(e), "results": []}


def predict_buyers_node2vec(seller_name, top_k=10):
    """Find potential buyers for a seller using Node2Vec embeddings."""
    results = []
    
    try:
        seller_emb = CompanyEmbedding.objects.filter(company_name=seller_name).first()
        if not seller_emb:
            return {"error": "Seller not found in embeddings", "results": []}
        
        seller_vector = np.array(seller_emb.embedding).reshape(1, -1)
        
        buyer_names = set(Transaction.objects.values_list('buyer', flat=True).distinct())
        
        existing_partners = set(
            Transaction.objects.filter(seller=seller_name)
            .values_list('buyer', flat=True).distinct()
        )
        
        buyer_embeddings = CompanyEmbedding.objects.filter(company_name__in=buyer_names)
        
        for buyer_emb in buyer_embeddings:
            if buyer_emb.company_name in existing_partners:
                continue
            
            buyer_vector = np.array(buyer_emb.embedding).reshape(1, -1)
            similarity = cosine_similarity(seller_vector, buyer_vector)[0][0]
            
            results.append({
                "buyer": buyer_emb.company_name,
                "raw_score": float(similarity),
                "method": "node2vec",
                "segment_tag": buyer_emb.cluster_tag
            })
        
        
        results.sort(key=lambda x: x['raw_score'], reverse=True)
        top_results = results[:top_k]
        
        
        for r in top_results:
            r['score'] = scale_confidence(r['raw_score'], max_val=1.0)
            del r['raw_score']
        
        return {"results": top_results}
    
    except Exception as e:
        return {"error": str(e), "results": []}





def predict_sellers_common_neighbors(buyer_name, top_k=10):
    """
    Find sellers that share common connections with the buyer.
    If buyer B1 and buyer B2 both trade with seller S1,
    and B2 also trades with S2, then S2 is recommended to B1.
    
    Returns normalized scores (0-1 range).
    """
    results = []
    
    
    current_sellers = set(
        Transaction.objects.filter(buyer=buyer_name)
        .values_list('seller', flat=True).distinct()
    )
    
    if not current_sellers:
        return {"error": "Buyer has no transaction history", "results": []}
    
    
    similar_buyers = set(
        Transaction.objects.filter(seller__in=current_sellers)
        .exclude(buyer=buyer_name)
        .values_list('buyer', flat=True).distinct()
    )
    
    
    candidate_sellers = defaultdict(int)
    for similar_buyer in similar_buyers:
        their_sellers = Transaction.objects.filter(buyer=similar_buyer).values_list('seller', flat=True).distinct()
        for seller in their_sellers:
            if seller not in current_sellers:
                candidate_sellers[seller] += 1  
    
    
    sorted_candidates = sorted(candidate_sellers.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    
    max_count = max([c[1] for c in sorted_candidates], default=1)
    
    for seller, count in sorted_candidates:
        normalized_score = count / max_count if max_count > 0 else 0
        results.append({
            "seller": seller,
            "score": scale_confidence(normalized_score, max_val=1.0),  
            "method": "common_neighbors",
            "common_buyer_count": count  
        })
    
    return {"results": results}


def predict_buyers_common_neighbors(seller_name, top_k=10):
    """Find buyers that share common connections with the seller.
    
    Returns normalized scores (0-1 range).
    """
    results = []
    
    current_buyers = set(
        Transaction.objects.filter(seller=seller_name)
        .values_list('buyer', flat=True).distinct()
    )
    
    if not current_buyers:
        return {"error": "Seller has no transaction history", "results": []}
    
    similar_sellers = set(
        Transaction.objects.filter(buyer__in=current_buyers)
        .exclude(seller=seller_name)
        .values_list('seller', flat=True).distinct()
    )
    
    candidate_buyers = defaultdict(int)
    for similar_seller in similar_sellers:
        their_buyers = Transaction.objects.filter(seller=similar_seller).values_list('buyer', flat=True).distinct()
        for buyer in their_buyers:
            if buyer not in current_buyers:
                candidate_buyers[buyer] += 1
    
    
    sorted_candidates = sorted(candidate_buyers.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    
    max_count = max([c[1] for c in sorted_candidates], default=1)
    
    for buyer, count in sorted_candidates:
        normalized_score = count / max_count if max_count > 0 else 0
        results.append({
            "buyer": buyer,
            "score": scale_confidence(normalized_score, max_val=1.0),  
            "method": "common_neighbors",
            "common_seller_count": count  
        })
    
    return {"results": results}





def predict_sellers_by_product(buyer_name, top_k=10):
    """
    Find sellers who sell the same products the buyer purchases.
    
    Returns normalized scores (0-1 range).
    """
    results = []
    
    
    buyer_products = set(
        Transaction.objects.filter(buyer=buyer_name)
        .exclude(product_item__isnull=True)
        .values_list('product_item_id', flat=True).distinct()
    )
    
    if not buyer_products:
        return {"error": "Buyer has no product history", "results": []}
    
    
    current_sellers = set(
        Transaction.objects.filter(buyer=buyer_name)
        .values_list('seller', flat=True).distinct()
    )
    
    
    candidate_sellers = list(
        Transaction.objects.filter(product_item_id__in=buyer_products)
        .exclude(seller__in=current_sellers)
        .values('seller')
        .annotate(product_match_count=Count('product_item_id', distinct=True))
        .order_by('-product_match_count')[:top_k]
    )
    
    
    max_count = max([item['product_match_count'] for item in candidate_sellers], default=1)
    
    for item in candidate_sellers:
        count = item['product_match_count']
        normalized_score = count / max_count if max_count > 0 else 0
        results.append({
            "seller": item['seller'],
            "score": scale_confidence(normalized_score, max_val=1.0),  
            "method": "product_cotrade",
            "matching_products": count  
        })
    
    return {"results": results}


def predict_buyers_by_product(seller_name, top_k=10):
    """Find buyers who purchase the same products the seller offers.
    
    Returns normalized scores (0-1 range).
    """
    results = []
    
    seller_products = set(
        Transaction.objects.filter(seller=seller_name)
        .exclude(product_item__isnull=True)
        .values_list('product_item_id', flat=True).distinct()
    )
    
    if not seller_products:
        return {"error": "Seller has no product history", "results": []}
    
    current_buyers = set(
        Transaction.objects.filter(seller=seller_name)
        .values_list('buyer', flat=True).distinct()
    )
    
    candidate_buyers = list(
        Transaction.objects.filter(product_item_id__in=seller_products)
        .exclude(buyer__in=current_buyers)
        .values('buyer')
        .annotate(product_match_count=Count('product_item_id', distinct=True))
        .order_by('-product_match_count')[:top_k]
    )
    
    
    max_count = max([item['product_match_count'] for item in candidate_buyers], default=1)
    
    for item in candidate_buyers:
        count = item['product_match_count']
        normalized_score = count / max_count if max_count > 0 else 0
        results.append({
            "buyer": item['buyer'],
            "score": scale_confidence(normalized_score, max_val=1.0),  
            "method": "product_cotrade",
            "matching_products": count  
        })
    
    return {"results": results}





def predict_sellers_jaccard(buyer_name, top_k=10):
    """
    Jaccard similarity based on shared seller connections.
    J(A,B) = |A ∩ B| / |A ∪ B|
    """
    results = []
    
    G = load_buyer_seller_graph()
    
    if buyer_name not in G:
        return {"error": "Buyer not in graph", "results": []}
    
    buyer_neighbors = set(G.neighbors(buyer_name))
    all_sellers = [n for n in G.nodes() if G.nodes[n].get('type') == 'seller']
    
    for seller in all_sellers:
        if seller in buyer_neighbors:
            continue  
        
        seller_neighbors = set(G.neighbors(seller))
        
        intersection = len(buyer_neighbors & seller_neighbors)
        union = len(buyer_neighbors | seller_neighbors)
        
        if union > 0:
            jaccard = intersection / union
            if jaccard > 0:
                results.append({
                    "seller": seller,
                    "raw_score": float(jaccard),
                    "method": "jaccard",
                    "common_connections": intersection
                })
    
    results.sort(key=lambda x: x['raw_score'], reverse=True)
    top_results = results[:top_k]
    
    
    for r in top_results:
        r['score'] = scale_confidence(r['raw_score'], max_val=1.0)
        del r['raw_score']
    
    return {"results": top_results}





def predict_sellers_preferential_attachment(buyer_name, top_k=10):
    """
    Preferential Attachment: Score = degree(buyer) * degree(seller)
    Popular nodes are more likely to form new connections.
    
    Returns normalized scores (0-1 range) using log normalization.
    """
    import math
    raw_results = []
    
    G = load_buyer_seller_graph()
    
    if buyer_name not in G:
        return {"error": "Buyer not in graph", "results": []}
    
    buyer_degree = G.degree(buyer_name)
    buyer_neighbors = set(G.neighbors(buyer_name))
    all_sellers = [n for n in G.nodes() if G.nodes[n].get('type') == 'seller']
    
    for seller in all_sellers:
        if seller in buyer_neighbors:
            continue
        
        seller_degree = G.degree(seller)
        pa_score = buyer_degree * seller_degree
        
        raw_results.append({
            "seller": seller,
            "raw_score": pa_score,
            "seller_connections": seller_degree
        })
    
    
    raw_results.sort(key=lambda x: x['raw_score'], reverse=True)
    top_results = raw_results[:top_k]
    
    
    if top_results:
        max_score = max(r['raw_score'] for r in top_results)
        log_max = math.log1p(max_score)  
        
        results = []
        for r in top_results:
            
            normalized = math.log1p(r['raw_score']) / log_max if log_max > 0 else 0
            results.append({
                "seller": r['seller'],
                "score": scale_confidence(normalized, max_val=1.0),  
                "method": "preferential_attachment",
                "seller_connections": r['seller_connections']
            })
        return {"results": results}
    
    return {"results": []}







METHOD_WEIGHTS = {
    'node2vec': 0.30,           
    'common_neighbors': 0.20,   
    'product_cotrade': 0.25,    
    'jaccard': 0.15,            
    'preferential_attachment': 0.10  
}


def predict_sellers_combined(buyer_name, top_k=10):
    """
    Combine all methods using weighted averaging.
    
    Returns:
        - final_confidence: Weighted average of all methods (0-1)
        - scores: Individual method scores (all 0-1)
        - rank: Position in results (1st, 2nd, etc.)
    """
    all_results = {}
    
    
    node2vec_results = predict_sellers_node2vec(buyer_name, top_k=50)
    for r in node2vec_results.get('results', []):
        seller = r['seller']
        if seller not in all_results:
            all_results[seller] = {
                'seller': seller, 
                'scores': {}, 
                'weighted_sum': 0,
                'weight_sum': 0,
                'segment_tag': r.get('segment_tag')
            }
        score = min(1.0, max(0.0, r['score']))  
        all_results[seller]['scores']['node2vec'] = score
        all_results[seller]['weighted_sum'] += score * METHOD_WEIGHTS['node2vec']
        all_results[seller]['weight_sum'] += METHOD_WEIGHTS['node2vec']
    
    
    cn_results = predict_sellers_common_neighbors(buyer_name, top_k=50)
    for r in cn_results.get('results', []):
        seller = r['seller']
        if seller not in all_results:
            all_results[seller] = {
                'seller': seller, 
                'scores': {}, 
                'weighted_sum': 0,
                'weight_sum': 0
            }
        score = min(1.0, max(0.0, r['score']))
        all_results[seller]['scores']['common_neighbors'] = score
        all_results[seller]['weighted_sum'] += score * METHOD_WEIGHTS['common_neighbors']
        all_results[seller]['weight_sum'] += METHOD_WEIGHTS['common_neighbors']
    
    
    product_results = predict_sellers_by_product(buyer_name, top_k=50)
    for r in product_results.get('results', []):
        seller = r['seller']
        if seller not in all_results:
            all_results[seller] = {
                'seller': seller, 
                'scores': {}, 
                'weighted_sum': 0,
                'weight_sum': 0
            }
        score = min(1.0, max(0.0, r['score']))
        all_results[seller]['scores']['product_cotrade'] = score
        all_results[seller]['weighted_sum'] += score * METHOD_WEIGHTS['product_cotrade']
        all_results[seller]['weight_sum'] += METHOD_WEIGHTS['product_cotrade']
    
    
    jaccard_results = predict_sellers_jaccard(buyer_name, top_k=50)
    for r in jaccard_results.get('results', []):
        seller = r['seller']
        if seller not in all_results:
            all_results[seller] = {
                'seller': seller, 
                'scores': {}, 
                'weighted_sum': 0,
                'weight_sum': 0
            }
        score = min(1.0, max(0.0, r['score']))
        all_results[seller]['scores']['jaccard'] = score
        all_results[seller]['weighted_sum'] += score * METHOD_WEIGHTS['jaccard']
        all_results[seller]['weight_sum'] += METHOD_WEIGHTS['jaccard']
    
    
    pa_results = predict_sellers_preferential_attachment(buyer_name, top_k=50)
    for r in pa_results.get('results', []):
        seller = r['seller']
        if seller not in all_results:
            all_results[seller] = {
                'seller': seller, 
                'scores': {}, 
                'weighted_sum': 0,
                'weight_sum': 0
            }
        score = min(1.0, max(0.0, r['score']))
        all_results[seller]['scores']['preferential_attachment'] = score
        all_results[seller]['weighted_sum'] += score * METHOD_WEIGHTS['preferential_attachment']
        all_results[seller]['weight_sum'] += METHOD_WEIGHTS['preferential_attachment']
    
    
    
    MAX_CONFIDENCE = 0.95
    TOTAL_METHODS = 5  
    
    for seller_data in all_results.values():
        if seller_data['weight_sum'] > 0:
            
            base_confidence = seller_data['weighted_sum'] / seller_data['weight_sum']
            
            
            methods_used = len(seller_data['scores'])
            coverage_factor = methods_used / TOTAL_METHODS  
            
            
            seller_data['final_confidence'] = min(
                MAX_CONFIDENCE, 
                base_confidence * (0.7 + 0.3 * coverage_factor)  
            )
        else:
            seller_data['final_confidence'] = 0.0
        
        
        seller_data['total_score'] = seller_data['final_confidence']
    
    
    sorted_results = sorted(all_results.values(), key=lambda x: x['final_confidence'], reverse=True)[:top_k]
    
    
    for idx, result in enumerate(sorted_results):
        result['rank'] = idx + 1
        
        del result['weighted_sum']
        del result['weight_sum']
    
    return {
        "buyer": buyer_name,
        "method": "combined",
        "results": sorted_results
    }


def predict_buyers_combined(seller_name, top_k=10):
    """
    Combine all methods for buyer prediction using weighted averaging.
    
    Returns:
        - final_confidence: Weighted average of all methods (0-0.95 max)
        - scores: Individual method scores (all 0-1)
        - rank: Position in results (1st, 2nd, etc.)
    """
    all_results = {}
    
    
    node2vec_results = predict_buyers_node2vec(seller_name, top_k=50)
    for r in node2vec_results.get('results', []):
        buyer = r['buyer']
        if buyer not in all_results:
            all_results[buyer] = {
                'buyer': buyer, 
                'scores': {}, 
                'weighted_sum': 0,
                'weight_sum': 0,
                'segment_tag': r.get('segment_tag')
            }
        score = min(1.0, max(0.0, r['score']))
        all_results[buyer]['scores']['node2vec'] = score
        all_results[buyer]['weighted_sum'] += score * METHOD_WEIGHTS['node2vec']
        all_results[buyer]['weight_sum'] += METHOD_WEIGHTS['node2vec']
    
    
    cn_results = predict_buyers_common_neighbors(seller_name, top_k=50)
    for r in cn_results.get('results', []):
        buyer = r['buyer']
        if buyer not in all_results:
            all_results[buyer] = {
                'buyer': buyer, 
                'scores': {}, 
                'weighted_sum': 0,
                'weight_sum': 0
            }
        score = min(1.0, max(0.0, r['score']))
        all_results[buyer]['scores']['common_neighbors'] = score
        all_results[buyer]['weighted_sum'] += score * METHOD_WEIGHTS['common_neighbors']
        all_results[buyer]['weight_sum'] += METHOD_WEIGHTS['common_neighbors']
    
    
    product_results = predict_buyers_by_product(seller_name, top_k=50)
    for r in product_results.get('results', []):
        buyer = r['buyer']
        if buyer not in all_results:
            all_results[buyer] = {
                'buyer': buyer, 
                'scores': {}, 
                'weighted_sum': 0,
                'weight_sum': 0
            }
        score = min(1.0, max(0.0, r['score']))
        all_results[buyer]['scores']['product_cotrade'] = score
        all_results[buyer]['weighted_sum'] += score * METHOD_WEIGHTS['product_cotrade']
        all_results[buyer]['weight_sum'] += METHOD_WEIGHTS['product_cotrade']
    
    
    
    MAX_CONFIDENCE = 0.95
    TOTAL_METHODS = 3  
    
    for buyer_data in all_results.values():
        if buyer_data['weight_sum'] > 0:
            
            base_confidence = buyer_data['weighted_sum'] / buyer_data['weight_sum']
            
            
            methods_used = len(buyer_data['scores'])
            coverage_factor = methods_used / TOTAL_METHODS  
            
            
            buyer_data['final_confidence'] = min(
                MAX_CONFIDENCE, 
                base_confidence * (0.7 + 0.3 * coverage_factor)  
            )
        else:
            buyer_data['final_confidence'] = 0.0
        
        
        buyer_data['total_score'] = buyer_data['final_confidence']
    
    
    sorted_results = sorted(all_results.values(), key=lambda x: x['final_confidence'], reverse=True)[:top_k]
    
    
    for idx, result in enumerate(sorted_results):
        result['rank'] = idx + 1
        
        del result['weighted_sum']
        del result['weight_sum']
    
    return {
        "seller": seller_name,
        "method": "combined",
        "results": sorted_results
    }
