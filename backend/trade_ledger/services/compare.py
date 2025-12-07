# services/compare.py
from django.db.models import Sum, Avg, StdDev, F, FloatField
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

        mom_growth = get_mom_growth_for_company(name, direction, filters.get('date_to'))  # ← UPDATED

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
            'mom_growth_pct': mom_growth,  # ← RENAMED KEY
            'price_volatility': float(price_std) if price_std else 0,
            'top_source_country': top_country['country'] if top_country else None,
            'partner_diversity': float(partner_diversity),
        }
    return results