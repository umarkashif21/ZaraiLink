from django.db.models import Sum, Avg, Count, F, Case, When, CharField, FloatField, Q
from trade_data.models import Transaction
from django.db.models.functions import TruncMonth
from .filters import apply_transaction_filters
from datetime import date, timedelta

def get_yoy_growth_for_partner(company_name, partner_name, direction='import'):
    """
    Computes Year-over-Year growth for a specific partner (Trailing 12 Months vs Prior 12 Months).
    """
    end_date = date.today()
    start_date_t12 = end_date - timedelta(days=365)
    start_date_prior = start_date_t12 - timedelta(days=365)
    
    qs = Transaction.objects.all()
    counterparty_filter = {'seller': partner_name} if direction == 'import' else {'buyer': partner_name}
    qs = qs.filter(**counterparty_filter)
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name)
    
    vol_t12 = qs.filter(reporting_date__range=[start_date_t12, end_date]).aggregate(v=Sum('qty_mt'))['v'] or 0
    vol_prior = qs.filter(reporting_date__range=[start_date_prior, start_date_t12]).aggregate(v=Sum('qty_mt'))['v'] or 0
    
    if vol_prior == 0:
        return None
        
    return round(((vol_t12 - vol_prior) / vol_prior) * 100, 2)

def get_top_partners(company_name, direction='import', limit=10, **filters):
    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    counterparty_expr = Case(
        When(buyer=company_name, then=F('seller')),
        default=F('buyer'),
        output_field=CharField()
    )
    
    country_expr = Case(
        When(buyer=company_name, then=F('origin_country')),
        default=F('destination_country'),
        output_field=CharField()
    )

    results = (
        qs.values(partner=counterparty_expr, partner_country=country_expr)
        .annotate(
            total_volume=Sum('qty_mt'),
            total_value=Sum(F('qty_mt') * F('usd_per_mt'), output_field=FloatField()),
            avg_price=Sum(F('qty_mt') * F('usd_per_mt'), output_field=FloatField()) / Sum('qty_mt', output_field=FloatField()),
            shipment_count=Count('id'),
        )
        .order_by('-total_volume')[:limit]
    )
    
    enriched_results = []
    for r in results:
        r['yoy_growth'] = get_yoy_growth_for_partner(company_name, r['partner'], direction)
        enriched_results.append(r)
        
    return enriched_results

def get_trade_volume_by_country(company_name, direction='import', **filters):
    qs = Transaction.objects.all()
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)
    
    country_expr = Case(
        When(buyer=company_name, then=F('origin_country')),
        default=F('destination_country'),
        output_field=CharField()
    )

    return (
        qs.values(country=country_expr)
        .annotate(total_volume=Sum('qty_mt'))
        .order_by('-total_volume')
    )

def get_partner_trends(company_name, direction='import', top_n=5, **filters):
    top_partners = get_top_partners(company_name, direction, limit=top_n, **filters)
    partner_names = [p['partner'] for p in top_partners]
    if not partner_names:
        return []

    counterparty_expr = Case(
        When(buyer=company_name, then=F('seller')),
        default=F('buyer'),
        output_field=CharField()
    )

    qs = Transaction.objects.annotate(partner=counterparty_expr).filter(partner__in=partner_names)
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    return (
        qs.annotate(month=TruncMonth('reporting_date'))
        .values('partner', 'month')
        .annotate(
            volume=Sum('qty_mt'),
            revenue=Sum(F('qty_mt') * F('usd_per_mt'), output_field=FloatField())
        )
        .order_by('partner', 'month')
    )

def get_product_mix_per_partner(company_name, direction='import', top_n_partners=5, **filters):
    top_partners = get_top_partners(company_name, direction, limit=top_n_partners, **filters)
    partner_names = [p['partner'] for p in top_partners]
    if not partner_names:
        return []

    counterparty_expr = Case(
        When(buyer=company_name, then=F('seller')),
        default=F('buyer'),
        output_field=CharField()
    )

    qs = Transaction.objects.annotate(partner=counterparty_expr).filter(partner__in=partner_names, product_item__isnull=False)
    qs = apply_transaction_filters(qs, direction=direction, company_name=company_name, **filters)

    mix = (
        qs.values('partner', product_name=F('product_item__name'))
        .annotate(
            volume=Sum('qty_mt'),
            revenue=Sum(F('qty_mt') * F('usd_per_mt'), output_field=FloatField())
        )
        .order_by('partner', '-volume')
    )
    
    partner_products = {}
    for row in mix:
        p = row['partner']
        if p not in partner_products:
            partner_products[p] = []
        if len(partner_products[p]) < 3:
            partner_products[p].append({
                'product_name': row['product_name'],
                'volume': row['volume'],
                'revenue': row['revenue']
            })
            
    res = []
    for partner, products in partner_products.items():
        res.append({
            'partner': partner,
            'top_products': products
        })
    return res