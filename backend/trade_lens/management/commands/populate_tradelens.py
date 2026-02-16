"""
Management command to populate TradeLens tables from Excel files.

Reads import_data_1year.xlsx and export_data.xlsx, creates:
- TradeLensProduct: one per distinct Sub-Category name
- TradeLensTransaction: one per Excel row, linked to its product
"""

import os
import pandas as pd
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from trade_lens.models import TradeLensProduct, TradeLensTransaction


class Command(BaseCommand):
    help = "Populate TradeLens tables from import/export Excel files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--import-file",
            type=str,
            default=None,
            help="Path to import_data_1year.xlsx",
        )
        parser.add_argument(
            "--export-file",
            type=str,
            default=None,
            help="Path to export_data.xlsx",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing TradeLens data before populating",
        )

    def handle(self, *args, **options):
        import_file = options["import_file"]
        export_file = options["export_file"]

        # Auto-detect files if not specified
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )))  # Goes up to ZaraiLink root
        
        if not import_file:
            candidate = os.path.join(base_dir, "import_data_1year.xlsx")
            if os.path.exists(candidate):
                import_file = candidate
            else:
                # Try parent directory
                candidate = os.path.join(os.path.dirname(base_dir), "import_data_1year.xlsx")
                if os.path.exists(candidate):
                    import_file = candidate

        if not export_file:
            candidate = os.path.join(base_dir, "export_data.xlsx")
            if os.path.exists(candidate):
                export_file = candidate
            else:
                candidate = os.path.join(os.path.dirname(base_dir), "export_data.xlsx")
                if os.path.exists(candidate):
                    export_file = candidate

        if not import_file and not export_file:
            self.stderr.write(self.style.ERROR(
                "No Excel files found. Use --import-file and --export-file to specify paths."
            ))
            return

        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing TradeLens data..."))
            TradeLensTransaction.objects.all().delete()
            TradeLensProduct.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared."))

        # Track products by (sub_category_name, hs_code) to avoid duplicates
        product_cache = {}
        total_transactions = 0

        # Process import file
        if import_file and os.path.exists(import_file):
            self.stdout.write(self.style.WARNING(f"Reading IMPORT file: {import_file}"))
            count = self._process_file(import_file, "IMPORT", product_cache)
            total_transactions += count
            self.stdout.write(self.style.SUCCESS(f"  -> {count} IMPORT transactions created"))
        else:
            self.stdout.write(self.style.WARNING(f"Import file not found: {import_file}"))

        # Process export file
        if export_file and os.path.exists(export_file):
            self.stdout.write(self.style.WARNING(f"Reading EXPORT file: {export_file}"))
            count = self._process_file(export_file, "EXPORT", product_cache)
            total_transactions += count
            self.stdout.write(self.style.SUCCESS(f"  -> {count} EXPORT transactions created"))
        else:
            self.stdout.write(self.style.WARNING(f"Export file not found: {export_file}"))

        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*50}\n"
            f"DONE! Created:\n"
            f"  TradeLensProducts:     {len(product_cache)}\n"
            f"  TradeLensTransactions: {total_transactions}\n"
            f"{'='*50}"
        ))

    def _process_file(self, file_path, trade_type, product_cache):
        """Process a single Excel file and create TradeLens records."""
        df = pd.read_excel(file_path, header=6)
        df.columns = df.columns.str.strip().str.replace(" ", "_")

        # Normalize column names to handle differences between import/export
        col_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if col_lower == "date":
                col_map["date"] = col
            elif col_lower == "hs_code":
                col_map["hs_code"] = col
            elif col_lower == "category":
                col_map["category"] = col
            elif col_lower in ("sub-category", "sub_category"):
                col_map["sub_category"] = col
            elif col_lower == "item_description":
                col_map["item_description"] = col
            elif col_lower == "buyer":
                col_map["buyer"] = col
            elif col_lower == "seller":
                col_map["seller"] = col
            elif col_lower == "shipping_agents":
                col_map["shipping_agents"] = col
            elif col_lower == "country":
                col_map["country"] = col
            elif col_lower == "qty_kg":
                col_map["qty_kg"] = col
            elif col_lower == "qty_mt":
                col_map["qty_mt"] = col
            elif col_lower in ("usd/kg", "usd_kg"):
                col_map["usd_kg"] = col
            elif col_lower in ("usd/mt", "usd_mt"):
                col_map["usd_mt"] = col
            elif col_lower == "pkr":
                col_map["pkr"] = col
            elif col_lower == "usd":
                col_map["usd"] = col

        required = ["date", "hs_code", "category", "sub_category", "buyer", "seller", "country"]
        missing = [r for r in required if r not in col_map]
        if missing:
            self.stderr.write(self.style.ERROR(f"Missing columns: {missing}"))
            return 0

        transactions_to_create = []
        skipped = 0

        with db_transaction.atomic():
            for idx, row in df.iterrows():
                # Skip rows with no date
                date_val = row[col_map["date"]]
                if pd.isna(date_val):
                    skipped += 1
                    continue

                try:
                    trade_date = pd.to_datetime(date_val).date()
                except Exception:
                    skipped += 1
                    continue

                # Extract fields
                hs_code = str(row[col_map["hs_code"]]).strip()
                category = str(row[col_map["category"]]).strip()
                sub_category = str(row[col_map["sub_category"]]).strip()
                buyer = str(row[col_map["buyer"]]).strip() if pd.notna(row[col_map["buyer"]]) else "Unknown"
                seller = str(row[col_map["seller"]]).strip() if pd.notna(row[col_map["seller"]]) else "Unknown"
                country = str(row[col_map["country"]]).strip() if pd.notna(row[col_map["country"]]) else "Unknown"

                # Skip invalid sub-categories
                if not sub_category or sub_category.lower() in ("nan", ""):
                    skipped += 1
                    continue

                # Get or create TradeLensProduct
                product_key = (sub_category, hs_code)
                if product_key not in product_cache:
                    product, created = TradeLensProduct.objects.get_or_create(
                        name=sub_category,
                        hs_code=hs_code,
                        defaults={
                            "category": category,
                            "description": f"{sub_category} (HS: {hs_code})",
                        }
                    )
                    product_cache[product_key] = product
                    if created:
                        self.stdout.write(f"  + Product: {sub_category} ({hs_code})")

                product = product_cache[product_key]

                # Parse numeric fields safely
                qty_mt = self._safe_decimal(row.get(col_map.get("qty_mt"), 0))
                usd_mt = self._safe_decimal(row.get(col_map.get("usd_mt"), 0))
                usd_total = self._safe_decimal(row.get(col_map.get("usd"), 0))

                # Price: prefer usd/mt, fall back to computing from total
                price = usd_mt
                if (not price or price == 0) and qty_mt and qty_mt > 0 and usd_total:
                    price = usd_total / qty_mt

                # Total value: prefer explicit, fall back to price * qty
                total_value = usd_total
                if (not total_value or total_value == 0) and price and qty_mt:
                    total_value = price * qty_mt

                # Direction logic
                if trade_type == "IMPORT":
                    seller_country = country  # Goods come FROM this country
                    buyer_country = "Pakistan"
                    buyer_name = buyer
                    seller_name = seller
                else:  # EXPORT
                    seller_country = "Pakistan"
                    buyer_country = country  # Goods go TO this country
                    buyer_name = buyer
                    seller_name = seller

                # Port / Province: extract from item_description if available
                item_desc = str(row.get(col_map.get("item_description", ""), "")).strip()
                port = self._extract_port(item_desc, country)
                province = self._extract_province(buyer_name if trade_type == "EXPORT" else seller_name)

                tx = TradeLensTransaction(
                    product=product,
                    trade_date=trade_date,
                    price_usd=price or Decimal("0"),
                    quantity_mt=qty_mt or Decimal("0"),
                    total_value_usd=total_value or Decimal("0"),
                    buyer_name=buyer_name,
                    seller_name=seller_name,
                    buyer_country=buyer_country,
                    seller_country=seller_country,
                    port=port,
                    province=province,
                    trade_type=trade_type,
                    hs_code=hs_code,
                )
                transactions_to_create.append(tx)

            # Bulk create in batches
            batch_size = 1000
            created_count = 0
            for i in range(0, len(transactions_to_create), batch_size):
                batch = transactions_to_create[i:i + batch_size]
                TradeLensTransaction.objects.bulk_create(batch)
                created_count += len(batch)
                self.stdout.write(f"  Batch {i // batch_size + 1}: {created_count}/{len(transactions_to_create)}")

        if skipped:
            self.stdout.write(self.style.WARNING(f"  Skipped {skipped} invalid rows"))

        return len(transactions_to_create)

    def _safe_decimal(self, value):
        """Safely convert a value to Decimal."""
        if pd.isna(value) if isinstance(value, float) else value is None:
            return Decimal("0")
        try:
            return Decimal(str(value).strip().replace(",", ""))
        except (InvalidOperation, ValueError):
            return Decimal("0")

    def _extract_port(self, item_desc, country):
        """Try to extract port info. Falls back to country name."""
        # Common Pakistani ports
        ports = ["Karachi", "Port Qasim", "Lahore", "Islamabad", "Peshawar", "Faisalabad"]
        item_upper = item_desc.upper()
        for port in ports:
            if port.upper() in item_upper:
                return port
        return country if country else "Unknown"

    def _extract_province(self, company_name):
        """Derive province from company info. Falls back to 'Unknown'."""
        # This is a best-effort heuristic
        provinces = {
            "SINDH": ["KARACHI", "HYDERABAD", "SUKKUR"],
            "PUNJAB": ["LAHORE", "FAISALABAD", "MULTAN", "RAWALPINDI", "SIALKOT", "GUJRANWALA"],
            "KPK": ["PESHAWAR", "ABBOTTABAD", "MARDAN"],
            "BALOCHISTAN": ["QUETTA", "GWADAR"],
            "ICT": ["ISLAMABAD"],
        }
        name_upper = company_name.upper() if company_name else ""
        for province, cities in provinces.items():
            for city in cities:
                if city in name_upper:
                    return province
        return "Unknown"
