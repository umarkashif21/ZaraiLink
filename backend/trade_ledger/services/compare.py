from django.db.models import Sum, Avg, StdDev, F, FloatField, Count, Min
from django.db.models.functions import Cast
from trade_data.models import Transaction, CompanyEmbedding
from .company import get_mom_growth_for_company
from .filters import apply_transaction_filters

def get_company_comparison_metrics(company_names, direction='import', **filters):
    results = {}
    for name in company_names:
        qs = Transaction.objects.all()
        qs = apply_transaction_filters(qs, direction=direction, company_name=name, **filters)

        
        aggs = qs.aggregate(
            total_vol=Sum('qty_mt'),
            total_val=Sum('usd'),
            active_partners=Count('seller' if direction == 'import' else 'buyer', distinct=True),
            total_prods=Count('product_item', distinct=True),
            first_txn=Min('reporting_date')
        )
        
        total_volume = aggs['total_vol'] or 0
        total_value = aggs['total_val'] or 0
        active_partners = aggs['active_partners'] or 0
        total_products = aggs['total_prods'] or 0
        active_since = aggs['first_txn']

        mom_growth = get_mom_growth_for_company(name, direction, filters.get('date_to'))
        price_std = qs.aggregate(s=StdDev('usd_per_mt'))['s']

        
        total_vol_query = total_volume if total_volume > 0 else 1
        hhi = (
            qs.values('seller' if direction == 'import' else 'buyer')
            .annotate(vol=Sum('qty_mt'))
            .aggregate(
                hhi=Sum(
                    Cast(
                        (F('vol') / total_vol_query) * (F('vol') / total_vol_query),
                        FloatField()
                    )
                )
            )['hhi'] or 1.0
        )
        partner_diversity = 1.0 - hhi

        
        pagerank = 0.0
        degree = 0
        try:
            emb = CompanyEmbedding.objects.filter(company_name=name).first()
            if emb:
                pagerank = emb.pagerank
                degree = emb.degree
        except:
            pass

        results[name] = {
            'trade_volume': float(total_volume),
            'estimated_revenue': float(total_value),
            'total_partners': active_partners,
            'total_products': total_products,
            'partner_diversity_score': float(partner_diversity),
            'mom_growth_pct': mom_growth,
            'price_volatility': float(price_std) if price_std else 0,
            'active_since': active_since.isoformat() if active_since else None,
            'pagerank': float(pagerank),
            'network_degree': degree,
        }
            
    return results