from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create initial subscription plans'

    def handle(self, *args, **options):
        plans_data = [
            
            {
                'plan_name': '500 Credits',
                'price': 9.00,
                'currency': 'PKR',
                'tokens_included': 500,
                'description': 'Starter monthly plan - perfect for occasional use',
                'features': {
                    'contacts_unlock': '500 contacts per month',
                    'support': 'Email support',
                    'validity': '30 days'
                }
            },
            {
                'plan_name': '5K Credits',
                'price': 32.00,
                'currency': 'PKR',
                'tokens_included': 5000,
                'description': 'Standard monthly plan - best for growing businesses',
                'features': {
                    'contacts_unlock': '5,000 contacts per month',
                    'support': 'Priority email support',
                    'validity': '30 days',
                    'popular': True
                }
            },
            {
                'plan_name': '15K Credits',
                'price': 99.00,
                'currency': 'PKR',
                'tokens_included': 15000,
                'description': 'Ultimate monthly plan - for power users',
                'features': {
                    'contacts_unlock': '15,000 contacts per month',
                    'support': 'Priority support + phone',
                    'validity': '30 days',
                    'advanced_analytics': True
                }
            },
            
            {
                'plan_name': '6000 Credits Annually',
                'price': 99.00,
                'currency': 'PKR',
                'tokens_included': 6000,
                'description': 'Starter annual plan - save with yearly billing',
                'features': {
                    'contacts_unlock': '6,000 contacts per year',
                    'support': 'Email support',
                    'validity': '365 days',
                    'save': '~10% vs monthly'
                }
            },
            {
                'plan_name': '60K Credits Annually',
                'price': 350.00,
                'currency': 'PKR',
                'tokens_included': 60000,
                'description': 'Standard annual plan - maximum savings',
                'features': {
                    'contacts_unlock': '60,000 contacts per year',
                    'support': 'Priority email support',
                    'validity': '365 days',
                    'save': '~10% vs monthly',
                    'popular': True
                }
            },
            {
                'plan_name': '900K Credits Annually',
                'price': 1090.00,
                'currency': 'PKR',
                'tokens_included': 900000,
                'description': 'Ultimate annual plan - best value',
                'features': {
                    'contacts_unlock': '900,000 contacts per year',
                    'support': 'Premium support + dedicated account manager',
                    'validity': '365 days',
                    'save': '~10% vs monthly',
                    'advanced_analytics': True,
                    'priority_access': True
                }
            },
        ]

        created_count = 0
        updated_count = 0

        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.update_or_create(
                plan_name=plan_data['plan_name'],
                defaults=plan_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Created: {plan.plan_name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'🔄 Updated: {plan.plan_name}'))

        self.stdout.write(self.style.SUCCESS(f'\n📊 Summary:'))
        self.stdout.write(f'   Created: {created_count} plans')
        self.stdout.write(f'   Updated: {updated_count} plans')
        self.stdout.write(f'   Total: {len(plans_data)} plans')
