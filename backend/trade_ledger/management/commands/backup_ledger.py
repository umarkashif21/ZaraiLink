import json
from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
from trade_data.models import Transaction, AggProductMonthCountry, AggCompanyMonthProduct
from datetime import datetime

class Command(BaseCommand):
    help = 'Backups transaction data to a JSON file'

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transactions_backup_{timestamp}.json"
        
        self.stdout.write(f"Backing up data to {filename}...")
        
        transactions = Transaction.objects.all().values()
        data = list(transactions)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=DjangoJSONEncoder, indent=2)
            
        self.stdout.write(self.style.SUCCESS(f"Successfully backed up {len(data)} transactions to {filename}"))
