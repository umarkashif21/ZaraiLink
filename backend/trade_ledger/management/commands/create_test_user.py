from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import User

class Command(BaseCommand):
    help = 'Creates a test user with tokens for frontend testing'

    def handle(self, *args, **options):
        User = get_user_model()
        email = 'test@example.com'
        password = 'password123'
        
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
                'token_balance': 90000
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully created user {email}'))
        else:
            user.set_password(password)
            user.token_balance = 90000
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Updated existing user {email}'))
            
        self.stdout.write(f'Credentials: {email} / {password}')
