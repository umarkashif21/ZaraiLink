import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from companies.models import Company, Sector, CompanyRole, CompanyType


class Command(BaseCommand):
    help = "Import companies from an Excel file (companies.xlsx)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=r'C:\Users\Dell\Desktop\zarailink\companies.xlsx',
            help='Path to the Excel file (default: companies.xlsx in project root)'
        )
        parser.add_argument(
            '--sheet',
            type=str,
            default=0,  # First sheet by default
            help='Sheet name or index (default: 0 for first sheet)'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        sheet_name = options['sheet']

        self.stdout.write(f"Reading Excel file: {file_path}")

        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            self.stdout.write(f"✓ Loaded {len(df)} rows from Excel")
        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")
        except Exception as e:
            raise CommandError(f"Error reading Excel file: {str(e)}")

        # Define column mapping (Excel column name → field name)
        # Adjust these based on your actual Excel column names
        column_mapping = {
            'Company Name': 'name',
            'Company Email': 'email',  # Not in Company model, but used for info
            'Contact details/Numbers': 'landline_numbers',
            'Sector': 'sector_name',
            'Country': 'country',
            'Year established': 'year_established',
            'Number of employees': 'number_of_employees',
            'Website': 'website',
            'Contact Level': 'contact_level',  # Used to determine role (Supplier/Buyer)
            'Description': 'description',
        }

        # Check for required columns
        for excel_col in column_mapping.keys():
            if excel_col not in df.columns:
                self.stdout.write(self.style.WARNING(f"⚠ Missing column: {excel_col}"))

        created_count = 0
        skipped_count = 0
        error_count = 0

        with transaction.atomic():
            for idx, row in df.iterrows():
                try:
                    # Extract data from row
                    company_name = row.get('Company Name', '').strip()
                    if not company_name:
                        self.stdout.write(self.style.WARNING(f"Row {idx + 2}: Skipped (no company name)"))
                        skipped_count += 1
                        continue

                    sector_name = row.get('Sector', '').strip() or 'Unknown'
                    country = row.get('Country', '').strip() or 'Unknown'
                    year_established = row.get('Year established')
                    number_of_employees = row.get('Number of employees')
                    website = row.get('Website', '').strip() or None
                    landline_numbers = row.get('Contact details/Numbers', '').strip() or None
                    description = row.get('Description', '').strip() or None
                    contact_level = row.get('Contact Level', '').strip().lower()

                    # Convert year to int if valid
                    try:
                        year_established = int(year_established) if pd.notna(year_established) else None
                    except (ValueError, TypeError):
                        year_established = None

                    # Determine company role based on contact level
                    # Assuming: "supplier" in contact level → Supplier role
                    #           otherwise → Buyer role
                    if 'supplier' in contact_level:
                        role_name = 'Supplier'
                        type_name = 'Sugar Mill'
                    else:
                        role_name = 'Buyer'
                        # Determine buyer type based on sector or other field
                        if 'pharma' in sector_name.lower():
                            type_name = 'Pharmaceuticals'
                        elif 'confect' in sector_name.lower():
                            type_name = 'Confectionary'
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
                            'number_of_employees': str(number_of_employees) if pd.notna(number_of_employees) else None,
                            'website': website,
                            'address': f"{country}",  # Placeholder: use country as address if no address field
                            'description': description,
                            'landline_numbers': landline_numbers,
                            'sector': sector,
                            'company_role': company_role,
                            'company_type': company_type,
                        }
                    )

                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Row {idx + 2}: ✓ Created '{company_name}' "
                                f"(Role: {role_name}, Type: {type_name}, Sector: {sector_name})"
                            )
                        )
                        created_count += 1
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Row {idx + 2}: ✓ Updated '{company_name}'"
                            )
                        )
                        created_count += 1

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f"Row {idx + 2}: ✗ Error: {str(e)}")
                    )

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS(f"Import Complete!"))
        self.stdout.write(self.style.SUCCESS(f"  Created/Updated: {created_count}"))
        self.stdout.write(self.style.WARNING(f"  Skipped: {skipped_count}"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"  Errors: {error_count}"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
