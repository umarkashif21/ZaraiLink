from django.db.models import Sum, Avg, Count, Q, F, Max, Min
from django.db.models.functions import ExtractYear
from trade_data.models import Transaction
from .filters import apply_transaction_filters
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

def get_explorer_companies(
    direction='import',
    date_from=None,
    date_to=None,
    country=None,
    product_category_id=None,
    product_subcategory_id=None,
    product_item_id=None,
    search_query=None,
    limit=100
):
    """
    Returns list of companies for Explorer page table.
    Direction determines company role: import → buyer, export → seller, both → all unique.

    Country classification:
      IMPORT tx: buyer=Pakistani (destination_country=Pakistan), seller=Foreign (origin_country=foreign)
      EXPORT tx: seller=Pakistani (origin_country=Pakistan), buyer=Foreign (destination_country=foreign)
    """
    base_qs = Transaction.objects.all()

    if date_from:
        base_qs = base_qs.filter(reporting_date__gte=date_from)
    if date_to:
        base_qs = base_qs.filter(reporting_date__lte=date_to)
    if country:
        base_qs = base_qs.filter(
            Q(origin_country__icontains=country) | Q(destination_country__icontains=country)
        )
    if product_item_id:
        base_qs = base_qs.filter(product_item_id=product_item_id)
    elif product_subcategory_id:
        base_qs = base_qs.filter(product_item__sub_category_id=product_subcategory_id)
    elif product_category_id:
        base_qs = base_qs.filter(product_item__sub_category__category_id=product_category_id)

    # ─────────────────────────────────────────────────────────
    # DIRECTION = BOTH  (used by Trade Ledger dashboard)
    # ─────────────────────────────────────────────────────────
    if direction == 'both':

        company_stats = defaultdict(lambda: {
            'import_volume': 0.0, 'export_volume': 0.0,
            'import_value': 0.0,  'export_value': 0.0,
            'transaction_count': 0, 'active_partners': set(),
            'first_trade': None, 'last_trade': None,
            'country': None,
            'roles': set(),   # e.g. {'Pakistani Buyer', 'Foreign Seller'}
        })

        fields = ('buyer', 'seller', 'qty_mt', 'usd',
                  'trade_type', 'origin_country', 'destination_country', 'reporting_date')

        for tx in base_qs.values(*fields):
            trade_type = tx['trade_type']        # 'IMPORT' or 'EXPORT'
            buyer  = (tx['buyer']  or '').strip()
            seller = (tx['seller'] or '').strip()
            qty    = float(tx['qty_mt'] or 0)
            val    = float(tx['usd']    or 0)
            orig   = tx['origin_country']  or 'Unknown'
            dest   = tx['destination_country'] or 'Unknown'
            date   = tx['reporting_date']

            if trade_type == 'IMPORT':
                # buyer is Pakistani (dest=Pakistan), seller is foreign (orig=foreign country)
                if buyer and buyer.lower() not in ('unknown', ''):
                    cs = company_stats[buyer]
                    cs['import_volume'] += qty
                    cs['import_value']  += val
                    cs['transaction_count'] += 1
                    cs['active_partners'].add(seller)
                    cs['roles'].add('Pakistani Buyer')
                    if cs['country'] is None:
                        cs['country'] = dest          # Pakistan
                    if cs['first_trade'] is None or date < cs['first_trade']:
                        cs['first_trade'] = date
                    if cs['last_trade'] is None or date > cs['last_trade']:
                        cs['last_trade'] = date

                if seller and seller.lower() not in ('unknown', ''):
                    cs = company_stats[seller]
                    cs['export_volume'] += qty        # they "exported" to Pakistan
                    cs['export_value']  += val
                    cs['transaction_count'] += 1
                    cs['active_partners'].add(buyer)
                    cs['roles'].add('Foreign Seller')
                    if cs['country'] is None:
                        cs['country'] = orig          # foreign country
                    if cs['first_trade'] is None or date < cs['first_trade']:
                        cs['first_trade'] = date
                    if cs['last_trade'] is None or date > cs['last_trade']:
                        cs['last_trade'] = date

            else:  # EXPORT
                # seller is Pakistani (orig=Pakistan), buyer is foreign (dest=foreign country)
                if seller and seller.lower() not in ('unknown', ''):
                    cs = company_stats[seller]
                    cs['export_volume'] += qty
                    cs['export_value']  += val
                    cs['transaction_count'] += 1
                    cs['active_partners'].add(buyer)
                    cs['roles'].add('Pakistani Seller')
                    if cs['country'] is None:
                        cs['country'] = orig          # Pakistan
                    if cs['first_trade'] is None or date < cs['first_trade']:
                        cs['first_trade'] = date
                    if cs['last_trade'] is None or date > cs['last_trade']:
                        cs['last_trade'] = date

                if buyer and buyer.lower() not in ('unknown', ''):
                    cs = company_stats[buyer]
                    cs['import_volume'] += qty        # they "imported" from Pakistan
                    cs['import_value']  += val
                    cs['transaction_count'] += 1
                    cs['active_partners'].add(seller)
                    cs['roles'].add('Foreign Buyer')
                    if cs['country'] is None:
                        cs['country'] = dest          # foreign country
                    if cs['first_trade'] is None or date < cs['first_trade']:
                        cs['first_trade'] = date
                    if cs['last_trade'] is None or date > cs['last_trade']:
                        cs['last_trade'] = date

        # Determine primary company_type
        def _primary_type(roles):
            if 'Pakistani Buyer' in roles and 'Pakistani Seller' in roles:
                return 'Pakistani Trader'
            if 'Pakistani Buyer' in roles:
                return 'Pakistani Buyer'
            if 'Pakistani Seller' in roles:
                return 'Pakistani Seller'
            if 'Foreign Buyer' in roles:
                return 'Foreign Buyer'
            if 'Foreign Seller' in roles:
                return 'Foreign Seller'
            return 'Unknown'

        companies = []
        for name, s in company_stats.items():
            total_volume = s['import_volume'] + s['export_volume']
            total_value  = s['import_value']  + s['export_value']
            companies.append({
                'company':          name,
                'country':          s['country'] or 'Unknown',
                'company_type':     _primary_type(s['roles']),
                'total_volume':     total_volume,
                'import_volume':    s['import_volume'],
                'export_volume':    s['export_volume'],
                'total_value':      total_value,
                'import_value':     s['import_value'],
                'export_value':     s['export_value'],
                'avg_price':        total_value / total_volume if total_volume > 0 else 0,
                'active_partners':  len(s['active_partners']),
                'transaction_count': s['transaction_count'],
                'first_trade':      s['first_trade'],
                'last_trade':       s['last_trade'],
                'top_products':     [],   # filled in bulk below
                'yoy_growth':       None,
            })

        logger.info(f"[explorer] direction=both: {len(companies)} unique companies from {base_qs.count()} txns")

        companies.sort(key=lambda x: x['total_volume'], reverse=True)
        if search_query:
            companies = [c for c in companies if search_query.lower() in c['company'].lower()]
        companies = companies[:limit]

        # ── Bulk top-products lookup (3 queries total, no N+1) ─────────
        company_names = [c['company'] for c in companies]

        product_data = (
            base_qs.filter(Q(buyer__in=company_names) | Q(seller__in=company_names))
            .filter(product_item__isnull=False)
            .values('buyer', 'seller', product_name=F('product_item__name'))
            .annotate(vol=Sum('qty_mt'))
            .order_by('-vol')
        )
        company_products = defaultdict(list)
        for row in product_data:
            for role in ('buyer', 'seller'):
                comp = row[role]
                if comp in company_names and row['product_name']:
                    prods = company_products[comp]
                    if row['product_name'] not in prods and len(prods) < 3:
                        prods.append(row['product_name'])

        for c in companies:
            c['top_products'] = company_products.get(c['company'], [])

        return companies

    # ─────────────────────────────────────────────────────────
    # DIRECTION = IMPORT or EXPORT
    # ─────────────────────────────────────────────────────────
    company_field = 'buyer' if direction == 'import' else 'seller'
    counterparty_field = 'seller' if direction == 'import' else 'buyer'

    qs = (
        base_qs.values(company=F(company_field))
        .annotate(
            total_volume=Sum('qty_mt'),
            avg_price=Avg('usd_per_mt'),
            total_value=Sum('usd'),
            import_volume=Sum('qty_mt'),
            export_volume=Sum('qty_mt'),
            import_value=Sum('usd'),
            export_value=Sum('usd'),
            active_partners=Count(counterparty_field, distinct=True),
            transaction_count=Count('id'),
            first_trade=Min('reporting_date'),
            last_trade=Max('reporting_date'),
        )
        .order_by('-total_volume')
    )

    if search_query:
        qs = qs.filter(company__icontains=search_query)

    companies = list(qs[:limit])

    company_names = [c['company'] for c in companies]

    # company_type
    company_type_val = 'Pakistani Buyer' if direction == 'import' else 'Pakistani Seller'

    # Country field
    country_field_name = 'origin_country' if direction == 'import' else 'destination_country'
    country_data = (
        base_qs.filter(**{f'{company_field}__in': company_names})
        .values(company=F(company_field), country_name=F(country_field_name))
        .annotate(country_volume=Sum('qty_mt'))
        .order_by('-country_volume')
    )
    company_countries = {}
    for row in country_data:
        comp = row['company']
        if comp not in company_countries:
            company_countries[comp] = row['country_name']

    # Top products
    product_data = (
        base_qs.filter(**{f'{company_field}__in': company_names})
        .values(company=F(company_field), product_name=F('product_item__name'))
        .annotate(product_volume=Sum('qty_mt'))
        .order_by('-product_volume')
    )
    company_products = defaultdict(list)
    for row in product_data:
        comp = row['company']
        if len(company_products[comp]) < 3 and row['product_name']:
            company_products[comp].append(row['product_name'])

    # YoY growth
    current_year = datetime.now().year
    prev_year = current_year - 1

    current_year_volume = dict(
        base_qs.filter(**{f'{company_field}__in': company_names})
        .annotate(year=ExtractYear('reporting_date'))
        .filter(year=current_year)
        .values(company=F(company_field))
        .annotate(volume=Sum('qty_mt'))
        .values_list('company', 'volume')
    )
    prev_year_volume = dict(
        base_qs.filter(**{f'{company_field}__in': company_names})
        .annotate(year=ExtractYear('reporting_date'))
        .filter(year=prev_year)
        .values(company=F(company_field))
        .annotate(volume=Sum('qty_mt'))
        .values_list('company', 'volume')
    )

    for c in companies:
        comp = c['company']
        c['country']      = company_countries.get(comp, 'Unknown')
        c['company_type'] = company_type_val
        c['top_products'] = company_products.get(comp, [])
        c['total_value']  = float(c['total_value']) if c['total_value'] else 0
        c['import_value'] = float(c['import_value']) if c['import_value'] else 0
        c['export_value'] = float(c['export_value']) if c['export_value'] else 0

        curr = current_year_volume.get(comp, 0) or 0
        prev = prev_year_volume.get(comp, 0) or 0
        c['yoy_growth'] = round(((curr - prev) / prev) * 100, 2) if prev > 0 else None

    return companies
