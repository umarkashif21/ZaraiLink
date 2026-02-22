import datetime
import difflib
from django.db.models import Sum, Count, Avg, Max, Min, F
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
                "seller": tx.seller,
                "origin_country": tx.origin_country,
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

        # 6. Who are they buying from?
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


class CountryComparator:
    """
    Family 7: Aggregates trade metrics grouped by country.

    DATA NOTE: The database contains only IMPORT records (Pakistan importing from the world).
    Grouping is therefore always by origin_country (the supplying country).
    Export destination data (where Pakistan exports to) is not available in this DB.
    The intent parameter is accepted for API consistency but does not change the query.
    """

    # Static market-entry notes per origin country
    MARKET_ENTRY_NOTES = {
        'China': {
            'tariff_tier': 'Low-Medium',
            'typical_lead_time': '25-40 days (sea)',
            'packaging_note': 'Standard 25kg/50kg bags; bulk containers available',
        },
        'India': {
            'tariff_tier': 'Medium',
            'typical_lead_time': '3-7 days (land/sea)',
            'packaging_note': 'FSSAI compliance may apply for food-grade goods',
        },
        'USA': {
            'tariff_tier': 'Medium-High',
            'typical_lead_time': '25-35 days (sea)',
            'packaging_note': 'FDA-compliant labeling required for food products',
        },
        'UAE': {
            'tariff_tier': 'Low',
            'typical_lead_time': '7-12 days (sea)',
            'packaging_note': 'Free-zone re-export hub; halal certification common',
        },
        'Thailand': {
            'tariff_tier': 'Low-Medium',
            'typical_lead_time': '18-25 days (sea)',
            'packaging_note': 'ASEAN origin advantage; food-grade standards strict',
        },
        'Indonesia': {
            'tariff_tier': 'Medium',
            'typical_lead_time': '20-28 days (sea)',
            'packaging_note': 'Halal certification required for food imports',
        },
        'Malaysia': {
            'tariff_tier': 'Low-Medium',
            'typical_lead_time': '18-25 days (sea)',
            'packaging_note': 'JAKIM halal cert preferred',
        },
        'Brazil': {
            'tariff_tier': 'Medium',
            'typical_lead_time': '35-50 days (sea)',
            'packaging_note': 'Large bulk shipments typical; sugar/agri speciality',
        },
        'Germany': {
            'tariff_tier': 'Medium-High',
            'typical_lead_time': '30-45 days (sea)',
            'packaging_note': 'EU GMP/food-grade standards; high quality assurance',
        },
        'France': {
            'tariff_tier': 'Medium-High',
            'typical_lead_time': '30-45 days (sea)',
            'packaging_note': 'EU standards; pharmaceutical-grade available',
        },
        'Turkey': {
            'tariff_tier': 'Low-Medium',
            'typical_lead_time': '12-18 days (sea)',
            'packaging_note': 'Growing export hub; competitive pricing',
        },
        'Saudi Arabia': {
            'tariff_tier': 'Low',
            'typical_lead_time': '5-10 days (sea)',
            'packaging_note': 'GCC standards; halal required',
        },
        'Vietnam': {
            'tariff_tier': 'Low-Medium',
            'typical_lead_time': '18-28 days (sea)',
            'packaging_note': 'ASEAN competitive; food-grade strict',
        },
        'South Korea': {
            'tariff_tier': 'Medium',
            'typical_lead_time': '20-30 days (sea)',
            'packaging_note': 'High-quality standards; Korean FDA equivalent',
        },
        'Japan': {
            'tariff_tier': 'Medium',
            'typical_lead_time': '20-30 days (sea)',
            'packaging_note': 'Strict quality/labeling standards; JAS certification',
        },
        'Russia': {
            'tariff_tier': 'Medium',
            'typical_lead_time': '20-35 days (sea/land)',
            'packaging_note': 'GOST standards; Cyrillic labeling may be required',
        },
        'Australia': {
            'tariff_tier': 'Low-Medium',
            'typical_lead_time': '25-35 days (sea)',
            'packaging_note': 'FSANZ compliance for food products',
        },
        'Canada': {
            'tariff_tier': 'Medium',
            'typical_lead_time': '30-40 days (sea)',
            'packaging_note': 'CFIA compliance; bilingual labeling required',
        },
        'Bangladesh': {
            'tariff_tier': 'Medium',
            'typical_lead_time': '3-7 days (land/sea)',
            'packaging_note': 'BSTI certification may be required',
        },
        'Sri Lanka': {
            'tariff_tier': 'Medium',
            'typical_lead_time': '5-10 days (sea)',
            'packaging_note': 'SLSI certification preferred',
        },
        'Egypt': {
            'tariff_tier': 'Medium',
            'typical_lead_time': '10-18 days (sea)',
            'packaging_note': 'Arabic labeling required; GOEIC certification',
        },
        'Kenya': {
            'tariff_tier': 'Medium-High',
            'typical_lead_time': '18-28 days (sea)',
            'packaging_note': 'KEBS certification required',
        },
        'Afghanistan': {
            'tariff_tier': 'Low',
            'typical_lead_time': '1-3 days (land)',
            'packaging_note': 'Informal trade common; documentation varies',
        },
        'Pakistan': {
            'tariff_tier': 'Home Market',
            'typical_lead_time': 'N/A (domestic)',
            'packaging_note': 'Domestic market; PSQCA standards apply for food products',
        },
    }

    def compare_countries(self, subcategory_ids, intent='SELL', country_filter=None,
                          time_filter=None, product_item_filter=None):
        """
        Returns a dict:
          {
            'results':      list of country dicts,
            'warnings':     list of warning dicts (e.g. country filter not applicable),
            'data_context': metadata about what the data represents,
          }
        Each country dict has: country, total_volume, avg_price, supplier_count,
        shipment_count, last_active, demand_growth_pct, top_buyers, market_entry.
        """
        warnings = []

        queryset = Transaction.objects.all()

        if subcategory_ids:
            queryset = queryset.filter(product_item__sub_category_id__in=subcategory_ids)

        if product_item_filter:
            queryset = queryset.filter(product_item__id__in=product_item_filter)

        # Always group by origin_country — only IMPORT records exist in this DB.
        country_field = 'origin_country'
        entity_field = 'seller'
        queryset = queryset.filter(trade_type='IMPORT')

        # Country filter with explicit warning when requested countries are not in DB
        if country_filter:
            available_origins = set(
                queryset.values_list(country_field, flat=True).distinct()
            )
            effective_filter = [c for c in country_filter if c in available_origins]
            if effective_filter:
                queryset = queryset.filter(**{f'{country_field}__in': effective_filter})
            else:
                label = 'country' if len(country_filter) == 1 else 'countries'
                # Attach any static market-entry notes we have for the requested countries.
                static_notes = [
                    {'country': c, 'notes': self.MARKET_ENTRY_NOTES[c]}
                    for c in country_filter if c in self.MARKET_ENTRY_NOTES
                ]
                # Return early — showing an unrelated table of all supply sources is misleading.
                return {
                    'results': [],
                    'warnings': [{
                        "code": "country_filter_not_applicable",
                        "message": (
                            f"The requested {label} ({', '.join(country_filter)}) do not appear "
                            f"as supply origin countries in this dataset. This database contains "
                            f"Pakistan import records only — export destination comparison is not "
                            f"available. Try querying without specifying a country to see all "
                            f"supply source countries for this product."
                        ),
                        "requested_countries": country_filter,
                        "market_entry_notes": static_notes,
                    }],
                    'data_context': {
                        'grouped_by': 'origin_country',
                        'note': 'Showing Pakistan import source countries. Export destination data is not available in this dataset.',
                    },
                }

        if time_filter:
            if time_filter.get('start_date'):
                queryset = queryset.filter(reporting_date__gte=time_filter['start_date'])
            if time_filter.get('end_date'):
                queryset = queryset.filter(reporting_date__lte=time_filter['end_date'])

        # --- Aggregate totals by country ---
        country_stats = (
            queryset
            .values(country_field)
            .annotate(
                total_volume=Sum('qty_mt'),
                avg_price=Avg('usd_per_mt'),
                supplier_count=Count(entity_field, distinct=True),
                shipment_count=Count('id'),
                last_active=Max('reporting_date'),
            )
            .order_by('-total_volume')
        )

        # --- YoY demand growth ---
        today = datetime.date.today()
        one_year_ago = today - datetime.timedelta(days=365)
        two_years_ago = today - datetime.timedelta(days=730)

        current_vol_by_country = {
            r[country_field]: float(r['vol'] or 0)
            for r in queryset.filter(reporting_date__gte=one_year_ago)
                             .values(country_field)
                             .annotate(vol=Sum('qty_mt'))
        }
        prev_vol_by_country = {
            r[country_field]: float(r['vol'] or 0)
            for r in queryset.filter(
                reporting_date__gte=two_years_ago,
                reporting_date__lt=one_year_ago
            ).values(country_field).annotate(vol=Sum('qty_mt'))
        }

        # --- Top 3 suppliers per country ---
        country_stats_list = list(country_stats)
        all_countries = [r[country_field] for r in country_stats_list if r[country_field]]
        top_buyers_by_country = {}
        for country in all_countries:
            rows = (
                queryset.filter(**{country_field: country})
                .values(entity_field)
                .annotate(vol=Sum('qty_mt'), avg_p=Avg('usd_per_mt'), cnt=Count('id'))
                .order_by('-vol')[:3]
            )
            top_buyers_by_country[country] = [
                {
                    'name': r[entity_field],
                    'volume': float(r['vol'] or 0),
                    'avg_price': float(r['avg_p'] or 0),
                    'shipment_count': r['cnt'],
                }
                for r in rows
            ]

        # --- Build result list ---
        results = []
        for r in country_stats_list:
            country = r[country_field]
            if not country:
                continue

            curr_vol = current_vol_by_country.get(country, 0)
            prev_vol = prev_vol_by_country.get(country, 0)

            if prev_vol > 0:
                growth_pct = round(((curr_vol - prev_vol) / prev_vol) * 100, 1)
            elif curr_vol > 0:
                growth_pct = 100.0
            else:
                growth_pct = 0.0

            growth_pct = max(-500.0, min(500.0, growth_pct))

            results.append({
                'country': country,
                'total_volume': float(r['total_volume'] or 0),
                'avg_price': float(r['avg_price'] or 0),
                'supplier_count': r['supplier_count'],
                'shipment_count': r['shipment_count'],
                'last_active': r['last_active'],
                'demand_growth_pct': growth_pct,
                'top_buyers': top_buyers_by_country.get(country, []),
                'market_entry': self.MARKET_ENTRY_NOTES.get(country, {}),
            })

        return {
            'results': results,
            'warnings': warnings,
            'data_context': {
                'grouped_by': 'origin_country',
                'note': 'Showing Pakistan import source countries. Export destination data is not available in this dataset.',
            },
        }


class EvidenceRetriever:
    """
    Family 8: Transaction Evidence / Buyer Verification.
    Direct retrieval of raw transaction rows for a named buyer — no ranking.
    """

    def get_transaction_evidence(self, subcategory_ids, buyer_name=None,
                                  country_filter=None, time_filter=None, top_n=100):
        """
        Returns:
          {
            'transactions':  list of raw transaction dicts,
            'buyer_summary': aggregate stats for the matched buyer (or None),
            'buyer_found':   True if an exact/partial DB match was found,
            'similar_buyers': list of close buyer names when no match found,
            'total_shown':   count of transactions returned,
          }
        """
        queryset = Transaction.objects.filter(trade_type='IMPORT')

        if subcategory_ids:
            queryset = queryset.filter(product_item__sub_category_id__in=subcategory_ids)

        if time_filter:
            if time_filter.get('start_date'):
                queryset = queryset.filter(reporting_date__gte=time_filter['start_date'])
            if time_filter.get('end_date'):
                queryset = queryset.filter(reporting_date__lte=time_filter['end_date'])

        if country_filter:
            queryset = queryset.filter(origin_country__in=country_filter)

        buyer_found = False
        similar_buyers = []
        matched_buyer_name = buyer_name  # store how we matched for summary

        if buyer_name:
            name = buyer_name.strip()
            # 1. Exact match (case-insensitive)
            exact_qs = queryset.filter(buyer__iexact=name)
            if exact_qs.exists():
                queryset = exact_qs
                buyer_found = True
            else:
                # 2. Partial / contains match
                partial_qs = queryset.filter(buyer__icontains=name)
                if partial_qs.exists():
                    queryset = partial_qs
                    buyer_found = True
                    # Use the most common actual name from DB
                    top_name = (
                        partial_qs.values('buyer')
                        .annotate(cnt=Count('id'))
                        .order_by('-cnt')
                        .first()
                    )
                    if top_name:
                        matched_buyer_name = top_name['buyer']
                else:
                    # 3. No match — fuzzy suggest from all buyers in this product
                    buyer_found = False
                    all_buyers = list(
                        queryset.values_list('buyer', flat=True).distinct()[:300]
                    )
                    similar_buyers = difflib.get_close_matches(
                        name, all_buyers, n=5, cutoff=0.55
                    )
                    # Return empty — don't show unrelated transactions
                    return {
                        'transactions': [],
                        'buyer_summary': None,
                        'buyer_found': False,
                        'similar_buyers': similar_buyers,
                        'total_shown': 0,
                    }

        # Build raw transaction list (most recent first, no ranking)
        transactions = []
        for tx in queryset.order_by('-reporting_date')[:top_n]:
            transactions.append({
                'id': tx.id,
                'tx_reference': tx.tx_reference or '',
                'seller': tx.seller or '',
                'buyer': tx.buyer or '',
                'origin_country': tx.origin_country or '',
                'destination_country': tx.destination_country or '',
                'qty_mt': float(tx.qty_mt or 0),
                'usd_per_mt': float(tx.usd_per_mt or 0),
                'date': tx.reporting_date,
                'shipping_agent': tx.shipping_agent or '',
            })

        # Buyer summary card (only when a buyer was named and found)
        buyer_summary = None
        if buyer_name and buyer_found and transactions:
            stats = queryset.aggregate(
                total_volume=Sum('qty_mt'),
                avg_price=Avg('usd_per_mt'),
                shipment_count=Count('id'),
                first_purchase=Min('reporting_date'),
                last_purchase=Max('reporting_date'),
            )
            unique_sellers = queryset.values('seller').distinct().count()
            months_active = (
                queryset
                .annotate(month=TruncMonth('reporting_date'))
                .values('month')
                .distinct()
                .count()
            )
            shipment_count = stats['shipment_count'] or 0
            buyer_summary = {
                'buyer_name': matched_buyer_name,
                'total_volume': float(stats['total_volume'] or 0),
                'avg_price': float(stats['avg_price'] or 0),
                'shipment_count': shipment_count,
                'first_purchase_date': stats['first_purchase'],
                'last_purchase_date': stats['last_purchase'],
                'unique_sellers': unique_sellers,
                'months_active': months_active,
                'verification_status': 'Verified' if shipment_count >= 3 else 'Limited History',
                'repeat_buyer': months_active >= 3 or shipment_count >= 5,
            }

        return {
            'transactions': transactions,
            'buyer_summary': buyer_summary,
            'buyer_found': buyer_found,
            'similar_buyers': similar_buyers,
            'total_shown': len(transactions),
        }
