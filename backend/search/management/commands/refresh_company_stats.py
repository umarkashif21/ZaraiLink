"""
Django management command: refresh_company_stats

Populates / refreshes the CompanyProductStats pre-aggregated table.

Run nightly or after new data ingestion:
    python manage.py refresh_company_stats
    python manage.py refresh_company_stats --truncate  (full rebuild)
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Refresh pre-aggregated CompanyProductStats table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--truncate',
            action='store_true',
            default=False,
            help='Truncate table before rebuilding (full refresh)',
        )

    def handle(self, *args, **options):
        from django.db import connection, transaction
        from django.db.models import Sum, Avg, Count, Max, Min
        from trade_data.models import Transaction, CompanyProductStats

        truncate = options['truncate']

        if truncate:
            self.stdout.write('Truncating CompanyProductStats...')
            CompanyProductStats.objects.all().delete()

        self.stdout.write('Building CompanyProductStats...')

        # Aggregate sellers by (seller, subcategory, origin_country)
        seller_agg = (
            Transaction.objects
            .filter(trade_type='IMPORT')
            .values('seller', 'product_item__sub_category_id', 'origin_country')
            .annotate(
                total_vol=Sum('qty_mt'),
                count=Count('id'),
                avg_price=Avg('usd_per_mt'),
                max_vol=Max('qty_mt'),
                avg_vol=Avg('qty_mt'),
                first_date=Min('reporting_date'),
                last_date=Max('reporting_date'),
            )
            .exclude(product_item__sub_category_id=None)
        )

        seller_records = []
        for row in seller_agg:
            seller_records.append(CompanyProductStats(
                company_name=row['seller'] or '',
                sub_category_id=row['product_item__sub_category_id'],
                entity_role='SELLER',
                country=row['origin_country'] or '',
                total_volume_mt=float(row['total_vol'] or 0),
                shipment_count=row['count'] or 0,
                avg_price_usd_mt=float(row['avg_price'] or 0),
                max_shipment_vol_mt=float(row['max_vol'] or 0),
                avg_shipment_vol_mt=float(row['avg_vol'] or 0),
                first_shipment_date=row['first_date'],
                last_shipment_date=row['last_date'],
            ))

        # Aggregate buyers by (buyer, subcategory, destination_country)
        buyer_agg = (
            Transaction.objects
            .filter(trade_type='IMPORT')
            .values('buyer', 'product_item__sub_category_id', 'destination_country')
            .annotate(
                total_vol=Sum('qty_mt'),
                count=Count('id'),
                avg_price=Avg('usd_per_mt'),
                max_vol=Max('qty_mt'),
                avg_vol=Avg('qty_mt'),
                first_date=Min('reporting_date'),
                last_date=Max('reporting_date'),
            )
            .exclude(product_item__sub_category_id=None)
        )

        buyer_records = []
        for row in buyer_agg:
            buyer_records.append(CompanyProductStats(
                company_name=row['buyer'] or '',
                sub_category_id=row['product_item__sub_category_id'],
                entity_role='BUYER',
                country=row['destination_country'] or '',
                total_volume_mt=float(row['total_vol'] or 0),
                shipment_count=row['count'] or 0,
                avg_price_usd_mt=float(row['avg_price'] or 0),
                max_shipment_vol_mt=float(row['max_vol'] or 0),
                avg_shipment_vol_mt=float(row['avg_vol'] or 0),
                first_shipment_date=row['first_date'],
                last_shipment_date=row['last_date'],
            ))

        all_records = seller_records + buyer_records
        self.stdout.write(f'  {len(seller_records)} seller aggregates + {len(buyer_records)} buyer aggregates = {len(all_records)} total')

        # Bulk upsert
        with transaction.atomic():
            CompanyProductStats.objects.bulk_create(
                all_records,
                update_conflicts=True,
                unique_fields=['company_name', 'sub_category', 'entity_role', 'country'],
                update_fields=[
                    'total_volume_mt', 'shipment_count', 'avg_price_usd_mt',
                    'max_shipment_vol_mt', 'avg_shipment_vol_mt',
                    'first_shipment_date', 'last_shipment_date', 'refreshed_at',
                ],
            )

        count = CompanyProductStats.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'Done. CompanyProductStats table: {count} rows'
        ))
