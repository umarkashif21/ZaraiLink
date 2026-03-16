"""
Django management command: run_entity_resolution

Runs the full entity resolution pipeline:
  1. Extracts all unique seller/buyer names from Transaction table
  2. Runs blocking + Fellegi-Sunter comparison
  3. Clusters via transitive closure
  4. Creates/updates CanonicalEntity records
  5. Refreshes denormalized stats on each entity

Usage:
    python manage.py run_entity_resolution
    python manage.py run_entity_resolution --dry-run
    python manage.py run_entity_resolution --refresh-stats-only
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run entity resolution pipeline to deduplicate company names'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Run pipeline but do not write to DB',
        )
        parser.add_argument(
            '--refresh-stats-only',
            action='store_true',
            default=False,
            help='Only refresh denormalized stats on existing CanonicalEntity records',
        )
        parser.add_argument(
            '--show-uncertain',
            action='store_true',
            default=False,
            help='Print uncertain pairs that need human review',
        )

    def handle(self, *args, **options):
        from entity_resolution.resolver import get_all_entities_from_db, resolve
        from entity_resolution.models import CanonicalEntity, EntityMergeLog

        if options['refresh_stats_only']:
            self.stdout.write('Refreshing denormalized stats only...')
            self._refresh_stats()
            return

        self.stdout.write('Extracting entities from database...')
        entities = get_all_entities_from_db()
        self.stdout.write(f'  Found {len(entities)} unique raw entity names')

        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no DB writes'))

        self.stdout.write('Running entity resolution pipeline...')
        golden_records = resolve(entities, dry_run=dry_run)

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone: {len(entities)} raw → {len(golden_records)} canonical entities '
                f'({len(entities) - len(golden_records)} merged)'
            )
        )

        if not dry_run:
            db_count = CanonicalEntity.objects.count()
            self.stdout.write(f'CanonicalEntity table: {db_count} records')

        # Show uncertain pairs
        if options['show_uncertain']:
            uncertain = EntityMergeLog.objects.filter(decision='UNCERTAIN', reviewed_by_human=False)
            if uncertain.exists():
                self.stdout.write(f'\n{uncertain.count()} uncertain pairs requiring human review:')
                for log in uncertain[:20]:
                    self.stdout.write(
                        f'  [{log.similarity_score:.2f}] {log.raw_name_a!r} ↔ {log.raw_name_b!r}'
                    )
                if uncertain.count() > 20:
                    self.stdout.write(f'  ... and {uncertain.count() - 20} more')

    def _refresh_stats(self):
        from entity_resolution.models import CanonicalEntity
        from trade_data.models import Transaction
        from django.db.models import Sum, Avg, Count, Max

        entities = CanonicalEntity.objects.all()
        updated = 0

        for entity in entities:
            seller_stats = Transaction.objects.filter(
                seller__in=entity.raw_names
            ).aggregate(
                total_vol=Sum('qty_mt'),
                avg_price=Avg('usd_per_mt'),
                count=Count('id'),
                last_date=Max('reporting_date'),
            )
            buyer_stats = Transaction.objects.filter(
                buyer__in=entity.raw_names
            ).aggregate(
                total_vol=Sum('qty_mt'),
                avg_price=Avg('usd_per_mt'),
                count=Count('id'),
                last_date=Max('reporting_date'),
            )

            total_vol = float(seller_stats['total_vol'] or 0) + float(buyer_stats['total_vol'] or 0)
            total_count = (seller_stats['count'] or 0) + (buyer_stats['count'] or 0)
            avg_price_vals = [v for v in [seller_stats['avg_price'], buyer_stats['avg_price']] if v]
            avg_price = float(sum(avg_price_vals) / len(avg_price_vals)) if avg_price_vals else 0.0
            dates = [d for d in [seller_stats['last_date'], buyer_stats['last_date']] if d]
            last_date = max(dates) if dates else None

            entity.shipment_count = total_count
            entity.total_volume_mt = total_vol
            entity.avg_price_usd_mt = avg_price
            entity.last_shipment_date = last_date
            entity.save(update_fields=['shipment_count', 'total_volume_mt', 'avg_price_usd_mt', 'last_shipment_date', 'updated_at'])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Updated stats for {updated} entities.'))
