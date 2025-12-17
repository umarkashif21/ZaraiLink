from django.core.management.base import BaseCommand
from companies.models import Sector, Company


class Command(BaseCommand):
    help = 'Merge duplicate Confectionary sectors'

    def handle(self, *args, **options):
        try:
            
            correct_sector = Sector.objects.get(id=4, name='Confectionery')
            duplicate_sector = Sector.objects.get(id=3, name='Confectionary')
            
            
            companies_moved = Company.objects.filter(sector=duplicate_sector).update(sector=correct_sector)
            
            self.stdout.write(f'Moved {companies_moved} companies from "Confectionary" to "Confectionery"')
            
            
            duplicate_sector.delete()
            self.stdout.write(self.style.SUCCESS('✓ Deleted duplicate sector: Confectionary'))
            
            
            remaining_sectors = Sector.objects.filter(name__icontains='confection')
            self.stdout.write(f'\nRemaining Confection* sectors: {remaining_sectors.count()}')
            for sector in remaining_sectors:
                self.stdout.write(f'  - ID {sector.id}: {sector.name}')
                
        except Sector.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Sector not found: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
