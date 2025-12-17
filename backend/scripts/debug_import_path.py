import os
import sys
import django


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zarailink.settings")
django.setup()

import trade_ledger.services.products as products
print(f"Products Module Path: {products.__file__}")

from trade_ledger.services.products import get_company_product_performance
import inspect
print(inspect.getsource(get_company_product_performance))
