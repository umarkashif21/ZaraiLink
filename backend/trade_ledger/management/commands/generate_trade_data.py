from django.core.management.base import BaseCommand
from trade_ledger.generate_fixture_data import main


class Command(BaseCommand):
    help = 'Generate trade ledger fixture data'

    def handle(self, *args, **options):
        main()
