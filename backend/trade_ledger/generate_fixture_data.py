"""
Trade Ledger Fixture Data Generator

This script creates realistic trade intelligence data for testing.
Run with: python manage.py shell < trade_ledger/generate_fixture_data.py

Or manually execute after making sure trade_ledger is migrated.
"""

import random
from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction
from companies.models import Company
from trade_ledger.models import (
    ProductCategory, TradeCompany, TradeProduct,
    TradePartner, TradeTrend
)


PARTNER_COUNTRIES = [
    ('UAE', ['Jebel Ali', 'Dubai Port', 'Abu Dhabi Port']),
    ('Saudi Arabia', ['Jeddah Islamic Port', 'King Abdullah Port', 'Dammam Port']),
    ('China', ['Shanghai Port', 'Shenzhen Port', 'Guangzhou Port']),
    ('USA', ['Los Angeles Port', 'New York Port', 'Houston Port']),
    ('UK', ['London Gateway', 'Southampton Port', 'Felixstowe']),
    ('Afghanistan', ['Karachi Port', 'Torkham Border', 'Chaman Border']),
    ('Iran', ['Gwadar Port', 'Chabahar Port']),
    ('Sri Lanka', ['Colombo Port']),
    ('Bangladesh', ['Chittagong Port', 'Mongla Port']),
    ('Malaysia', ['Port Klang', 'Penang Port']),
]

COMPANY_REFERENCES = [
    ('Al-Noor Rice Mills', 'Rice', True, False),
    ('Sindh Agricultural Exports', 'Mixed', True, True),
    ('Lahore Grain Traders', 'Grains', True, False),
    ('Karachi Fresh Exports', 'Fruits & Vegetables', True, False),
    ('Punjab Cotton Mills', 'Cotton', True, False),
    ('Pakistan Agricultural Solutions', 'Mixed', True, True),
    ('Multan Agro Products', 'Fruits', True, False),
    ('Faisalabad Textile & Cotton', 'Cotton', True, False),
    ('Hyderabad Rice Corporation', 'Rice', True, False),
    ('Peshawar Dry Fruits Co.', 'Dry Fruits', True, False),
    ('Gujranwala Vegetable Exports', 'Vegetables', True, False),
    ('Sialkot International Trade', 'Mixed', True, True),
    ('Rawalpindi Grain Suppliers', 'Grains', False, True),
    ('Quetta Agricultural Hub', 'Fruits', True, False),
    ('Sukkur Rice Mills Ltd.', 'Rice', True, False),
]


def clear_existing_data():
    """Clear existing trade ledger data"""
    print("Clearing existing trade ledger data...")
    TradeTrend.objects.all().delete()
    TradePartner.objects.all().delete()
    TradeProduct.objects.all().delete()
    TradeCompany.objects.all().delete()
    ProductCategory.objects.all().delete()
    print("✓ Cleared existing data")


def create_product_categories():
    """Create all product categories"""
    print("\nCreating product categories...")
    
    categories_data = [
        {"id": 1, "name": "Basmati Rice", "hs_code": "1006.30", "description": "Premium long-grain aromatic rice"},
        {"id": 2, "name": "Non-Basmati Rice", "hs_code": "1006.10", "description": "Standard rice varieties"},
        {"id": 3, "name": "Kinnow (Citrus)", "hs_code": "0805.21", "description": "Pakistani citrus fruit"},
        {"id": 4, "name": "Mango", "hs_code": "0804.50", "description": "Fresh mangoes"},
        {"id": 5, "name": "Potato", "hs_code": "0701.90", "description": "Fresh potatoes"},
        {"id": 6, "name": "Onion", "hs_code": "0703.10", "description": "Fresh onions"},
        {"id": 7, "name": "Cotton", "hs_code": "5201.00", "description": "Raw cotton"},
        {"id": 8, "name": "Wheat", "hs_code": "1001.99", "description": "Wheat grain"},
        {"id": 9, "name": "Dates", "hs_code": "0804.10", "description": "Fresh or dried dates"},
        {"id": 10, "name": "Spices", "hs_code": "0910.99", "description": "Various spices"},
    ]
    
    created_count = 0
    for cat_data in categories_data:
        category, created = ProductCategory.objects.get_or_create(
            id=cat_data["id"],
            defaults={
                "name": cat_data["name"],
                "hs_code": cat_data["hs_code"],
                "description": cat_data["description"]
            }
        )
        if created:
            created_count += 1
    
    print(f"✓ Created {created_count} product categories")
    return created_count


@transaction.atomic
def generate_trade_companies():
    """Generate TradeCompany entries"""
    print("\nGenerating trade companies...")
    
    
    companies = []
    for name, sector_name, is_exporter, is_importer in COMPANY_REFERENCES:
        company, created = Company.objects.get_or_create(
            name=name,
            defaults={
                'country': 'Pakistan',
                'province': random.choice(['Punjab', 'Sindh', 'KPK', 'Balochistan']),
                'verification_status': 'verified',
                'has_trade_data': True,
                'year_established': random.randint(1990, 2020),
            }
        )
        
        
        trade_company, tc_created = TradeCompany.objects.get_or_create(
            company=company,
            defaults={
                'estimated_revenue': Decimal(random.uniform(500000, 50000000)),
                'trade_volume': Decimal(random.uniform(300000, 40000000)),
                'active_since': date(random.randint(1995, 2018), random.randint(1, 12), 1),
                'is_exporter': is_exporter,
                'is_importer': is_importer,
            }
        )
        companies.append((trade_company, sector_name))
        
    print(f"✓ Created {len(companies)} trade companies")
    return companies


def generate_trade_products(companies):
    """Generate TradeProduct entries"""
    print("\nGenerating trade products...")
    
    categories = {
        'Rice': [1, 2],  
        'Fruits': [3, 4, 9],  
        'Fruits & Vegetables': [3, 4, 5, 6],  
        'Vegetables': [5, 6],  
        'Cotton': [7],
        'Grains': [8, 2],  
        'Dry Fruits': [9],
        'Mixed': [1, 3, 5, 8, 10],  
    }
    
    all_products = []
    for trade_company, sector_name in companies:
        category_ids = categories.get(sector_name, [1, 5, 8])
        num_products = random.randint(2, 5)
        
        for _ in range(num_products):
            category_id = random.choice(category_ids)
            category = ProductCategory.objects.get(pk=category_id)
            
            product = TradeProduct.objects.create(
                company=trade_company,
                category=category,
                product_name=f"{category.name} - {random.choice(['Premium', 'Standard', 'Super', 'Grade A'])}",
                hs_code=category.hs_code,
                avg_price=Decimal(random.uniform(200, 2000)),
                currency='USD',
                volume=Decimal(random.uniform(1000, 500000)),
                unit=random.choice(['ton', 'kg', 'container']),
                yoy_growth=Decimal(random.uniform(-15, 35)),
            )
            all_products.append(product)
    
    print(f"✓ Created {len(all_products)} trade products")
    return all_products


def generate_trade_partners(companies):
    """Generate TradePartner entries"""
    print("\nGenerating trade partners...")
    
    all_partners = []
    for trade_company, _ in companies:
        num_partners = random.randint(3, 8)
        selected_countries = random.sample(PARTNER_COUNTRIES, min(num_partners, len(PARTNER_COUNTRIES)))
        
        total_volume = float(trade_company.trade_volume)
        remaining = 100.0
        
        for i, (country, ports) in enumerate(selected_countries):
            is_last = (i == len(selected_countries) - 1)
            percentage = remaining if is_last else random.uniform(5, min(35, remaining - 5 * (len(selected_countries) - i - 1)))
            remaining -= percentage
            
            partner = TradePartner.objects.create(
                company=trade_company,
                country=country,
                port_name=random.choice(ports),
                trade_volume=Decimal(total_volume * percentage / 100),
                percentage_share=Decimal(percentage),
                is_export=trade_company.is_exporter,
            )
            all_partners.append(partner)
    
    print(f"✓ Created {len(all_partners)} trade partners")
    return all_partners


def generate_trade_trends(companies, products):
    """Generate TradeTrend entries for past 24 months"""
    print("\nGenerating trade trends (this may take a moment)...")
    
    trends_created = 0
    current_date = date.today()
    
    for trade_company, _ in companies:
        company_products = [p for p in products if p.company == trade_company]
        
        if not company_products:
            continue
        
        
        for months_ago in range(24):
            trend_date = current_date - timedelta(days=30 * months_ago)
            month = trend_date.month
            year = trend_date.year
            
            
            for product in random.sample(company_products, min(2, len(company_products))):
                base_volume = float(product.volume) / 12  
                base_price = float(product.avg_price)
                
                
                seasonal_factor = 1 + 0.2 * random.uniform(-1, 1)
                volume = Decimal(base_volume * seasonal_factor)
                price = Decimal(base_price * (1 + 0.1 * random.uniform(-1, 1)))
                
                
                yoy_vol_growth = Decimal(random.uniform(-10, 25)) if months_ago < 12 else None
                yoy_price_growth = Decimal(random.uniform(-5, 15)) if months_ago < 12 else None
                
                TradeTrend.objects.create(
                    company=trade_company,
                    product=product,
                    month=month,
                    year=year,
                    volume=volume,
                    avg_price=price,
                    yoy_volume_growth=yoy_vol_growth,
                    yoy_price_growth=yoy_price_growth,
                )
                trends_created += 1
    
    print(f"✓ Created {trends_created} trade trend records")
    return trends_created


def main():
    """Main execution function"""
    print("=" * 60)
    print("TRADE LEDGER FIXTURE DATA GENERATOR")
    print("=" * 60)
    
    
    clear_existing_data()
    
    
    create_product_categories()
    
    
    companies = generate_trade_companies()
    products = generate_trade_products(companies)
    partners = generate_trade_partners(companies)
    trends = generate_trade_trends(companies, products)
    
    print("\n" + "=" * 60)
    print("DATA GENERATION COMPLETE!")
    print("=" * 60)
    print(f"✓ {len(companies)} Trade Companies")
    print(f"✓ {len(products)} Trade Products")
    print(f"✓ {len(partners)} Trade Partners")
    print(f"✓ {trends} Trade Trends")
    print("\nYou can now access the Trade Intelligence features!")
    print("=" * 60)


if __name__ == '__main__':
    main()
