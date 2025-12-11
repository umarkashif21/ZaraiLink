# services/explorer.py
from django.db.models import Sum, Avg, Count, Q, F
from trade_data.models import Transaction
from .filters import apply_transaction_filters
# Debug import check removed - was causing encoding issues

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
    Direction determines company role: import → buyer, export → seller.
    """
    base_qs = Transaction.objects.all()
    base_qs = apply_transaction_filters(
        base_qs,
        direction=direction,
        date_from=date_from,
        date_to=date_to,
        country=country,
        product_category_id=product_category_id,
        product_subcategory_id=product_subcategory_id,
        product_item_id=product_item_id
    )

    company_field = 'buyer' if direction == 'import' else 'seller'
    counterparty_field = 'seller' if direction == 'import' else 'buyer'

    qs = (
        base_qs.values(company=F(company_field))
        .annotate(
            total_volume=Sum('qty_mt'),
            avg_price=Avg('usd_per_mt'),
            active_partners=Count(counterparty_field, distinct=True),
        )
        .order_by('-total_volume')
    )

    if search_query:
        qs = qs.filter(company__icontains=search_query)

    return list(qs[:limit])