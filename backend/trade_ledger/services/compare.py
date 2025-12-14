# services/compare.py
from django.db.models import Sum, Avg, StdDev, F, FloatField, Count
from django.db.models.functions import Cast
from trade_data.models import Transaction
from .company import get_mom_growth_for_company
from .filters import apply_transaction_filters

def get_company_comparison_metrics(company_names, direction='import', **filters):
    results = {}
    for name in company_names:
        qs = Transaction.objects.all()
        qs = apply_transaction_filters(qs, direction=direction, company_name=name, **filters)

        total_volume = qs.aggregate(v=Sum('qty_mt'))['v'] or 0
        total_value = qs.aggregate(v=Sum('usd'))['v'] or 0
        active_partners = qs.aggregate(
            c=Count('seller' if direction == 'import' else 'buyer', distinct=True)
        )['c'] or 0

        mom_growth = get_mom_growth_for_company(name, direction, filters.get('date_to'))

        price_std = qs.aggregate(s=StdDev('usd_per_mt'))['s']

        top_country = (
            qs.values('country')
            .annotate(vol=Sum('qty_mt'))
            .order_by('-vol')
            .first()
        )

        total_vol = qs.aggregate(v=Sum('qty_mt'))['v'] or 1
        hhi = (
            qs.values('seller' if direction == 'import' else 'buyer')
            .annotate(vol=Sum('qty_mt'))
            .aggregate(
                hhi=Sum(
                    Cast(
                        (F('vol') / total_vol) * (F('vol') / total_vol),
                        FloatField()
                    )
                )
            )['hhi'] or 1
        )
        partner_diversity = 1 - hhi

        results[name] = {
            'est_revenue_usd': float(total_value),
            'total_volume_mt': float(total_volume),
            'active_partners': active_partners,
            'mom_growth_pct': mom_growth,
            'price_volatility': float(price_std) if price_std else 0,
            'top_source_country': top_country['country'] if top_country else None,
            'partner_diversity': float(partner_diversity),
        }
    return results


def get_dummy_comparison_data(company_names):
    """Generate realistic dummy data for comparison when no real data exists"""
    import random
    import datetime
    
    results = []
    for idx, name in enumerate(company_names):
        base_volume = random.randint(50000, 500000)
        base_revenue = base_volume * random.randint(800, 1500)
        
        results.append({
            'name': name,
            'trade_volume': base_volume,
            'estimated_revenue': base_revenue,
            'total_products': random.randint(5, 25),
            'total_partners': random.randint(10, 50),
            'partner_diversity_score': round(random.uniform(0.6, 0.9), 2),
            'active_since': (datetime.date.today() - datetime.timedelta(days=random.randint(365, 3650))).isoformat(),
            'pagerank': round(random.uniform(0.001, 0.05), 4),
            'network_degree': random.randint(5, 30)
        })
    
    return {'companies': results}