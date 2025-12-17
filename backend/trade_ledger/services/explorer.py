from django.db.models import Sum, Avg, Count, Q, F, Max, Min
from django.db.models.functions import ExtractYear
from trade_data.models import Transaction
from .filters import apply_transaction_filters
from datetime import datetime, timedelta
from collections import defaultdict

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
    Enhanced to include: country, top products, YoY growth, transaction count, total value.
    """
    base_qs = Transaction.objects.all()
    
    
    if date_from:
        base_qs = base_qs.filter(reporting_date__gte=date_from)
    if date_to:
        base_qs = base_qs.filter(reporting_date__lte=date_to)
    if country:
        base_qs = base_qs.filter(country=country)
    if product_item_id:
        base_qs = base_qs.filter(product_item_id=product_item_id)
    elif product_subcategory_id:
        base_qs = base_qs.filter(product_item__sub_category_id=product_subcategory_id)
    elif product_category_id:
        base_qs = base_qs.filter(product_item__sub_category__category_id=product_category_id)

    
    if direction == 'both':
        
        company_stats = defaultdict(lambda: {
            'total_volume': 0, 'total_value': 0, 'avg_price': 0.0, 
            'transaction_count': 0, 'active_partners': set(), 
            'first_trade': None, 'last_trade': None
        })
        
        for tx in base_qs.values('buyer', 'seller', 'qty_mt', 'usd', 'usd_per_mt', 'reporting_date'):
            for role in ['buyer', 'seller']:
                name = tx[role]
                if name and name.lower() != 'unknown':
                    cs = company_stats[name]
                    cs['total_volume'] += float(tx['qty_mt'] or 0)
                    cs['total_value'] += float(tx['usd'] or 0)
                    cs['transaction_count'] += 1
                    cs['active_partners'].add(tx['seller' if role == 'buyer' else 'buyer'])
                    if cs['first_trade'] is None or tx['reporting_date'] < cs['first_trade']:
                        cs['first_trade'] = tx['reporting_date']
                    if cs['last_trade'] is None or tx['reporting_date'] > cs['last_trade']:
                        cs['last_trade'] = tx['reporting_date']
        
        
        companies = []
        for name, stats in company_stats.items():
            companies.append({
                'company': name,
                'total_volume': stats['total_volume'],
                'total_value': stats['total_value'],
                'avg_price': stats['total_value'] / stats['total_volume'] if stats['total_volume'] > 0 else 0,
                'active_partners': len(stats['active_partners']),
                'transaction_count': stats['transaction_count'],
                'first_trade': stats['first_trade'],
                'last_trade': stats['last_trade'],
            })
        
        
        companies.sort(key=lambda x: x['total_volume'], reverse=True)
        if search_query:
            companies = [c for c in companies if search_query.lower() in c['company'].lower()]
        companies = companies[:limit]
        
    else:
        
        company_field = 'buyer' if direction == 'import' else 'seller'
        counterparty_field = 'seller' if direction == 'import' else 'buyer'

        
        qs = (
            base_qs.values(company=F(company_field))
            .annotate(
                total_volume=Sum('qty_mt'),
                avg_price=Avg('usd_per_mt'),
                total_value=Sum('usd'),
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
    
    
    if direction == 'both':
        
        company_countries = {}
        company_products = defaultdict(list)
        
        for comp_name in company_names:
            
            country_row = (
                base_qs.filter(Q(buyer=comp_name) | Q(seller=comp_name))
                .values('country')
                .annotate(vol=Sum('qty_mt'))
                .order_by('-vol')
                .first()
            )
            company_countries[comp_name] = country_row['country'] if country_row else 'N/A'
            
            
            prods = (
                base_qs.filter(Q(buyer=comp_name) | Q(seller=comp_name))
                .values(product_name=F('product_item__name'))
                .annotate(vol=Sum('qty_mt'))
                .order_by('-vol')[:3]
            )
            company_products[comp_name] = [p['product_name'] for p in prods if p['product_name']]
        
        
        for c in companies:
            comp = c['company']
            c['country'] = company_countries.get(comp, 'N/A')
            c['top_products'] = company_products.get(comp, [])
            c['yoy_growth'] = None  
            c['total_value'] = float(c['total_value']) if c['total_value'] else 0
        
    else:
        
        
        country_data = (
            base_qs.filter(**{f'{company_field}__in': company_names})
            .values(company=F(company_field), country_name=F('country'))
            .annotate(country_volume=Sum('qty_mt'))
            .order_by(f'-country_volume')
        )
        company_countries = {}
        for row in country_data:
            comp = row['company']
            if comp not in company_countries:
                company_countries[comp] = row['country_name']
        
        
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
            c['country'] = company_countries.get(comp, 'N/A')
            c['top_products'] = company_products.get(comp, [])
            
            
            curr = current_year_volume.get(comp, 0) or 0
            prev = prev_year_volume.get(comp, 0) or 0
            if prev > 0:
                c['yoy_growth'] = round(((curr - prev) / prev) * 100, 2)
            else:
                c['yoy_growth'] = None
            
            
            c['total_value'] = float(c['total_value']) if c['total_value'] else 0
    
    return companies

