import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

print("=" * 60)
print("VERIFICATION: Trade Ledger Explorer + Company Endpoints")
print("=" * 60)

from trade_ledger.services.explorer import get_explorer_companies
from trade_data.models import Transaction

# 1. direction=both
print("\n[1] direction=both (limit=5) ...")
try:
    result = get_explorer_companies(direction='both', limit=5)
    print(f"    PASS: {len(result)} companies returned")
    for c in result:
        print(f"    - {c['company']} | country={c.get('country','?')} | vol={c.get('total_volume',0):.1f} | txns={c.get('transaction_count',0)}")
except Exception as e:
    import traceback
    print(f"    FAIL: {e}")
    traceback.print_exc()

# 2. direction=import
print("\n[2] direction=import (limit=5) ...")
try:
    result = get_explorer_companies(direction='import', limit=5)
    print(f"    PASS: {len(result)} companies returned")
    for c in result:
        print(f"    - {c['company']} | country={c.get('country','?')} | vol={c.get('total_volume',0):.1f}")
except Exception as e:
    import traceback
    print(f"    FAIL: {e}")
    traceback.print_exc()

# 3. direction=export
print("\n[3] direction=export (limit=5) ...")
try:
    result = get_explorer_companies(direction='export', limit=5)
    print(f"    PASS: {len(result)} companies returned")
    for c in result:
        print(f"    - {c['company']} | country={c.get('country','?')} | vol={c.get('total_volume',0):.1f}")
except Exception as e:
    import traceback
    print(f"    FAIL: {e}")
    traceback.print_exc()

# 4. Real company name
sample = Transaction.objects.values_list('buyer', flat=True).exclude(buyer='').order_by('-id').first()
print(f"\n[4] Using company: '{sample}'")

# 5. Company overview service
print("\n[5] get_company_overview_metrics ...")
try:
    from trade_ledger.services.company import get_company_overview_metrics
    metrics = get_company_overview_metrics(company_name=sample, direction='import')
    print(f"    PASS: total_volume_mt={metrics.get('total_volume_mt',0):.2f}, active_partners={metrics.get('active_partners',0)}")
    print(f"    top_countries={metrics.get('top_countries',[])}") 
except Exception as e:
    import traceback
    print(f"    FAIL: {e}")
    traceback.print_exc()

# 6. Partners service
print("\n[6] get_top_partners ...")
try:
    from trade_ledger.services.partners import get_top_partners
    partners = list(get_top_partners(company_name=sample, direction='import', limit=3))
    print(f"    PASS: {len(partners)} partners returned")
    for p in partners:
        print(f"    - {p.get('partner','?')} | origin_country={p.get('origin_country','?')} | vol={p.get('total_volume',0)}")
except Exception as e:
    import traceback
    print(f"    FAIL: {e}")
    traceback.print_exc()

# 7. Country filter
print("\n[7] country filter test ...")
try:
    sample_country = Transaction.objects.values_list('origin_country', flat=True).first()
    result = get_explorer_companies(direction='both', country=sample_country, limit=5)
    print(f"    PASS: country='{sample_country}' -> {len(result)} companies")
except Exception as e:
    import traceback
    print(f"    FAIL: {e}")
    traceback.print_exc()

# 8. Trade volume by country
print("\n[8] get_trade_volume_by_country ...")
try:
    from trade_ledger.services.partners import get_trade_volume_by_country
    vol_by_country = list(get_trade_volume_by_country(company_name=sample, direction='import'))
    print(f"    PASS: {len(vol_by_country)} countries returned")
    for v in vol_by_country[:3]:
        print(f"    - origin_country={v.get('origin_country','?')} | vol={v.get('total_volume',0)}")
except Exception as e:
    import traceback
    print(f"    FAIL: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
