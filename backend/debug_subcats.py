
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import ProductSubCategory, Transaction

def check(term):
    with open('debug_output.txt', 'a') as f:
        f.write(f'\n--- Subcategories matching "{term}" ---\n')
        cats = ProductSubCategory.objects.filter(name__icontains=term)
        for c in cats:
            count = Transaction.objects.filter(product_item__sub_category=c).count()
            f.write(f'{c.id}: {c.name} - Tx Count: {count}\n')

if __name__ == "__main__":
    if os.path.exists('debug_output.txt'):
        os.remove('debug_output.txt')
    check('dextrose')
    check('fructose')
