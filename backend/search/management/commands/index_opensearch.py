"""
management/commands/index_opensearch.py

Django management command to index trade data into OpenSearch.

Usage:
    python manage.py index_opensearch
    python manage.py index_opensearch --full            # delete & recreate indices first
    python manage.py index_opensearch --products-only   # only index ProductSubCategory
    python manage.py index_opensearch --batch-size=500  # custom chunk size
"""

import time
import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Index Transaction and ProductSubCategory records into OpenSearch.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            default=False,
            help='Delete and recreate indices before indexing (full re-index).',
        )
        parser.add_argument(
            '--products-only',
            action='store_true',
            default=False,
            help='Only index ProductSubCategory records; skip transactions.',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            dest='batch_size',
            help='Number of documents per bulk request (default: 500).',
        )

    def handle(self, *args, **options):
        from search.services.opensearch_client import (
            get_os_client,
            create_indices,
            bulk_index_transactions,
            OS_TRANSACTIONS_INDEX,
            OS_PRODUCTS_INDEX,
            TRANSACTION_MAPPING,
            PRODUCT_MAPPING,
        )

        start_time = time.time()
        full = options['full']
        products_only = options['products_only']
        batch_size = options['batch_size']

        # ── Connect ───────────────────────────────────────────────────────────
        self.stdout.write('Connecting to OpenSearch...')
        client = get_os_client()

        if not client.ping():
            self.stderr.write(self.style.ERROR(
                'Cannot reach OpenSearch. Is the service running? '
                'Check OPENSEARCH_HOST / OPENSEARCH_PORT in settings.'
            ))
            return

        self.stdout.write(self.style.SUCCESS('Connected to OpenSearch.'))

        # ── Full re-index: delete existing indices ────────────────────────────
        if full:
            for index_name in [OS_TRANSACTIONS_INDEX, OS_PRODUCTS_INDEX]:
                if client.indices.exists(index=index_name):
                    client.indices.delete(index=index_name)
                    self.stdout.write(f'Deleted index: {index_name}')

        # ── Create indices (idempotent) ───────────────────────────────────────
        create_indices(client)
        self.stdout.write('Indices ready.')

        total_transactions = 0
        total_products = 0

        # ── Index ProductSubCategory records ─────────────────────────────────
        self.stdout.write('Indexing ProductSubCategory records...')
        try:
            from trade_data.models import ProductSubCategory
            products = list(ProductSubCategory.objects.all().values('id', 'name', 'hs_code'))
        except Exception as exc:
            self.stderr.write(self.style.WARNING(
                f'Could not load ProductSubCategory: {exc}'
            ))
            products = []

        if products:
            from opensearchpy.helpers import bulk as os_bulk
            actions = [
                {
                    '_op_type': 'index',
                    '_index': OS_PRODUCTS_INDEX,
                    '_id': p['id'],
                    'id': p['id'],
                    'name': p['name'] or '',
                    'hs_code': p['hs_code'] or '',
                }
                for p in products
            ]
            success, errors = os_bulk(client, actions, stats_only=False, raise_on_error=False)
            total_products = success
            if errors:
                self.stderr.write(self.style.WARNING(
                    f'Product indexing errors: {len(errors)}'
                ))
            self.stdout.write(self.style.SUCCESS(
                f'Indexed {total_products} product(s).'
            ))
        else:
            self.stdout.write('No products found to index.')

        # ── Index Transaction records ─────────────────────────────────────────
        if not products_only:
            from trade_data.models import Transaction

            tx_total = Transaction.objects.count()
            self.stdout.write(
                f'Indexing {tx_total:,} transaction(s) '
                f'(batch_size={batch_size})...'
            )

            # Stream transactions in chunks to avoid loading all into RAM
            processed = 0
            indexed = 0
            errors_total = 0

            def transaction_iterator():
                """Yield all transactions using iterator() for memory efficiency."""
                return (
                    Transaction.objects
                    .select_related('product_item')
                    .iterator(chunk_size=batch_size)
                )

            chunk = []
            for tx in transaction_iterator():
                chunk.append(tx)
                if len(chunk) >= batch_size:
                    idx, err = bulk_index_transactions(client, chunk, chunk_size=batch_size)
                    indexed += idx
                    errors_total += err
                    processed += len(chunk)
                    chunk = []

                    if processed % 1000 == 0 or processed == tx_total:
                        self.stdout.write(
                            f'  Progress: {processed:,} / {tx_total:,} processed, '
                            f'{indexed:,} indexed, {errors_total} errors'
                        )

            # Flush remainder
            if chunk:
                idx, err = bulk_index_transactions(client, chunk, chunk_size=batch_size)
                indexed += idx
                errors_total += err
                processed += len(chunk)

            total_transactions = indexed

            # Final progress line
            self.stdout.write(
                f'  Progress: {processed:,} / {tx_total:,} processed, '
                f'{indexed:,} indexed, {errors_total} errors'
            )

            if errors_total:
                self.stderr.write(self.style.WARNING(
                    f'Completed with {errors_total} bulk errors. '
                    'Check logs for details.'
                ))

        # ── Summary ───────────────────────────────────────────────────────────
        elapsed = time.time() - start_time
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== OpenSearch Indexing Summary ==='))
        if not products_only:
            self.stdout.write(f'  Transactions indexed : {total_transactions:,}')
        self.stdout.write(f'  Products indexed     : {total_products:,}')
        self.stdout.write(f'  Elapsed time         : {elapsed:.1f}s')
        self.stdout.write(self.style.SUCCESS('Done.'))
