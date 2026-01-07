import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from trade_lens.models import TradeLensProduct, TradeLensTransaction


class Command(BaseCommand):
    help = 'Seed Trade Lens with dummy data (Products and Transactions)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--records',
            type=int,
            default=10000,
            help='Number of transaction records to create (default: 10000)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding'
        )

    def handle(self, *args, **options):
        num_records = options['records']
        
        if options['clear']:
            self.stdout.write('Clearing existing Trade Lens data...')
            TradeLensTransaction.objects.all().delete()
            TradeLensProduct.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared all Trade Lens data.'))

        products_data = [
            {
                'name': 'Basmati Rice',
                'hs_code': '100630',
                'category': 'Cereals',
                'description': 'Premium long-grain aromatic rice from Punjab region',
                'price_range': (800, 1500),
                'qty_range': (50, 500),
            },
            {
                'name': 'Raw Cotton',
                'hs_code': '520100',
                'category': 'Textiles',
                'description': 'High-quality raw cotton for textile manufacturing',
                'price_range': (1200, 2000),
                'qty_range': (100, 1000),
            },
            {
                'name': 'Wheat',
                'hs_code': '100199',
                'category': 'Cereals',
                'description': 'Staple grain for flour and food production',
                'price_range': (250, 400),
                'qty_range': (200, 2000),
            },
            {
                'name': 'Mangoes',
                'hs_code': '080450',
                'category': 'Fruits',
                'description': 'Premium Pakistani mangoes including Sindhri and Chaunsa varieties',
                'price_range': (600, 1200),
                'qty_range': (20, 200),
            },
            {
                'name': 'Citrus Fruits',
                'hs_code': '080510',
                'category': 'Fruits',
                'description': 'Oranges, Kinno and other citrus from Punjab orchards',
                'price_range': (300, 600),
                'qty_range': (50, 400),
            },
            {
                'name': 'Surgical Instruments',
                'hs_code': '901890',
                'category': 'Medical Equipment',
                'description': 'Precision surgical instruments from Sialkot',
                'price_range': (5000, 15000),
                'qty_range': (5, 50),
            },
            {
                'name': 'Sports Goods',
                'hs_code': '950662',
                'category': 'Sports Equipment',
                'description': 'Footballs, cricket equipment and other sports goods',
                'price_range': (2000, 8000),
                'qty_range': (10, 100),
            },
            {
                'name': 'Leather Garments',
                'hs_code': '420310',
                'category': 'Leather Products',
                'description': 'High-quality leather jackets and garments',
                'price_range': (3000, 10000),
                'qty_range': (5, 80),
            },
        ]

        pakistani_provinces = [
            'Punjab', 'Sindh', 'Khyber Pakhtunkhwa', 'Balochistan', 
            'Gilgit-Baltistan', 'Azad Kashmir'
        ]

        ports = [
            'Karachi Port', 'Port Qasim', 'Gwadar Port', 
            'Lahore Dry Port', 'Faisalabad Dry Port', 'Peshawar Dry Port'
        ]

        countries = [
            ('United States', 0.15),
            ('China', 0.18),
            ('United Arab Emirates', 0.12),
            ('United Kingdom', 0.08),
            ('Germany', 0.07),
            ('Saudi Arabia', 0.10),
            ('Afghanistan', 0.08),
            ('Netherlands', 0.05),
            ('Italy', 0.04),
            ('Bangladesh', 0.06),
            ('Turkey', 0.04),
            ('Malaysia', 0.03),
        ]

        buyer_names = [
            'Global Agri Trading LLC', 'PrimeCotton International', 'EuroGrain GmbH',
            'Al-Haramain Traders', 'Pacific Foods Corp', 'MediSupply International',
            'SportsMart Global', 'LeatherWorld Inc', 'AgroExport Partners',
            'FreshFruit Distributors', 'Oriental Trading Co', 'Atlantic Commodities',
            'Gulf Import Solutions', 'Asian Trade Hub', 'Continental Exports Ltd',
            'Premier Foods Group', 'Quality Imports Inc', 'Delta Trade Services',
            'Summit Global Trading', 'Horizon International', 'Royal Commodities',
            'Excel Trade Partners', 'First Choice Imports', 'Golden Gate Trading',
            'Sunrise Exports LLC', 'United Commerce Group', 'Prime Select Trading',
        ]

        seller_names = [
            'Punjab Agricultural Corp', 'Sindh Farmers Cooperative', 'Pakistan Rice Mills',
            'Multan Cotton Exchange', 'Sialkot Surgical Industries', 'Lahore Leather Works',
            'Karachi Export House', 'Faisalabad Textile Mills', 'Peshawar Fruit Growers',
            'Hyderabad Mango Farms', 'Gujranwala Sports Manufacturing', 'Rawalpindi Trade Center',
            'Quetta Dry Fruits Ltd', 'Sargodha Citrus Farms', 'Jhang Cotton Mills',
            'Sahiwal Agro Products', 'Bahawalpur Rice Traders', 'Sukkur Wheat Exchange',
            'Mirpur Leather Goods', 'Abbottabad Fresh Produce', 'Mardan Agricultural Co',
        ]

        self.stdout.write('Creating products...')
        products = []
        for p_data in products_data:
            product, created = TradeLensProduct.objects.get_or_create(
                hs_code=p_data['hs_code'],
                defaults={
                    'name': p_data['name'],
                    'category': p_data['category'],
                    'description': p_data['description'],
                }
            )
            products.append({
                'product': product,
                'price_range': p_data['price_range'],
                'qty_range': p_data['qty_range'],
                'created': created,
            })
            if created:
                self.stdout.write(f'  Created: {product.name}')
            else:
                self.stdout.write(f'  Exists: {product.name}')

        self.stdout.write(f'\nGenerating {num_records} transaction records...')
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=730)
        
        transactions = []
        for i in range(num_records):
            product_info = random.choice(products)
            product = product_info['product']
            
            trade_date = start_date + timedelta(days=random.randint(0, 730))
            
            price_min, price_max = product_info['price_range']
            month_offset = (trade_date - start_date).days // 30
            seasonal_factor = 1 + 0.1 * random.uniform(-1, 1) * (1 + 0.02 * month_offset)
            price = Decimal(str(round(random.uniform(price_min, price_max) * seasonal_factor, 2)))
            
            qty_min, qty_max = product_info['qty_range']
            quantity = Decimal(str(round(random.uniform(qty_min, qty_max), 2)))
            
            country = random.choices(
                [c[0] for c in countries],
                weights=[c[1] for c in countries]
            )[0]
            
            trade_type = random.choice(['IMPORT', 'EXPORT'])
            if trade_type == 'EXPORT':
                buyer_country = country
                seller_country = 'Pakistan'
            else:
                buyer_country = 'Pakistan'
                seller_country = country
            
            transaction = TradeLensTransaction(
                product=product,
                trade_date=trade_date,
                price_usd=price,
                quantity_mt=quantity,
                total_value_usd=price * quantity,
                buyer_name=random.choice(buyer_names),
                seller_name=random.choice(seller_names),
                buyer_country=buyer_country,
                seller_country=seller_country,
                port=random.choice(ports),
                province=random.choice(pakistani_provinces),
                trade_type=trade_type,
                hs_code=product.hs_code,
            )
            transactions.append(transaction)
            
            if (i + 1) % 1000 == 0:
                TradeLensTransaction.objects.bulk_create(transactions)
                self.stdout.write(f'  Progress: {i + 1}/{num_records} records created')
                transactions = []
        
        if transactions:
            TradeLensTransaction.objects.bulk_create(transactions)
        
        total_products = TradeLensProduct.objects.count()
        total_transactions = TradeLensTransaction.objects.count()
        
        self.stdout.write(self.style.SUCCESS(
            f'\nSeeding complete!'
            f'\n  Products: {total_products}'
            f'\n  Transactions: {total_transactions}'
        ))
