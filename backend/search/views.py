from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

import logging
from .services.search_service import SearchService
from .services.aggregation import SupplierAggregator

logger = logging.getLogger(__name__)

# ============================================================
# GLOBAL INIT — models load once at startup
# ============================================================
logger.info("Initializing Global SearchService on Startup...")
global_search_service = SearchService()


class SearchViewSet(viewsets.ViewSet):
    """
    Revamped Modern Search API.
    Endpoints:
      GET /api/search/?q=...&scope=import&hs_code=1702.4  → supplier list
      GET /api/search/autocomplete/?q=dex                    → product suggestions
      GET /api/search/supplier-detail/?name=...&query=...    → supplier deep-dive
    """
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_service = global_search_service
        self.aggregator = SupplierAggregator()

    # ----------------------------------------------------------------
    # MAIN SEARCH — GET /api/search/?q=...
    # ----------------------------------------------------------------
    def list(self, request):
        query        = request.query_params.get('q', '').strip()
        scope_param  = request.query_params.get('scope', 'import').lower()
        hs_code      = request.query_params.get('hs_code', None)
        subcat_id    = request.query_params.get('subcat_id', None)   # Exact subcategory DB id
        variant_name = request.query_params.get('variant_name', None) # Exact product name user clicked
        intent       = request.query_params.get('intent', None)      # Explicit intent bypass

        if not query:
            return Response({"error": "Query parameter 'q' is required"}, status=400)

        ui_context = "export" if scope_param == "export" else "import"
        top_k = self._extract_top_n(query) or 100

        search_result = self.search_service.execute_search(
            raw_query=query,
            ui_context=ui_context,
            top_k=top_k,
            hs_code=hs_code,
            subcat_id=int(subcat_id) if subcat_id else None,
            variant_name=variant_name,
            explicit_intent=intent,
        )

        if search_result.get('is_category_bridge'):
            return Response({
                "is_category_bridge": True,
                "hs_code": search_result['hs_code']
            })

        parsed_query = search_result.get('nlu', {})
        raw_profiles = search_result.get('profiles', [])

        # ── Disambiguation — return early with variant picker ──────────
        if search_result.get('needs_disambiguation'):
            return Response({
                "query":                query,
                "parsed_query":         parsed_query,
                "needs_disambiguation": True,
                "variants":             search_result.get('variants', []),
                "results":              [],
                "matched_subcategories": [],
                "available_variants":   [],
                "active_variant":       None,
                "market_snapshot":      None,
                "count":                0,
            })

        # ── Normal results ─────────────────────────────────────────────
        mapped_results = []
        for p in raw_profiles:
            tx_count   = p["transaction_count"]
            total_vol  = p["total_volume"]
            avg_shipped = total_vol / tx_count if tx_count > 0 else 0

            mapped_results.append({
                "name":               p["company_name"],
                "country":            p.get("country", "N/A"),
                "total_volume":       round(float(total_vol), 3),
                "avg_price":          round(float(p.get("avg_price", 0.0)), 2),
                "shipment_count":     tx_count,
                "last_shipment_date": p["last_shipped"],
                "avg_shipment_vol":   round(float(avg_shipped), 3),
                "max_shipment_vol":   0,
                "type":               "Buyer" if p["type"] == "BUYER" else "Supplier",
                "hs_codes":           p.get("hs_codes", []),
                "volume_score":       p.get("volume_score"),
                "volume_fit":         p.get("volume_fit", "N/A"),
                "relevance_score":    p.get("relevance_score", 0.0),
            })

        prices = [r["avg_price"] for r in mapped_results if r["avg_price"] > 0]
        # Volume-weighted average price: high-volume suppliers dominate, tiny outliers get near-zero weight.
        _vw_num = sum(r["avg_price"] * r["total_volume"] for r in mapped_results if r["avg_price"] > 0 and r["total_volume"] > 0)
        _vw_den = sum(r["total_volume"] for r in mapped_results if r["avg_price"] > 0 and r["total_volume"] > 0)
        vw_avg_price = round(_vw_num / _vw_den, 2) if _vw_den > 0 else 0
        market_snapshot = {
            "total_count":      len(mapped_results),
            "avg_price_global": vw_avg_price,
            "top_country":      mapped_results[0]["country"] if mapped_results else "N/A",
        }

        return Response({
            "query":                query,
            "parsed_query":         parsed_query,
            "needs_disambiguation": False,
            "is_broad_search":      search_result.get("is_broad_search", False),
            "variants":             [],
            "matched_subcategories": [],
            "available_variants":  [],
            "active_variant":      None,
            "results":             mapped_results,
            "market_snapshot":     market_snapshot,
            "count":               len(mapped_results),
            "search_engine":       search_result.get("search_engine", "orm"),
        })

    # ----------------------------------------------------------------
    # AUTOCOMPLETE — GET /api/search/autocomplete/?q=dex
    # ----------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='autocomplete')
    def autocomplete(self, request):
        partial = request.query_params.get('q', '').strip()

        if len(partial) < 2:
            return Response([])

        suggestions = self.search_service.autocomplete_products(partial, limit=8)

        result = []
        for s in suggestions:
            label = s["name"]
            if s["total_volume"] > 0:
                label += f" ({s['total_volume']:,.0f} MT)"
            result.append({
                "label":        label,
                "name":         s["name"],
                "hs_code":      s["hs_code"],
                "category":     s["category"],
                "total_volume": s["total_volume"],
                "tx_count":     s["tx_count"],
            })

        return Response(result)

    # ----------------------------------------------------------------
    # HS CODE TREE — GET /api/search/hs-code-tree/?q=17
    # ----------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='hs-code-tree')
    def hs_code_tree(self, request):
        q = request.query_params.get('q', '').strip()
        
        from trade_data.models import Transaction, ProductCategory
        from django.db.models import Min, Count
        from django.db.models.functions import Substr
        
        results = []
        clean_q = q.replace(".", "")
        if len(clean_q) < 1:
            return Response(results)

        if len(clean_q) <= 2:
            # Chapter (1-2 digits) -> Derive 4-digit headings from Transaction.hs_code via Substr
            # ProductCategory does NOT store 4-digit codes, so Transaction is the ground truth.
            rows = (
                Transaction.objects
                .filter(hs_code__startswith=clean_q)
                .annotate(heading=Substr('hs_code', 1, 4))
                .values('heading')
                .annotate(count=Count('id'))
                .order_by('heading')[:20]
            )
            # Name lookup: ProductCategory stores codes like "1702.3"; there are no 4-digit rows.
            # Best we can do is group by heading prefix and pick the first category name.
            heading_names = {}
            for row in rows:
                h = row['heading']
                cat = ProductCategory.objects.filter(hs_code__startswith=h).values('name').first()
                heading_names[h] = cat['name'] if cat else f"Heading {h}"

            for row in rows:
                h = row['heading']
                results.append({"hs_code": h, "name": heading_names.get(h, h), "is_final": False})

        elif len(clean_q) <= 3:
            # 3 digits: still show 4-digit headings
            rows = (
                Transaction.objects
                .filter(hs_code__startswith=clean_q)
                .annotate(heading=Substr('hs_code', 1, 4))
                .values('heading')
                .annotate(count=Count('id'))
                .order_by('heading')[:20]
            )
            for row in rows:
                h = row['heading']
                cat = ProductCategory.objects.filter(hs_code__startswith=h).values('name').first()
                name = cat['name'] if cat else f"Heading {h}"
                results.append({"hs_code": h, "name": name, "is_final": False})

        elif len(clean_q) <= 7:
            # 4-7 digits: show distinct hs_codes from ProductCategory (the real tariff subcategory level)
            items = (
                ProductCategory.objects
                .filter(hs_code__startswith=q)
                .values('hs_code')
                .annotate(name=Min('name'))
                .order_by('hs_code')[:20]
            )
            for item in items:
                results.append({"hs_code": item['hs_code'], "name": item['name'], "is_final": True})

        else:
            # 8+ digits: exact tariff match
            items = (
                ProductCategory.objects
                .filter(hs_code__startswith=q)
                .values('hs_code')
                .annotate(name=Min('name'))
                .order_by('hs_code')[:5]
            )
            for item in items:
                results.append({"hs_code": item['hs_code'], "name": item['name'], "is_final": True})

        return Response(results)

    # ----------------------------------------------------------------
    # HS SUMMARY — GET /api/search/hs-summary/?q=1702
    # ----------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='hs-summary')
    def hs_summary(self, request):
        from trade_data.models import Transaction, ProductCategory, ProductSubCategory
        from django.db.models import Count, Min, Q
        from django.db.models.functions import Substr
        
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response({"error": "Query required"}, status=400)

        # Helper method for Context Naming
        def get_contextual_name(hs_code, base_name):
            vague_names = ["other", "other items", "not elsewhere specified"]
            if base_name.lower().strip() in vague_names:
                # Need parent context. If hs_code is 1704.909, parent is heading 1704 or similar
                four_digit = hs_code[:4]
                parent = ProductCategory.objects.filter(hs_code=four_digit).first()
                if parent:
                    return f"{parent.name} > {base_name}"
                elif len(hs_code) >= 6:
                    # try a closer parent
                    parent = ProductCategory.objects.filter(hs_code__startswith=hs_code[:6]).first()
                    if parent:
                        return f"{parent.name} > {base_name}"
            return base_name

        is_alpha = not all(c.isdigit() or c == '.' for c in q)
        
        if is_alpha:
            # Word search: like "Glucose" -> Find all matching codes in Category/Subcategory
            cat_qs = ProductCategory.objects.filter(name__icontains=q)
            subcat_qs = ProductSubCategory.objects.filter(name__icontains=q)
            
            matched_codes = {}
            for row in cat_qs:
                matched_codes[row.hs_code] = row.name
            for row in subcat_qs:
                if row.hs_code not in matched_codes:
                    matched_codes[row.hs_code] = row.name
                    
            results = []
            for hs, b_name in matched_codes.items():
                # Count transactions
                cnt = Transaction.objects.filter(hs_code__startswith=hs).count()
                if cnt > 0:
                    cname = get_contextual_name(hs, b_name)
                    is_leaf = len(hs.replace('.', '')) >= 5  # Arbitrary threshold for alpha matched codes
                    results.append({"hs_code": hs, "name": cname, "count": cnt, "is_leaf": is_leaf})
            
            results.sort(key=lambda x: x["count"], reverse=True)
            return Response(results)

        clean_q = q.replace(".", "")
        if not clean_q or len(clean_q) >= 7:
            return Response({"error": "Summary view only supports < 7 raw digits"}, status=400)
            
        if len(clean_q) <= 3:
            # Group Transactions by 4-digit heading (Substr of hs_code, stripping dots)
            qs = list(
                Transaction.objects
                .filter(hs_code__startswith=q if '.' in q else clean_q)
                .annotate(child_code=Substr('hs_code', 1, 4))
                .values('child_code')
                .annotate(count=Count('id'))
                .order_by('child_code')[:50]
            )
            results = []
            seen = set()
            for item in qs:
                c = item['child_code']
                if c in seen:
                    continue
                seen.add(c)
                cat = ProductCategory.objects.filter(hs_code__startswith=c).values('name').order_by('hs_code').first()
                name = f"Heading {c}"
                if cat:
                    from trade_data.models import Product
                    prod = Product.objects.filter(hs_code=c[:2]).values('name').first()
                    if prod:
                        name = f"{prod['name']} ({c})"
                    else:
                        name = f"Heading {c}"
                
                results.append({"hs_code": c, "name": get_contextual_name(c, name), "count": item['count'], "is_leaf": False})
        else:
            # 4-6 digits: Use the raw query
            qs = list(
                Transaction.objects
                .filter(hs_code__startswith=q)
                .values('hs_code')
                .annotate(count=Count('id'))
                .order_by('-count')[:50]
            )
            child_codes = [item['hs_code'] for item in qs]
            cat_query = ProductCategory.objects.filter(hs_code__in=child_codes).values('hs_code').annotate(name=Min('name'))
            name_map = {c['hs_code']: c['name'] for c in cat_query}
            
            results = []
            for item in qs:
                c = item['hs_code']
                b_name = name_map.get(c, f"Tariff {c}")
                results.append({
                    "hs_code": c,
                    "name": get_contextual_name(c, b_name),
                    "count": item['count'],
                    "is_leaf": True
                })
                
        return Response(results)

    # ----------------------------------------------------------------
    # HS DASHBOARD — GET /api/search/hs-dashboard/?q=1704.909&intent=FOREIGN_SUPPLIERS
    # ----------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='hs-dashboard')
    def hs_dashboard(self, request):
        from trade_data.models import Transaction, ProductCategory
        from django.db.models import Count, Sum, Avg, Max
        
        q = request.query_params.get('q', '').strip()
        intent = request.query_params.get('intent', 'FOREIGN_SUPPLIERS').upper()
        subcat_filter = request.query_params.get('subcat', None)
        
        if not q:
            return Response({"error": "HS code parameter 'q' is required"}, status=400)

        qs = Transaction.objects.filter(hs_code__startswith=q).select_related(
            'product_item', 'product_item__sub_category'
        )
        
        cat = ProductCategory.objects.filter(hs_code__startswith=q).values('hs_code', 'name').order_by('hs_code').first()
        hs_description = cat['name'] if cat else q
        total_count = qs.count()
        
        if intent in ('FOREIGN_SUPPLIERS', 'PAKISTANI_BUYERS'):
            qs = qs.filter(trade_type='IMPORT')
        else:
            qs = qs.filter(trade_type='EXPORT')

        if subcat_filter:
            subcat_names = [s.strip() for s in subcat_filter.split(',') if s.strip()]
            if subcat_names:
                qs = qs.filter(product_item__sub_category__name__in=subcat_names)

        # Sidebar: use ProductSubCategory names (clean tariff names, not raw invoice text)
        refinements = list(
            qs.values('product_item__sub_category__name')
              .annotate(count=Count('id'))
              .order_by('-count')
        )
        sidebar_counts = [
            {"name": r['product_item__sub_category__name'] or "Other", "count": r['count']}
            for r in refinements
        ]

        # Determine which entity field to aggregate by
        if intent in ('FOREIGN_SUPPLIERS', 'PAKISTANI_SUPPLIERS'):
            entity_field = 'seller'
            country_field = 'origin_country'
        else:
            entity_field = 'buyer'
            country_field = 'destination_country'

        raw_profiles = list(
            qs.values(entity_field, country_field)
              .annotate(
                  total_volume=Sum('qty_mt'),
                  avg_price=Avg('usd_per_mt'),
                  shipment_count=Count('id'),
                  last_shipment=Max('reporting_date'),
              )
              .order_by('-total_volume')[:50]
        )

        profiles = []
        for p in raw_profiles:
            vol   = float(p['total_volume'] or 0)
            price = float(p['avg_price'] or 0)
            count = p['shipment_count']
            profiles.append({
                "name":               p[entity_field] or "Unknown",
                "country":            p[country_field] or "N/A",
                "total_volume":       round(vol, 2),
                "avg_price":          round(price, 2),
                "shipment_count":     count,
                "last_shipment_date": str(p['last_shipment']) if p['last_shipment'] else None,
                "avg_shipment_vol":   round(vol / count, 2) if count > 0 else 0,
                "type":               "Supplier" if intent in ('FOREIGN_SUPPLIERS', 'PAKISTANI_SUPPLIERS') else "Buyer",
            })

        # Raw shipment rows — this is what the DataDashboard table renders
        raw_rows = qs.select_related('product_item__sub_category').order_by('-reporting_date')[:500]
        shipments = []
        for tx in raw_rows:
            shipments.append({
                "date":                str(tx.reporting_date),
                "description":         tx.product_item.sub_category.name if tx.product_item and tx.product_item.sub_category else (tx.product_item.name if tx.product_item else ""),
                "seller":              tx.seller,
                "buyer":               tx.buyer,
                "origin_country":      tx.origin_country,
                "destination_country": tx.destination_country,
                "quantity":            float(tx.qty_mt or 0),
                "price":               float(tx.usd_per_mt or 0) if tx.usd_per_mt else None,
            })

        return Response({
            "hs_code":          q,
            "hs_description":   hs_description,
            "total_shipments":  total_count,
            "sidebar_counts":   sidebar_counts,
            "profiles":         profiles,
            "shipments":        shipments,
        })


    # ----------------------------------------------------------------
    # SUPPLIER DETAIL — GET /api/search/supplier-detail/?name=...&query=...
    # ----------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='supplier-detail')
    def supplier_detail(self, request):
        seller_name = request.query_params.get('name')
        query       = request.query_params.get('query')
        subcat_id   = request.query_params.get('subcat_id')
        variant_name = request.query_params.get('variant_name')

        if not seller_name or not query:
            return Response({"error": "Params 'name' and 'query' are required"}, status=400)

        scope = request.query_params.get('scope', 'import').lower()
        orm_scope = 'EXPORT' if scope == 'export' else 'IMPORT'

        # Use the NLU cache — same key as execute_search uses — to avoid
        # a fresh LLM call that might return a different intent.
        import hashlib
        from django.core.cache import cache
        _cache_raw = f"nlu:{query.lower().strip()}:{scope}"
        _cache_key = "nlu_" + hashlib.md5(_cache_raw.encode()).hexdigest()
        parsed_query = cache.get(_cache_key)
        if parsed_query is None:
            parsed_query = self.search_service._nlu_engine.parse(query)

        intent = parsed_query.get('intent', 'BUY')

        # Resolve exact subcategory if selected from UI
        subcat_ids, _, product_item_ids = self.search_service._resolve_subcategories(
            product_keyword=parsed_query.get("product", ""),
            hs_code=parsed_query.get("hs_code", ""),
            intent=intent,
            subcat_id=int(subcat_id) if subcat_id else None,
            variant_name=variant_name,
            scope=orm_scope
        )

        # Route to the correct aggregator based on BOTH intent AND scope.
        if intent == 'SELL':
            details = self.aggregator.get_buyer_details(seller_name, subcat_ids, product_item_filter=product_item_ids, scope=orm_scope)
        else:
            details = self.aggregator.get_supplier_details(seller_name, subcat_ids, product_item_filter=product_item_ids, scope=orm_scope)

        if not details:
            entity_type = "Buyer" if intent == 'SELL' else "Supplier"
            return Response({"error": f"{entity_type} not found"}, status=404)

        return Response({
            "supplier":              details,
            "comparables":           [],
            "trade_lens_product_id": None,
            "type":                  "BUYER" if intent == 'SELL' else "SUPPLIER",
        })

    # ----------------------------------------------------------------
    # SUPPLIER COMPARE — GET /api/search/compare/?suppliers=A,B,C&query=...
    # ----------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='compare')
    def supplier_compare(self, request):
        suppliers_param = request.query_params.get('suppliers')
        query = request.query_params.get('query')
        subcat_id = request.query_params.get('subcat_id')
        variant_name = request.query_params.get('variant_name')
        scope = request.query_params.get('scope', 'import').lower()

        if not suppliers_param or not query:
            return Response({"error": "Params 'suppliers' and 'query' are required"}, status=400)

        seller_names = [s.strip() for s in suppliers_param.split(',')]
        orm_scope = 'EXPORT' if scope == 'export' else 'IMPORT'

        import hashlib
        from django.core.cache import cache
        _cache_raw = f"nlu:{query.lower().strip()}:{scope}"
        _cache_key = "nlu_" + hashlib.md5(_cache_raw.encode()).hexdigest()
        parsed_query = cache.get(_cache_key)
        if parsed_query is None:
            parsed_query = self.search_service._nlu_engine.parse(query)
        intent = request.query_params.get('intent')
        if not intent:
            intent = parsed_query.get('intent', 'BUY')
        intent = intent.upper()

        subcat_ids, _, product_item_ids = self.search_service._resolve_subcategories(
            product_keyword=parsed_query.get("product", ""),
            hs_code=parsed_query.get("hs_code", ""),
            intent=intent,
            subcat_id=int(subcat_id) if subcat_id else None,
            variant_name=variant_name,
            scope=orm_scope
        )

        comparison_data = self.aggregator.get_supplier_comparison(
            seller_names,
            subcat_ids,
            product_item_filter=product_item_ids,
            scope=orm_scope,
            intent=intent
        )
        return Response(comparison_data)

    def _extract_top_n(self, query):
        import re
        match = re.search(r'\b(?:top|best|first|suggest)\s+(\d+)\b', query.lower())
        return int(match.group(1)) if match else None
