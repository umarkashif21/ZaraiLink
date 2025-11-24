from django.core.management.base import BaseCommand
from companies.models import CompanyRole

class Command(BaseCommand):
    help = 'Seeds initial company roles'

    def handle(self, *args, **kwargs):
        roles = ['Buyer', 'Supplier', 'Distributor', 'Manufacturer', 'Service Provider']
        for role_name in roles:
            role, created = CompanyRole.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created role: {role_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Role already exists: {role_name}'))
