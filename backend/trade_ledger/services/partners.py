from django.db.models import Sum, Avg, Count, F
from trade_data.models import Transaction
from django.db.models.functions import TruncMonth, TruncQuarter
from .filters import apply_transaction_filters

def get_top_partners(company_name, direction='import', limit=10, **filters):
    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    counterparty = 'seller' if direction == 'import' else 'buyer'

    return (
        qs.values('country', partner=F(counterparty))
        .annotate(
            total_volume=Sum('qty_mt'),
            avg_price=Avg('usd_per_mt'),
        )
        .order_by('-total_volume')[:limit]
    )

def get_trade_volume_by_country(company_name, direction='import', **filters):
    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    return (
        qs.values('country')
        .annotate(total_volume=Sum('qty_mt'))
        .order_by('-total_volume')
    )

def get_partner_trends(company_name, direction='import', top_n=5, **filters):
    
    filters.pop('limit', None)
    top_partners = get_top_partners(company_name, direction, limit=top_n, **filters)
    partner_names = [p['partner'] for p in top_partners]
    if not partner_names:
        return []

    counterparty = 'seller' if direction == 'import' else 'buyer'

    qs = Transaction.objects.filter(**{f"{counterparty}__in": partner_names})
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    return (
    qs.annotate(month=TruncMonth('reporting_date'))
    .values('month')
    .annotate(
        partner=F(counterparty),
        vol=Sum('qty_mt')
    )
    .order_by('partner', 'month')
)

def get_product_mix_per_partner(company_name, partner_name, direction='import', **filters):
    qs = Transaction.objects.all()
    if direction == 'import':
        qs = qs.filter(buyer=company_name, seller=partner_name)
    else:
        qs = qs.filter(seller=company_name, buyer=partner_name)

    qs = apply_transaction_filters(qs, **filters)

    return (
        qs.filter(product_item__isnull=False)
        .values(product_name=F('product_item__name'))
        .annotate(vol=Sum('qty_mt'))
        .order_by('-vol')[:3]
    )