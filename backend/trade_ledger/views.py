# trade_ledger/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
import json
from .services.explorer import get_explorer_companies
from .services.company import get_company_overview_metrics
from .services.products import get_company_product_performance, get_avg_price_trend_monthly, get_volume_share
from .services.partners import get_top_partners, get_trade_volume_by_country, get_partner_trends, get_product_mix_per_partner
from .services.trends import get_volume_price_monthly, get_yoy_growth_by_quarter
from .services.compare import get_company_comparison_metrics
from trade_data.models import CompanyEmbedding, ProductEmbedding  # For GNN data

def _parse_date(date_str):
    if not date_str:
        return None
    from datetime import datetime
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return None


# ----------------------------
# EXPLORER (Enhanced with GNN Segment Tags)
# ----------------------------
@cache_page(60 * 15)  # Cache for 15 minutes
def explorer_api(request):
    direction = request.GET.get('direction', 'import')
    date_from = _parse_date(request.GET.get('date_from'))
    date_to = _parse_date(request.GET.get('date_to'))
    country = request.GET.get('country')
    product_category_id = request.GET.get('product_category_id')
    product_subcategory_id = request.GET.get('product_subcategory_id')
    product_item_id = request.GET.get('product_item_id')
    search_query = request.GET.get('search')
    limit = min(int(request.GET.get('limit', 100)), 1000)

    companies = get_explorer_companies(
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        country=country,
        product_category_id=product_category_id,
        product_subcategory_id=product_subcategory_id,
        product_item_id=product_item_id,
        search_query=search_query,
        limit=limit
    )

    # Add GNN segment tags
    company_names = [c['company'] for c in companies]
    embedding_map = {
        e.company_name: e.cluster_tag
        for e in CompanyEmbedding.objects.filter(company_name__in=company_names)
    }
    for c in companies:
        c['segment_tag'] = embedding_map.get(c['company'], "Other")

    return JsonResponse({"results": companies})


# ----------------------------
# COMPANY PROFILE - OVERVIEW (Enhanced with Network Influence)
# ----------------------------
@cache_page(60 * 60)  # Cache for 1 hour
def company_overview_api(request, company_name):
    direction = request.GET.get('direction', 'import')
    date_from = _parse_date(request.GET.get('date_from'))
    date_to = _parse_date(request.GET.get('date_to'))
    country = request.GET.get('country')
    product_category_id = request.GET.get('product_category_id')
    product_subcategory_id = request.GET.get('product_subcategory_id')
    product_item_id = request.GET.get('product_item_id')

    metrics = get_company_overview_metrics(
        company_name=company_name,
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        country=country,
        product_category_id=product_category_id,
        product_subcategory_id=product_subcategory_id,
        product_item_id=product_item_id
    )

    # Add GNN network influence
    try:
        emb = CompanyEmbedding.objects.get(company_name=company_name)
        metrics['network_influence'] = {
            'pagerank': float(emb.pagerank),
            'degree': emb.degree
        }
        metrics['reputation_tags'] = [emb.cluster_tag]
    except CompanyEmbedding.DoesNotExist:
        metrics['network_influence'] = {'pagerank': 0.0, 'degree': 0}
        metrics['reputation_tags'] = ["Other"]

    return JsonResponse(metrics)


# ----------------------------
# COMPANY PROFILE - PRODUCTS (Enhanced with Product Clusters)
# ----------------------------
@cache_page(60 * 60)  # Cache for 1 hour
def company_products_api(request, company_name):
    direction = request.GET.get('direction', 'import')
    date_from = _parse_date(request.GET.get('date_from'))
    date_to = _parse_date(request.GET.get('date_to'))
    country = request.GET.get('country')

    performance = list(get_company_product_performance(
        company_name=company_name,
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        country=country
    ))

    volume_share = list(get_volume_share(
        company_name=company_name,
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        country=country
    ))

    # Avg price trend for top product
    top_product = performance[0] if performance else None
    price_trend = []
    if top_product:
        try:
            from trade_data.models import ProductItem
            item = ProductItem.objects.get(name=top_product['product_name'])
            price_trend = list(get_avg_price_trend_monthly(
                company_name=company_name,
                product_item_id=item.id,
                direction=direction,
                date_from=date_from,
                date_to=date_to,
                country=country
            ))
        except:
            pass

    # Add product clusters
    product_clusters = list(
        ProductEmbedding.objects.values_list('cluster_tag', flat=True).distinct()
    )

    return JsonResponse({
        "product_performance": performance,
        "avg_price_trend": price_trend,
        "volume_share": volume_share,
        "product_clusters": product_clusters
    })


# ----------------------------
# COMPANY PROFILE - PARTNERS
# ----------------------------
@cache_page(60 * 60)  # Cache for 1 hour
def company_partners_api(request, company_name):
    direction = request.GET.get('direction', 'import')
    date_from = _parse_date(request.GET.get('date_from'))
    date_to = _parse_date(request.GET.get('date_to'))
    country = request.GET.get('country')

    top_partners = list(get_top_partners(
        company_name=company_name,
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        country=country,
        limit=10
    ))

    trade_by_country = list(get_trade_volume_by_country(
        company_name=company_name,
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        country=country
    ))

    partner_trends = list(get_partner_trends(
        company_name=company_name,
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        country=country,
        limit=5
    ))

    product_mix = {}
    for partner in top_partners[:3]:
        partner_name = partner['partner']
        mix = list(get_product_mix_per_partner(
            company_name=company_name,
            partner_name=partner_name,
            direction=direction,
            date_from=date_from,
            date_to=date_to,
            country=country
        ))
        product_mix[partner_name] = mix

    return JsonResponse({
        "top_partners": top_partners,
        "trade_volume_by_country": trade_by_country,
        "partner_trends": partner_trends,
        "product_mix_per_partner": product_mix
    })


# ----------------------------
# COMPANY PROFILE - TRENDS
# ----------------------------
@cache_page(60 * 60)  # Cache for 1 hour
def company_trends_api(request, company_name):
    direction = request.GET.get('direction', 'import')
    date_from = _parse_date(request.GET.get('date_from'))
    date_to = _parse_date(request.GET.get('date_to'))
    country = request.GET.get('country')

    volume_price = list(get_volume_price_monthly(
        company_name=company_name,
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        country=country
    ))

    quarterly = list(get_yoy_growth_by_quarter(
        company_name=company_name,
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        country=country
    ))

    return JsonResponse({
        "volume_price_trend": volume_price,
        "quarterly_volume": quarterly
    })


# ----------------------------
# COMPARE COMPANIES
# ----------------------------
@csrf_exempt
@require_http_methods(["POST"])
def compare_companies_api(request):
    from .services.compare import get_company_comparison_metrics, get_dummy_comparison_data
    
    try:
        data = json.loads(request.body)
        company_names = data.get('companies', [])
        direction = data.get('direction', 'import')
        date_from = _parse_date(data.get('date_from'))
        date_to = _parse_date(data.get('date_to'))
        country = data.get('country')
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if len(company_names) < 2:
        return JsonResponse({"error": "Select at least 2 companies"}, status=400)

    # Use dummy data for testing (change to False when real data is available)
    use_dummy = True
    
    if use_dummy:
        result = get_dummy_comparison_data(company_names)
    else:
        metrics = get_company_comparison_metrics(
            company_names=company_names,
            direction=direction,
            date_from=date_from,
            date_to=date_to,
            country=country
        )
        result = metrics
    
    return JsonResponse(result)


# ============================
# GNN-SPECIFIC APIS
# ============================

# NOTE: @cache_page disabled - requires Redis. Re-enable when Redis is available.
# @cache_page(60 * 60 * 24)  # Cache for 24 hours
def similar_companies_api(request, company_name):
    """Explorer → Peer company recommendation"""
    try:
        emb = CompanyEmbedding.objects.get(company_name=company_name)
    except CompanyEmbedding.DoesNotExist:
        return JsonResponse({"similar_companies": []})

    from .services.gnn import get_similar_companies
    similar = get_similar_companies(company_name, top_k=4)
    return JsonResponse({"similar_companies": similar})


# NOTE: @cache_page disabled - requires Redis
# @cache_page(60 * 60 * 24)  # Cache for 24 hours
def potential_partners_api(request, company_name):
    """Overview → Link prediction (same as similar companies)"""
    return similar_companies_api(request, company_name)


# NOTE: @cache_page disabled - requires Redis
# @cache_page(60 * 60 * 24)  # Cache for 24 hours
def network_influence_api(request, company_name):
    """Overview → Centrality metrics"""
    try:
        emb = CompanyEmbedding.objects.get(company_name=company_name)
        return JsonResponse({
            "pagerank": float(emb.pagerank),
            "degree": emb.degree
        })
    except CompanyEmbedding.DoesNotExist:
        return JsonResponse({"pagerank": 0.0, "degree": 0})


@cache_page(60 * 60 * 24)  # Cache for 24 hours
def product_clusters_api(request):
    """Products → Latent category cards"""
    clusters = list(
        ProductEmbedding.objects.values_list('cluster_tag', flat=True).distinct()
    )
    return JsonResponse({"clusters": clusters})


# ----------------------------
# LINK PREDICTION APIs
# ----------------------------
def predict_sellers_api(request, buyer_name):
    """
    Predict potential sellers for a buyer.
    Query params:
        - method: node2vec, common_neighbors, product, jaccard, preferential, combined (default)
        - top_k: number of results (default 10)
    """
    from .services.link_prediction import (
        predict_sellers_node2vec,
        predict_sellers_common_neighbors,
        predict_sellers_by_product,
        predict_sellers_jaccard,
        predict_sellers_preferential_attachment,
        predict_sellers_combined
    )
    
    method = request.GET.get('method', 'combined')
    top_k = int(request.GET.get('top_k', 10))
    
    if method == 'node2vec':
        result = predict_sellers_node2vec(buyer_name, top_k)
    elif method == 'common_neighbors':
        result = predict_sellers_common_neighbors(buyer_name, top_k)
    elif method == 'product':
        result = predict_sellers_by_product(buyer_name, top_k)
    elif method == 'jaccard':
        result = predict_sellers_jaccard(buyer_name, top_k)
    elif method == 'preferential':
        result = predict_sellers_preferential_attachment(buyer_name, top_k)
    else:  # combined
        result = predict_sellers_combined(buyer_name, top_k)
    
    return JsonResponse(result)


def predict_buyers_api(request, seller_name):
    """
    Predict potential buyers for a seller.
    Query params:
        - method: node2vec, common_neighbors, product, combined (default)
        - top_k: number of results (default 10)
    """
    from .services.link_prediction import (
        predict_buyers_node2vec,
        predict_buyers_common_neighbors,
        predict_buyers_by_product,
        predict_buyers_combined
    )
    
    method = request.GET.get('method', 'combined')
    top_k = int(request.GET.get('top_k', 10))
    
    if method == 'node2vec':
        result = predict_buyers_node2vec(seller_name, top_k)
    elif method == 'common_neighbors':
        result = predict_buyers_common_neighbors(seller_name, top_k)
    elif method == 'product':
        result = predict_buyers_by_product(seller_name, top_k)
    else:  # combined
        result = predict_buyers_combined(seller_name, top_k)
    
    return JsonResponse(result)


def link_prediction_methods_api(request):
    """Return available link prediction methods and their descriptions."""
    methods = [
        {
            "id": "node2vec",
            "name": "Node2Vec Similarity",
            "description": "Uses graph neural network embeddings to find similar trading patterns"
        },
        {
            "id": "common_neighbors",
            "name": "Common Neighbors",
            "description": "Finds sellers/buyers that share connections with similar companies"
        },
        {
            "id": "product",
            "name": "Product Co-Trade",
            "description": "Matches based on product category overlap"
        },
        {
            "id": "jaccard",
            "name": "Jaccard Coefficient",
            "description": "Normalized similarity measure based on shared connections"
        },
        {
            "id": "preferential",
            "name": "Preferential Attachment",
            "description": "Recommends popular/well-connected trading partners"
        },
        {
            "id": "combined",
            "name": "Combined (All Methods)",
            "description": "Aggregates scores from all methods for best results"
        }
    ]
    return JsonResponse({"methods": methods})