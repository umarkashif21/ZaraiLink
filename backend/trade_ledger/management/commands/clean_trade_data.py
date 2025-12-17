from django.core.management.base import BaseCommand
from trade_ledger.models import (
    TradeTrend, TradePartner, TradeProduct, TradeCompany, ProductCategory
)


class Command(BaseCommand):
    help = 'Clean all trade ledger fixture data (does not delete base Company records)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without prompting',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            confirm = input(
                'This will delete ALL trade ledger data (ProductCategory, TradeCompany, '
                'TradeProduct, TradePartner, TradeTrend). Continue? (yes/no): '
            )
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return

        self.stdout.write('Cleaning trade ledger data...')
        
        
        trend_count = TradeTrend.objects.count()
        TradeTrend.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {trend_count} trade trends'))
        
        partner_count = TradePartner.objects.count()
        TradePartner.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {partner_count} trade partners'))
        
        product_count = TradeProduct.objects.count()
        TradeProduct.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {product_count} trade products'))
        
        company_count = TradeCompany.objects.count()
        TradeCompany.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {company_count} trade companies'))
        
        category_count = ProductCategory.objects.count()
        ProductCategory.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {category_count} product categories'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Trade ledger data cleaned successfully!'))
        self.stdout.write(self.style.WARNING('Note: Base Company records were NOT deleted.'))
