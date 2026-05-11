import csv, os, sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')

import django
django.setup()

from companies.models import Company

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'companies.csv')

all_companies = {c.name.strip().lower(): c for c in Company.objects.all()}

matched = []
unmatched = []

with open(CSV_PATH, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        csv_name = row['company_name'].strip()
        csv_key = csv_name.lower()
        if csv_key in all_companies:
            matched.append((csv_name, all_companies[csv_key].name))
        else:
            candidates = [db_name for db_name in all_companies
                          if csv_key in db_name or db_name in csv_key]
            if candidates:
                unmatched.append((csv_name, f'PARTIAL MATCH -> {candidates[:3]}'))
            else:
                unmatched.append((csv_name, 'NO MATCH IN DB'))

print(f'=== MATCHED ({len(matched)}) ===')
for csv_n, db_n in matched:
    print(f'  OK  "{csv_n}"  ->  "{db_n}"')

print()
print(f'=== NOT MATCHED ({len(unmatched)}) ===')
for csv_n, reason in unmatched:
    print(f'  !!  "{csv_n}"  ->  {reason}')

print()
print(f'Total in CSV: {len(matched) + len(unmatched)}')
print(f'Matched: {len(matched)}')
print(f'Unmatched: {len(unmatched)}')
