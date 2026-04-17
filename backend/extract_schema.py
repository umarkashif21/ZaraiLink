import os
import json
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from django.apps import apps
out = {}
for app in apps.get_app_configs():
    if not app.label.startswith('auth') and not app.label.startswith('django') and app.label not in ['admin', 'contenttypes', 'sessions', 'auditlog', 'corsheaders', 'django_ckeditor_5', 'rest_framework']:
        for model in app.get_models():
            fields = []
            rels = []
            for f in model._meta.get_fields():
                if f.is_relation and (f.one_to_one or f.many_to_one or f.many_to_many or f.one_to_many):
                    rel_type = 'One-to-One' if f.one_to_one else 'Many-to-One' if f.many_to_one else 'One-to-Many' if f.one_to_many else 'Many-to-Many'
                    related_model = f.related_model._meta.object_name if getattr(f, 'related_model', None) else str(f.name)
                    rels.append(f'{rel_type} with {related_model}')
                    if hasattr(f, 'column'):
                        fields.append({'name': f.name, 'type': f.__class__.__name__, 'null': getattr(f, 'null', False), 'primary_key': getattr(f, 'primary_key', False), 'unique': getattr(f, 'unique', False), 'is_fk': True, 'related': related_model})
                elif hasattr(f, 'column'):
                    fields.append({'name': f.name, 'type': f.__class__.__name__, 'null': getattr(f, 'null', False), 'primary_key': getattr(f, 'primary_key', False), 'unique': getattr(f, 'unique', False), 'is_fk': False})
            
            out[model._meta.object_name] = {'app': app.label, 'fields': fields, 'rels': rels, 'desc': model.__doc__.strip() if model.__doc__ else ''}

with open('schema_dump.json', 'w') as f:
    json.dump(out, f, indent=2)
