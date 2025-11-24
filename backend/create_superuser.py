import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(email='admin@zarailink.com').exists():
    User.objects.create_superuser('admin', 'admin@zarailink.com', 'adminpassword')
    print('Superuser created successfully.')
else:
    print('Superuser already exists.')
