import os
import sys
import time
import subprocess
import requests
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from django.contrib.auth import get_user_model
from urllib.parse import quote

User = get_user_model()
username = 'rel_test_user'
email = 'rel@test.com'
password = 'rel_test_password123'

user, created = User.objects.get_or_create(username=username, email=email)
user.set_password(password)
user.token_balance = 0  # required to test no-token unlock path
user.save()

print("Starting Django server in the background for reliability testing...")
server_process = subprocess.Popen(
    [sys.executable, 'manage.py', 'runserver', '8000', '--noreload'],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

BASE_URL = "http://localhost:8000"

url = f"{BASE_URL}/api/search/autocomplete/?q=sug"
server_ready = False
for _ in range(60):
    try:
        r = requests.get(url, timeout=2)
        if r.status_code in [200, 403, 404]:
            server_ready = True
            break
    except Exception:
        pass
    time.sleep(1)

if not server_ready:
    print("Server failed to start. Exiting.")
    server_process.kill()
    sys.exit(1)

print("Server is ready. Starting reliability tests...\n")

session = requests.Session()
login_payload = {'email': email, 'password': password}
login_url = f"{BASE_URL}/accounts/api/login/"
resp = session.post(login_url, json=login_payload)
if resp.status_code != 200:
    print(f"Warning: Login failed. Status: {resp.status_code}")

test_cases = [
    ('Search', 'Empty query', 'GET', f'/api/search/?q=&scope=IMPORT', None, False),
    ('Search', 'Whitespace query', 'GET', f'/api/search/?q={quote("   ")}&scope=IMPORT', None, False),
    ('Search', 'Special chars', 'GET', f'/api/search/?q={quote("!@#$%")}&scope=IMPORT', None, False),
    ('Search', 'Gibberish query', 'GET', f'/api/search/?q=xyzxyzxyz&scope=IMPORT', None, False),
    ('Search', 'Unlikely NLU query', 'GET', f'/api/search/?q={quote("sugar from mars")}&scope=IMPORT', None, False),
    ('Search', 'Oversized query', 'GET', f'/api/search/?q={"a"*300}&scope=IMPORT', None, False),

    ('Intelligence', 'Non-existent supplier (detail)', 'GET', f'/api/search/supplier-detail/?name=FakeCompanyXYZ123&query=sugar', None, True),
    ('Intelligence', 'Non-existent supplier (tx)', 'GET', f'/api/search/supplier-transactions/?name=FakeCompanyXYZ123&query=sugar', None, True),
    ('Intelligence', 'Missing params (detail)', 'GET', f'/api/search/supplier-detail/', None, True),
    ('Intelligence', 'Missing params (tx)', 'GET', f'/api/search/supplier-transactions/', None, True),

    ('Directory', 'Non-existent company ID', 'GET', f'/api/companies/99999999/', None, False),
    ('Directory', 'Invalid filters', 'GET', f'/api/companies/?country=FAKECOUNTRY&sector=FAKESECTOR', None, False),
    ('Directory', 'Empty search', 'GET', f'/api/companies/?search=xyzxyzxyz', None, False),

    ('Auth', 'Wrong credentials', 'POST', f'/accounts/api/login/', {"email": "fake@fake.com", "password": "wrongpassword"}, False),
    ('Auth', 'Invalid reset token format', 'GET', f'/accounts/api/verify-email/invalidtoken123abc/', None, False),

    ('Subscription', 'Invalid redemption code', 'POST', f'/api/subscriptions/redeem/', {"code": "FAKECODE123"}, True),
    ('Subscription', 'Unlock with no tokens', 'POST', f'/api/key-contacts/1/unlock/', None, True),

    ('Autocomplete', 'Empty query', 'GET', f'/api/search/autocomplete/?q=', None, False),
    ('Autocomplete', 'Special chars', 'GET', f'/api/search/autocomplete/?q={quote("!@#$")}', None, False),
    ('Autocomplete', 'Gibberish query', 'GET', f'/api/search/autocomplete/?q=xyzxyzxyz', None, False),
]

results = []

for module, name, method, path, payload, use_auth in test_cases:
    client = session if use_auth else requests
    full_url = BASE_URL + path

    try:
        if method == 'GET':
            r = client.get(full_url, timeout=10)
        else:
            r = client.post(full_url, json=payload, timeout=10)

        status = r.status_code
        crashed = (status == 500)
        passed = not crashed

    except Exception as e:
        status = 'Error'
        crashed = True
        passed = False

    results.append({
        'module': module,
        'name': name,
        'status': status,
        'crashed': 'Yes' if crashed else 'No',
        'passed': 'PASS' if passed else 'FAIL'
    })

server_process.kill()

print("RELIABILITY TEST — FULL PLATFORM")
print("==================================")
print(f"{'Module':<15} | {'Test Case':<32} | {'Status':<6} | {'Crashed (500)?':<14} | {'Pass/Fail'}")
for r in results:
    print(f"{r['module']:<15} | {r['name']:<32} | {r['status']:<6} | {r['crashed']:<14} | {r['passed']}")

passed_count = sum(1 for r in results if r['passed'] == 'PASS')
failed_count = len(results) - passed_count

print("\nRELIABILITY SUMMARY")
print("===================")
print(f"Total tests: {len(results)}")
print(f"Passed (no crash): {passed_count}")
print(f"Failed (500 error): {failed_count}")
