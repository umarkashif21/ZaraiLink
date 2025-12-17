from django.core.management.base import BaseCommand
from companies.models import Sector, Company, CompanyProduct
import random


class Command(BaseCommand):
    help = 'Fix duplicate Confectionary sectors and add dummy HSN codes'

    def handle(self, *args, **options):
        self.stdout.write('='*60)
        self.stdout.write('FIXING SECTORS AND HSN CODES')
        self.stdout.write('='*60 + '\n')
        
        
        self.stdout.write('1. Checking for duplicate Confectionary sectors...')
        confect_sectors = Sector.objects.filter(name__icontains='confectionary')
        
        if confect_sectors.count() > 1:
            self.stdout.write(f'   Found {confect_sectors.count()} Confectionary sectors')
            
            
            primary_sector = confect_sectors.first()
            duplicate_sectors = confect_sectors.exclude(id=primary_sector.id)
            
            for dup_sector in duplicate_sectors:
                
                companies_moved = Company.objects.filter(sector=dup_sector).update(sector=primary_sector)
                self.stdout.write(f'   - Moved {companies_moved} companies from "{dup_sector.name}" to "{primary_sector.name}"')
                
                
                dup_name = dup_sector.name
                dup_sector.delete()
                self.stdout.write(self.style.SUCCESS(f'   ✓ Deleted duplicate sector: {dup_name}'))
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ Merged all into: {primary_sector.name}\n'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ No duplicate Confectionary sectors found\n'))
        
        
        self.stdout.write('2. Adding dummy HSN codes to products...')
        products_without_hsn = CompanyProduct.objects.filter(hsn_code='')
        
        if products_without_hsn.exists():
            
            dummy_hsn_codes = [
                '1006', '1001', '1005', '5201',  
                '0713', '0901', '0902', '1701',  
                '1207', '1511', '1512', '0801',  
                '1704', '1806', '2106',          
            ]
            
            for product in products_without_hsn:
                
                product.hsn_code = random.choice(dummy_hsn_codes)
                product.save()
            
            self.stdout.write(self.style.SUCCESS(f'   ✓ Added HSN codes to {products_without_hsn.count()} products\n'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ All products already have HSN codes\n'))
        
        
        self.stdout.write('='*60)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'  Total Sectors: {Sector.objects.count()}')
        self.stdout.write(f'  Confectionary Sectors: {Sector.objects.filter(name__icontains="confectionary").count()}')
        self.stdout.write(f'  Products with HSN: {CompanyProduct.objects.exclude(hsn_code="").count()}')
        self.stdout.write(f'  Total Products: {CompanyProduct.objects.count()}')
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('\n✅ All fixes complete!'))
