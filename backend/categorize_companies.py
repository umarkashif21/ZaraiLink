import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from companies.models import Company
from trade_data.models import Transaction

def categorize():
    buyers = set(Transaction.objects.values_list('buyer', flat=True))
    sellers = set(Transaction.objects.values_list('seller', flat=True))

    pb = 0
    ps = 0
    fb = 0
    fs = 0
    both_pak = 0
    both_for = 0
    none_pak = 0
    none_for = 0

    updates = []

    for c in Company.objects.all():
        is_b = c.name in buyers
        is_s = c.name in sellers
        is_pak = c.country.lower() == 'pakistan'
        
        # company_role_id: 1=Buyer, 2=Supplier, 3=Distributor (Both)
        role_id = None
        
        if is_b and not is_s:
            role_id = 1
            if is_pak: pb += 1
            else: fb += 1
        elif is_s and not is_b:
            role_id = 2
            if is_pak: ps += 1
            else: fs += 1
        elif is_b and is_s:
            role_id = 3
            if is_pak: both_pak += 1
            else: both_for += 1
        else:
            if is_pak: none_pak += 1
            else: none_for += 1
            
        if role_id is not None:
            c.company_role_id = role_id
            updates.append(c)

    # Optional: Update the database with correct roles
    Company.objects.bulk_update(updates, ['company_role_id'])
    print("Database updated!")

    print(f"Total: {Company.objects.count()}")
    print(f"Pakistani Buyers: {pb}")
    print(f"Pakistani Sellers: {ps}")
    print(f"Foreign Buyers: {fb}")
    print(f"Foreign Sellers: {fs}")
    print(f"Pakistani Both: {both_pak}")
    print(f"Foreign Both: {both_for}")
    print(f"Pakistani No transactions: {none_pak}")
    print(f"Foreign No transactions: {none_for}")

if __name__ == '__main__':
    categorize()
