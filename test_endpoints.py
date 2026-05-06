import requests
import time

BASE_URL = 'http://localhost:8000'

perf_endpoints = [
    ('GET', '/api/search/?q=sugar&scope=IMPORT'),
    ('GET', '/api/search/?q=dextrose&scope=EXPORT'),
    ('GET', '/api/search/autocomplete/?q=sug'),
    ('GET', '/api/companies/'),
]

sec_endpoints = [
    ('GET', '/api/search/'),
    ('GET', '/api/companies/'),
    ('GET', '/api/tokens/balance/'),
    ('GET', '/api/profile/'),
    ('POST', '/api/tokens/unlock/'),
    ('GET', '/api/watchlist/'),
]

print("PERFORMANCE TEST")
print("================")
print(f"{'Endpoint':<45} | {'Avg Response Time':<18} | {'Pass (< 3000ms)?'}")
print("-" * 85)

for method, path in perf_endpoints:
    times = []
    for _ in range(3):
        start = time.time()
        if method == 'GET':
            requests.get(BASE_URL + path)
        else:
            requests.post(BASE_URL + path)
        times.append((time.time() - start) * 1000)
    
    avg_time = sum(times) / len(times)
    passed = "Pass" if avg_time < 3000 else "Fail"
    print(f"{path:<45} | {avg_time:>13.2f} ms | {passed}")

print("\nSECURITY TEST")
print("=============")
print(f"{'Endpoint':<30} | {'Status Code':<11} | {'Expected 401/403':<16} | {'Pass/Fail'}")
print("-" * 80)

for method, path in sec_endpoints:
    if method == 'GET':
        r = requests.get(BASE_URL + path)
    else:
        r = requests.post(BASE_URL + path)
    
    status = r.status_code
    expected = "401/403"
    passed = "Pass" if status in [401, 403] else "Fail"
    print(f"{path:<30} | {status:<11} | {expected:<16} | {passed}")
