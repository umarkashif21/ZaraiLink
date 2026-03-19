import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction

print("Deleting duplicate transactions from relative paths...")
# We keep paths starting with C:\ (the absolute paths) which have exactly 1x records.
# We delete paths starting with ../ which have 2x records.

deleted_count = 0
for bad_path in ['../export_data.xlsx', '../import_data_1year.xlsx']:
    qs = Transaction.objects.filter(source_file=bad_path)
    count = qs.count()
    qs.delete()
    print(f"Deleted {count} rows from {bad_path}")
    deleted_count += count

print(f"\nSuccessfully removed {deleted_count} duplicate records.")
print("\nRemaining data state:")
from django.db.models import Count
for row in Transaction.objects.values('source_file').annotate(count=Count('id')).order_by('-count'):
    print(f"  {row['source_file']}: {row['count']} rows")
