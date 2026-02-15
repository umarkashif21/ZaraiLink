import datetime
from django.db.models import Sum, Count, Avg, Max, Case, When, Value, CharField
from django.db.models.functions import TruncMonth
from trade_data.models import Transaction

class SupplierAggregator:
    def get_suppliers_for_subcategories(self, subcategory_ids, intent='BUY', scope='WORLDWIDE', country_filter=None, price_filter=None, volume_filter=None, time_filter=None):
        """
        Aggregates counterparty data (Suppliers or Buyers) for the given subcategory IDs.
        
        Args:
            intent: 'BUY' (Find Suppliers) or 'SELL' (Find Buyers).
            scope: 'WORLDWIDE' or 'PAKISTAN'.
            country_filter: List of countries to filter by.
            price_filter: Dict with 'ceiling' and 'floor'.
            volume_filter: Minimum volume capability (Max shipment size).
            time_filter: Dict with 'start_date' and 'end_date'.
        """
        queryset = Transaction.objects.filter(
            product_item__sub_category_id__in=subcategory_ids
        )
        
        # Default Scope
        scope = scope or 'WORLDWIDE'
        
        # Intent & Scope Logic
        # Mapping: (Intent, Scope) -> (TradeType, TargetField, CountryField)
        
        if intent == 'SELL':
            # User wants to SELL
            if scope == 'PAKISTAN':
                # Pakistani seller selling locally (to Pakistani buyers)
                # Look at Pakistan's IMPORTS (local buyers importing)
                target_field = 'buyer'
                country_field = 'destination_country'
                queryset = queryset.filter(trade_type='IMPORT', destination_country='Pakistan')
            else:
                # WORLDWIDE: Pakistani seller exporting to world
                # Look at Pakistan's EXPORTS and find the buyers
                target_field = 'buyer'
                country_field = 'destination_country'
                queryset = queryset.filter(trade_type='EXPORT', origin_country='Pakistan')
                
        else:
            # User wants to BUY
            if scope == 'PAKISTAN':
                # Foreign buyer buying FROM Pakistan
                # Look at Pakistan's EXPORTS (Pakistani suppliers selling abroad)
                target_field = 'seller'
                country_field = 'origin_country'
                queryset = queryset.filter(trade_type='EXPORT', origin_country='Pakistan')
            else:
                # WORLDWIDE: Pakistani buyer importing from world
                # Look at Pakistan's IMPORTS (foreign suppliers selling TO Pakistan)
                target_field = 'seller'
                country_field = 'origin_country'
                queryset = queryset.filter(trade_type='IMPORT', destination_country='Pakistan')

        # Apply Filters
        if country_filter and len(country_filter) > 0:
            filter_kwargs = {f"{country_field}__in": country_filter}
            queryset = queryset.filter(**filter_kwargs)
            
        if price_filter:
            if price_filter.get('ceiling'):
                queryset = queryset.filter(usd_per_mt__lte=price_filter['ceiling'])
            if price_filter.get('floor'):
                queryset = queryset.filter(usd_per_mt__gte=price_filter['floor'])

        if time_filter:
            if time_filter.get('start_date'):
                queryset = queryset.filter(reporting_date__gte=time_filter['start_date'])
            if time_filter.get('end_date'):
                queryset = queryset.filter(reporting_date__lte=time_filter['end_date'])

        # Aggregate
        # We need to explicitly select the 'country' related to the counterparty
        results = queryset.values(target_field, country_field).annotate(
            total_volume=Sum('qty_mt'),
            avg_price=Avg('usd_per_mt'),
            shipment_count=Count('id'),
            last_shipment_date=Max('reporting_date'),
            max_shipment_vol=Max('qty_mt')
        )
        
        # Apply Volume Filter (Capacity check)
        # Include suppliers who either shipped volume_filter in a single shipment
        # OR whose total volume meets the requirement
        if volume_filter:
            from django.db.models import Q
            results = results.filter(
                Q(max_shipment_vol__gte=volume_filter) | Q(total_volume__gte=volume_filter)
            )
            
        results = results.order_by('-total_volume')
        
        # Convert to list
        counterparties = []
        for r in results:
            counterparties.append({
                "name": r[target_field],
                "country": r[country_field],
                "total_volume": float(r['total_volume'] or 0),
                "avg_price": float(r['avg_price']) if r['avg_price'] is not None else None,
                "shipment_count": r['shipment_count'],
                "last_shipment_date": r['last_shipment_date'],
                "max_shipment_vol": float(r['max_shipment_vol'] or 0),
                "type": "Buyer" if intent == 'SELL' else "Supplier"
            })
            
        return counterparties


    def get_supplier_details(self, name, subcategory_ids, intent='BUY'):
        """
        Get detailed stats, sparklines, and history for a specific supplier/buyer within a category.
        For BUY intent, name is a seller. For SELL intent, name is a buyer.
        """
        # Determine which field to filter on based on intent
        if intent == 'SELL':
            filter_kwargs = {'buyer': name}
        else:
            filter_kwargs = {'seller': name}

        queryset = Transaction.objects.filter(
            product_item__sub_category_id__in=subcategory_ids,
            **filter_kwargs
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
        # Use the counterparty field and country field based on intent
        if intent == 'SELL':
            counterparty_field = 'seller'
            country_field_name = 'destination_country'
        else:
            counterparty_field = 'buyer'
            country_field_name = 'origin_country'

        history = []
        for tx in queryset[:50]:
            history.append({
                "id": tx.id,
                "transaction_hash": tx.tx_reference,
                "counterparty": getattr(tx, counterparty_field),
                "country": getattr(tx, country_field_name),
                "quantity": float(tx.qty_mt or 0),
                "price": float(tx.usd_per_mt or 0),
                "date": tx.reporting_date
            })

        # 4. Filters (Countries & Years)
        countries = list(queryset.values_list(country_field_name, flat=True).distinct().order_by(country_field_name))
        
        # 5. Typical Shipment Sizes
        # Bucket: 0-25, 25-50, 50-100, 100+
        # We can do this in Python since we already have the queryset (or optimize with DB conditional aggregation)
        # Given potential volume, let's do DB aggregation for performance
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
            "name": name,
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
