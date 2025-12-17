import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from trade_data.models import CompanyEmbedding, ProductEmbedding

def get_company_embedding(company_name):
    """Get embedding vector for a company. Uses fuzzy matching if exact match fails."""
    
    try:
        emb = CompanyEmbedding.objects.get(company_name=company_name)
        return np.array(emb.embedding), company_name
    except CompanyEmbedding.DoesNotExist:
        pass
    
    
    try:
        emb = CompanyEmbedding.objects.get(company_name__iexact=company_name)
        return np.array(emb.embedding), emb.company_name
    except CompanyEmbedding.DoesNotExist:
        pass
    
    
    query_lower = company_name.lower()
    all_embeddings = CompanyEmbedding.objects.all()
    
    for emb in all_embeddings:
        emb_name_lower = emb.company_name.lower()
        
        if query_lower in emb_name_lower or emb_name_lower in query_lower:
            return np.array(emb.embedding), emb.company_name
        
        query_words = query_lower.split()
        emb_words = emb_name_lower.split()
        if query_words and emb_words and query_words[0] == emb_words[0]:
            return np.array(emb.embedding), emb.company_name
    
    return None, None

def get_similar_companies(company_name, top_k=4):
    """Get top-k similar companies by cosine similarity."""
    target_vec, matched_name = get_company_embedding(company_name)
    if target_vec is None:
        return []
    
    target_dim = len(target_vec)
    
    
    all_embeddings = list(CompanyEmbedding.objects.exclude(company_name=matched_name))
    
    
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
    """Get centrality metrics for a company, including Combined Influence Score."""
    from django.db.models import Max
    
    try:
        emb = CompanyEmbedding.objects.get(company_name=company_name)
        
        
        stats = CompanyEmbedding.objects.aggregate(max_pr=Max('pagerank'), max_deg=Max('degree'))
        max_pr = stats['max_pr'] or 1.0
        max_deg = stats['max_deg'] or 1.0
        
        pagerank = float(emb.pagerank)
        degree = emb.degree
        
        
        
        norm_pr = pagerank / max_pr if max_pr > 0 else 0
        norm_deg = degree / max_deg if max_deg > 0 else 0
        
        combined_score = (0.5 * norm_pr + 0.5 * norm_deg) * 100
        
        return {
            "pagerank": pagerank,
            "degree": degree,
            "influence_percentile": None, 
            "combined_score": round(combined_score, 1)
        }
    except CompanyEmbedding.DoesNotExist:
        return {
            "pagerank": 0.0, 
            "degree": 0, 
            "influence_percentile": 0, 
            "combined_score": 0.0
        }