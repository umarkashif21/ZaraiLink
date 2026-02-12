import datetime
from django.db.models import Sum, Count, Avg, Max, F
from django.db.models.functions import TruncMonth
from trade_data.models import Transaction

class SupplierAggregator:
    def get_suppliers_for_subcategories(self, subcategory_ids):
        """
        Aggregates supplier data for the given subcategory IDs.
        """
        # Filter transactions for these subcategories
        # Note: We removed trade_type='IMPORT' filter because the current dataset has empty trade_type fields
        queryset = Transaction.objects.filter(
            product_item__sub_category_id__in=subcategory_ids
        )
        
        # Aggregate by seller
        results = queryset.values('seller', 'country').annotate(
            total_volume=Sum('qty_mt'),
            avg_price=Avg('usd_per_mt'),
            shipment_count=Count('id'),
            last_shipment_date=Max('reporting_date')
        )
        
        # Convert to list of dicts and clean up
        suppliers = []
        for r in results:
            suppliers.append({
                "name": r['seller'],
                "country": r['country'],
                "total_volume": float(r['total_volume'] or 0),
                "avg_price": float(r['avg_price'] or 0),
                "shipment_count": r['shipment_count'],
                "last_shipment_date": r['last_shipment_date']
            })
            
        return suppliers

    def get_supplier_details(self, seller_name, subcategory_ids):
        """
        Get detailed stats, sparklines, and history for a specific supplier within a category.
        """
        # Filter transactions for specific seller and subcategories
        # Note: Removed trade_type='IMPORT' filter here as well
        queryset = Transaction.objects.filter(
            seller=seller_name,
            product_item__sub_category_id__in=subcategory_ids
        ).order_by('-reporting_date')

        if not queryset.exists():
            return None

        # 1. High-level Stats
        stats = queryset.aggregate(
            total_volume=Sum('qty_mt'),
            avg_price=Avg('usd_per_mt'),
            shipment_count=Count('id'),
            last_shipment_date=Max('reporting_date')
        )
        
        # 2. Sparklines (Monthly Aggregation)
        # Group by Month and calculate Avg Price & Total Volume
        monthly_data = queryset.annotate(
            month=TruncMonth('reporting_date')
        ).values('month').annotate(
            vol=Sum('qty_mt'),
            price=Avg('usd_per_mt')
        ).order_by('month')

        sparkline = []
        for entry in monthly_data:
            sparkline.append({
                "date": entry['month'].strftime("%Y-%m-%d"),
                "volume": float(entry['vol'] or 0),
                "price": float(entry['price'] or 0)
            })

        # 3. Transaction History (Top 50 for table)
        history = []
        for tx in queryset[:50]:
            history.append({
                "id": tx.id,
                "transaction_hash": tx.tx_reference, # Unique ID
                "buyer": tx.buyer,
                "country": tx.country,
                "quantity": float(tx.qty_mt or 0),
                "price": float(tx.usd_per_mt or 0),
                "date": tx.reporting_date
            })

        # 4. Filters (Countries & Years)
        countries = list(queryset.values_list('country', flat=True).distinct().order_by('country'))
        
        # 5. Typical Shipment Sizes
        # Bucket: 0-25, 25-50, 50-100, 100+
        # We can do this in Python since we already have the queryset (or optimize with DB conditional aggregation)
        # Given potential volume, let's do DB aggregation for performance
        from django.db.models import Case, When, Value, CharField
        
        size_buckets = queryset.annotate(
            bucket=Case(
                When(qty_mt__lte=25, then=Value('0-25')),
                When(qty_mt__lte=50, then=Value('25-50')),
                When(qty_mt__lte=100, then=Value('50-100')),
                default=Value('100+'),
                output_field=CharField(),
            )
        ).values('bucket').annotate(
            count=Count('id'),
            avg_price=Avg('usd_per_mt')
        ).order_by('bucket')
        
        # Format for frontend
        shipment_sizes = []
        bucket_order = ['0-25', '25-50', '50-100', '100+']
        size_dict = {item['bucket']: item for item in size_buckets}
        
        for b in bucket_order:
            if b in size_dict:
                shipment_sizes.append({
                    "range": f"{b} MT",
                    "count": size_dict[b]['count'],
                    "avg_price": float(size_dict[b]['avg_price'] or 0)
                })
            else:
                 shipment_sizes.append({
                    "range": f"{b} MT",
                    "count": 0,
                    "avg_price": 0
                })

        # 6. Buyer Insights
        # Unique buyers total
        total_buyers = queryset.values('buyer').distinct().count()
        
        # Unique buyers last 30d (approx, since reporting_date is date)
        last_month_start = datetime.date.today() - datetime.timedelta(days=30)
        recent_buyers = queryset.filter(reporting_date__gte=last_month_start).values('buyer').distinct().count()
        
        # New buyers (First time seen in last 30d vs history) - Expensive query, let's skip for now or approx
        # Approx: Just return total vs recent for now
        
        return {
            "name": seller_name,
            "stats": {
                "total_volume": float(stats['total_volume'] or 0),
                "avg_price": float(stats['avg_price'] or 0),
                "shipment_count": stats['shipment_count'],
                "last_shipment_date": stats['last_shipment_date'],
            },
            "filters": {
                "countries": countries
            },
            "shipment_sizes": shipment_sizes,
            "buyer_insights": {
                "total_relationships": total_buyers,
                "recent_buyers": recent_buyers
            },
            "sparkline": sparkline,
            "history": history
        }
