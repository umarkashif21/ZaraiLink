from django.core.management.base import BaseCommand
from companies.models import CompanyRole, Company


class Command(BaseCommand):
    help = 'Setup company roles (Buyers, Suppliers, Both) and assign companies'

    def handle(self, *args, **options):
        self.stdout.write('Setting up company roles...')
        
        
        buyers, _ = CompanyRole.objects.get_or_create(
            name='Buyers',
            defaults={'description': 'Companies that purchase products'}
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created/Found: {buyers.name} (ID: {buyers.id})'))
        
        suppliers, _ = CompanyRole.objects.get_or_create(
            name='Suppliers',
            defaults={'description': 'Companies that supply/sell products'}
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created/Found: {suppliers.name} (ID: {suppliers.id})'))
        
        both, _ = CompanyRole.objects.get_or_create(
            name='Both',
            defaults={'description': 'Companies acting as both buyers and suppliers'}
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created/Found: {both.name} (ID: {both.id})'))
        
        
        companies_without_role = Company.objects.filter(company_role__isnull=True)
        count = companies_without_role.count()
        
        if count > 0:
            self.stdout.write(f'\nFound {count} companies without roles. Assigning to "Both"...')
            companies_without_role.update(company_role=both)
            self.stdout.write(self.style.SUCCESS(f'✓ Assigned {count} companies to "Both"'))
        else:
            self.stdout.write('\n✓ All companies already have roles assigned')
        
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'  Buyers: {Company.objects.filter(company_role=buyers).count()} companies')
        self.stdout.write(f'  Suppliers: {Company.objects.filter(company_role=suppliers).count()} companies')
        self.stdout.write(f'  Both: {Company.objects.filter(company_role=both).count()} companies')
        self.stdout.write('='*50)
        self.stdout.write(self.style.SUCCESS('\n✅ Company roles setup complete!'))
