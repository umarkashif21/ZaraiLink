# trade_ledger/services/gnn.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from trade_data.models import CompanyEmbedding, ProductEmbedding

def get_company_embedding(company_name):
    """Get embedding vector for a company."""
    try:
        emb = CompanyEmbedding.objects.get(company_name=company_name)
        return np.array(emb.embedding)
    except CompanyEmbedding.DoesNotExist:
        return None

def get_similar_companies(company_name, top_k=4):
    """Get top-k similar companies by cosine similarity."""
    target_vec = get_company_embedding(company_name)
    if target_vec is None:
        return []
    
    target_dim = len(target_vec)
    
    # Get all companies except target, filter for matching embedding dimensions
    all_embeddings = list(CompanyEmbedding.objects.exclude(company_name=company_name))
    
    # Filter to only embeddings with matching dimensions
    valid_companies = []
    names = []
    vectors = []
    
    for c in all_embeddings:
        if isinstance(c.embedding, list) and len(c.embedding) == target_dim:
            valid_companies.append(c)
            names.append(c.company_name)
            vectors.append(c.embedding)
    
    if not vectors:
        return []
    
    vectors = np.array(vectors)
    similarities = cosine_similarity([target_vec], vectors)[0]
    top_indices = np.argsort(similarities)[-top_k:][::-1]

    return [
        {
            "company_name": names[i],
            "similarity": float(similarities[i]),
            "segment_tag": valid_companies[i].cluster_tag,
            "total_volume_mt": None
        }
        for i in top_indices
    ]

def get_product_clusters():
    """Get unique product cluster tags."""
    return list(
        ProductEmbedding.objects.values_list('cluster_tag', flat=True).distinct()
    )

def get_network_influence(company_name):
    """Get centrality metrics for a company."""
    try:
        emb = CompanyEmbedding.objects.get(company_name=company_name)
        return {
            "pagerank": float(emb.pagerank),
            "degree": emb.degree,
            "influence_percentile": None  # Optional: compute from all companies
        }
    except CompanyEmbedding.DoesNotExist:
        return {"pagerank": 0.0, "degree": 0, "influence_percentile": 0}