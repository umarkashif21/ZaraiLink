from django.db import models
from django.db.models import Sum, Avg, F
from trade_data.models import Transaction, ProductEmbedding
from .filters import apply_transaction_filters
from datetime import date, timedelta
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def get_yoy_growth_for_product(company_name, product_item_id, direction='import'):
    """
    Computes Year-over-Year growth (Trailing 12 Months vs Prior 12 Months).
    """
    end_date = date.today()
    start_date_t12 = end_date - timedelta(days=365)
    start_date_prior = start_date_t12 - timedelta(days=365)
    
    qs = Transaction.objects.filter(product_item_id=product_item_id)
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name)
    
    
    vol_t12 = qs.filter(reporting_date__range=[start_date_t12, end_date]).aggregate(v=Sum('qty_mt'))['v'] or 0
    
    
    vol_prior = qs.filter(reporting_date__range=[start_date_prior, start_date_t12]).aggregate(v=Sum('qty_mt'))['v'] or 0
    
    if vol_prior == 0:
        return None
        
    return round(((vol_t12 - vol_prior) / vol_prior) * 100, 2)

def get_company_product_performance(company_name, direction='import', **filters):
    from django.db.models import Sum, F, Count, Case, When, CharField, Q, FloatField

    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    import_cond = Q(destination_country__icontains='Pakistan')
    export_cond = Q(origin_country__icontains='Pakistan')
    
    counterparty_expr = Case(
        When(buyer=company_name, then=F('seller')),
        default=F('buyer'),
        output_field=CharField()
    )

    from django.db.models.functions import Coalesce
    results = (
        qs.filter(product_item__sub_category__isnull=False)
        .values(
            product_id=F('product_item__sub_category_id'),
            product_name=Coalesce(F('product_item__sub_category__name'), models.Value('Unknown Product')),
            subcat=Coalesce(F('product_item__sub_category__category__name'), models.Value('Subcategory')),
        )
        .annotate(
            total_volume=Sum('qty_mt'),
            total_value=Sum(F('qty_mt') * F('usd_per_mt'), output_field=FloatField()),
            import_volume=Sum('qty_mt', filter=import_cond),
            export_volume=Sum('qty_mt', filter=export_cond),
            avg_price=Sum(F('qty_mt') * F('usd_per_mt'), output_field=FloatField()) / Sum('qty_mt', output_field=FloatField()),
            shipment_count=Count('id'),
            unique_partners=Count(counterparty_expr, distinct=True)
        )
        .order_by('-total_volume')
    )
    
    enriched_results = []
    for r in results:
        r['yoy_growth'] = get_yoy_growth_for_product(company_name, r['product_id'], direction)
        enriched_results.append(r)
        
    return enriched_results

def get_avg_price_trend_monthly(company_name, sub_category_id=None, direction='import', **filters):
    from django.db.models import Sum, F, FloatField
    qs = Transaction.objects.filter(product_item__sub_category__isnull=False)
    if sub_category_id:
        qs = qs.filter(product_item__sub_category_id=sub_category_id)
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    return (
        qs.annotate(month=models.functions.TruncMonth('reporting_date'))
        .values('month')
        .annotate(
            volume=Sum('qty_mt'),
            revenue=Sum(F('qty_mt') * F('usd_per_mt'), output_field=FloatField()),
            avg_price=Sum(F('qty_mt') * F('usd_per_mt'), output_field=FloatField()) / Sum('qty_mt', output_field=FloatField())
        )
        .order_by('month')
    )

def get_product_partner_matrix(company_name, top_n_products=5, direction='import', **filters):
    from django.db.models import Sum, F, FloatField, Case, When, CharField
    qs = Transaction.objects.filter(product_item__isnull=False)
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)
    
    counterparty_expr = Case(
        When(buyer=company_name, then=F('seller')),
        default=F('buyer'),
        output_field=CharField()
    )
    
    top_products = list(
        qs.values('product_item__sub_category_id')
        .annotate(vol=Sum('qty_mt'))
        .order_by('-vol')[:top_n_products]
    )
    top_pids = [p['product_item__sub_category_id'] for p in top_products]
    
    if not top_pids: return []
    
    from django.db.models.functions import Coalesce
    matrix = (
        qs.filter(product_item__sub_category_id__in=top_pids)
        .annotate(partner_name=counterparty_expr)
        .values('product_item__sub_category_id', 'partner_name')
        .annotate(
            product_item__name=Coalesce(F('product_item__sub_category__name'), models.Value('Unknown Product')),
            partner=F('partner_name'),
            volume=Sum('qty_mt'),
            revenue=Sum(F('qty_mt') * F('usd_per_mt'), output_field=FloatField())
        )
        .order_by('product_item__name', '-volume')
    )
    return list(matrix)

def get_top_partner_per_product(company_name, top_n_products=5, direction='import', **filters):
    matrix = get_product_partner_matrix(company_name, top_n_products=top_n_products, direction=direction, **filters)
    res = {}
    for row in matrix:
        pname = row['product_item__name']
        if pname not in res:
            res[pname] = row
    return list(res.values())

def get_volume_share(company_name, direction='import', **filters):
    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    from django.db.models import ExpressionWrapper, DecimalField
    from decimal import Decimal

    total_vol = qs.aggregate(v=Sum('qty_mt'))['v'] or Decimal('1.0')

    return (
        qs.filter(product_item__isnull=False)
        .values(product_name=F('product_item__name'))
        .annotate(
            volume=Sum('qty_mt'),
            share_pct=ExpressionWrapper(
                (Sum('qty_mt') / total_vol) * 100,
                output_field=models.DecimalField(max_digits=10, decimal_places=2)
            )
        )
        .order_by('-volume')
    )

def get_portfolio_similarity(company_name, top_k=4):
    """
    Computes company similarity based on product portfolio (weighted average of product embeddings).
    """
    
    
    target_txs = Transaction.objects.filter(
        models.Q(buyer=company_name) | models.Q(seller=company_name)
    ).values('product_item').annotate(vol=Sum('qty_mt')).filter(product_item__isnull=False)
    
    target_profile = {x['product_item']: float(x['vol']) for x in target_txs}
    if not target_profile:
        return []

    
    product_embeddings = {
        pe.product_item_id: np.array(pe.embedding) 
        for pe in ProductEmbedding.objects.all()
    }
    
    
    def compute_weighted_vector(profile_dict):
        total_weight = 0
        weighted_sum = None
        for pid, vol in profile_dict.items():
            if pid in product_embeddings:
                if weighted_sum is None:
                    weighted_sum = np.zeros_like(product_embeddings[pid])
                weighted_sum += product_embeddings[pid] * vol
                total_weight += vol
        
        if total_weight == 0 or weighted_sum is None:
            return None
        return weighted_sum / total_weight

    target_vector = compute_weighted_vector(target_profile)
    if target_vector is None:
        return []

    
    
    
    
    
    all_txs = Transaction.objects.exclude(
        models.Q(buyer=company_name) | models.Q(seller=company_name)
    ).values('buyer', 'seller', 'product_item').annotate(vol=Sum('qty_mt'))
    
    company_profiles = {}
    for tx in all_txs:
        
        
        
        
        
        
        b = tx['buyer']
        s = tx['seller']
        pid = tx['product_item']
        vol = float(tx['vol'])
        
        if pid not in product_embeddings:
            continue
            
        if b != 'Unknown':
            if b not in company_profiles: company_profiles[b] = {}
            company_profiles[b][pid] = company_profiles[b].get(pid, 0) + vol
            
        if s != 'Unknown':
            if s not in company_profiles: company_profiles[s] = {}
            company_profiles[s][pid] = company_profiles[s].get(pid, 0) + vol

    scores = []
    
    for other_company, profile in company_profiles.items():
        vec = compute_weighted_vector(profile)
        if vec is not None:
             sim = cosine_similarity([target_vector], [vec])[0][0]
             total_vol = sum(profile.values())
             scores.append({
                 'company': other_company,
                 'similarity': sim,
                 'total_volume': total_vol
             })
    
    
    scores.sort(key=lambda x: x['similarity'], reverse=True)
    return scores[:top_k]

def get_co_traded_products(product_item_id, top_k=5):
    """
    Finds products that are frequently traded alongside the target product.
    Logic: Companies that trade X also trade Y.
    """
    
    companies = set(
        Transaction.objects.filter(product_item_id=product_item_id)
        .values_list('buyer', flat=True)
    ) | set(
        Transaction.objects.filter(product_item_id=product_item_id)
        .values_list('seller', flat=True)
    )
    
    
    co_traded = (
        Transaction.objects.filter(
            models.Q(buyer__in=companies) | models.Q(seller__in=companies)
        )
        .exclude(product_item_id=product_item_id)
        .values(name=F('product_item__name'))
        .annotate(frequency=models.Count('id'))
        .order_by('-frequency')[:top_k]
    )
    
    return list(co_traded)

def get_product_clusters(company_name, direction='import'):
    """
    Returns the AI-generated cluster tags for the company's products.
    """
    
    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name)
    product_ids = qs.values_list('product_item_id', flat=True).distinct()
    
    
    clusters = (
        ProductEmbedding.objects.filter(product_item_id__in=product_ids)
        .values('cluster_tag')
        .annotate(count=models.Count('id'))
        .order_by('-count')
    )
    
    return list(clusters)