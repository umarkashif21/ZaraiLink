from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan, RedeemCode
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Generate redeem codes for subscription plans'

    def add_arguments(self, parser):
        parser.add_argument(
            'plan_id',
            type=int,
            help='Subscription plan ID to generate codes for'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of codes to generate (default: 10)'
        )
        parser.add_argument(
            '--length',
            type=int,
            default=12,
            help='Code length (default: 12)'
        )
        parser.add_argument(
            '--expires-days',
            type=int,
            default=None,
            help='Number of days until expiration (optional)'
        )

    def handle(self, *args, **options):
        plan_id = options['plan_id']
        count = options['count']
        length = options['length']
        expires_days = options['expires_days']

        # Get the subscription plan
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Subscription plan with ID {plan_id} does not exist'))
            return

        # Calculate expiration date if specified
        expires_at = None
        if expires_days:
            expires_at = timezone.now() + timedelta(days=expires_days)

        # Generate codes
        generated_codes = []
        for i in range(count):
            # Generate unique code
            while True:
                code = RedeemCode.generate_code(length=length)
                if not RedeemCode.objects.filter(code=code).exists():
                    break

            # Create the redeem code
            redeem_code = RedeemCode.objects.create(
                code=code,
                plan=plan,
                status='active',
                expires_at=expires_at
            )
            generated_codes.append(redeem_code.code)

        # Display results
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully generated {count} redeem codes for "{plan.plan_name}"'))
        self.stdout.write(f'\nPlan: {plan.plan_name}')
        self.stdout.write(f'Tokens: {plan.tokens_included}')
        self.stdout.write(f'Billing Cycle: {plan.billing_cycle if hasattr(plan, "billing_cycle") else "N/A"}')
        
        if expires_at:
            self.stdout.write(f'Expires: {expires_at.strftime("%Y-%m-%d %H:%M:%S")}')
        else:
            self.stdout.write('Expires: Never')

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('\nGenerated Codes:'))
        self.stdout.write('=' * 50 + '\n')
        
        for idx, code in enumerate(generated_codes, 1):
            self.stdout.write(f'{idx:3d}. {code}')

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(f'\n💾 Codes saved to database and ready to redeem!')
        self.stdout.write(f'📋 Total codes generated: {count}\n')
