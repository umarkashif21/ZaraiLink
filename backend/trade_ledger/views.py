from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
import json
from .services.explorer import get_explorer_companies
from .services.company import get_company_overview_metrics
from .services.products import get_company_product_performance, get_avg_price_trend_monthly, get_volume_share, get_co_traded_products, get_product_clusters
from .services.partners import get_top_partners, get_trade_volume_by_country, get_partner_trends, get_product_mix_per_partner
from .services.trends import get_volume_price_monthly, get_yoy_growth_by_quarter
from .services.compare import get_company_comparison_metrics
from trade_data.models import CompanyEmbedding, ProductEmbedding, Transaction  



def _parse_date(date_str):
    if not date_str:
        return None
    from datetime import datetime
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return None





def explorer_api(request):
    direction = request.GET.get('direction', 'import')
    date_from = _parse_date(request.GET.get('date_from'))
    date_to = _parse_date(request.GET.get('date_to'))
    country = request.GET.get('country')
    product_category_id = request.GET.get('product_category_id')
    product_subcategory_id = request.GET.get('product_subcategory_id')
    product_item_id = request.GET.get('product_item_id')
    search_query = request.GET.get('search')
    
    limit = min(int(request.GET.get('limit', 1000)), 5000)

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

    
    company_names = [c['company'] for c in companies]
    embedding_map = {
        e.company_name: e.cluster_tag
        for e in CompanyEmbedding.objects.filter(company_name__in=company_names)
    }
    for c in companies:
        c['segment_tag'] = embedding_map.get(c['company'], "Other")

    print(f"[explorer_api] direction={direction}, country={country}, companies_found={len(companies)}")
    return JsonResponse({"results": companies})





def company_overview_api(request, company_name):
    from .services.gnn import get_similar_companies
    from trade_data.models import Transaction
    from django.db.models import Sum
    
    direction = request.GET.get('direction', 'import')
    date_from = _parse_date(request.GET.get('date_from'))
    date_to = _parse_date(request.GET.get('date_to'))
    country = request.GET.get('country')
    product_category_id = request.GET.get('product_category_id')
    product_subcategory_id = request.GET.get('product_subcategory_id')
    product_item_id = request.GET.get('product_item_id')

    # Collect all filter parameters into a dictionary
    filters = {
        'direction': direction,
        'date_from': date_from,
        'date_to': date_to,
        'country': country,
        'product_category_id': product_category_id,
        'product_subcategory_id': product_subcategory_id,
        'product_item_id': product_item_id,
    }
    # Remove None values from filters
    filters = {k: v for k, v in filters.items() if v is not None}

    metrics = get_company_overview_metrics(
        company_name=company_name,
        **filters # Pass dynamic filters
    )

    
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
    
    
    try:
        similar_companies = get_similar_companies(company_name, top_k=4)
        
        metrics['similar_companies'] = similar_companies if isinstance(similar_companies, list) else []
    except Exception as e:
        print(f"Error getting similar companies: {e}")
        metrics['similar_companies'] = []
    
    # Legacy aliases for backward compatibility with other pages
    metrics['total_volume']   = metrics.get('total_volume_mt', 0)
    metrics['total_partners'] = metrics.get('active_partners', 0)
    metrics['products'] = [
        {
            'name': p.get('product'), 'product_name': p.get('product'),
            'vol': p.get('volume', 0), 'volume': p.get('volume', 0),
            'share_pct': p.get('percent', 0),
        }
        for p in metrics.get('top_products', [])
    ]
    metrics['total_products'] = len(metrics.get('top_products', []))
    metrics['country_distribution'] = [
        {'name': g.get('country'), 'volume': g.get('volume', 0), 'value': g.get('value', 0)}
        for g in metrics.get('partner_geography', [])
    ]

    return JsonResponse(metrics)






def company_products_api(request, company_name):
    from .services.products import (
        get_company_product_performance,
        get_avg_price_trend_monthly,
        get_product_partner_matrix,
        get_top_partner_per_product
    )
    direction = request.GET.get('direction', 'import')
    date_from = _parse_date(request.GET.get('date_from'))
    date_to = _parse_date(request.GET.get('date_to'))
    country = request.GET.get('country')
    product_name_filter = request.GET.get('product_name')

    filters = {}
    if date_from: filters['date_from'] = date_from
    if date_to: filters['date_to'] = date_to
    if country: filters['country'] = country
    # Note: apply_transaction_filters might not support product_item__name__icontains directly, 
    # but we can filter the performance list or handle it there. 
    # We will pass the product_name straight to the filter if the generic filter handles it, 
    # but since apply_transaction_filters doesn't handle product_name directly, we do it via QS.
    # Actually, apply_transaction_filters accepts kwargs? No, it only accepts specific named args.
    # WAIT! Looking at apply_transaction_filters, it does NOT accept **kwargs.
    
    # Let's import Transaction and apply the product filter explicitly before calling services if possible?
    # No, services instantiate qs inside. 
    # So we'll pass product_name as search query or just filter the results in python for product_name.
    # Since product list is small, python filter is fine for `product_name_filter`.

    performance = list(get_company_product_performance(
        company_name=company_name,
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        country=country
    ))

    if product_name_filter:
        performance = [p for p in performance if product_name_filter.lower() in p['product_name'].lower()]

    summary = {
        "total_products": len(performance),
        "total_volume": sum((p.get('total_volume') or 0) for p in performance),
        "total_value": sum((p.get('total_value') or 0) for p in performance),
    }

    # Fetch top 5 products trend (now at subcategory level)
    top_5_pids = [p['product_id'] for p in performance[:5]]
    trend_data = {}
    for pid in top_5_pids:
        pname = next(p['product_name'] for p in performance if p['product_id'] == pid)
        trend = list(get_avg_price_trend_monthly(
            company_name=company_name,
            sub_category_id=pid,
            direction=direction,
            date_from=date_from,
            date_to=date_to,
            country=country
        ))
        trend_data[pname] = trend

    matrix = get_product_partner_matrix(company_name, top_n_products=5, direction=direction, date_from=date_from, date_to=date_to, country=country)
    top_partners = get_top_partner_per_product(company_name, top_n_products=5, direction=direction, date_from=date_from, date_to=date_to, country=country)

    return JsonResponse({
        "summary": summary,
        "products": performance,
        "avg_price_trend": trend_data,
        "product_partner_matrix": matrix,
        "top_partner_per_product": top_partners
    })





def company_partners_api(request, company_name):
    from .services.partners import (
        get_top_partners,
        get_trade_volume_by_country,
        get_partner_trends,
        get_product_mix_per_partner
    )
    direction = request.GET.get('direction', 'import')
    date_from = _parse_date(request.GET.get('date_from'))
    date_to = _parse_date(request.GET.get('date_to'))
    country = request.GET.get('country')
    product_name_filter = request.GET.get('product_name')

    filters = {}
    if date_from: filters['date_from'] = date_from
    if date_to: filters['date_to'] = date_to
    if country: filters['country'] = country
    if product_name_filter: filters['product_name'] = product_name_filter

    top_partners = list(get_top_partners(
        company_name=company_name,
        direction=direction,
        limit=10,
        **filters
    ))

    trade_by_country = list(get_trade_volume_by_country(
        company_name=company_name,
        direction=direction,
        **filters
    ))

    partner_trends = list(get_partner_trends(
        company_name=company_name,
        direction=direction,
        top_n=5,
        **filters
    ))

    product_mix = list(get_product_mix_per_partner(
        company_name=company_name,
        direction=direction,
        top_n_partners=5,
        **filters
    ))
    
    summary = {
        "total_partners": len(top_partners),
        "total_volume": sum((p.get('total_volume') or 0) for p in top_partners),
        "total_value": sum((p.get('total_value') or 0) for p in top_partners),
    }

    return JsonResponse({
        "summary": summary,
        "top_partners": top_partners,
        "volume_by_country": trade_by_country,
        "monthly_partner_trends": partner_trends,
        "product_mix_per_partner": product_mix
    })






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





@csrf_exempt
@require_http_methods(["POST"])
def compare_companies_api(request):
    from .services.compare import get_company_comparison_metrics
    
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

    
    metrics = get_company_comparison_metrics(
        company_names=company_names,
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        country=country
    )
    
    
    companies_data = []
    for name, data in metrics.items():
        
        data_with_name = data.copy()
        data_with_name['name'] = name
        companies_data.append(data_with_name)
    
    result = {'companies': companies_data}

    return JsonResponse(result)








def similar_companies_api(request, company_name):
    """Explorer → Peer company recommendation (uses fuzzy matching for company names)"""
    from .services.gnn import get_similar_companies
    similar = get_similar_companies(company_name, top_k=4)
    return JsonResponse({"similar_companies": similar})




def potential_partners_api(request, company_name):
    """Overview → Link prediction (same as similar companies)"""
    return similar_companies_api(request, company_name)




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


@cache_page(60 * 60 * 24)  
def product_clusters_api(request):
    """Products → Latent category cards"""
    clusters = list(
        ProductEmbedding.objects.values_list('cluster_tag', flat=True).distinct()
    )
    return JsonResponse({"clusters": clusters})





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
    else:  
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
    else:  
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