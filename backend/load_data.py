"""
Simple script to import companies from Excel file into the database.
Usage: python load_data.py
"""

import os
import sys
import django
from pathlib import Path


sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

import pandas as pd
from companies.models import Company, Sector, CompanyRole, CompanyType, KeyContact
from django.db import transaction


BASE_DIR = Path(__file__).resolve().parent
EXCEL_FILE = os.path.join(BASE_DIR, 'companies.xlsx')
CONTACTS_FILE = os.path.join(BASE_DIR, 'keycontacts.xlsx')
print(EXCEL_FILE, CONTACTS_FILE)
SHEET_NAME = 0  


def import_companies():
    """Import companies from Excel file"""
    
    print(f"Reading Excel file: {EXCEL_FILE}")
    
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
        print(f"Loaded {len(df)} rows from Excel\n")
    except FileNotFoundError:
        print(f"Error: File not found: {EXCEL_FILE}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        sys.exit(1)

    
    print("Available columns in Excel:")
    for col in df.columns:
        print(f"   - {col}")
    print()

    created_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0

    with transaction.atomic():
        for idx, row in df.iterrows():
            try:
                
                def safe_str(val):
                    """Convert value to string, handle NaN/None"""
                    if pd.isna(val):
                        return ''
                    return str(val).strip()

                company_name = safe_str(row.get('Company Name', ''))
                if not company_name:
                    print(f"Row {idx + 2}: Skipped (no company name)")
                    skipped_count += 1
                    continue

                sector_name = safe_str(row.get('Sector', '')) or 'Unknown'
                country = safe_str(row.get('Country', '')) or 'Unknown'
                company_role = safe_str(row.get('Company role', '')).lower()  
                company_type = safe_str(row.get('Company type', ''))  
                year_established = row.get('Year_established')
                number_of_employees_raw = row.get('Number of employees')
                
                try:
                    if pd.notna(number_of_employees_raw):
                        number_of_employees = str(int(number_of_employees_raw))  
                    else:
                        number_of_employees = None
                except (ValueError, TypeError):
                    number_of_employees = None
                
                website = safe_str(row.get('Website', '')) or None
                if not website:
                    
                    website = 'https://example.com'  
                
                phone = safe_str(row.get('Landline Numbers', '')) or None  
                
                if phone and len(phone) > 50:
                    phone = phone[:50]
                
                description = safe_str(row.get('Description', '')) or 'N/A'  
                address = safe_str(row.get('Address', '')) or country

                
                try:
                    year_established = int(year_established) if pd.notna(year_established) else None
                except (ValueError, TypeError):
                    year_established = None

                
                
                role_name = company_role.capitalize() if company_role else 'Supplier'  
                type_name = company_type.strip() if company_type else 'Sugar Mill'  
                
                
                if not type_name or type_name == '':
                    if 'supplier' in role_name.lower():
                        type_name = 'Sugar Mill'
                    else:
                        type_name = 'Confectionary'  

                
                sector, _ = Sector.objects.get_or_create(name=sector_name)

                
                company_role, _ = CompanyRole.objects.get_or_create(name=role_name)

                
                company_type, _ = CompanyType.objects.get_or_create(name=type_name)

                
                company, created = Company.objects.update_or_create(
                    name=company_name,
                    defaults={
                        'country': country,
                        'year_established': year_established,
                        'number_of_employees': number_of_employees if number_of_employees else None,
                        'website': website,
                        'address': address,
                        'description': description,
                        'phone': phone,
                        'sector': sector,
                        'company_role': company_role,
                        'company_type': company_type,
                    }
                )

                if created:
                    print(f"Row {idx + 2}: Created '{company_name}' | Role: {role_name} | Type: {type_name}")
                    created_count += 1
                else:
                    print(f"Row {idx + 2}: Updated '{company_name}'")
                    updated_count += 1

            except Exception as e:
                error_count += 1
                print(f"Row {idx + 2}: Error: {str(e)}")

    
    print("\n" + "=" * 70)
    print("IMPORT COMPLETE!")
    print(f"  Created:  {created_count}")
    print(f"  Updated:  {updated_count}")
    print(f"  Skipped:  {skipped_count}")
    if error_count > 0:
        print(f"  Errors:   {error_count}")
    print("=" * 70)


def import_contacts(sheet_name=0):
    """Import key contacts from separate Excel file"""
    
    print(f"\nReading contacts from file: {CONTACTS_FILE}")
    
    try:
        df = pd.read_excel(CONTACTS_FILE, sheet_name=sheet_name)
        print(f"Loaded {len(df)} contact rows from Excel\n")
    except FileNotFoundError:
        print(f"Error: File not found: {CONTACTS_FILE}")
        return
    except Exception as e:
        print(f"Error reading contacts file: {str(e)}")
        return

    
    print("Available columns in Contacts sheet:")
    for col in df.columns:
        print(f"   - {col}")
    print()

    created_count = 0
    skipped_count = 0
    error_count = 0

    def safe_str(val):
        """Convert value to string, handle NaN/None"""
        if pd.isna(val):
            return ''
        return str(val).strip()

    with transaction.atomic():
        for idx, row in df.iterrows():
            try:
                company_name = safe_str(row.get('Company', ''))
                contact_name = safe_str(row.get('Name', ''))
                
                if not company_name or not contact_name:
                    print(f"Row {idx + 2}: Skipped (missing company or name)")
                    skipped_count += 1
                    continue

                
                try:
                    company = Company.objects.get(name__iexact=company_name)
                except Company.DoesNotExist:
                    print(f"Row {idx + 2}: Company '{company_name}' not found in database (exact match required)")
                    error_count += 1
                    continue

                designation = safe_str(row.get('Designation', '')) or None
                phone = safe_str(row.get('Phone', '')) or None
                whatsapp = safe_str(row.get('Whatsapp', '')) or None
                email = safe_str(row.get('Email', '')) or None

                
                if not phone and whatsapp:
                    phone = whatsapp
                
                if not phone:
                    phone = 'N/A'
                
                
                if not email:
                    email = f"contact_{idx}_{company.id}@example.com"

                
                if designation and len(designation) > 150:
                    designation = designation[:150]
                if phone and len(phone) > 50:
                    phone = phone[:50]
                if whatsapp and len(whatsapp) > 50:
                    whatsapp = whatsapp[:50]
                if email and len(email) > 255:
                    email = email[:255]

                
                contact, created = KeyContact.objects.update_or_create(
                    company=company,
                    name=contact_name,
                    defaults={
                        'designation': designation,
                        'phone': phone,
                        'whatsapp': whatsapp,
                        'email': email,
                        'is_public': False,  
                    }
                )

                if created:
                    print(f"Row {idx + 2}: Created contact '{contact_name}' for '{company_name}'")
                    created_count += 1
                else:
                    print(f"Row {idx + 2}: Updated contact '{contact_name}'")

            except Exception as e:
                error_count += 1
                print(f"Row {idx + 2}: Error: {str(e)}")

    
    print("\n" + "=" * 70)
    print("CONTACTS IMPORT COMPLETE!")
    print(f"  Created:  {created_count}")
    print(f"  Skipped:  {skipped_count}")
    if error_count > 0:
        print(f"  Errors:   {error_count}")
    print("=" * 70)


if __name__ == '__main__':
    import_companies()
    import_contacts()  
