import sys
import os
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
import django
django.setup()

from search.services.aggregation import SupplierAggregator
import inspect

sig = inspect.signature(SupplierAggregator.get_supplier_comparison)
print("Signature:", sig)
