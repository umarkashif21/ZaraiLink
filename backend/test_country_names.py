import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction

# Check unique origin countries in IMPORT data
print("====== UNIQUE ORIGIN COUNTRIES IN IMPORT DATA ======")
countries = Transaction.objects.filter(trade_type='IMPORT').values_list('origin_country', flat=True).distinct()
countries_list = sorted(set(countries))
print(f"Total unique countries: {len(countries_list)}")
print("\nFirst 20 countries:")
for country in countries_list[:20]:
    print(f"  '{country}'")

# Check if we can find "China" (case-sensitive)
print("\n====== EXACT MATCH TEST ======")
exact_match = Transaction.objects.filter(trade_type='IMPORT', origin_country='China').count()
print(f"Exact 'China': {exact_match}")

iexact_match = Transaction.objects.filter(trade_type='IMPORT', origin_country__iexact='China').count()
print(f"Case-insensitive 'China': {iexact_match}")

contains_match = Transaction.objects.filter(trade_type='IMPORT', origin_country__icontains='china').count()
print(f"Contains 'china': {contains_match}")
