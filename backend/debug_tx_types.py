
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction

def check_types(subcat_id):
    with open('debug_output_types.txt', 'a') as f:
        f.write(f'\n--- Subcategory ID {subcat_id} ---\n')
        imports = Transaction.objects.filter(product_item__sub_category_id=subcat_id, trade_type='IMPORT').count()
        exports = Transaction.objects.filter(product_item__sub_category_id=subcat_id, trade_type='EXPORT').count()
        f.write(f'IMPORT: {imports}\n')
        f.write(f'EXPORT: {exports}\n')

if __name__ == "__main__":
    if os.path.exists('debug_output_types.txt'):
         os.remove('debug_output_types.txt')
    check_types(717) # Dextrose Anhydrous
    check_types(726) # Fructose
