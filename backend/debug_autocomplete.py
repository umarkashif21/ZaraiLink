import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import ProductSubCategory

queries = ['1702', '1702.', '1702.1', '1702.11', '1704.9', '1704.90']
for q in queries:
    count = ProductSubCategory.objects.filter(hs_code__startswith=q).count()
    sample = list(ProductSubCategory.objects.filter(hs_code__startswith=q).values_list('hs_code','name')[:3])
    print(f"'{q}' → {count} results | sample: {sample}")
