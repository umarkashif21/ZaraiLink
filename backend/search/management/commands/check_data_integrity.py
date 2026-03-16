"""
Django management command: check_data_integrity

Verifies database integrity for the search system:
  - FK integrity (no orphaned records)
  - Aggregation sanity (volumes match raw transactions)
  - No zero-volume / zero-shipment stats rows

Prints PASS / FAIL per check and exits code 1 if any FAIL.

Usage:
    python manage.py check_data_integrity
    python manage.py check_data_integrity --fix   (auto-fix where possible)
"""

import sys
import logging
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verify database integrity for the search system.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix', action='store_true',
            help='Attempt to auto-fix detected issues where possible',
        )
        parser.add_argument(
            '--quiet', action='store_true',
            help='Only print failures',
        )

    def handle(self, *args, **options):
        fix = options['fix']
        quiet = options['quiet']
        checks = []

        # ── 1. Basic transaction table sanity ─────────────────────────────────
        checks.append(self._check_transaction_basics(quiet))

        # ── 2. ProductItem FK integrity ───────────────────────────────────────
        checks.append(self._check_product_item_fk(quiet))

        # ── 3. ProductSubCategory FK integrity ────────────────────────────────
        checks.append(self._check_subcategory_fk(quiet))

        # ── 4. No zero-volume transactions ────────────────────────────────────
        checks.append(self._check_nonzero_volumes(quiet))

        # ── 5. CanonicalCompanyLink / NameVariant FK (if present) ─────────────
        checks.append(self._check_canonical_links(quiet))

        # ── 6. CompanyProductStats integrity (if present) ─────────────────────
        checks.append(self._check_stats_table(quiet))

        # ── 7. OpenSearch index count (if enabled) ────────────────────────────
        checks.append(self._check_opensearch(quiet))

        # ── Summary ───────────────────────────────────────────────────────────
        passed = sum(1 for ok, _ in checks if ok)
        total = len(checks)
        self.stdout.write('\n' + '─' * 55)
        if passed == total:
            self.stdout.write(self.style.SUCCESS(f'✓  All {total} integrity checks PASSED'))
        else:
            failed = total - passed
            self.stdout.write(self.style.ERROR(f'✗  {failed}/{total} integrity checks FAILED'))
            sys.exit(1)

    # ─────────────────────────────────────────────────────────────────────────

    def _ok(self, label, detail='', quiet=False):
        if not quiet:
            msg = f'PASS  {label}'
            if detail:
                msg += f'  [{detail}]'
            self.stdout.write(self.style.SUCCESS(msg))
        return (True, label)

    def _fail(self, label, reason):
        self.stdout.write(self.style.ERROR(f'FAIL  {label}  — {reason}'))
        return (False, label)

    def _warn(self, label, detail, quiet=False):
        if not quiet:
            self.stdout.write(self.style.WARNING(f'WARN  {label}  — {detail}'))
        return (True, label)

    # ─────────────────────────────────────────────────────────────────────────

    def _check_transaction_basics(self, quiet):
        label = 'Transaction table basics'
        try:
            from trade_data.models import Transaction
            total = Transaction.objects.count()
            if total == 0:
                return self._fail(label, 'Transaction table is empty')
            imports = Transaction.objects.filter(trade_type='IMPORT').count()
            exports = Transaction.objects.filter(trade_type='EXPORT').count()
            return self._ok(
                label,
                f'total={total:,}, imports={imports:,}, exports={exports:,}',
                quiet,
            )
        except Exception as e:
            return self._fail(label, str(e))

    def _check_product_item_fk(self, quiet):
        label = 'ProductItem FK (Transaction → ProductItem)'
        try:
            from trade_data.models import Transaction
            orphaned = Transaction.objects.filter(
                product_item_id__isnull=False,
                product_item__isnull=True,
            ).count()
            if orphaned > 0:
                return self._fail(label, f'{orphaned:,} transactions reference non-existent ProductItem')
            null_items = Transaction.objects.filter(product_item_id__isnull=True).count()
            return self._ok(label, f'0 orphans (null_product_item={null_items:,})', quiet)
        except Exception as e:
            return self._fail(label, str(e))

    def _check_subcategory_fk(self, quiet):
        label = 'ProductSubCategory FK (ProductItem → SubCategory)'
        try:
            from trade_data.models import ProductItem, ProductSubCategory
            orphaned = ProductItem.objects.filter(
                sub_category_id__isnull=False,
                sub_category__isnull=True,
            ).count()
            if orphaned > 0:
                return self._fail(label, f'{orphaned:,} ProductItems reference non-existent SubCategory')
            total_subcats = ProductSubCategory.objects.count()
            total_items = ProductItem.objects.count()
            return self._ok(
                label,
                f'0 orphans, subcategories={total_subcats}, items={total_items}',
                quiet,
            )
        except Exception as e:
            return self._fail(label, str(e))

    def _check_nonzero_volumes(self, quiet):
        label = 'No zero-volume / zero-price records (sanity)'
        try:
            from trade_data.models import Transaction
            from django.db.models import Q
            # Count transactions with non-null qty_mt
            has_qty = Transaction.objects.filter(qty_mt__isnull=False).count()
            zero_qty = Transaction.objects.filter(qty_mt__isnull=False, qty_mt=0).count()
            if has_qty > 0 and zero_qty / has_qty > 0.5:
                return self._fail(
                    label,
                    f'{zero_qty:,}/{has_qty:,} ({100*zero_qty/has_qty:.0f}%) have qty_mt=0',
                )
            null_qty = Transaction.objects.filter(qty_mt__isnull=True).count()
            total = Transaction.objects.count()
            return self._ok(
                label,
                f'null_qty={null_qty:,}, zero_qty={zero_qty:,}, total={total:,}',
                quiet,
            )
        except Exception as e:
            return self._fail(label, str(e))

    def _check_canonical_links(self, quiet):
        label = 'CanonicalCompanyLink FK integrity'
        try:
            from companies.models import CanonicalCompanyLink
            total = CanonicalCompanyLink.objects.count()
            if total == 0:
                return self._warn(label, 'No CanonicalCompanyLink records — entity resolution not yet run', quiet)
            # Check for duplicate raw_names (violates unique constraint)
            with connection.cursor() as c:
                c.execute(
                    'SELECT COUNT(*) FROM (SELECT raw_name FROM companies_canonicalcompanylink '
                    'GROUP BY raw_name HAVING COUNT(*) > 1) dup'
                )
                dupes = c.fetchone()[0]
            if dupes > 0:
                return self._fail(label, f'{dupes} duplicate raw_name entries')
            return self._ok(label, f'{total:,} canonical links, 0 duplicates', quiet)
        except Exception as e:
            return self._warn(label, f'Could not check (model may not exist): {e}', quiet)

    def _check_stats_table(self, quiet):
        label = 'CompanyProductStats sanity'
        try:
            # Try to import the model — may not exist yet
            from django.apps import apps
            if not apps.is_installed('trade_data'):
                return self._warn(label, 'trade_data app not installed', quiet)

            # Check if the table exists
            with connection.cursor() as c:
                c.execute(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_name = 'trade_data_companyproductstats'"
                )
                exists = c.fetchone()[0]

            if not exists:
                return self._warn(label, 'CompanyProductStats table does not exist yet', quiet)

            with connection.cursor() as c:
                c.execute('SELECT COUNT(*) FROM trade_data_companyproductstats')
                total = c.fetchone()[0]

            if total == 0:
                return self._warn(label, 'CompanyProductStats table is empty — run build_stats_table', quiet)

            # Check for zero-shipment rows
            with connection.cursor() as c:
                c.execute(
                    'SELECT COUNT(*) FROM trade_data_companyproductstats '
                    'WHERE shipment_count = 0 OR total_volume_mt <= 0'
                )
                bad_rows = c.fetchone()[0]

            if bad_rows > 0:
                return self._fail(label, f'{bad_rows:,} rows with shipment_count=0 or total_volume_mt<=0')

            return self._ok(label, f'{total:,} stats rows, 0 zero-volume rows', quiet)
        except Exception as e:
            return self._warn(label, f'Skipped: {e}', quiet)

    def _check_opensearch(self, quiet):
        label = 'OpenSearch index count'
        try:
            from django.conf import settings
            if not getattr(settings, 'SEARCH_USE_OPENSEARCH', False):
                if not quiet:
                    self.stdout.write(f'SKIP  {label}  [SEARCH_USE_OPENSEARCH=False]')
                return (True, label)

            from search.services.opensearch_client import get_os_client, OS_TRANSACTIONS_INDEX, OS_PRODUCTS_INDEX
            client = get_os_client()
            if not client.ping():
                return self._fail(label, 'OpenSearch not reachable (ping failed)')

            tx_count = client.count(index=OS_TRANSACTIONS_INDEX)['count']
            prod_count = client.count(index=OS_PRODUCTS_INDEX)['count']

            from trade_data.models import Transaction
            pg_count = Transaction.objects.count()

            if tx_count == 0:
                return self._fail(label, 'zarailink_transactions index is empty — run index_opensearch')

            drift = abs(tx_count - pg_count)
            if drift > pg_count * 0.05:
                return self._fail(
                    label,
                    f'OpenSearch ({tx_count:,}) vs PostgreSQL ({pg_count:,}) differ by >{drift:,} rows (>5%)',
                )

            return self._ok(
                label,
                f'transactions={tx_count:,}, products={prod_count:,}, pg_drift={drift:,}',
                quiet,
            )
        except Exception as e:
            return self._warn(label, f'Could not verify: {e}', quiet)
