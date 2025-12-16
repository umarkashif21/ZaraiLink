# services/trends.py
from django.db import models
from django.db.models import Sum, Avg
from django.db.models.functions import TruncMonth, TruncQuarter
from trade_data.models import Transaction
from .filters import apply_transaction_filters
from datetime import date, timedelta

def get_volume_price_monthly(company_name, direction='import', **filters):
    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    data = list(
        qs.annotate(month=TruncMonth('reporting_date'))
        .values('month')
        .annotate(
            volume=Sum('qty_mt'),
            avg_price=Avg('usd_per_mt')
        )
        .order_by('month')
    )
    
    # Calculate YoY
    # Map (year, month) -> record
    lookup = {}
    for x in data:
        # x['month'] is date or datetime
        d = x['month']
        lookup[(d.year, d.month)] = x
        
    for x in data:
        d = x['month']
        prev_key = (d.year - 1, d.month)
        
        # Default fields
        x['product_name'] = 'All Products' # As requested
        x['yoy_volume_growth'] = None
        x['yoy_price_growth'] = None
        
        if prev_key in lookup:
            prev = lookup[prev_key]
            
            # Volume Growth
            cur_vol = float(x['volume'] or 0)
            prev_vol = float(prev['volume'] or 0)
            if prev_vol > 0:
                x['yoy_volume_growth'] = round(((cur_vol - prev_vol) / prev_vol) * 100, 2)
                
            # Price Growth
            cur_price = float(x['avg_price'] or 0)
            prev_price = float(prev['avg_price'] or 0)
            if prev_price > 0:
                x['yoy_price_growth'] = round(((cur_price - prev_price) / prev_price) * 100, 2)
                
    return data

def get_yoy_growth_by_quarter(company_name, direction='import', **filters):
    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    data = list(
        qs.annotate(quarter=TruncQuarter('reporting_date'))
        .values('quarter')
        .annotate(vol=Sum('qty_mt'))
        .order_by('quarter')
    )
    
    # Calculate YoY Quarter Growth
    lookup = {}
    for x in data:
        d = x['quarter']
        # TruncQuarter returns first day of quarter (Jan 1, Apr 1, Jul 1, Oct 1)
        lookup[(d.year, d.month)] = x
        
    for x in data:
        d = x['quarter']
        prev_key = (d.year - 1, d.month)
        
        x['yoy_growth'] = None
        # Add year/quarter explicitly for frontend
        x['year'] = d.year
        x['quarter'] = (d.month - 1) // 3 + 1
        
        if prev_key in lookup:
            prev = lookup[prev_key]
            cur_vol = float(x['vol'] or 0)
            prev_vol = float(prev['vol'] or 0)
            if prev_vol > 0:
                x['yoy_growth'] = round(((cur_vol - prev_vol) / prev_vol) * 100, 2)
                
    return data
