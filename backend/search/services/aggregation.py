import datetime
from django.db.models import Sum, Count, Avg, Max, F
from django.db.models.functions import TruncMonth
from trade_data.models import Transaction
import math

class SupplierAggregator:
    def get_suppliers_for_subcategories(self, subcategory_ids, intent='BUY', scope='WORLDWIDE', country_filter=None, price_filter=None, volume_filter=None, time_filter=None, product_item_filter=None):
        """
        Aggregates counterparty data (Suppliers or Buyers) for the given subcategory IDs.
        
        Args:
            intent: 'BUY' (Find Suppliers) or 'SELL' (Find Buyers).
            scope: 'WORLDWIDE' or 'PAKISTAN'.
            country_filter: List of countries to filter by.
            price_filter: Dict with 'ceiling' and 'floor'.
            volume_filter: Requested volume in MT (used for soft compatibility scoring, NOT hard filter).
            time_filter: Dict with 'start_date' and 'end_date'.
            product_item_filter: List of ProductItem IDs to filter by (specific variants).
        """
        queryset = Transaction.objects.all()
        
        # Subcategory filter (optional — None means all products for filter-only queries)
        if subcategory_ids:
            queryset = queryset.filter(product_item__sub_category_id__in=subcategory_ids)
            
        # Specific Product Item (Variant) Filter
        if product_item_filter:
            queryset = queryset.filter(product_item__id__in=product_item_filter)
        
        # Default Scope
        scope = scope or 'WORLDWIDE'
        
        # Intent & Scope Logic
        if intent == 'SELL':
            # User wants to SELL
            if scope == 'PAKISTAN':
                target_field = 'buyer'
                country_field = 'destination_country'
                queryset = queryset.filter(trade_type='IMPORT', destination_country='Pakistan')
            else:
                # WORLDWIDE: Pakistani seller exporting to world
                target_field = 'buyer'
                country_field = 'destination_country'
                queryset = queryset.filter(trade_type='EXPORT')
                
        else:
            # User wants to BUY
            if scope == 'PAKISTAN':
                target_field = 'seller'
                country_field = 'origin_country'
                queryset = queryset.filter(trade_type='EXPORT', origin_country='Pakistan')
            else:
                # WORLDWIDE: Pakistani buyer importing from world
                target_field = 'seller'
                country_field = 'origin_country'
                queryset = queryset.filter(trade_type='IMPORT')

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

        # Aggregate — NO hard volume filter at DB level
        results = queryset.values(target_field, country_field).annotate(
            total_volume=Sum('qty_mt'),
            avg_price=Avg('usd_per_mt'),
            shipment_count=Count('id'),
            last_shipment_date=Max('reporting_date'),
            max_shipment_vol=Max('qty_mt'),
            avg_shipment_vol=Avg('qty_mt')
        ).order_by('-total_volume')
        
        # Convert to list + Volume Compatibility Scoring
        counterparties = []
        for r in results:
            entry = {
                "name": r[target_field],
                "country": r[country_field],
                "total_volume": float(r['total_volume'] or 0),
                "avg_price": float(r['avg_price'] or 0),
                "shipment_count": r['shipment_count'],
                "last_shipment_date": r['last_shipment_date'],
                "max_shipment_vol": float(r['max_shipment_vol'] or 0),
                "avg_shipment_vol": float(r['avg_shipment_vol'] or 0),
                "type": "Buyer" if intent == 'SELL' else "Supplier",
                "volume_score": None,
                "volume_fit": "N/A"
            }
            
            if volume_filter and volume_filter > 0:
                mss = entry['max_shipment_vol']
                total = entry['total_volume']
                avg = entry['avg_shipment_vol']
                V = float(volume_filter)
                
                # Soft floor: exclude extreme mismatches (max single < 30% of V)
                # BUT only if they also have low total volume
                if mss < 0.3 * V and total < 0.5 * V:
                    continue
                
                # Volume Compatibility Score
                single_match = min(mss / V, 1.0) if V > 0 else 0
                capacity_match = min(total / V, 1.0) if V > 0 else 0
                avg_match = min(avg / V, 1.0) if V > 0 else 0
                
                vol_score = 0.5 * single_match + 0.3 * capacity_match + 0.2 * avg_match
                entry['volume_score'] = round(vol_score, 3)
                
                # Label
                if vol_score >= 0.8:
                    entry['volume_fit'] = 'Strong'
                elif vol_score >= 0.5:
                    entry['volume_fit'] = 'Good'
                elif vol_score >= 0.3:
                    entry['volume_fit'] = 'Partial'
                else:
                    entry['volume_fit'] = 'Low'
            
            counterparties.append(entry)
        
        # If volume scoring was applied, sort by volume_score descending
        if volume_filter and volume_filter > 0:
            counterparties.sort(key=lambda x: x.get('volume_score', 0), reverse=True)
            
        return counterparties


    def get_supplier_details(self, seller_name, subcategory_ids):
        """
        Get detailed stats, sparklines, and history for a specific supplier within a category.
        """
        # Filter transactions for specific seller and subcategories
        # Filter transactions for specific seller and subcategories
        # Note: Removed trade_type='IMPORT' filter here as well
        queryset = Transaction.objects.filter(
            seller__iexact=seller_name.strip(),
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
                "country": tx.destination_country, 
                "quantity": float(tx.qty_mt or 0),
                "price": float(tx.usd_per_mt or 0),
                "date": tx.reporting_date
            })

        # 4. Filters (Countries & Years)
        countries = list(queryset.values_list('destination_country', flat=True).distinct().order_by('destination_country'))
        
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

    def get_buyer_details(self, buyer_name, subcategory_ids):
        """
        Get detailed stats, sparklines, and history for a specific BUYER within a category.
        """
        # Filter transactions where 'buyer' is the target
        queryset = Transaction.objects.filter(
            buyer__iexact=buyer_name.strip(),
            product_item__sub_category_id__in=subcategory_ids
        ).order_by('-reporting_date')



        if not queryset.exists():
            # Fallback: Try finding buyer without product constraint (General Profile)
            queryset = Transaction.objects.filter(
                buyer__iexact=buyer_name.strip()
            ).order_by('-reporting_date')
            
            if not queryset.exists():
                return None

        # 1. High-level Stats (Purchasing)
        stats = queryset.aggregate(
            total_volume=Sum('qty_mt'),
            avg_price=Avg('usd_per_mt'),
            shipment_count=Count('id'),
            last_shipment_date=Max('reporting_date')
        )
        
        # 2. Sparklines (Monthly Purchasing)
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

        # 3. Transaction History (Top 50 latest purchases)
        history = []
        for tx in queryset[:50]:
            history.append({
                "id": tx.id,
                "transaction_hash": tx.tx_reference,
                "seller": tx.seller,  # Show who they bought from
                "origin_country": tx.origin_country, # Where it came from
                "quantity": float(tx.qty_mt or 0),
                "price": float(tx.usd_per_mt or 0),
                "date": tx.reporting_date
            })

        # 4. Filters (Source Countries)
        countries = list(queryset.values_list('origin_country', flat=True).distinct().order_by('origin_country'))
        
        # 5. Typical Order Sizes (Buying habits)
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

        # 6. Returns "Supplier Insights" logic from Buyer perspective
        # i.e. "Who are they buying from?"
        total_suppliers = queryset.values('seller').distinct().count()
        
        last_month_start = datetime.date.today() - datetime.timedelta(days=30)
        recent_suppliers = queryset.filter(reporting_date__gte=last_month_start).values('seller').distinct().count()
        
        return {
            "name": buyer_name,
            "type": "BUYER",
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
            "supplier_insights": {
                "total_relationships": total_suppliers,
                "recent_suppliers": recent_suppliers
            },
            "sparkline": sparkline,
            "history": history
        }
