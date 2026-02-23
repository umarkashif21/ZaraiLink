"""
Simple script to import companies from Excel file into the database.
Usage: python load_data.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

import pandas as pd
from companies.models import Company, Sector, CompanyRole, CompanyType, KeyContact
from django.db import transaction

# Configuration
EXCEL_FILE = r'C:\Users\Dell\Desktop\zarailink\companies.xlsx'
CONTACTS_FILE = r'C:\Users\Dell\Desktop\zarailink\keycontacts.xlsx'
SHEET_NAME = 0  # First sheet


def import_companies():
    """Import companies from Excel file"""
    
    print(f"📂 Reading Excel file: {EXCEL_FILE}")
    
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
        print(f"✓ Loaded {len(df)} rows from Excel\n")
    except FileNotFoundError:
        print(f"❌ Error: File not found: {EXCEL_FILE}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading Excel file: {str(e)}")
        sys.exit(1)

    # Print available columns for debugging
    print("📋 Available columns in Excel:")
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
                # Extract data from row (handle NaN values)
                def safe_str(val):
                    """Convert value to string, handle NaN/None"""
                    if pd.isna(val):
                        return ''
                    return str(val).strip()

                company_name = safe_str(row.get('Company Name', ''))
                if not company_name:
                    print(f"⊘ Row {idx + 2}: Skipped (no company name)")
                    skipped_count += 1
                    continue

                sector_name = safe_str(row.get('Sector', '')) or 'Unknown'
                country = safe_str(row.get('Country', '')) or 'Unknown'
                company_role = safe_str(row.get('Company role', '')).lower()  # From Excel
                company_type = safe_str(row.get('Company type', ''))  # From Excel
                year_established = row.get('Year_established')
                number_of_employees_raw = row.get('Number of employees')
                # Convert to string and truncate to 50 chars
                try:
                    if pd.notna(number_of_employees_raw):
                        number_of_employees = str(int(number_of_employees_raw))  # Clean integer
                    else:
                        number_of_employees = None
                except (ValueError, TypeError):
                    number_of_employees = None
                
                website = safe_str(row.get('Website', '')) or None
                if not website:
                    # website is required, so use a placeholder
                    website = 'https://example.com'  # Placeholder URL
                
                phone = safe_str(row.get('Landline Numbers', '')) or None  # Map to phone field
                # Truncate phone to 50 chars max
                if phone and len(phone) > 50:
                    phone = phone[:50]
                
                description = safe_str(row.get('Description', '')) or 'N/A'  # Default to 'N/A' if empty
                address = safe_str(row.get('Address', '')) or country

                # Convert year to int if valid
                try:
                    year_established = int(year_established) if pd.notna(year_established) else None
                except (ValueError, TypeError):
                    year_established = None

                # Use company_role and company_type from Excel directly
                # Normalize them for database lookup
                role_name = company_role.capitalize() if company_role else 'Supplier'  # Default to Supplier
                type_name = company_type.strip() if company_type else 'Sugar Mill'  # Default based on role
                
                # If type is empty, infer from role
                if not type_name or type_name == '':
                    if 'supplier' in role_name.lower():
                        type_name = 'Sugar Mill'
                    else:
                        type_name = 'Confectionary'  # Default buyer type

                # Get or create Sector
                sector, _ = Sector.objects.get_or_create(name=sector_name)

                # Get or create CompanyRole
                company_role, _ = CompanyRole.objects.get_or_create(name=role_name)

                # Get or create CompanyType
                company_type, _ = CompanyType.objects.get_or_create(name=type_name)

                # Create or update Company
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
                    print(f"✓ Row {idx + 2}: Created '{company_name}' | Role: {role_name} | Type: {type_name}")
                    created_count += 1
                else:
                    print(f"⟳ Row {idx + 2}: Updated '{company_name}'")
                    updated_count += 1

            except Exception as e:
                error_count += 1
                print(f"✗ Row {idx + 2}: Error: {str(e)}")

    # Summary
    print("\n" + "=" * 70)
    print("✓ IMPORT COMPLETE!")
    print(f"  Created:  {created_count}")
    print(f"  Updated:  {updated_count}")
    print(f"  Skipped:  {skipped_count}")
    if error_count > 0:
        print(f"  Errors:   {error_count}")
    print("=" * 70)


def import_contacts(sheet_name=0):
    """Import key contacts from separate Excel file"""
    
    print(f"\n📂 Reading contacts from file: {CONTACTS_FILE}")
    
    try:
        df = pd.read_excel(CONTACTS_FILE, sheet_name=sheet_name)
        print(f"✓ Loaded {len(df)} contact rows from Excel\n")
    except FileNotFoundError:
        print(f"❌ Error: File not found: {CONTACTS_FILE}")
        return
    except Exception as e:
        print(f"⚠️  Error reading contacts file: {str(e)}")
        return

    # Print available columns for debugging
    print("📋 Available columns in Contacts sheet:")
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
                    print(f"⊘ Row {idx + 2}: Skipped (missing company or name)")
                    skipped_count += 1
                    continue

                # Get the company - require exact match (case-insensitive)
                try:
                    company = Company.objects.get(name__iexact=company_name)
                except Company.DoesNotExist:
                    print(f"✗ Row {idx + 2}: Company '{company_name}' not found in database (exact match required)")
                    error_count += 1
                    continue

                designation = safe_str(row.get('Designation', '')) or None
                phone = safe_str(row.get('Phone', '')) or None
                whatsapp = safe_str(row.get('Whatsapp', '')) or None
                email = safe_str(row.get('Email', '')) or None

                # If phone is empty, use whatsapp as phone (since phone is required in DB)
                if not phone and whatsapp:
                    phone = whatsapp
                # If still no phone, use a placeholder
                if not phone:
                    phone = 'N/A'
                
                # If email is empty, create a placeholder (since email might be required)
                if not email:
                    email = f"contact_{idx}_{company.id}@example.com"

                # Truncate fields to model limits
                if designation and len(designation) > 150:
                    designation = designation[:150]
                if phone and len(phone) > 50:
                    phone = phone[:50]
                if whatsapp and len(whatsapp) > 50:
                    whatsapp = whatsapp[:50]
                if email and len(email) > 255:
                    email = email[:255]

                # Create or update KeyContact
                contact, created = KeyContact.objects.update_or_create(
                    company=company,
                    name=contact_name,
                    defaults={
                        'designation': designation,
                        'phone': phone,
                        'whatsapp': whatsapp,
                        'email': email,
                        'is_public': False,  # Default to private
                    }
                )

                if created:
                    print(f"✓ Row {idx + 2}: Created contact '{contact_name}' for '{company_name}'")
                    created_count += 1
                else:
                    print(f"⟳ Row {idx + 2}: Updated contact '{contact_name}'")

            except Exception as e:
                error_count += 1
                print(f"✗ Row {idx + 2}: Error: {str(e)}")

    # Summary
    print("\n" + "=" * 70)
    print("✓ CONTACTS IMPORT COMPLETE!")
    print(f"  Created:  {created_count}")
    print(f"  Skipped:  {skipped_count}")
    if error_count > 0:
        print(f"  Errors:   {error_count}")
    print("=" * 70)


if __name__ == '__main__':
    import_companies()
    import_contacts()  # Import contacts after companies
