from trade_data.models import Transaction
t = Transaction.objects.filter(seller__icontains='Tereos').first()
if t:
    print('Tereos is under:', t.product_item.sub_category.name)
    print('HS:', t.product_item.sub_category.hs_code)
    print('ID:', t.product_item.sub_category.id)
else:
    print('Not found')
