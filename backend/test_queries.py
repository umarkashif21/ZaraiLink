import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_intelligence.settings')
django.setup()

from django.db.models import Sum, F, Count, Case, When, CharField, Q, FloatField
from django.db.models.functions import Coalesce, TruncMonth
from trade_data.models import Transaction
from trade_ledger.services.filters import apply_transaction_filters

company_name = "M.A Oils Pvt Ltd"
direction = "import"

qs = Transaction.objects.all()
qs = apply_transaction_filters(qs, direction=direction, company_name=company_name)

import_cond = Q(destination_country__icontains='Pakistan')
export_cond = Q(origin_country__icontains='Pakistan')
counterparty_expr = Case(
    When(buyer=company_name, then=F('seller')),
    default=F('buyer'),
    output_field=CharField()
)

results = (
    qs.filter(product_item__isnull=False)
    .values(
        product_id=F('product_item__id'),
        product_name=F('product_item__name'),
    )
    .annotate(
        total_volume=Sum('qty_mt'),
        total_value=Sum(F('qty_mt') * F('usd_per_mt'), output_field=FloatField()),
        import_volume=Sum('qty_mt', filter=import_cond),
        export_volume=Sum('qty_mt', filter=export_cond),
        avg_price=Sum(F('qty_mt') * F('usd_per_mt'), output_field=FloatField()) / Sum('qty_mt', output_field=FloatField()),
        shipment_count=Count('id'),
        unique_partners=Count(counterparty_expr, distinct=True)
    )
    .order_by('-total_volume')[:5]
)

print(list(results))
