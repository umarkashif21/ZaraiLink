import os
import sys
import time
import subprocess
import requests
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import UserAccess

User = get_user_model()
username = 'perf_test_user2'
email = 'perf2@test.com'
password = 'perf_test_password123'

user, created = User.objects.get_or_create(username=username, email=email)
user.set_password(password)
user.save()

# Give access so authenticated endpoints return 200 (data) rather than fast 403s
UserAccess.objects.get_or_create(user=user, access_type='HS_CODE', hscode='1701', tokens_spent=0)
UserAccess.objects.get_or_create(user=user, access_type='HS_CODE', hscode='1702', tokens_spent=0)
UserAccess.objects.get_or_create(user=user, access_type='HS_CODE', hscode='2940', tokens_spent=0)

print("Starting Django server in the background for testing...")
server_process = subprocess.Popen(
    [sys.executable, 'manage.py', 'runserver', '8000', '--noreload'],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

url = "http://localhost:8000/api/search/autocomplete/?q=sug"
server_ready = False
for _ in range(60):
    try:
        r = requests.get(url, timeout=2)
        if r.status_code in [200, 403, 404]:
            server_ready = True
            break
    except requests.exceptions.ConnectionError:
        pass
    except requests.exceptions.Timeout:
        pass
    time.sleep(1)

if not server_ready:
    print("Server failed to start. Exiting.")
    server_process.kill()
    sys.exit(1)

print("Server is ready. Starting performance tests...\n")

BASE_URL = "http://localhost:8000"

public_endpoints = [
    "/api/search/?q=sugar&scope=IMPORT",
    "/api/search/?q=dextrose&scope=EXPORT", 
    "/api/search/autocomplete/?q=sug",
    "/api/companies/",
]

authenticated_endpoints = [
    "/api/search/supplier-detail/?name=Seawall%20Enterprise%20Ltd&query=dextrose",
    "/api/search/supplier-transactions/?name=Seawall%20Enterprise%20Ltd&query=dextrose",
    "/api/subscriptions/profile-data/",
    "/api/companies/?search=sugar",
]

session = requests.Session()
login_payload = {
    'email': email,
    'password': password
}
login_url = f"{BASE_URL}/accounts/api/login/"
resp = session.post(login_url, json=login_payload)
if resp.status_code != 200:
    print(f"Warning: Login might have failed. Status: {resp.status_code}")

try:
    session.get(f"{BASE_URL}/api/search/?q=warmup", timeout=15)
except Exception:
    pass

results = []

def test_endpoint(path, use_session=False):
    target = 500 if 'autocomplete' in path else 3000
    times = []

    full_url = BASE_URL + path
    client = session if use_session else requests

    for _ in range(3):
        try:
            start = time.time()
            client.get(full_url, timeout=15)
            end = time.time()
            times.append(int((end - start) * 1000))
        except Exception:
            times.append(9999)

    avg = sum(times) // 3
    passed = "PASS" if avg <= target else "FAIL"

    results.append({
        'path': path,
        'r1': times[0],
        'r2': times[1],
        'r3': times[2],
        'avg': avg,
        'target': target,
        'passed': passed
    })

for path in public_endpoints:
    test_endpoint(path, use_session=False)

for path in authenticated_endpoints:
    test_endpoint(path, use_session=True)

server_process.kill()

print("PERFORMANCE TEST RESULTS")
print("========================")
print(f"{'Endpoint':<75} | {'Run1':<6} | {'Run2':<6} | {'Run3':<6} | {'Avg':<6} | {'Target':<7} | {'Pass/Fail'}")
for r in results:
    clean_path = r['path'].replace('%20', ' ')
    print(f"{clean_path:<75} | {r['r1']}ms{' '*(4-len(str(r['r1'])))} | {r['r2']}ms{' '*(4-len(str(r['r2'])))} | {r['r3']}ms{' '*(4-len(str(r['r3'])))} | {r['avg']}ms{' '*(4-len(str(r['avg'])))} | {r['target']}ms{' '*(5-len(str(r['target'])))} | {r['passed']}")

passed_count = sum(1 for r in results if r['passed'] == 'PASS')
failed_endpoints = [r['path'].replace('%20', ' ') for r in results if r['passed'] == 'FAIL']

print("\nSUMMARY")
print("=======")
print(f"Total endpoints tested: {len(results)}")
print(f"Passed: {passed_count}")
print(f"Failed: {len(failed_endpoints)}")
if failed_endpoints:
    print("Failed endpoints:")
    for path in failed_endpoints:
        print(f"  - {path}")
