"""
Django management command: fit_anomaly_models

Fits IsolationForest + Prophet anomaly detection models for all subcategories.

Usage:
    python manage.py fit_anomaly_models
    python manage.py fit_anomaly_models --subcategory-id=42
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Fit anomaly detection models for trade price and volume data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--subcategory-id',
            type=int,
            default=None,
            help='Fit model for a single subcategory ID (default: all)',
        )

    def handle(self, *args, **options):
        from search.services.anomaly_detector import TradeAnomalyDetector

        detector = TradeAnomalyDetector()
        subcat_id = options.get('subcategory_id')

        if subcat_id:
            self.stdout.write(f'Fitting anomaly model for subcategory {subcat_id}...')
            ok = detector.fit_price_model(subcat_id)
            if ok:
                self.stdout.write(self.style.SUCCESS(f'Done. Model fitted for subcat {subcat_id}'))
            else:
                self.stdout.write(self.style.WARNING(
                    f'Skipped subcat {subcat_id} (insufficient data or fit error)'
                ))
        else:
            self.stdout.write('Fitting anomaly models for all subcategories...')
            results = detector.fit_all(verbose=False)
            self.stdout.write(self.style.SUCCESS(
                f'Done. Fitted: {results["fitted"]}, '
                f'Skipped: {results["skipped"]}, '
                f'Errors: {results["errors"]}'
            ))
