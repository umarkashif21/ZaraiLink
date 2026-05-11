import requests
from urllib.parse import quote

BASE_URL = 'http://localhost:8000'
seller = quote("Soneri Foods Pvt Ltd")

endpoints = [
    ('Premium trade data access', 'GET', f'/api/search/supplier-transactions/?name={seller}&query=sugar'),
    ('Token balance and spending', 'POST', '/api/subscriptions/purchase-access/'),
    ('Contact unlocking', 'POST', '/api/key-contacts/1/unlock/'),
    ('User profile data', 'GET', '/api/subscriptions/profile-data/'),
    ('Subscription/entitlement (Redeem)', 'POST', '/api/subscriptions/redeem/'),
    ('Deal detail data', 'GET', f'/api/search/supplier-detail/?name={seller}&query=sugar'),
]

print("REAL SECURITY TEST")
print("==================")
print(f"{'Feature':<35} | {'Status Code':<11} | {'Expected 401/403':<16} | {'Pass/Fail'}")
print("-" * 85)

for feature, method, path in endpoints:
    if method == 'GET':
        r = requests.get(BASE_URL + path)
    else:
        r = requests.post(BASE_URL + path)

    status = r.status_code
    expected = "401/403"
    passed = "Pass" if status in [401, 403] else "Fail"
    print(f"{feature:<35} | {status:<11} | {expected:<16} | {passed}")
