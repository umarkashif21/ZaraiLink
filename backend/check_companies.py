import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
import django
django.setup()

from companies.models import Company
from django.db.models import Count


print("=== Verification Status Distribution ===")
stats = Company.objects.values('verification_status').annotate(count=Count('id'))
for s in stats:
    print(f"  {s['verification_status']}: {s['count']}")


print("\n=== Suppliers by Verification Status ===")
suppliers = Company.objects.filter(company_role__name__icontains='supplier')
for s in suppliers.values('verification_status').annotate(count=Count('id')):
    print(f"  {s['verification_status']}: {s['count']}")

print("\n=== Sample Verified Suppliers ===")
verified_suppliers = Company.objects.filter(
    company_role__name__icontains='supplier',
    verification_status='verified'
)
print(f"Total verified suppliers: {verified_suppliers.count()}")

print("\n=== All Suppliers (any status) ===")
all_suppliers = Company.objects.filter(company_role__name__icontains='supplier')
for c in all_suppliers[:5]:
    print(f"  {c.name} - {c.verification_status}")
