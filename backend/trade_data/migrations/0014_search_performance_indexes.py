"""
Migration: Search Performance Indexes
======================================
Adds three indexes identified as missing in the search engine audit:

1. GIN trigram index on ProductSubCategory.name
   - Required for Pass 3 product resolution (pg_trgm TrigramSimilarity queries).
   - Without this, every trigram search does a sequential scan of all product names.
   - Requires PostgreSQL extension: pg_trgm (enabled below).

2. Functional index LOWER(Transaction.seller)
   - get_supplier_details() uses seller__iexact which cannot use a plain B-tree index.
   - A functional index on LOWER(seller) enables index-seeks for case-insensitive lookups.

3. Functional index LOWER(Transaction.buyer)
   - Same reason as seller, for get_buyer_details().
"""

from django.db import migrations


class Migration(migrations.Migration):
    # CONCURRENTLY cannot run inside a transaction block
    atomic = False

    dependencies = [
        ('trade_data', '0013_transaction_tx_type_product_idx_and_more'),
    ]

    operations = [
        # Enable pg_trgm extension (idempotent — safe to run if already enabled)
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            reverse_sql="-- extension left in place on reverse",
        ),

        # GIN trigram index on ProductSubCategory.name
        # Enables TrigramSimilarity('name', keyword) queries to use an index instead of seq-scan.
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS
                    idx_productsubcategory_name_trgm
                ON trade_data_productsubcategory
                USING GIN (name gin_trgm_ops);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_productsubcategory_name_trgm;",
        ),

        # GIN trigram index on ProductItem.name (also used in product resolution)
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS
                    idx_productitem_name_trgm
                ON trade_data_productitem
                USING GIN (name gin_trgm_ops);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_productitem_name_trgm;",
        ),

        # Functional index on LOWER(seller) for case-insensitive supplier detail lookups
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS
                    idx_transaction_seller_lower
                ON trade_data_transaction (LOWER(seller));
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_transaction_seller_lower;",
        ),

        # Functional index on LOWER(buyer) for case-insensitive buyer detail lookups
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS
                    idx_transaction_buyer_lower
                ON trade_data_transaction (LOWER(buyer));
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_transaction_buyer_lower;",
        ),

        # Index on ProductSubCategory.hs_code for HS code-based product resolution
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS
                    idx_productsubcategory_hs_code
                ON trade_data_productsubcategory (hs_code);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_productsubcategory_hs_code;",
        ),
    ]
