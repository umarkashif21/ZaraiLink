"""
Import company profiles from companies.csv into the DB.
Run with: python import_companies.py
"""
import csv, os, sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
import django
django.setup()

from companies.models import Company, CompanyType

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'companies.csv')

# ── Manual name corrections (CSV name -> exact DB name, lowercase) ──────────
MANUAL_MAP = {
    'ab astepsworth':              'aba stepsworth dwc llc',
    'best buy brands':             'best brands general trading llc',
    'makeup4u':                    'makeup 4u',
    'meggle group':                'meggle gmbh & co kg',
    'shiprose':                    'rose containerline inc',
    's&s trading':                 'shree sai trading',
    'arshine chemical':            'arshine food additives co ltd',
    'apeloa pharmaceutical':       'apeloa hong kong ltd',
    # Partial matches confirmed 100% correct
    'emrays':                      'emrays international general trading co llc',
    'jrs pharma':                  'jrs pharma gmbh & co kg',
    'leprino foods':               'leprino foods dairy products co',
    'sethness roquette':           'sethness roquette food (lianyungang) co ltd',
    'advan pharma':                'advan pharmachem co ltd',
    'aipu food industry':          'aipu food industry co ltd',
    'anhui ebuy international':    'anhui ebuy international co ltd',
    'kemfood international':       'anhui kemfood international co ltd',
    'arshine food additives':      'arshine food additives co ltd',
    'access usa shipping (myus)':  'access usa shipping',
    'tate & lyle sugars':          'tate & lyle sugars ltd',
    'greyhound chromatography':    'greyhound chromatography and allied chemicals ltd',
    'armor proteines':             'armor proteines sas',
    'signet excipients':           'signet excipients pvt ltd',
    'industrial design services (ids)': 'industrial design services',  # skip if not found
}

# ── Load all DB companies keyed by lowercase name ───────────────────────────
all_companies = {c.name.strip().lower(): c for c in Company.objects.all()}

# ── Process CSV ──────────────────────────────────────────────────────────────
updated = []
skipped = []

with open(CSV_PATH, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        csv_name   = row['company_name'].strip()
        csv_key    = csv_name.lower()
        description = row.get('description', '').strip()
        type_str   = row.get('type', '').strip()
        year_str   = row.get('year_established', '').strip()
        emp_str    = row.get('employees', '').strip()
        website    = row.get('website', '').strip()

        # Resolve DB key
        db_key = MANUAL_MAP.get(csv_key, csv_key)

        if db_key not in all_companies:
            skipped.append((csv_name, f'NOT FOUND IN DB as "{db_key}"'))
            continue

        company = all_companies[db_key]

        # Update fields (only if CSV has a non-empty value)
        changed = False

        if description:
            company.description = description
            changed = True

        if website:
            company.website = website
            changed = True

        if year_str:
            try:
                company.year_established = int(year_str)
                changed = True
            except ValueError:
                pass

        if emp_str:
            try:
                company.number_of_employees = int(emp_str)
                changed = True
            except ValueError:
                pass

        # company_type is a FK to CompanyType — get_or_create by name
        if type_str:
            ct, _ = CompanyType.objects.get_or_create(name=type_str)
            company.company_type = ct
            changed = True

        if changed:
            company.save()
            updated.append((csv_name, db_key))
        else:
            skipped.append((csv_name, 'NO DATA TO UPDATE'))

print(f"=== UPDATED ({len(updated)}) ===")
for csv_n, db_n in updated:
    print(f'  OK  "{csv_n}"  ->  "{db_n}"')

print()
print(f"=== SKIPPED ({len(skipped)}) ===")
for csv_n, reason in skipped:
    print(f'  !!  "{csv_n}"  ->  {reason}')

print()
print(f"Done. Updated: {len(updated)}  |  Skipped: {len(skipped)}")
