from django.db import models
from trade_data.models import Transaction

def apply_transaction_filters(
    qs,
    direction=None,           
    company_name=None,        
    date_from=None,
    date_to=None,
    country=None,
    product_category_id=None,
    product_subcategory_id=None,
    product_item_id=None,
):
    """
    Applies all supported filters to a Transaction QuerySet.
    """
    
    if direction == 'import':
        if company_name:
            qs = qs.filter(buyer=company_name)
    elif direction == 'export':
        if company_name:
            qs = qs.filter(seller=company_name)
    else:
        
        if company_name:
            qs = qs.filter(models.Q(buyer=company_name) | models.Q(seller=company_name))

    
    if date_from:
        qs = qs.filter(reporting_date__gte=date_from)
    if date_to:
        qs = qs.filter(reporting_date__lte=date_to)

    
    if country:
        qs = qs.filter(country=country)

    
    if product_item_id:
        qs = qs.filter(product_item_id=product_item_id)
    elif product_subcategory_id:
        qs = qs.filter(product_item__sub_category_id=product_subcategory_id)
    elif product_category_id:
        qs = qs.filter(product_item__sub_category__category_id=product_category_id)

    return qs