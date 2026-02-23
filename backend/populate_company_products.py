import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from companies.models import Company, CompanyProduct
from trade_data.models import Transaction
from django.db import transaction

def populate_products():
    print("Deleting all existing CompanyProducts...")
    CompanyProduct.objects.all().delete()
    print("Done. Fetching unique company-product combinations from transactions...")

    companies = {c.name.lower(): c for c in Company.objects.all()}
    
    # company_id -> hs_code -> subcategory_name
    products_to_add = {}
    
    # We join all the way to sub_category to get the clean name (e.g., "Dextrose Anhydrous")
    transactions = Transaction.objects.select_related('product_item__sub_category').values(
        'buyer', 'seller', 'hs_code', 'product_item__sub_category__name'
    ).iterator(chunk_size=1000)
    
    for count, tx in enumerate(transactions):
        if count % 50000 == 0:
            print(f"Processed {count} transactions...")
            
        buyer_name = (tx['buyer'] or '').lower().strip()
        seller_name = (tx['seller'] or '').lower().strip()
        
        hs_code = tx['hs_code'] or ''
        clean_name = tx['product_item__sub_category__name'] or 'Unknown Product'
        
        for name, company in [(buyer_name, companies.get(buyer_name)), (seller_name, companies.get(seller_name))]:
            if company:
                if company.id not in products_to_add:
                    products_to_add[company.id] = {}
                
                # By tying to sub_category name, we get a consistent clean name per HS code
                products_to_add[company.id][hs_code] = clean_name

    new_products = []
    for comp_id, hs_dict in products_to_add.items():
        comp = Company.objects.get(id=comp_id)
        for hs, clean_name in hs_dict.items():
            new_products.append(CompanyProduct(
                company=comp,
                name=clean_name[:255],
                hsn_code=hs[:20]
            ))

    print(f"Total clean, deduped products found for companies: {len(new_products)}")
    print("Bulk creating products in database...")
    
    # Bulk create in chunks
    CompanyProduct.objects.bulk_create(new_products, batch_size=5000)
    
    print(f"Successfully created {CompanyProduct.objects.count()} CompanyProduct records.")

if __name__ == '__main__':
    populate_products()
