import requests

BASE_URL = 'http://localhost:8000'

mapped_endpoints = [
    ('GET', '/api/search/'),
    ('GET', '/api/companies/'),
    ('GET', '/accounts/api/check-auth/'),
    ('GET', '/accounts/api/update-profile/'),
    ('POST', '/api/key-contacts/1/unlock/'),
]

for method, path in mapped_endpoints:
    if method == 'GET':
        r = requests.get(BASE_URL + path)
    else:
        r = requests.post(BASE_URL + path)
    print(f"{path:<40} | {r.status_code}")
