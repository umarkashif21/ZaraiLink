import os
import django
import sys
import json
from django.db.models import Count

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction, ProductItem

def audit_seawall_json():
    out = {}
    
    items = ProductItem.objects.filter(name__icontains="Dextrose Monohydrate")
    item_ids = list(items.values_list('id', flat=True))
    out['item_ids'] = item_ids
    
    qs = Transaction.objects.filter(
        seller__icontains="Seawall Enterprise",
        product_item__id__in=item_ids
    )
    
    out['total_count'] = qs.count()
    
    variations = qs.values('seller').annotate(c=Count('id'))
    out['variations'] = list(variations)
    
    out['trade_types'] = {
        'EXPORT': qs.filter(trade_type='EXPORT').count(),
        'IMPORT': qs.filter(trade_type='IMPORT').count()
    }
    
    # Dump detailed list of all 39
    out['details'] = list(qs.values('id', 'seller', 'trade_type', 'reporting_date', 'product_item_id', 'qty_mt'))

    with open('audit_seawall.json', 'w') as f:
        json.dump(out, f, indent=2, default=str)

if __name__ == "__main__":
    audit_seawall_json()
