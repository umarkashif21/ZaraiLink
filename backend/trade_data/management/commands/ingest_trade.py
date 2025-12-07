import pandas as pd
from django.core.management.base import BaseCommand
from trade_data.models import Transaction, Product, ProductCategory, ProductSubCategory, ProductItem
from django.db import transaction as db_transaction  # for atomic save
from datetime import datetime

class Command(BaseCommand):
    help = "Ingest XLSX/CSV trade data into Transaction model with product hierarchy"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path to import_data_1year.xlsx or CSV file"
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        self.stdout.write(self.style.WARNING(f"Reading file: {file_path}"))

        # Load file and use header row 6 for Excel
        if file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path, header=6)
        else:
            df = pd.read_csv(file_path)

        # Clean column names
        df.columns = df.columns.str.strip().str.replace(" ", "_").str.lower()

        # Required columns mapped to your model
        required = ["date", "hs_code", "category", "sub-category", "item_description",
                    "buyer", "seller", "shipping_agents", "country", "qty_kg", "qty_mt",
                    "usd/kg", "usd/mt", "pkr", "usd"]

        missing = [col for col in required if col.lower().replace(" ", "_") not in df.columns]
        if missing:
            raise ValueError(f"❌ Missing columns in file: {missing}")

        transactions_to_create = []

        with db_transaction.atomic():
            for idx, row in df.iterrows():
                if pd.isna(row["date"]):
                    continue

                try:
                    reporting_date = pd.to_datetime(row["date"]).date()
                except Exception:
                    self.stdout.write(self.style.ERROR(f"Invalid date at row {idx}, skipping"))
                    continue

                # ------------------------
                # Product hierarchy
                # ------------------------
                hs_code_full = str(row["hs_code"]).strip()
                category_name = str(row["category"]).strip()
                sub_category_name = str(row["sub-category"]).strip()
                item_name = str(row["item_description"]).strip()

                # Level 1: Product (first 2 digits of HS code, e.g., "17")
                product_hs = hs_code_full.split(".")[0]
                product, _ = Product.objects.get_or_create(hs_code=product_hs, defaults={"name": "Sugar"})  # default name can be improved

                # Level 2: ProductCategory (first 4 digits, e.g., "1702")
                category_hs = ".".join(hs_code_full.split(".")[:2])
                category, _ = ProductCategory.objects.get_or_create(
                    product=product,
                    hs_code=category_hs,
                    defaults={"name": category_name}
                )

                # Level 3: ProductSubCategory (full HS code, e.g., "1702.3000")
                sub_category, _ = ProductSubCategory.objects.get_or_create(
                    category=category,
                    hs_code=hs_code_full,
                    defaults={"name": sub_category_name}
                )

                # Level 4: ProductItem (actual item)
                product_item, _ = ProductItem.objects.get_or_create(
                    sub_category=sub_category,
                    name=item_name
                )

                # ------------------------
                # Transaction record
                # ------------------------
                tx = Transaction(
                    source_file=file_path,
                    tx_reference=f"ROW-{idx}",
                    reporting_date=reporting_date,
                    hs_code=hs_code_full,
                    product_item=product_item,
                    buyer=str(row["buyer"]),
                    seller=str(row["seller"]),
                    shipping_agent=str(row["shipping_agents"]),
                    country=str(row["country"]),
                    qty_kg=row["qty_kg"] or 0,
                    qty_mt=row["qty_mt"] or 0,
                    usd_per_kg=row.get("usd/kg"),
                    usd_per_mt=row.get("usd/mt"),
                    pkr=row.get("pkr"),
                    usd=row.get("usd"),
                    std_unit="MT"
                )

                transactions_to_create.append(tx)

            if transactions_to_create:
                Transaction.objects.bulk_create(transactions_to_create, ignore_conflicts=True)
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Ingested {len(transactions_to_create)} records successfully."
                ))
            else:
                self.stdout.write(self.style.WARNING("⚠️ No valid records found to ingest."))
