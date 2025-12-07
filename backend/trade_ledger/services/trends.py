# services/trends.py
from django.db import models
from django.db.models import Sum, Avg
from django.db.models.functions import TruncMonth, TruncQuarter
from trade_data.models import Transaction
from .filters import apply_transaction_filters


def get_volume_price_monthly(company_name, direction='import', **filters):
    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    return (
        qs.annotate(month=TruncMonth('reporting_date'))
        .values('month')
        .annotate(
            volume=Sum('qty_mt'),
            avg_price=Avg('usd_per_mt')
        )
        .order_by('month')
    )

def get_yoy_growth_by_quarter(company_name, direction='import', **filters):
    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    return (
        qs.annotate(quarter=TruncQuarter('reporting_date'))
        .values('quarter')
        .annotate(vol=Sum('qty_mt'))
        .order_by('quarter')
    )
