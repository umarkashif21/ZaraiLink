from django.core.management.base import BaseCommand, CommandError
from subscriptions.models import SubscriptionPlan, RedeemCode
from django.db.models import Q

class Command(BaseCommand):
    help = 'Generate redeem codes for a specific subscription plan'

    def add_arguments(self, parser):
        parser.add_argument('plan_identifier', type=str, help='ID or Name of the subscription plan')
        parser.add_argument('--count', type=int, default=10, help='Number of codes to generate (default: 10)')

    def handle(self, *args, **options):
        plan_identifier = options['plan_identifier']
        count = options['count']

        try:
            
            if plan_identifier.isdigit():
                plan = SubscriptionPlan.objects.get(id=int(plan_identifier))
            else:
                
                try:
                    plan = SubscriptionPlan.objects.get(plan_name=plan_identifier)
                except SubscriptionPlan.DoesNotExist:
                    plan = SubscriptionPlan.objects.get(plan_name__iexact=plan_identifier)

        except SubscriptionPlan.DoesNotExist:
            
            plans = SubscriptionPlan.objects.filter(plan_name__icontains=plan_identifier)
            if plans.count() == 1:
                plan = plans.first()
            elif plans.count() > 1:
                plan_names = ", ".join([p.plan_name for p in plans])
                raise CommandError(f'Multiple plans found matching "{plan_identifier}": {plan_names}. Please be more specific.')
            else:
                raise CommandError(f'Plan "{plan_identifier}" not found.')

        self.stdout.write(f'Generating {count} codes for plan: {plan.plan_name}...')

        codes = []
        for _ in range(count):
            while True:
                code = RedeemCode.generate_code()
                if not RedeemCode.objects.filter(code=code).exists():
                    break
            
            RedeemCode.objects.create(
                code=code,
                plan=plan,
                status='active'
            )
            codes.append(code)

        self.stdout.write(self.style.SUCCESS(f'Successfully generated {count} codes:'))
        for code in codes:
            self.stdout.write(code)
