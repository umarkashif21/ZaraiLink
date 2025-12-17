from django.core.management.base import BaseCommand
from companies.models import Company, CompanyRole
from django.db.models import Count


class Command(BaseCommand):
    help = 'Debug company visibility issues'

    def handle(self, *args, **options):
        self.stdout.write('=== DEBUGGING COMPANY VISIBILITY ===\n')
        
        
        self.stdout.write('1. COMPANY COUNT:')
        total = Company.objects.count()
        verified = Company.objects.filter(verification_status='verified').count()
        self.stdout.write(f'   Total: {total}')
        self.stdout.write(f'   Verified: {verified}\n')
        
        
        self.stdout.write('2. COMPANY ROLES:')
        roles = CompanyRole.objects.all()
        for role in roles:
            count = Company.objects.filter(company_role=role, verification_status='verified').count()
            self.stdout.write(f'   {role.name} (ID: {role.id}): {count} verified companies')
        
        
        self.stdout.write('\n3. SAMPLE COMPANIES:')
        sample_companies = Company.objects.filter(verification_status='verified')[:5]
        for comp in sample_companies:
            role_name = comp.company_role.name if comp.company_role else 'NO ROLE'
            self.stdout.write(f'   - {comp.name}: status={comp.verification_status}, role={role_name}')
        
        
        self.stdout.write('\n4. API QUERYSET TEST:')        
        from companies.views import CompanyViewSet
        viewset = CompanyViewSet()
        viewset.request = type('obj', (object,), {'query_params': {'role': '6'}})()
        qs = viewset.get_queryset()
        self.stdout.write(f'   Queryset with role=6: {qs.count()} companies')
        
        viewset.request = type('obj', (object,), {'query_params': {'role': '7'}})()
        qs = viewset.get_queryset()
        self.stdout.write(f'   Queryset with role=7: {qs.count()} companies')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('✅ Debug complete!'))
