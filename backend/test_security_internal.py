import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from rest_framework.test import APIClient
from urllib.parse import quote

client = APIClient(SERVER_NAME='localhost')
seller = quote("Soneri Foods Pvt Ltd")

endpoints = [
    ('Premium trade data access', 'GET', f'/api/search/supplier-transactions/?name={seller}&query=sugar'),
    ('Token balance and spending', 'POST', '/api/subscriptions/purchase-access/'),
    ('Contact unlocking', 'POST', '/api/key-contacts/1/unlock/'),
    ('User profile data', 'GET', '/api/subscriptions/profile-data/'),
    ('Subscription/entitlement (Redeem)', 'POST', '/api/subscriptions/redeem/'),
    ('Deal detail data', 'GET', f'/api/search/supplier-detail/?name={seller}&query=sugar'),
    ('Supplier compare', 'GET', f'/api/search/compare/?suppliers={seller}&query=sugar'),
]

print("INTERNAL SECURITY AUDIT")
print("=======================")
print(f"{'Feature':<35} | {'Status Code':<11} | {'Expected 401/403':<16} | {'Pass/Fail'}")
print("-" * 85)

for feature, method, path in endpoints:
    if method == 'GET':
        r = client.get(path)
    else:
        r = client.post(path)

    status = r.status_code
    expected = "401/403"
    passed = "Pass" if status in [401, 403] else "Fail"
    print(f"{feature:<35} | {status:<11} | {expected:<16} | {passed}")
