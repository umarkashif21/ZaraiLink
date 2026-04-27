import datetime
from django.db.models import Sum, Count, Avg, Max, Min, F, ExpressionWrapper, FloatField, Q
from django.db.models.functions import TruncMonth, TruncQuarter
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
        if intent == 'UNKNOWN':
            # No trade direction signal — return ALL companies across both import/export
            # Sellers from import records + Buyers from export records
            import_qs = queryset.filter(trade_type='IMPORT')
            export_qs = queryset.filter(trade_type='EXPORT')

            def _agg(qs, field, country_field, label):
                rows = qs.values(field, country_field).annotate(
                    total_volume=Sum('qty_mt'),
                    weighted_price_sum=Sum(ExpressionWrapper(F('qty_mt') * F('usd_per_mt'), output_field=FloatField())),
                    shipment_count=Count('tx_reference', distinct=True),
                    last_shipment_date=Max('reporting_date'),
                    max_shipment_vol=Max('qty_mt'),
                    avg_shipment_vol=Avg('qty_mt')
                ).order_by('-total_volume')
                results = []
                for r in rows:
                    tv = float(r['total_volume'] or 0)
                    wps = float(r.get('weighted_price_sum') or 0)
                    avg_price = round(wps / tv, 2) if tv > 0 else 0.0
                    name = r.get(field) or ''
                    if not name:
                        continue
                    results.append({
                        'name': name,
                        'country': r[country_field],
                        'total_volume': tv,
                        'avg_price': avg_price,
                        'shipment_count': r['shipment_count'],
                        'last_shipment_date': r['last_shipment_date'],
                        'max_shipment_vol': float(r['max_shipment_vol'] or 0),
                        'avg_shipment_vol': float(r['avg_shipment_vol'] or 0),
                        'type': label,
                        'volume_score': None,
                        'volume_fit': 'N/A',
                    })
                return results

            sellers  = _agg(import_qs, 'seller', 'origin_country', 'Supplier')
            buyers   = _agg(export_qs, 'buyer',  'destination_country', 'Buyer')
            combined = sellers + buyers
            combined.sort(key=lambda x: x['total_volume'], reverse=True)
            return combined

        elif scope == 'IMPORT':
            # Looking at IMPORT Data (Origin is foreign, destination is Pakistan)
            queryset = queryset.filter(trade_type='IMPORT')
            if intent == 'BUY':
                # Import + Buy -> Foreign Suppliers
                target_field = 'seller'
                country_field = 'origin_country'
            else:
                # Import + Sell -> Pakistani Buyers
                target_field = 'buyer'
                country_field = 'destination_country'

        else: # scope == 'EXPORT'
            # Looking at EXPORT Data (Origin is Pakistan, destination is foreign)
            queryset = queryset.filter(trade_type='EXPORT')
            if intent == 'SELL':
                # Export + Sell -> Foreign Buyers
                target_field = 'buyer'
                country_field = 'destination_country'
            else:
                # Export + Buy -> Pakistani Suppliers
                target_field = 'seller'
                country_field = 'origin_country'

        # Apply Filters
        if country_filter and len(country_filter) > 0:
            filter_kwargs = {f"{country_field}__in": country_filter}
            queryset = queryset.filter(**filter_kwargs)

        if time_filter:
            if time_filter.get('start_date'):
                queryset = queryset.filter(reporting_date__gte=time_filter['start_date'])
            if time_filter.get('end_date'):
                queryset = queryset.filter(reporting_date__lte=time_filter['end_date'])

        # NOTE: Price filter is NOT applied here (not a row-level WHERE).
        # It will be applied AFTER aggregation on the computed avg_price.
        # Rationale: filtering individual rows by usd_per_mt would exclude a supplier
        # if even ONE of their shipments was above the ceiling, even if their average
        # price is well within the limit.  The correct semantic is supplier-level.

        import logging; logging.getLogger(__name__).warning(f"[Aggregator] after country filter count={queryset.count()} | SQL={str(queryset.query)}")

        # Aggregate — NO hard volume filter at DB level
        results = queryset.values(target_field, country_field).annotate(
            total_volume=Sum('qty_mt'),
            weighted_price_sum=Sum(ExpressionWrapper(F('qty_mt') * F('usd_per_mt'), output_field=FloatField())),
            shipment_count=Count('tx_reference', distinct=True),
            last_shipment_date=Max('reporting_date'),
            max_shipment_vol=Max('qty_mt'),
            avg_shipment_vol=Avg('qty_mt')
        ).order_by('-total_volume')
        
        # Convert to list + Volume Compatibility Scoring
        counterparties = []
        for r in results:
            tv = float(r['total_volume'] or 0)
            wps = float(r.get('weighted_price_sum') or 0)
            avg_price = round(wps / tv, 2) if tv > 0 else 0.0

            # Post-aggregation price filter (HAVING-equivalent on computed avg_price)
            # This is the correct level: filter based on supplier's weighted average price,
            # not individual transaction row prices.
            if price_filter:
                ceiling = price_filter.get('ceiling')
                floor = price_filter.get('floor')
                supplier_name = r.get(target_field, '?')

                if ceiling is not None:
                    passes = avg_price <= ceiling
                    if not passes:
                        continue

                if floor is not None:
                    passes = avg_price == 0 or avg_price >= floor
                    if not passes:
                        continue

            entry = {
                "name": r[target_field],
                "country": r[country_field],
                "total_volume": tv,
                "avg_price": avg_price,
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
            
        import logging; logging.getLogger(__name__).warning(f"[Aggregator] after price filter supplier_count={len(results)}")
        import logging; logging.getLogger(__name__).warning(f"[Aggregator] returning {len(counterparties)} suppliers")
        return counterparties


    def get_supplier_details(self, seller_name, subcategory_ids, product_item_filter=None, scope='WORLDWIDE'):
        """
        Get detailed stats, sparklines, and history for a specific supplier within a category.
        """
        # 1. First, build the MARKET queryset (all transactions for these products in this scope)
        market_qs = Transaction.objects.all()
        if subcategory_ids:
            market_qs = market_qs.filter(product_item__sub_category_id__in=subcategory_ids)
            
        scope = scope or 'WORLDWIDE'
        if scope == 'EXPORT':
            market_qs = market_qs.filter(trade_type='EXPORT')
        elif scope == 'PAKISTAN':
            market_qs = market_qs.filter(trade_type='EXPORT', origin_country='Pakistan')
        else:
            market_qs = market_qs.filter(trade_type='IMPORT')

        if product_item_filter:
            market_qs = market_qs.filter(product_item__id__in=product_item_filter)

        # 2. Derive the ENTITY queryset from the market queryset
        queryset = market_qs.filter(seller__iexact=seller_name.strip()).order_by('-reporting_date')

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
            valid_price = float(entry['price'] or 0)
            if valid_price > 0:
                sparkline.append({
                    "date": entry['month'].strftime("%Y-%m-%d"),
                    "volume": float(entry['vol'] or 0),
                    "price": valid_price
                })
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
        # Unique buyers total — across ALL transactions for this seller (not scoped to product)
        total_unique_buyers = Transaction.objects.filter(
            seller__iexact=seller_name.strip()
        ).values('buyer').distinct().count()
        
        # Unique buyers last 30d (approx, since reporting_date is date)
        last_month_start = datetime.date.today() - datetime.timedelta(days=30)
        recent_buyers = queryset.filter(reporting_date__gte=last_month_start).values('buyer').distinct().count()
        
        intelligence = self._calculate_intelligence(queryset, is_buyer=False, entity_name=seller_name)
        overview = self._compute_overview_metrics(queryset, is_buyer=False, intelligence=intelligence)

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
                "total_relationships": total_unique_buyers,
                "recent_buyers": recent_buyers
            },
            "sparkline": sparkline,
            "history": history,
            "intelligence": intelligence,
            "overview": overview,
            "market_pricing": self._compute_market_pricing(queryset, market_qs, is_buyer=False, entity_name=seller_name),
            "company_intel": self._compute_company_profile(seller_name, is_buyer=False)
        }

    def get_buyer_details(self, buyer_name, subcategory_ids, product_item_filter=None, scope='WORLDWIDE'):
        """
        Get detailed stats, sparklines, and history for a specific BUYER within a category.
        """
        # 1. First, build the MARKET queryset
        market_qs = Transaction.objects.all()
        if subcategory_ids:
            market_qs = market_qs.filter(product_item__sub_category_id__in=subcategory_ids)
            
        scope = scope or 'WORLDWIDE'
        if scope == 'IMPORT':
            market_qs = market_qs.filter(trade_type='IMPORT')
        elif scope == 'PAKISTAN':
            market_qs = market_qs.filter(trade_type='IMPORT', destination_country='Pakistan')
        else:  # EXPORT or WORLDWIDE
            market_qs = market_qs.filter(trade_type='EXPORT')
        
        if product_item_filter:
            market_qs = market_qs.filter(product_item__id__in=product_item_filter)

        # 2. Derive the ENTITY queryset
        queryset = market_qs.filter(buyer__iexact=buyer_name.strip()).order_by('-reporting_date')



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
            valid_price = float(entry['price'] or 0)
            if valid_price > 0:
                sparkline.append({
                    "date": entry['month'].strftime("%Y-%m-%d"),
                    "volume": float(entry['vol'] or 0),
                    "price": valid_price
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

        # 6. Supplier Insights from Buyer perspective — "Who are they buying from?"
        # Total unique sellers across ALL transactions for this buyer (lifetime)
        total_unique_sellers = Transaction.objects.filter(
            buyer__iexact=buyer_name.strip()
        ).values('seller').distinct().count()
        
        last_month_start = datetime.date.today() - datetime.timedelta(days=30)
        recent_suppliers = queryset.filter(reporting_date__gte=last_month_start).values('seller').distinct().count()
        
        intelligence = self._calculate_intelligence(queryset, is_buyer=True, entity_name=buyer_name)
        overview = self._compute_overview_metrics(queryset, is_buyer=True, intelligence=intelligence)

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
                "total_relationships": total_unique_sellers,
                "recent_suppliers": recent_suppliers
            },
            "sparkline": sparkline,
            "history": history,
            "intelligence": intelligence,
            "overview": overview,
            "market_pricing": self._compute_market_pricing(queryset, market_qs, is_buyer=True, entity_name=buyer_name),
            "company_intel": self._compute_company_profile(buyer_name, is_buyer=True)
        }

    def _compute_overview_metrics(self, queryset, is_buyer=False, intelligence=None):
        """
        Compute all metrics needed for the Overview tab.
        Pass pre-computed intelligence dict to avoid a double DB call.
        """
        from django.db.models import Sum, Count, Avg, Min, Max, Case, When, Value, CharField
        from django.db.models.functions import TruncMonth
        import datetime

        # ── Active Period ──────────────────────────────────────────────────
        dates      = queryset.aggregate(first=Min('reporting_date'), last=Max('reporting_date'))
        first_date = dates['first']
        last_date  = dates['last']

        active_period    = 'N/A'
        last_active      = 'N/A'
        vol_trend_text   = None
        price_trend_text = None

        if first_date and last_date:
            months_span = (last_date.year - first_date.year) * 12 + (last_date.month - first_date.month)
            years = max(1, round(months_span / 12))
            year_str = f"{years} year{'s' if years != 1 else ''}"
            active_period = f"{first_date.strftime('%b %Y')} - {last_date.strftime('%b %Y')} ({year_str})"

            days_since = (datetime.date.today() - last_date).days
            if days_since <= 90:
                last_active = f"{last_date.strftime('%b %Y')} (Recent)"
            elif days_since <= 365:
                m = max(1, days_since // 30)
                last_active = f"{last_date.strftime('%b %Y')} ({m} month{'s' if m != 1 else ''} ago)"
            else:
                y = max(1, days_since // 365)
                last_active = f"{last_date.strftime('%b %Y')} ({y} year{'s' if y != 1 else ''} ago)"

        # ── Typical Shipment Size (25th–75th percentile) ───────────────────
        qtys = list(queryset.values_list('qty_mt', flat=True).order_by('qty_mt')[:500])
        typical_shipment_size = 'N/A'
        if qtys:
            n   = len(qtys)
            p25 = float(qtys[max(0, n * 25 // 100)])
            p75 = float(qtys[min(n - 1, n * 75 // 100)])
            if abs(p75 - p25) < 1:
                typical_shipment_size = f"{round(p25):,} MT per shipment"
            else:
                typical_shipment_size = f"{round(p25):,}\u2013{round(p75):,} MT per shipment"

        # ── Geographic Data ────────────────────────────────────────────────
        total_vol = float(queryset.aggregate(total=Sum('qty_mt'))['total'] or 0)

        geo_vols = list(
            queryset.values('origin_country')
                    .annotate(vol=Sum('qty_mt'))
                    .exclude(origin_country__isnull=True)
                    .exclude(origin_country='')
                    .order_by('-vol')[:5]
        )

        primary_region = 'N/A'
        geo_presence   = []
        geo_summary    = ''

        if geo_vols and total_vol > 0:
            top     = geo_vols[0]
            top_pct = round(float(top['vol']) / total_vol * 100)
            primary_region = f"{top['origin_country']} ({top_pct}% of volume)"

            for gv in geo_vols:
                vol = float(gv['vol'] or 0)
                pct = round(vol / total_vol * 100)
                if pct > 0:
                    geo_presence.append({'country': gv['origin_country'], 'volume_mt': round(vol), 'pct': pct})

            if len(geo_presence) >= 2:
                geo_summary = (f"Primarily {geo_presence[0]['country']}-sourced with secondary suppliers "
                               f"in {geo_presence[1]['country']}")
                if len(geo_presence) >= 3:
                    geo_summary += f" and {geo_presence[2]['country']}"
            elif geo_presence:
                geo_summary = f"Primarily sourced from {geo_presence[0]['country']}"

        # ── Top Counterparties ─────────────────────────────────────────────
        cp_field = 'seller' if is_buyer else 'buyer'

        top_cps = list(
            queryset.values(cp_field)
                    .annotate(vol=Sum('qty_mt'), count=Count('id'))
                    .exclude(**{cp_field + '__isnull': True})
                    .exclude(**{cp_field: ''})
                    .order_by('-vol')[:6]
        )

        top_cp_list = []
        for cp in top_cps[:5]:
            name = cp[cp_field] or 'Unknown'
            vol  = float(cp['vol'] or 0)
            top_cp_list.append({'name': name, 'volume_mt': round(vol),
                                 'shipment_count': cp['count'], 'is_others': False})

        total_cps = (queryset.values(cp_field)
                             .exclude(**{cp_field + '__isnull': True})
                             .exclude(**{cp_field: ''})
                             .distinct().count())
        if total_cps > 5:
            top5_vol   = sum(c['volume_mt'] for c in top_cp_list)
            others_vol = max(0, round(total_vol - top5_vol))
            top_cp_list.append({'name': f'+{total_cps - 5} other {"suppliers" if is_buyer else "buyers"}',
                                 'volume_mt': others_vol, 'shipment_count': None, 'is_others': True})

        if total_cps >= 6:
            cp_note = f"Diversified {'supplier' if is_buyer else 'buyer'} base with strong repeat relationships"
        elif total_cps >= 3:
            cp_note = f"Moderate {'supplier' if is_buyer else 'buyer'} base with established relationships"
        else:
            cp_note = f"Concentrated {'supplier' if is_buyer else 'buyer'} base with key long-term partners"

        # ── Shipment Size Distribution ─────────────────────────────────────
        size_dist_qs = queryset.annotate(
            bucket=Case(
                When(qty_mt__lt=50,  then=Value('Small (< 50 MT)')),
                When(qty_mt__lt=100, then=Value('Small (50\u2013100 MT)')),
                When(qty_mt__lt=200, then=Value('Medium (100\u2013200 MT)')),
                default=Value('Large (200+ MT)'),
                output_field=CharField(),
            )
        ).values('bucket').annotate(count=Count('id'))

        size_dict    = {s['bucket']: s['count'] for s in size_dist_qs}
        total_tx_cnt = sum(size_dict.values()) or 1
        bucket_order = ['Small (< 50 MT)', 'Small (50\u2013100 MT)', 'Medium (100\u2013200 MT)', 'Large (200+ MT)']
        size_distribution = [
            {'range': b, 'count': size_dict[b], 'pct': round(size_dict[b] / total_tx_cnt * 100)}
            for b in bucket_order if size_dict.get(b, 0) > 0
        ]

        # ── Frequency Pattern ──────────────────────────────────────────────
        monthly_data = list(
            queryset.annotate(month=TruncMonth('reporting_date'))
                    .values('month').annotate(count=Count('id')).order_by('month')
        )

        freq_label       = 'Sporadic'
        freq_desc        = 'Occasional activity with gaps'
        activity_pattern = 'Sporadic'

        if monthly_data:
            active_months = len(monthly_data)
            first_m, last_m = monthly_data[0]['month'], monthly_data[-1]['month']
            span = max(1, (last_m.year - first_m.year) * 12 + (last_m.month - first_m.month) + 1)
            rate  = active_months / span
            avg_pm = round(sum(m['count'] for m in monthly_data) / active_months, 1)

            if rate >= 0.8:
                freq_label, activity_pattern = 'Monthly Consistent', 'Consistent'
                freq_desc = f"Average {avg_pm} shipment{'s' if avg_pm != 1 else ''} per month"
            elif rate >= 0.5:
                freq_label, activity_pattern = 'Regular', 'Regular'
                freq_desc = f"Average {avg_pm} shipment{'s' if avg_pm != 1 else ''} per active month"
            else:
                freq_desc = f"Occasional activity ({active_months} active months over {span})"

            # Volume trend: compare first vs second half
            if len(monthly_data) >= 6:
                mid = len(monthly_data) // 2
                monthly_vols = list(
                    queryset.annotate(month=TruncMonth('reporting_date'))
                            .values('month').annotate(vol=Sum('qty_mt')).order_by('month')
                )
                first_vols = [float(m['vol'] or 0) for m in monthly_vols[:mid]]
                last_vols  = [float(m['vol'] or 0) for m in monthly_vols[mid:]]
                avg_fv = sum(first_vols) / len(first_vols) if first_vols else 0
                avg_lv = sum(last_vols)  / len(last_vols)  if last_vols  else 0
                if avg_fv > 0:
                    vpct = round((avg_lv - avg_fv) / avg_fv * 100)
                    vol_trend_text = (f"\u2191 +{vpct}% over period" if vpct > 0
                                     else f"\u2193 {vpct}% over period" if vpct < 0
                                     else "Stable over period")

            # Price trend
            monthly_prices = list(
                queryset.annotate(month=TruncMonth('reporting_date'))
                        .values('month').annotate(price=Avg('usd_per_mt')).order_by('month')
            )
            valid_mp = [float(m['price'] or 0) for m in monthly_prices if m.get('price')]
            if len(valid_mp) >= 6:
                mid_p = len(valid_mp) // 2
                avg_pf = sum(valid_mp[:mid_p]) / mid_p
                avg_pl = sum(valid_mp[mid_p:]) / (len(valid_mp) - mid_p)
                if avg_pf > 0:
                    ppct = round((avg_pl - avg_pf) / avg_pf * 100)
                    if ppct != 0:
                        price_trend_text = (f"\u2191 +{ppct}% trend" if ppct > 0 else f"\u2193 {ppct}% trend")

        # ── Behavioral Summary ─────────────────────────────────────────────
        behavioral_summary = 'Regular shipment activity observed'
        if size_distribution:
            dom = max(size_distribution, key=lambda x: x['count'])
            cadence = 'consistent' if activity_pattern == 'Consistent' else 'regular' if activity_pattern == 'Regular' else 'irregular'
            if 'Large' in dom['range']:
                behavioral_summary = f"Large bulk shipments with {cadence} cadence"
            elif 'Medium' in dom['range']:
                behavioral_summary = f"Mid-size bulk shipments with {cadence} cadence"
            else:
                behavioral_summary = f"Small frequent shipments with {cadence} cadence"

        # ── Market / Price Positioning ─────────────────────────────────────
        market_position_label = 'Mid-Range Competitive'
        market_position_desc  = 'Pricing positioned in the middle tier for this product category'
        price_stability       = 'Stable pricing with minimal volatility'

        if intelligence:
            pl = intelligence.get('pricing_label', '')
            ml = intelligence.get('momentum_label', '')
            if pl == 'Premium':
                market_position_label = 'Premium Positioned'
                market_position_desc  = 'Pricing positioned in the upper tier for this product category'
            elif pl == 'Competitive':
                market_position_label = 'Highly Competitive'
                market_position_desc  = 'Pricing positioned in the lower tier for this product category'
            elif pl == 'Opportunistic':
                market_position_label = 'Opportunistic Pricing'
                market_position_desc  = 'Pricing varies significantly based on market conditions'

            if ml == 'Growing':
                price_stability = 'Consistent with gradual upward trend'
            elif ml == 'Declining':
                price_stability = 'Showing gradual downward price movement'

        return {
            'active_period':           active_period,
            'last_active':             last_active,
            'typical_shipment_size':   typical_shipment_size,
            'primary_region':          primary_region,
            'top_counterparties':      top_cp_list,
            'top_counterparties_note': cp_note,
            'geo_presence':            geo_presence,
            'geo_summary':             geo_summary,
            'frequency_label':         freq_label,
            'frequency_desc':          freq_desc,
            'activity_pattern':        activity_pattern,
            'behavioral_summary':      behavioral_summary,
            'size_distribution':       size_distribution,
            'market_position_label':   market_position_label,
            'market_position_desc':    market_position_desc,
            'price_stability':         price_stability,
            'vol_trend_text':          vol_trend_text,
            'price_trend_text':        price_trend_text,
        }

    def _calculate_intelligence(self, queryset, is_buyer=False, entity_name=""):
        """
        Calculates dynamic intelligence metrics based on a queryset of transactions.
        """
        if not queryset.exists():
            return None

        # 1. Repeat Ratio
        # Counterparty field depends on perspective
        cp_field = 'seller' if is_buyer else 'buyer'
        total_tx = queryset.count()
        
        # Count counterparties with more than 1 transaction in this data
        cp_counts = queryset.values(cp_field).annotate(count=Count('id')).filter(count__gt=1)
        repeat_counts_sum = sum(c['count'] for c in cp_counts)
        
        repeat_ratio = round((repeat_counts_sum / total_tx) * 100) if total_tx > 0 else 0
        
        repeat_label = "Strong" if repeat_ratio > 70 else "Moderate" if repeat_ratio > 30 else "Low"

        # 2. Concentration Ratio (Top 3 counterparties by volume)
        total_vol = queryset.aggregate(total=Sum('qty_mt'))['total'] or 0
        top_cp_vol = queryset.values(cp_field).annotate(vol=Sum('qty_mt')).order_by('-vol')[:3]
        top_3_vol = sum(c['vol'] for c in top_cp_vol)
        
        concentration_ratio = round((top_3_vol / total_vol) * 100) if total_vol > 0 else 0
        concentration_label = "High" if concentration_ratio > 60 else "Moderate" if concentration_ratio > 30 else "Low"

        # 3. Pricing Label
        # Based on price trend and volatility
        # Cast to float — Django Avg() returns Decimal which breaks math.sqrt / division
        avg_price = float(queryset.aggregate(avg=Avg('usd_per_mt'))['avg'] or 0)
        prices = [float(p) for p in queryset.values_list('usd_per_mt', flat=True)]
        
        # Simple Volatility (Std Dev approximation)
        if len(prices) > 1:
            variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
            volatility = math.sqrt(variance)
            vol_ratio = volatility / avg_price if avg_price > 0 else 0
        else:
            vol_ratio = 0

        # Price Trend (Latest vs First in the dataset)
        latest_tx = queryset.order_by('-reporting_date').first()
        earliest_tx = queryset.order_by('reporting_date').first()
        
        if latest_tx and earliest_tx and latest_tx.qty_mt > 0:
            price_change = (latest_tx.usd_per_mt - earliest_tx.usd_per_mt) / earliest_tx.usd_per_mt if earliest_tx.usd_per_mt > 0 else 0
        else:
            price_change = 0

        if is_buyer:
            # Buyer perspective: Price Sensitivity
            if vol_ratio > 0.15: pricing_label = "Opportunistic"
            elif price_change < -0.05: pricing_label = "High Sensitivity"
            else: pricing_label = "Stable Procurement"
        else:
            # Supplier perspective: Pricing Power
            if price_change > 0.05 and repeat_ratio > 50: pricing_label = "Premium"
            elif price_change < -0.05: pricing_label = "Competitive"
            else: pricing_label = "Stable"

        # 4. Momentum Label
        # Based on shipment growth in last 90 days vs previous 90
        today = datetime.date.today()
        last_90 = today - datetime.timedelta(days=90)
        prev_90 = today - datetime.timedelta(days=180)
        
        vol_recent = queryset.filter(reporting_date__gte=last_90).aggregate(s=Sum('qty_mt'))['s'] or 0
        vol_prev = queryset.filter(reporting_date__gte=prev_90, reporting_date__lt=last_90).aggregate(s=Sum('qty_mt'))['s'] or 0
        
        growth = (vol_recent - vol_prev) / vol_prev if vol_prev > 0 else 0
        
        if growth > 0.1: momentum_label = "Growing"
        elif growth < -0.1: momentum_label = "Declining"
        else: momentum_label = "Stable"
        
        # If no recent volume but has history
        if vol_recent == 0 and total_vol > 0:
            momentum_label = "Declining"

        # 5. Generated Summary
        summary = ""
        if is_buyer:
             summary = f"is a {momentum_label.lower()} buyer with {concentration_label.lower()} supplier concentration. They show {pricing_label.lower()} behavior in recent transactions."
        else:
             summary = f"maintains a {momentum_label.lower()} market position with {repeat_label.lower()} customer loyalty and {pricing_label.lower()} pricing characteristics."

        return {
            "repeat_ratio": repeat_ratio,
            "repeat_label": repeat_label,
            "concentration_ratio": concentration_ratio,
            "concentration_label": concentration_label,
            "pricing_label": pricing_label,
            "momentum_label": momentum_label,
            "generated_summary": summary
        }

    def get_supplier_comparison(self, company_names, subcategory_ids, product_item_filter=None, scope='WORLDWIDE', intent='BUY'):
        """
        Get aggregated stats for a list of companies for side-by-side comparison.
        """
        from django.db.models import Min, Max, Sum, Avg, Count
        from django.db.models.functions import TruncMonth

        results = []
        for company in company_names:
            if intent == 'SELL':
                queryset = Transaction.objects.filter(buyer__iexact=company.strip())
            else:
                queryset = Transaction.objects.filter(seller__iexact=company.strip())
                
            if subcategory_ids:
                queryset = queryset.filter(product_item__sub_category_id__in=subcategory_ids)
                
            scope = scope or 'WORLDWIDE'
            if intent == 'SELL':
                # Buyers appear on EXPORT transactions (Pakistani seller exporting to foreign buyer)
                if scope == 'PAKISTAN':
                    queryset = queryset.filter(trade_type='IMPORT', destination_country='Pakistan')
                else:
                    queryset = queryset.filter(trade_type='EXPORT').exclude(destination_country='Pakistan')
            else:
                # Sellers appear on IMPORT transactions (Pakistani buyer importing from foreign seller)
                if scope == 'PAKISTAN':
                    queryset = queryset.filter(trade_type='EXPORT', origin_country='Pakistan')
                else:
                    queryset = queryset.filter(trade_type='IMPORT')

            if product_item_filter:
                queryset = queryset.filter(product_item__id__in=product_item_filter)

            if not queryset.exists():
                continue

            # Stats
            stats = queryset.aggregate(
                total_volume=Sum('qty_mt'),
                avg_price=Avg('usd_per_mt'),
                min_price=Min('usd_per_mt'),
                max_price=Max('usd_per_mt'),
                shipment_count=Count('id'),
                last_shipment_date=Max('reporting_date')
            )

            # Sparklines (Monthly Aggregation)
            monthly_data = queryset.annotate(
                month=TruncMonth('reporting_date')
            ).values('month').annotate(
                price=Avg('usd_per_mt')
            ).order_by('month')

            sparkline = []
            for entry in monthly_data:
                valid_price = float(entry['price'] or 0)
                if valid_price > 0:
                    sparkline.append({
                        "date": entry['month'].strftime("%Y-%m-%d"),
                        "price": valid_price
                    })

            # Countries
            if intent == 'SELL':
                # For buyers, we care about where they are buying from (origin) or who they are (destination)
                # Actually, buyer's primary location is destination_country.
                primary_qs = queryset.values('destination_country').annotate(c=Count('id')).order_by('-c').first()
                primary_country = primary_qs['destination_country'] if primary_qs else 'Unknown'
                
                # Associated countries: where do they import from?
                if scope == 'PAKISTAN':
                    ships_to = ['Pakistan']
                else:
                    origins = list(queryset.values_list('origin_country', flat=True).distinct())
                    ships_to = [c for c in origins if c and c.strip()]
            else:
                # For sellers
                if scope == 'PAKISTAN':
                    dests = list(queryset.values_list('destination_country', flat=True).distinct())
                    countries = [c for c in dests if c and c.strip()]
                    primary_country = 'Pakistan'
                    ships_to = countries
                else:
                    primary_qs = queryset.values('origin_country').annotate(c=Count('id')).order_by('-c').first()
                    primary_country = primary_qs['origin_country'] if primary_qs else 'Unknown'
                    ships_to = ['Pakistan']

            results.append({
                "name": company,
                "country": primary_country,
                "avg_price": float(stats['avg_price'] or 0),
                "price_min": float(stats['min_price'] or 0),
                "price_max": float(stats['max_price'] or 0),
                "total_volume": float(stats['total_volume'] or 0),
                "shipment_count": stats['shipment_count'] or 0,
                "last_active": stats['last_shipment_date'].strftime("%b %Y") if stats['last_shipment_date'] else None,
                "ships_to": ships_to,
                "sparkline": sparkline
            })

        return results

    def _compute_market_pricing(self, entity_qs, market_qs, is_buyer, entity_name):
        """
        Computes market-level metrics and benchmarks the specific entity against the market.
        Used for the 'Market & Pricing' sub-tab.
        """
        result = {}
        
        # 1. Market Overview
        market_stats = market_qs.aggregate(
            total_vol=Sum('qty_mt'),
            total_tx=Count('id'),
            min_price=Min('usd_per_mt'),
            max_price=Max('usd_per_mt')
        )
        total_market_vol = float(market_stats['total_vol'] or 0)
        
        trade_dir = market_qs.values_list('trade_type', flat=True).first() or "Unknown"
        
        if is_buyer:
            top_route_qs = market_qs.values('destination_country', 'origin_country').annotate(v=Sum('qty_mt')).order_by('-v').first()
            top_route = f"{top_route_qs['origin_country']} → {top_route_qs['destination_country']}" if top_route_qs else "Unknown"
        else:
            top_route_qs = market_qs.values('origin_country', 'destination_country').annotate(v=Sum('qty_mt')).order_by('-v').first()
            top_route = f"{top_route_qs['origin_country']} → {top_route_qs['destination_country']}" if top_route_qs else "Unknown"

        result["overview"] = {
            "total_volume": total_market_vol,
            "total_transactions": market_stats['total_tx'],
            "trade_direction": trade_dir,
            "top_route": top_route
        }
        
        # 2. Price Intelligence (Monthly Trend)
        monthly_market = market_qs.annotate(
            month=TruncMonth('reporting_date')
        ).values('month').annotate(
            avg_price=Avg('usd_per_mt'),
            vol=Sum('qty_mt')
        ).order_by('month')
        
        market_trend = []
        prices = []
        for m in monthly_market:
            m_price = float(m['avg_price'] or 0)
            if m_price > 0:
                prices.append(m_price)
            market_trend.append({
                "date": m['month'].strftime("%Y-%m-%d"),
                "price": m_price,
                "volume": float(m['vol'] or 0)
            })
        
        prices.sort()
        median_price = prices[len(prices)//2] if prices else 0.0
        
        result["price_intelligence"] = {
            "trend": market_trend,
            "min": float(market_stats['min_price'] or 0),
            "max": float(market_stats['max_price'] or 0),
            "median": median_price
        }

        # 3. Supplier/Buyer Price Positioning
        entity_stats = entity_qs.aggregate(
            weighted_price_sum=Sum(ExpressionWrapper(F('qty_mt') * F('usd_per_mt'), output_field=FloatField())),
            total_vol=Sum('qty_mt')
        )
        e_vol = float(entity_stats['total_vol'] or 0)
        e_wps = float(entity_stats.get('weighted_price_sum') or 0)
        entity_avg_price = round(e_wps / e_vol, 2) if e_vol > 0 else 0.0

        market_wps_agg = market_qs.aggregate(
            weighted_price_sum=Sum(ExpressionWrapper(F('qty_mt') * F('usd_per_mt'), output_field=FloatField()))
        )
        m_wps = float(market_wps_agg.get('weighted_price_sum') or 0)
        market_avg_price = round(m_wps / total_market_vol, 2) if total_market_vol > 0 else 0.0

        diff_pct = 0.0
        if market_avg_price > 0:
            diff_pct = round(((entity_avg_price - market_avg_price) / market_avg_price) * 100, 1)

        result["positioning"] = {
            "market_avg": market_avg_price,
            "entity_avg": entity_avg_price,
            "differential_pct": diff_pct
        }

        # 4. Country Level Pricing & Volume
        geo_field = 'destination_country' if is_buyer else 'origin_country'
        country_agg = market_qs.values(geo_field).annotate(
            avg_price=Avg('usd_per_mt'),
            vol=Sum('qty_mt')
        ).order_by('-vol')

        country_metrics = []
        for c in country_agg:
            v_amt = float(c['vol'] or 0)
            sh = (v_amt / total_market_vol * 100) if total_market_vol > 0 else 0
            country_metrics.append({
                "country": c[geo_field],
                "avg_price": float(c['avg_price'] or 0),
                "volume": v_amt,
                "share_pct": round(sh, 1)
            })
        
        result["country_pricing"] = country_metrics

        # 5. Supply Chain Flow
        routes = market_qs.values('origin_country', 'destination_country').annotate(
            vol=Sum('qty_mt'),
            avg_p=Avg('usd_per_mt')
        ).order_by('-vol')[:10]
        
        flow = []
        for r in routes:
            v_amt = float(r['vol'] or 0)
            sh = (v_amt / total_market_vol * 100) if total_market_vol > 0 else 0
            flow.append({
                "source": r['origin_country'],
                "destination": r['destination_country'],
                "volume": v_amt,
                "share_pct": round(sh, 1),
                "avg_price": float(r['avg_p'] or 0)
            })
        result["supply_chain"] = flow

        # 6. Demand & Volume Trends
        # We reuse the market_trend list but calculate direction
        if len(market_trend) >= 6:
            last_3 = sum(x['volume'] for x in market_trend[-3:])
            prev_3 = sum(x['volume'] for x in market_trend[-6:-3])
            trend_val = ((last_3 - prev_3) / prev_3 * 100) if prev_3 > 0 else 0
        else:
            trend_val = 0
            
        peak_month = max(market_trend, key=lambda x: x['volume']) if market_trend else None
        low_month = min(market_trend, key=lambda x: x['volume']) if market_trend else None

        result["demand_trends"] = {
            "trend_direction_pct": round(trend_val, 1),
            "peak_period": peak_month['date'] if peak_month else None,
            "low_period": low_month['date'] if low_month else None
        }

        # 7. Competitive Benchmarking
        competitor_field = 'seller'
        competitors = market_qs.values(competitor_field).annotate(
            total_vol=Sum('qty_mt'),
            wps=Sum(ExpressionWrapper(F('qty_mt') * F('usd_per_mt'), output_field=FloatField()))
        ).order_by('-total_vol')[:50]  # Get top 50 for the scatter plot
        
        comp_data = []
        for cpt in competitors:
            c_name = cpt[competitor_field]
            if not c_name: continue
            
            c_vol = float(cpt['total_vol'] or 0)
            c_wps = float(cpt.get('wps') or 0)
            c_avg = round(c_wps / c_vol, 2) if c_vol > 0 else 0.0
            
            c_diff = 0.0
            if market_avg_price > 0:
                c_diff = round(((c_avg - market_avg_price) / market_avg_price) * 100, 1)

            comp_data.append({
                "name": c_name,
                "volume": c_vol,
                "avg_price": c_avg,
                "is_current": c_name.lower() == entity_name.lower(),
                "price_diff": c_diff
            })
            
        result["benchmarks"] = comp_data

        return result

    def _compute_company_profile(self, entity_name, is_buyer):
        """
        Computes the entirely unified metrics for the Company across ALL their products.
        """
        import datetime
        from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, FloatField
        from django.db.models.functions import TruncQuarter

        # 1. Base Queryset (All products for this entity)
        entity_q = entity_name.strip()
        if is_buyer:
            qs = Transaction.objects.filter(buyer__iexact=entity_q)
            partner_field = 'seller'
            route_label = 'origin_country' # the countries they source from
            export_label = 'destination_country' # countries they export to (rare if they are pure buyer acting as supplier here? well entity could be both)
        else:
            qs = Transaction.objects.filter(seller__iexact=entity_q)
            partner_field = 'buyer'
            route_label = 'destination_country'
            export_label = 'origin_country'
            
        total_tx = qs.count()
        if total_tx == 0:
            return None
            
        # Overall KPIs
        stats = qs.aggregate(
            vol=Sum('qty_mt'),
            val=Sum(ExpressionWrapper(F('qty_mt') * F('usd_per_mt'), output_field=FloatField()))
        )
        total_vol = float(stats['vol'] or 0)
        total_val = float(stats['val'] or 0)

        # Trade Direction
        import_tx = qs.filter(trade_type='IMPORT').count()
        export_tx = qs.filter(trade_type='EXPORT').count()
        if total_tx > 0:
            dominant_direction = "Export" if export_tx > import_tx else "Import"
            direction_pct = round(max(export_tx, import_tx) / total_tx * 100)
        else:
            dominant_direction = "Unknown"
            direction_pct = 0

        # Product Portfolio
        products = qs.values('product_item__sub_category__name').annotate(
            vol=Sum('qty_mt'),
            wps=Sum(ExpressionWrapper(F('qty_mt') * F('usd_per_mt'), output_field=FloatField()))
        ).order_by('-vol')
        
        portfolio = []
        for p in products:
            p_vol = float(p['vol'] or 0)
            if p_vol <= 0: continue
            p_val = float(p.get('wps') or 0)
            p_avg = round(p_val / p_vol, 2)
            share = round((p_vol / total_vol * 100), 1) if total_vol > 0 else 0
            
            p_name = p['product_item__sub_category__name'] or "Unknown Product Category"
            portfolio.append({
                "product": p_name,
                "volume": p_vol,
                "avg_price": p_avg,
                "share_pct": share
            })
            
        top_products = portfolio[:5]
        
        # Partner Network
        partners = qs.values(partner_field).annotate(
            vol=Sum('qty_mt'),
            first_tx=Min('reporting_date'),
            last_tx=Max('reporting_date'),
            tx_count=Count('id')
        ).order_by('-vol')
        
        partner_list = []
        total_partners = len([p for p in partners if p[partner_field]])
        long_term_partners = 0
        total_relationship_days = 0
        relationships_counted = 0
        repeat_partners = 0

        for p in partners:
            p_name = p.get(partner_field)
            if not p_name: continue
            
            p_vol = float(p['vol'] or 0)
            share = round((p_vol / total_vol * 100), 1) if total_vol > 0 else 0
            
            # Days between first and last tx
            first_d = p['first_tx']
            last_d = p['last_tx']
            days_length = 0
            if first_d and last_d:
                days_length = (last_d - first_d).days
                total_relationship_days += days_length
                relationships_counted += 1
                if days_length >= 365:
                    long_term_partners += 1
                    
            if p['tx_count'] > 1:
                repeat_partners += 1
            
            partner_list.append({
                "name": p_name,
                "volume": p_vol,
                "share_pct": share
            })
            
        top_partners = partner_list[:5]
        
        # Partner Concentration check
        top_5_share = sum(p['share_pct'] for p in top_partners)
        if top_5_share > 80:
            concentration_label = "Highly Concentrated"
        elif top_5_share > 50:
            concentration_label = "Moderately Diversified"
        else:
            concentration_label = "Highly Diversified"
            
        avg_rel_length_years = round((total_relationship_days / relationships_counted) / 365.25, 1) if relationships_counted > 0 else 0.0
        repeat_ratio = round((repeat_partners / total_partners) * 100) if total_partners > 0 else 0

        # Geographic Presence (Export = destination for a Supplier, or source for a Buyer)
        # We will calculate top Origins and top Destinations.
        def get_geo(field):
            geo = qs.values(field).annotate(vol=Sum('qty_mt')).order_by('-vol')
            g_list = []
            for g in geo:
                if not g[field]: continue
                v = float(g['vol'] or 0)
                sh = round((v / total_vol * 100), 1) if total_vol > 0 else 0
                g_list.append({"country": g[field], "volume": v, "share_pct": sh})
            return g_list[:5]
            
        export_geo = get_geo('destination_country')
        source_geo = get_geo('origin_country')

        # Activity & Growth Trends (Quarterly)
        qtr_trends = qs.annotate(
            qtr=TruncQuarter('reporting_date')
        ).values('qtr').annotate(
            vol=Sum('qty_mt')
        ).order_by('qtr')
        
        activity_trends = []
        for q in qtr_trends:
            if not q['qtr']: continue
            q_date = q['qtr']
            # Format as Q1 2022
            quarter = (q_date.month - 1) // 3 + 1
            activity_trends.append({
                "date_raw": q_date,
                "qtr": f"Q{quarter} {q_date.year}",
                "volume": float(q['vol'] or 0)
            })
            
        # YoY Growth
        # To calculate YoY, let's take the last 4 quarters vs the previous 4 quarters from the activity_trends
        yoy_growth = 0
        trend_label = "Stable"
        peak_qtr = "N/A"
        if len(activity_trends) > 0:
            peak = max(activity_trends, key=lambda x: x['volume'])
            peak_qtr = peak['qtr']
            
            if len(activity_trends) >= 8:
                last_4 = sum(x['volume'] for x in activity_trends[-4:])
                prev_4 = sum(x['volume'] for x in activity_trends[-8:-4])
                if prev_4 > 0:
                    yoy_growth = round(((last_4 - prev_4) / prev_4) * 100)
                    if yoy_growth > 5: trend_label = "Growing"
                    elif yoy_growth < -5: trend_label = "Declining"
            elif len(activity_trends) >= 2:
                # Fallback to simple latest vs previous if we don't have enough data
                last_1 = activity_trends[-1]['volume']
                prev_1 = activity_trends[-2]['volume']
                if prev_1 > 0:
                    yoy_growth = round(((last_1 - prev_1) / prev_1) * 100)
                    if yoy_growth > 5: trend_label = "Growing"
                    elif yoy_growth < -5: trend_label = "Declining"
                    
        # Product <-> Partner Mapping
        # For the top 5 products, who are the top 3 buyers/sellers?
        product_names = [p['product'] for p in top_products]
        mapping = []
        for p_name in product_names:
            p_qs = qs.filter(product_item__sub_category__name=p_name).values(partner_field).annotate(vol=Sum('qty_mt')).order_by('-vol')
            p_partners = []
            for pq in p_qs:
                if not pq[partner_field]: continue
                p_partners.append({"name": pq[partner_field], "volume": float(pq['vol'] or 0)})
            p_partners = p_partners[:3]
            mapping.append({
                "product": p_name,
                "partners": p_partners
            })

        return {
            "overview": {
                "total_volume": total_vol,
                "total_transactions": total_tx,
                "trade_value": total_val,
                "trade_direction_label": dominant_direction,
                "trade_direction_pct": direction_pct
            },
            "portfolio": {
                "top": top_products,
                "all_count": len(portfolio)
            },
            "network": {
                "top": top_partners,
                "total_count": total_partners,
                "concentration_label": concentration_label,
                "top_5_share_pct": top_5_share
            },
            "geography": {
                "exports": export_geo,
                "sources": source_geo
            },
            "trends": {
                "quarterly": [{ "qtr": x["qtr"], "volume": x["volume"] } for x in activity_trends],
                "yoy_growth": yoy_growth,
                "trend_label": trend_label,
                "peak_qtr": peak_qtr,
                "status": "Active" # Or calculate based on recent activity
            },
            "behavior": {
                "unique_partners": total_partners,
                "repeat_ratio_pct": repeat_ratio,
                "avg_length_years": avg_rel_length_years,
                "long_term_partners": long_term_partners
            },
            "mapping": mapping
        }

    def get_supplier_transactions(self, entity_name, is_buyer, subcat_ids, product_item_filter, scope, filters, page, page_size):
        """
        Gets paginated transactions with server-side filtering for the Transactions Tab.
        """
        queryset = Transaction.objects.all()

        # Apply Product constraints
        if subcat_ids:
            queryset = queryset.filter(product_item__sub_category_id__in=subcat_ids)
        if product_item_filter:
            queryset = queryset.filter(product_item__id__in=product_item_filter)

        # Apply Scope 
        scope = scope or 'WORLDWIDE'
        if is_buyer:
            if scope == 'PAKISTAN':
                queryset = queryset.filter(trade_type='IMPORT', destination_country='Pakistan')
            elif scope == 'IMPORT':
                queryset = queryset.filter(trade_type='IMPORT')
            else:
                queryset = queryset.filter(trade_type='EXPORT')
            queryset = queryset.filter(buyer__iexact=entity_name.strip())
            cp_field = 'seller'
            cp_country_field = 'origin_country'
        else:
            if scope == 'PAKISTAN':
                queryset = queryset.filter(trade_type='EXPORT', origin_country='Pakistan')
            else:
                queryset = queryset.filter(trade_type='IMPORT')
            queryset = queryset.filter(seller__iexact=entity_name.strip())
            cp_field = 'buyer'
            cp_country_field = 'destination_country'

        # Apply User Filters
        if filters.get('start_date'):
            queryset = queryset.filter(reporting_date__gte=filters['start_date'])
        if filters.get('end_date'):
            queryset = queryset.filter(reporting_date__lte=filters['end_date'])
        if filters.get('min_qty'):
            queryset = queryset.filter(qty_mt__gte=filters['min_qty'])
        if filters.get('max_qty'):
            queryset = queryset.filter(qty_mt__lte=filters['max_qty'])
        if filters.get('min_price'):
            queryset = queryset.filter(usd_per_mt__gte=filters['min_price'])
        if filters.get('max_price'):
            queryset = queryset.filter(usd_per_mt__lte=filters['max_price'])

        if is_buyer and filters.get('seller'):
            queryset = queryset.filter(seller__icontains=filters['seller'])
        elif not is_buyer and filters.get('buyer'):
            queryset = queryset.filter(buyer__icontains=filters['buyer'])

        if filters.get('country') and filters['country'].lower() != 'all countries':
            queryset = queryset.filter(**{f"{cp_country_field}__iexact": filters['country']})

        # Calculate Summaries (based on filtered data)
        stats = queryset.aggregate(
            total_vol=Sum('qty_mt'),
            total_tx=Count('id'),
            avg_price=Avg('usd_per_mt')
        )

        total_tx = stats['total_tx'] or 0
        total_vol = float(stats['total_vol'] or 0)
        avg_price = float(stats['avg_price'] or 0)

        # Top Counterparties (based on filtered data)
        # Handle cases where cp_field might be null
        top_cps = list(
            queryset.exclude(**{f"{cp_field}__isnull": True})
                    .exclude(**{f"{cp_field}": ''})
                    .values(cp_field)
                    .annotate(vol=Sum('qty_mt'))
                    .order_by('-vol')[:5]
        )
        top_cps_formatted = [{"name": cp[cp_field], "volume": float(cp['vol'] or 0)} for cp in top_cps]

        # Top Countries (based on filtered data)
        top_countries = list(
            queryset.exclude(**{f"{cp_country_field}__isnull": True})
                    .exclude(**{f"{cp_country_field}": ''})
                    .values(cp_country_field)
                    .annotate(vol=Sum('qty_mt'))
                    .order_by('-vol')[:3]
        )
        top_countries_formatted = [{"name": cp[cp_country_field], "volume": float(cp['vol'] or 0)} for cp in top_countries]

        # Pagination for Records
        offset = (page - 1) * page_size
        records_qs = queryset.order_by('-reporting_date')[offset : offset + page_size]

        records = []
        for tx in records_qs:
            records.append({
                "id": tx.id,
                "date": str(tx.reporting_date) if tx.reporting_date else "-",
                "buyer": tx.buyer or "-",
                "seller": tx.seller or "-",
                "country": getattr(tx, cp_country_field) or "-",
                "quantity": float(tx.qty_mt or 0),
                "price": float(tx.usd_per_mt or 0)
            })

        return {
            "summary": {
                "total_transactions": total_tx,
                "total_volume": total_vol,
                "average_price": avg_price
            },
            "top_entities": top_cps_formatted,
            "top_countries": top_countries_formatted,
            "records": records,
            "total_count": total_tx
        }
