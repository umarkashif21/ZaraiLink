import os
import django
import sys
import json
from django.db.models import Count

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction

def audit_seawall_broad_json():
    out = {}
    
    qs = Transaction.objects.filter(seller__icontains="Seawall Enterprise")
    out['total_count'] = qs.count()
    
    # Groups
    groups = qs.values('product_item__name', 'product_item__id').annotate(c=Count('id')).order_by('-c')
    out['products'] = list(groups)
    
    with open('audit_broad.json', 'w') as f:
        json.dump(out, f, indent=2, default=str)

if __name__ == "__main__":
    audit_seawall_broad_json()
