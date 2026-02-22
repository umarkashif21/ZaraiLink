from django.db.models import Sum, Avg, Count, Q, F
from django.db.models.functions import TruncMonth
from datetime import date, timedelta
from trade_data.models import Transaction
from collections import defaultdict


def get_mom_growth_for_company(company_name, direction='import', date_to=None):
    """
    Computes Month-over-Month growth in volume (%).
    Compares the last full month vs the prior full month.
    """
    if date_to is None:
        date_to = date.today()

    last_month_end = date_to.replace(day=1) - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    prior_month_end = last_month_start - timedelta(days=1)
    prior_month_start = prior_month_end.replace(day=1)

    base_qs = Transaction.objects.all()
    if direction == 'import':
        base_qs = base_qs.filter(buyer=company_name)
    else:
        base_qs = base_qs.filter(seller=company_name)

    last_vol = base_qs.filter(
        reporting_date__range=[last_month_start, last_month_end]
    ).aggregate(v=Sum('qty_mt'))['v'] or 0

    prior_vol = base_qs.filter(
        reporting_date__range=[prior_month_start, prior_month_end]
    ).aggregate(v=Sum('qty_mt'))['v'] or 0

    if prior_vol == 0:
        return None
    return round(((last_vol - prior_vol) / prior_vol) * 100, 2)



def _classify_company(company_name):
    """
    Determine company type by checking which trade records it appears in.
    Returns: 'Pakistani Importer', 'Pakistani Exporter', 'Pakistani Trader', 
             'Foreign Seller', 'Foreign Buyer', or 'Unknown'
    """
    as_buyer_import  = Transaction.objects.filter(buyer=company_name,  trade_type='IMPORT').exists()
    as_seller_export = Transaction.objects.filter(seller=company_name, trade_type='EXPORT').exists()
    as_seller_import = Transaction.objects.filter(seller=company_name, trade_type='IMPORT').exists()
    as_buyer_export  = Transaction.objects.filter(buyer=company_name,  trade_type='EXPORT').exists()

    is_pk = as_buyer_import or as_seller_export
    is_foreign = as_seller_import or as_buyer_export

    if is_pk and is_foreign:
        return 'Pakistani Trader'
    if as_buyer_import and as_seller_export:
        return 'Pakistani Trader'
    if as_buyer_import:
        return 'Pakistani Importer'
    if as_seller_export:
        return 'Pakistani Exporter'
    if as_seller_import:
        return 'Foreign Seller'
    if as_buyer_export:
        return 'Foreign Buyer'
    return 'Unknown'


def get_company_overview_metrics(company_name, **filters):
    """
    compute full overview metrics for a company regardless of direction.
    Handles IMPORT and EXPORT transactions separately based on trade_type.
    """
    date_from = filters.get('date_from')
    date_to   = filters.get('date_to')
    product_category_id    = filters.get('product_category_id')
    product_subcategory_id = filters.get('product_subcategory_id')
    product_item_id        = filters.get('product_item_id')
    product_name           = filters.get('product_name')

    # All transactions involving this company
    qs = Transaction.objects.filter(Q(buyer=company_name) | Q(seller=company_name))

    if date_from:
        qs = qs.filter(reporting_date__gte=date_from)
    if date_to:
        qs = qs.filter(reporting_date__lte=date_to)
    if product_item_id:
        qs = qs.filter(product_item_id=product_item_id)
    elif product_subcategory_id:
        qs = qs.filter(product_item__sub_category_id=product_subcategory_id)
    elif product_category_id:
        qs = qs.filter(product_item__sub_category__category_id=product_category_id)
    if product_name:
        qs = qs.filter(product_item__sub_category__name__icontains=product_name)


    # ── Split by role ────────────────────────────────────────
    # Import: this company is the buyer in an IMPORT tx (goods coming INTO Pakistan)
    import_qs = qs.filter(buyer=company_name, trade_type='IMPORT')
    # Export: this company is the seller in an EXPORT tx (goods going OUT of Pakistan)
    export_qs = qs.filter(seller=company_name, trade_type='EXPORT')

    # Also handle: Foreign seller in IMPORT, Foreign buyer in EXPORT
    as_foreign_seller = qs.filter(seller=company_name, trade_type='IMPORT')
    as_foreign_buyer  = qs.filter(buyer=company_name,  trade_type='EXPORT')

    # Combine all roles for total aggregation
    all_qs = qs  # already filtered to buyer OR seller

    # ── Totals ───────────────────────────────────────────────
    def _agg(q):
        return q.aggregate(vol=Sum('qty_mt'), val=Sum('usd'))

    imp = _agg(import_qs)
    exp = _agg(export_qs)
    fs  = _agg(as_foreign_seller)
    fb  = _agg(as_foreign_buyer)

    import_volume  = float(imp['vol'] or 0)
    export_volume  = float(exp['vol'] or 0)
    import_revenue = float(imp['val'] or 0)
    export_revenue = float(exp['val'] or 0)

    # For foreign roles, add to totals
    import_volume  += float(fs['vol'] or 0)
    export_volume  += float(fb['vol'] or 0)
    import_revenue += float(fs['val'] or 0)
    export_revenue += float(fb['val'] or 0)

    total_volume  = import_volume + export_volume
    total_revenue = import_revenue + export_revenue

    # ── Company type ─────────────────────────────────────────
    company_type = _classify_company(company_name)

    # Determine the company's own country
    if 'Pakistani' in company_type:
        company_country = 'Pakistan'
    elif company_type == 'Foreign Seller':
        row = as_foreign_seller.values('origin_country').first()
        company_country = row['origin_country'] if row else 'Unknown'
    elif company_type == 'Foreign Buyer':
        row = as_foreign_buyer.values('destination_country').first()
        company_country = row['destination_country'] if row else 'Unknown'
    else:
        company_country = 'Unknown'

    # ── Active partners ───────────────────────────────────────
    buyer_partners  = set(import_qs.values_list('seller', flat=True)) | \
                      set(as_foreign_buyer.values_list('seller', flat=True))
    seller_partners = set(export_qs.values_list('buyer', flat=True)) | \
                      set(as_foreign_seller.values_list('buyer', flat=True))
    all_partners = buyer_partners | seller_partners
    active_partners = len(all_partners - {'', None})

    # ── Transaction counts ────────────────────────────────────
    total_transactions = qs.filter(
        Q(buyer=company_name) | Q(seller=company_name)
    ).distinct().count()

    # ── Top 5 products by volume ──────────────────────────────
    prod_qs = (
        all_qs.filter(product_item__sub_category__isnull=False)
        .values(product=F('product_item__sub_category__name'))
        .annotate(volume=Sum('qty_mt'))
        .order_by('-volume')[:5]
    )
    vol_denom = total_volume or 1.0
    top_products = [
        {
            'product': p['product'],
            'volume':  float(p['volume'] or 0),
            'percent': round((float(p['volume'] or 0) / vol_denom) * 100, 1),
        }
        for p in prod_qs
    ]

    # ── Top 5 partners by volume ──────────────────────────────
    # Collect (partner_name, volume) from all roles
    partner_vols = defaultdict(float)
    for row in import_qs.values('seller').annotate(v=Sum('qty_mt')):
        if row['seller']:
            partner_vols[row['seller']] += float(row['v'] or 0)
    for row in export_qs.values('buyer').annotate(v=Sum('qty_mt')):
        if row['buyer']:
            partner_vols[row['buyer']] += float(row['v'] or 0)
    for row in as_foreign_seller.values('buyer').annotate(v=Sum('qty_mt')):
        if row['buyer']:
            partner_vols[row['buyer']] += float(row['v'] or 0)
    for row in as_foreign_buyer.values('seller').annotate(v=Sum('qty_mt')):
        if row['seller']:
            partner_vols[row['seller']] += float(row['v'] or 0)

    sorted_partners = sorted(partner_vols.items(), key=lambda x: -x[1])[:5]
    top_partners = [
        {
            'partner': name,
            'volume':  vol,
            'percent': round((vol / vol_denom) * 100, 1),
        }
        for name, vol in sorted_partners
    ]

    # ── Product mix (top 5 + Other) ───────────────────────────
    product_mix = list(top_products)
    if top_products:
        covered_pct = sum(p['percent'] for p in top_products)
        other_pct = max(0, round(100 - covered_pct, 1))
        if other_pct > 0:
            product_mix.append({'product': 'Other', 'volume': 0, 'percent': other_pct})

    # ── Partner geography ─────────────────────────────────────
    # For Pakistani Importer: partners are foreign sellers → origin_country
    # For Pakistani Exporter: partners are foreign buyers → destination_country
    # For Foreign Seller/Buyer: opposite
    geo = []
    if 'Importer' in company_type or company_type == 'Pakistani Trader':
        for row in (import_qs.values('origin_country')
                    .annotate(volume=Sum('qty_mt'), value=Sum('usd'))
                    .order_by('-volume')[:10]):
            geo.append({
                'country':    row['origin_country'] or 'Unknown',
                'volume':     float(row['volume'] or 0),
                'value':      float(row['value'] or 0),
                'trade_type': 'import',
            })
    if 'Exporter' in company_type or company_type == 'Pakistani Trader':
        for row in (export_qs.values('destination_country')
                    .annotate(volume=Sum('qty_mt'), value=Sum('usd'))
                    .order_by('-volume')[:10]):
            geo.append({
                'country':    row['destination_country'] or 'Unknown',
                'volume':     float(row['volume'] or 0),
                'value':      float(row['value'] or 0),
                'trade_type': 'export',
            })
    if company_type == 'Foreign Seller':
        for row in (as_foreign_seller.values('destination_country')
                    .annotate(volume=Sum('qty_mt'), value=Sum('usd'))
                    .order_by('-volume')[:10]):
            geo.append({
                'country':    row['destination_country'] or 'Unknown',
                'volume':     float(row['volume'] or 0),
                'value':      float(row['value'] or 0),
                'trade_type': 'export',
            })
    if company_type == 'Foreign Buyer':
        for row in (as_foreign_buyer.values('origin_country')
                    .annotate(volume=Sum('qty_mt'), value=Sum('usd'))
                    .order_by('-volume')[:10]):
            geo.append({
                'country':    row['origin_country'] or 'Unknown',
                'volume':     float(row['volume'] or 0),
                'value':      float(row['value'] or 0),
                'trade_type': 'import',
            })

    # Sort geo by volume descending and deduplicate country entries
    seen_geo = {}
    for g in sorted(geo, key=lambda x: -x['volume']):
        key = (g['country'], g['trade_type'])
        if key not in seen_geo:
            seen_geo[key] = g
    partner_geography = list(seen_geo.values())[:10]

    # ── Monthly volume trend ──────────────────────────────────
    monthly_qs = (
        all_qs
        .annotate(month=TruncMonth('reporting_date'))
        .values('month')
        .annotate(volume=Sum('qty_mt'), value=Sum('usd'))
        .order_by('month')
    )
    volume_trend = [
        {
            'month': row['month'].strftime('%Y-%m') if row['month'] else None,
            'volume': float(row['volume'] or 0),
            'value':  float(row['value']  or 0),
        }
        for row in monthly_qs if row['month']
    ]

    return {
        'key_metrics': {
            'total_volume':    total_volume,
            'import_volume':   import_volume,
            'export_volume':   export_volume,
            'estimated_revenue': total_revenue,
            'import_revenue':  import_revenue,
            'export_revenue':  export_revenue,
            'top_products':    top_products,
            'top_partners':    top_partners,
        },
        'product_mix':        product_mix,
        'partner_geography':  partner_geography,
        'volume_trend':        volume_trend,
        # Legacy fields kept for other views
        'company_type':       company_type,
        'company_country':    company_country,
        'active_partners':    active_partners,
        'total_transactions': total_transactions,
        'total_volume_mt':    total_volume,
        'est_revenue_usd':    total_revenue,
        'top_products':       top_products,
    }