import pandas as pd
from django.core.management.base import BaseCommand
from trade_data.models import (
    Transaction,
    Product,
    ProductCategory,
    ProductSubCategory,
    ProductItem,
)
from django.db import transaction as db_transaction


class Command(BaseCommand):
    help = "Ingest EXPORT trade data into Transaction model"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path to export_data.xlsx or CSV file",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        self.stdout.write(self.style.WARNING(f"Reading file: {file_path}"))

        # -------------------------
        # Load File
        # -------------------------
        if file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path, header=6)
        else:
            df = pd.read_csv(file_path)

        # Normalize column names: lowercase, strip, replace spaces with underscores
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        self.stdout.write(self.style.WARNING(f"Columns in file: {list(df.columns)}"))

        # Required columns after normalization
        required = [
            "date",
            "hs_code",
            "category",
            "sub-category",
            "item_description",
            "buyer",
            "seller",
            "shipping_agents",
            "country",
            "qty_kg",
            "qty_mt",
            "usd/kg",
            "usd/mt",
            "pkr",
            "usd",
        ]

        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"[ERROR] Missing columns in file: {missing}")

        transactions_to_create = []

        # -------------------------
        # Ingestion
        # -------------------------
        with db_transaction.atomic():
            for idx, row in df.iterrows():
                if pd.isna(row["date"]):
                    continue

                try:
                    reporting_date = pd.to_datetime(row["date"]).date()
                except Exception:
                    self.stdout.write(
                        self.style.ERROR(f"Invalid date at row {idx}, skipping")
                    )
                    continue

                # -------------------------
                # Product Hierarchy
                # -------------------------
                hs_code_full = str(row["hs_code"]).strip()
                category_name = str(row["category"]).strip()
                sub_category_name = str(row["sub-category"]).strip()
                item_name = str(row["item_description"]).strip()

                product_hs = hs_code_full.split(".")[0]
                product, _ = Product.objects.get_or_create(
                    hs_code=product_hs,
                    defaults={"name": "Sugar"}
                )

                category_hs = ".".join(hs_code_full.split(".")[:2])
                category, _ = ProductCategory.objects.get_or_create(
                    product=product,
                    hs_code=category_hs,
                    defaults={"name": category_name}
                )

                sub_category, _ = ProductSubCategory.objects.get_or_create(
                    category=category,
                    hs_code=hs_code_full,
                    defaults={"name": sub_category_name}
                )

                product_item, _ = ProductItem.objects.get_or_create(
                    sub_category=sub_category,
                    name=item_name
                )

                # -------------------------
                # Safe Numeric Handling
                # -------------------------
                qty_kg = row["qty_kg"] if pd.notna(row["qty_kg"]) else 0
                qty_mt = row["qty_mt"] if pd.notna(row["qty_mt"]) else 0
                usd_per_kg = row["usd/kg"] if pd.notna(row["usd/kg"]) else None
                usd_per_mt = row["usd/mt"] if pd.notna(row["usd/mt"]) else None
                pkr = row["pkr"] if pd.notna(row["pkr"]) else None
                usd = row["usd"] if pd.notna(row["usd"]) else None

                # -------------------------
                # Direction Logic (EXPORT)
                # -------------------------
                origin_country = "Pakistan"
                destination_country = str(row["country"]).strip()

                tx = Transaction(
                    source_file=file_path,
                    tx_reference=f"EXPORT-ROW-{idx}",
                    reporting_date=reporting_date,
                    trade_type="EXPORT",

                    hs_code=hs_code_full,
                    product_item=product_item,

                    buyer=str(row["buyer"]),
                    seller=str(row["seller"]),
                    shipping_agent=str(row["shipping_agents"]),

                    origin_country=origin_country,
                    destination_country=destination_country,

                    qty_kg=qty_kg,
                    qty_mt=qty_mt,

                    usd_per_kg=usd_per_kg,
                    usd_per_mt=usd_per_mt,
                    pkr=pkr,
                    usd=usd,

                    std_unit="MT",
                )

                transactions_to_create.append(tx)

            if transactions_to_create:
                Transaction.objects.bulk_create(
                    transactions_to_create,
                    ignore_conflicts=True
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] Ingested {len(transactions_to_create)} EXPORT records successfully."
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING("[WARN] No valid records found to ingest.")
                )
