import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction

print("Deleting all transactions to start fresh...")
Transaction.objects.all().delete()
print("All transactions deleted.")
