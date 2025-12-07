# services/products.py
from django.db import models
from django.db.models import Sum, Avg, F
from trade_data.models import Transaction
from .filters import apply_transaction_filters

def get_company_product_performance(company_name, direction='import', **filters):
    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    return (
        qs.filter(product_item__isnull=False)
        .values(
            product_name=F('product_item__name'),
            subcat=F('product_item__sub_category__name'),
        )
        .annotate(
            total_volume=Sum('qty_mt'),
            avg_price=Avg('usd_per_mt'),
        )
        .order_by('-total_volume')
    )

def get_avg_price_trend_monthly(company_name, product_item_id, direction='import', **filters):
    qs = Transaction.objects.filter(product_item_id=product_item_id)
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    return (
        qs.annotate(month=models.TruncMonth('reporting_date'))
        .values('month')
        .annotate(avg_price=Avg('usd_per_mt'))
        .order_by('month')
    )

def get_volume_share(company_name, direction='import', **filters):
    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    total_vol = qs.aggregate(v=Sum('qty_mt'))['v'] or 1

    return (
        qs.filter(product_item__isnull=False)
        .values(product_name=F('product_item__name'))
        .annotate(
            vol=Sum('qty_mt'),
            share_pct=(Sum('qty_mt') / total_vol) * 100
        )
        .order_by('-vol')
    )