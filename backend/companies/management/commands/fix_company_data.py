from django.core.management.base import BaseCommand
from companies.models import Company, Sector


class Command(BaseCommand):
    help = 'Verify all companies and fix sectors'

    def handle(self, *args, **options):
        self.stdout.write('Fixing company data...')
        
        
        unverified_count = Company.objects.exclude(verification_status='verified').count()
        if unverified_count > 0:
            self.stdout.write(f'Found {unverified_count} unverified companies. Verifying...')
            Company.objects.all().update(verification_status='verified')
            self.stdout.write(self.style.SUCCESS(f'✓ Verified {unverified_count} companies'))
        else:
            self.stdout.write('✓ All companies already verified')
        
        
        try:
            unknown_sector = Sector.objects.get(name='Unknown')
            unknown_sector.name = 'Confectionary'
            unknown_sector.description = 'Confectionary and sweets products'
            unknown_sector.save()
            self.stdout.write(self.style.SUCCESS('✓ Changed "Unknown" sector to "Confectionary"'))
        except Sector.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠ "Unknown" sector not found'))
        
        
        total_companies = Company.objects.count()
        verified_companies = Company.objects.filter(verification_status='verified').count()
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'  Total Companies: {total_companies}')
        self.stdout.write(f'  Verified Companies: {verified_companies}')
        self.stdout.write('='*50)
        self.stdout.write(self.style.SUCCESS('\n✅ Company data fixed!'))
