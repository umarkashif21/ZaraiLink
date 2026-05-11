import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from rest_framework.test import APIClient
from urllib.parse import quote
from django.contrib.auth import get_user_model
from subscriptions.models import UserAccess
from search.services.search_service import SearchService

User = get_user_model()
search_service = SearchService()

no_access_user, _ = User.objects.get_or_create(email='noaccess2@test.com', username='noaccess2')
no_access_user.set_password('password')
no_access_user.save()

access_user, _ = User.objects.get_or_create(email='access2@test.com', username='access2')
access_user.set_password('password')
access_user.save()

seller_name = "Soneri Foods Pvt Ltd"
query_term = "sugar"

parsed_query = search_service._nlu_engine.parse(query_term)
hs_code_hint = query_term if all(c.isdigit() or c == '.' for c in query_term.strip()) else parsed_query.get("hs_code", "")

subcat_ids, _, _ = search_service._resolve_subcategories(
    product_keyword=parsed_query.get("product", query_term),
    hs_code=hs_code_hint,
    intent='BUY',
    subcat_id=None,
    variant_name=None,
    scope='IMPORT'
)

print(f"Resolved subcat_ids: {subcat_ids}")
active_hs_code = parsed_query.get("hs_code", "")
if not active_hs_code and hs_code_hint:
    active_hs_code = hs_code_hint
active_subcat_id = subcat_ids[0] if subcat_ids else None

print(f"Initial active_hs_code: {active_hs_code}, active_subcat_id: {active_subcat_id}")

if not active_hs_code and active_subcat_id:
    from trade_data.models import ProductSubCategory
    sub = ProductSubCategory.objects.filter(id=active_subcat_id).first()
    if sub:
        active_hs_code = sub.hs_code
        
print(f"Final active_hs_code being checked for access: {active_hs_code}")

if active_hs_code:
    UserAccess.objects.get_or_create(
        user=access_user,
        access_type='HS_CODE',
        hscode=active_hs_code,
        tokens_spent=5000
    )
elif active_subcat_id:
    UserAccess.objects.get_or_create(
        user=access_user,
        access_type='PRODUCT',
        subcat_id=active_subcat_id,
        tokens_spent=500
    )

seller_param = quote(seller_name)
endpoints = [
    ('supplier-transactions', f'/api/search/supplier-transactions/?name={seller_param}&query={query_term}'),
    ('supplier-detail', f'/api/search/supplier-detail/?name={seller_param}&query={query_term}'),
    ('supplier-compare', f'/api/search/compare/?suppliers={seller_param}&query={query_term}'),
]

print("LAYER 2 ENTITLEMENT TEST")
print("=========================")
print(f"{'Endpoint':<25} | {'Auth + No Entitlement':<25} | {'Auth + Valid Entitlement':<25}")
print("-" * 80)

for feature, path in endpoints:
    client_no_access = APIClient(SERVER_NAME='localhost')
    client_no_access.force_authenticate(user=no_access_user)
    r_no = client_no_access.get(path)

    client_access = APIClient(SERVER_NAME='localhost')
    client_access.force_authenticate(user=access_user)
    r_yes = client_access.get(path)

    print(f"{feature:<25} | {r_no.status_code:<25} | {r_yes.status_code:<25}")
