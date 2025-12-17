import os
import django
import sys


sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction

def check_dates():
    company_name = "Aamster Laboratories (Branch)"
    print(f"--- Dates for: {company_name} ---")
    txs = Transaction.objects.filter(buyer=company_name)
    for tx in txs:
        print(f"Date: {tx.reporting_date}, Product: {tx.product_item.name if tx.product_item else 'None'}")

if __name__ == "__main__":
    check_dates()
