from django.db.models import Sum, Avg, Count, F
from datetime import date, timedelta
from trade_data.models import Transaction
from .filters import apply_transaction_filters


def get_mom_growth_for_company(company_name, direction='import', date_to=None):
    """
    Computes Month-over-Month growth in volume (%).
    Compares the last full month vs the prior full month.
    """
    if date_to is None:
        date_to = date.today()

    
    if date_to.day == 1:
        
        last_month_end = date_to.replace(day=1) - timedelta(days=1)
    else:
        last_month_end = date_to.replace(day=1) - timedelta(days=1)

    
    last_month_start = last_month_end.replace(day=1)

    
    prior_month_end = last_month_start - timedelta(days=1)
    prior_month_start = prior_month_end.replace(day=1)

    base_qs = Transaction.objects.all()
    if direction == 'import':
        base_qs = base_qs.filter(buyer=company_name)
    else:
        base_qs = base_qs.filter(seller=company_name)

    
    last_month_vol = base_qs.filter(
        reporting_date__range=[last_month_start, last_month_end]
    ).aggregate(v=Sum('qty_mt'))['v'] or 0

    
    prior_month_vol = base_qs.filter(
        reporting_date__range=[prior_month_start, prior_month_end]
    ).aggregate(v=Sum('qty_mt'))['v'] or 0

    if prior_month_vol == 0:
        return None 
    return round(((last_month_vol - prior_month_vol) / prior_month_vol) * 100, 2)

def get_company_overview_metrics(company_name, direction='import', **filters):
    from datetime import timedelta  

    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    total_volume = qs.aggregate(v=Sum('qty_mt'))['v'] or 0
    total_value = qs.aggregate(v=Sum('usd'))['v'] or (total_volume * (qs.aggregate(p=Avg('usd_per_mt'))['p'] or 0))
    active_partners = qs.aggregate(
        c=Count('seller' if direction == 'import' else 'buyer', distinct=True)
    )['c'] or 0

    mom_growth = get_mom_growth_for_company(company_name, direction, filters.get('date_to'))

    top_products = (
        qs.filter(product_item__isnull=False)
        .values(
            name=F('product_item__name'),
            subcat=F('product_item__sub_category__name'),
            cat=F('product_item__sub_category__category__name')
        )
        .annotate(vol=Sum('qty_mt'))
        .order_by('-vol')[:3]
    )
    
    
    top_products_list = []
    vol_denom = float(total_volume) if total_volume else 1.0
    
    for p in top_products:
        p_vol = float(p['vol'])
        p['share_pct'] = round((p_vol / vol_denom) * 100, 1)
        top_products_list.append(p)

    top_countries = (
        qs.values('country')
        .annotate(vol=Sum('qty_mt'))
        .order_by('-vol')[:3]
    )

    return {
        'est_revenue_usd': float(total_value),
        'total_volume_mt': float(total_volume),
        'active_partners': active_partners,
        'mom_growth_pct': mom_growth,
        'top_products': top_products_list,
        'top_countries': list(top_countries),
    }