import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from companies.models import Company, Sector, CompanyRole, CompanyType


class Command(BaseCommand):
    help = "Import companies from an Excel file (companies.xlsx)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=r"C:\Users\ibrahim\Desktop\Zarailink\companies.xlsx",
            help="Path to the Excel file",
        )
        parser.add_argument(
            "--sheet",
            type=str,
            default=0,
            help="Sheet name or index (default: 0 for first sheet)",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        sheet_name = options["sheet"]

        # Convert any excel cell -> safe string (never None)
        def safe_str(val, default="N/A"):
            if pd.isna(val):
                return default
            s = str(val).strip()
            return s if s else default

        def safe_int(val, default=None):
            try:
                if pd.isna(val):
                    return default
                return int(val)
            except Exception:
                return default

        self.stdout.write(self.style.WARNING(f"Reading Excel file: {file_path}"))

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            self.stdout.write(self.style.SUCCESS(f"✓ Loaded {len(df)} rows from Excel"))
        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")
        except Exception as e:
            raise CommandError(f"Error reading Excel file: {str(e)}")

        # expected columns (based on what you showed)
        expected_columns = [
            "Company role",
            "Company type",
            "Company Name",
            "Country",
            "Year_established",
            "Number of employees",
            "Website",
            "Email",
            "Landline Numbers",
            "Address",
            "Description",
            "Sector",
        ]
        for c in expected_columns:
            if c not in df.columns:
                self.stdout.write(self.style.WARNING(f"⚠ Missing column in Excel: {c}"))

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        company_field_names = {f.name for f in Company._meta.fields}

        with transaction.atomic():
            for idx, row in df.iterrows():
                row_number = idx + 2  # excel row number-ish (header assumed row 1)

                try:
                    company_name = safe_str(row.get("Company Name", ""), default="").strip()
                    if not company_name:
                        skipped_count += 1
                        self.stdout.write(self.style.WARNING(f"Row {row_number}: Skipped (no Company Name)"))
                        continue

                    # Normalize role/type/sector/country
                    role_name = safe_str(row.get("Company role", "Buyer"), default="Buyer")
                    # optional: singularize Buyers/Suppliers
                    if role_name.lower() in ("buyers", "buyer"):
                        role_name = "Buyer"
                    elif role_name.lower() in ("suppliers", "supplier"):
                        role_name = "Supplier"

                    type_name = safe_str(row.get("Company type", "Unknown"), default="Unknown")
                    sector_name = safe_str(row.get("Sector", "Unknown"), default="Unknown")
                    country = safe_str(row.get("Country", "Unknown"), default="Unknown")

                    # These may be empty in excel -> force placeholders so DB never gets NULL
                    website = safe_str(row.get("Website", ""), default="N/A")
                    email = safe_str(row.get("Email", ""), default="N/A")
                    description = safe_str(row.get("Description", ""), default="N/A")
                    address = safe_str(row.get("Address", ""), default=country)

                    landline_numbers = safe_str(row.get("Landline Numbers", ""), default="N/A")

                    year_established = safe_int(row.get("Year_established"), default=None)
                    num_employees = row.get("Number of employees")
                    num_employees_str = safe_str(num_employees, default="N/A")

                    # Get/Create lookup tables
                    sector, _ = Sector.objects.get_or_create(name=sector_name)
                    company_role, _ = CompanyRole.objects.get_or_create(name=role_name)
                    company_type, _ = CompanyType.objects.get_or_create(name=type_name)

                    defaults = {
                        "country": country,
                        "sector": sector,
                        "company_role": company_role,
                        "company_type": company_type,
                    }

                    # Only set fields that actually exist in your Company model
                    if "year_established" in company_field_names:
                        defaults["year_established"] = year_established
                    if "number_of_employees" in company_field_names:
                        defaults["number_of_employees"] = num_employees_str
                    if "website" in company_field_names:
                        defaults["website"] = website
                    if "email" in company_field_names:
                        defaults["email"] = email
                    if "address" in company_field_names:
                        defaults["address"] = address
                    if "description" in company_field_names:
                        defaults["description"] = description
                    if "landline_numbers" in company_field_names:
                        defaults["landline_numbers"] = landline_numbers

                    company, created = Company.objects.update_or_create(
                        name=company_name,
                        defaults=defaults,
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Row {row_number}: ✓ Created '{company_name}' "
                                f"(Role: {role_name}, Type: {type_name}, Sector: {sector_name})"
                            )
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS(f"Row {row_number}: ✓ Updated '{company_name}'"))

                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f"Row {row_number}: ✗ Error: {str(e)}"))

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("Import Complete!"))
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"  Updated: {updated_count}"))
        self.stdout.write(self.style.WARNING(f"  Skipped: {skipped_count}"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"  Errors: {error_count}"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
