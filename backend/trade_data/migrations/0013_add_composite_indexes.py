from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trade_data', '0012_fix_company_stats_unique'),
    ]

    operations = [
        # Composite index for the main aggregation query:
        # WHERE product_item_id IN (...) AND trade_type='IMPORT'
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(
                fields=['trade_type', 'product_item'],
                name='tx_tradetype_productitem_idx',
            ),
        ),
        # Composite index for time-filtered aggregation queries
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(
                fields=['product_item', 'trade_type', 'reporting_date'],
                name='tx_item_type_date_idx',
            ),
        ),
        # Composite index for country+tradetype scans (CountryComparator)
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(
                fields=['trade_type', 'origin_country', 'reporting_date'],
                name='tx_type_origin_date_idx',
            ),
        ),
    ]
