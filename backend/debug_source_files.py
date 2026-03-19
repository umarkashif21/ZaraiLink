import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction
from django.db.models import Count

with open('debug_sources_clean.txt', 'w') as f:
    for row in Transaction.objects.values('source_file').annotate(count=Count('id')).order_by('-count'):
        f.write(f"{row['source_file']}: {row['count']} rows\n")
