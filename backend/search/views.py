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
                "hs_code": search_result['hs_code'],
                "subcat_id": search_result.get('subcat_id'),
                "variant_name": search_result.get('variant_name')
            })

        parsed_query = search_result.get('nlu', {})
        raw_profiles = search_result.get('profiles', [])

        # ── Scope Mismatch — product exists only in opposite scope ─────
        if search_result.get('scope_mismatch'):
            return Response({
                "query":                query,
                "parsed_query":         parsed_query,
                "needs_disambiguation": False,
                "scope_mismatch":       search_result['scope_mismatch'],
                "results":              [],
                "variants":             [],
                "market_snapshot":      None,
                "count":                0,
            })

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

        # ── Apply Access Restrictions ──────────────────────────────────────────
        from subscriptions.services import get_access_state, FULL_ACCESS, PRODUCT_ACCESS, HS_CODE_PRICE, PRODUCT_PRICE
        
        active_hs_code = hs_code or parsed_query.get('hs_code', '')
        resolved_hs_code = search_result.get('active_hs_code')
        if resolved_hs_code:
            active_hs_code = resolved_hs_code

        active_subcat_id = None
        if subcat_id:
            try:
                active_subcat_id = int(subcat_id)
            except ValueError:
                pass

        if not active_subcat_id:
            active_subcat_id = search_result.get('active_subcat_id')

        resolved_variant_name = variant_name
        if active_subcat_id and not resolved_variant_name:
            from trade_data.models import ProductSubCategory
            variant_obj = ProductSubCategory.objects.filter(id=active_subcat_id).first()
            if variant_obj:
                resolved_variant_name = variant_obj.name

        access_state = get_access_state(request.user, active_hs_code, active_subcat_id)

        # Store total count before slicing so frontend can show "36 results found, showing 2"
        total_profiles_count = len(mapped_results)

        if access_state not in (FULL_ACCESS, PRODUCT_ACCESS):
            mapped_results = mapped_results[:2]

        paywall_price = PRODUCT_PRICE if active_subcat_id else HS_CODE_PRICE

        return Response({
            "query":                query,
            "parsed_query":         parsed_query,
            "needs_disambiguation": False,
            "is_broad_search":      search_result.get("is_broad_search", False),
            "variants":             [],
            "matched_subcategories": [],
            "available_variants":  [],
            "active_variant":      resolved_variant_name,
            "active_subcat_id":    active_subcat_id,
            "results":             mapped_results,
            "market_snapshot":     market_snapshot,
            "count":               len(mapped_results),
            "search_engine":       search_result.get("search_engine", "orm"),
            "access_state":        access_state,
            "paywall_price":       paywall_price,
            "total_profiles_count": total_profiles_count,
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
                "is_final":     s.get("is_final", False),
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
            # Word search: like "dextrose" -> Return each individual subcategory variant
            # so users see the full list (e.g. "Dextrose Ball", "Dextrose Anhydrous", etc.)
            # matching what the autocomplete dropdown shows — NOT HS-code-grouped rows.
            subcat_qs = list(ProductSubCategory.objects.filter(name__icontains=q))
            cat_qs = list(ProductCategory.objects.filter(name__icontains=q))

            results = []
            seen_subcat_ids = set()

            # Each individual subcategory variant gets its own row
            for sc in subcat_qs:
                if sc.id in seen_subcat_ids:
                    continue
                seen_subcat_ids.add(sc.id)
                cnt = Transaction.objects.filter(hs_code__startswith=sc.hs_code).count()
                if cnt > 0:
                    results.append({
                        "hs_code": sc.hs_code,
                        "name": sc.name,
                        "subcat_id": sc.id,
                        "count": cnt,
                        "is_leaf": True,
                    })

            # Add broad categories not already covered by a subcategory row
            seen_hs = {r["hs_code"] for r in results}
            for cat in cat_qs:
                if cat.hs_code not in seen_hs:
                    cnt = Transaction.objects.filter(hs_code__startswith=cat.hs_code).count()
                    if cnt > 0:
                        is_leaf = len(cat.hs_code.replace('.', '')) >= 5
                        results.append({
                            "hs_code": cat.hs_code,
                            "name": cat.name,
                            "subcat_id": None,
                            "count": cnt,
                            "is_leaf": is_leaf,
                        })
                    seen_hs.add(cat.hs_code)

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

        qs_base = qs

        subcat_names = []
        if subcat_filter:
            subcat_names = [s.strip() for s in subcat_filter.split(',') if s.strip()]
            if subcat_names:
                from django.db.models import Q
                qs = qs.filter(
                    Q(product_item__sub_category__name__in=subcat_names) | 
                    Q(product_item__name__in=subcat_names)
                )

        # Sidebar: use ProductSubCategory names (clean tariff names, not raw invoice text)
        refinements = list(
            qs_base.values('product_item__sub_category__name')
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

        # Sort and construct profiles
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
                "total_volume":       round(vol, 4) if vol > 0 and vol < 1 else round(vol, 2),
                "avg_price":          round(price, 2),
                "shipment_count":     count,
                "last_shipment_date": str(p['last_shipment']) if p['last_shipment'] else None,
                "avg_shipment_vol":   round(vol / count, 4) if count > 0 and (vol / count) < 1 else (round(vol / count, 2) if count > 0 else 0),
                "type":               "Supplier" if intent in ('FOREIGN_SUPPLIERS', 'PAKISTANI_SUPPLIERS') else "Buyer",
            })

        # ─── 4. Apply Access Restrictions ─────────────────────────────────────────────
        from subscriptions.services import get_access_state, FULL_ACCESS, PRODUCT_ACCESS, NO_ACCESS, HS_CODE_PRICE, PRODUCT_PRICE

        # If they filtered to a subcategory, find its ID for access check
        primary_product_name = subcat_names[0] if subcat_names else None
        active_subcat_id = None
        if primary_product_name:
            from trade_data.models import ProductSubCategory
            subcat_obj = ProductSubCategory.objects.filter(name=primary_product_name, hs_code__startswith=q).first()
            if not subcat_obj:
                subcat_obj = ProductSubCategory.objects.filter(name=primary_product_name).first()
            if subcat_obj:
                active_subcat_id = subcat_obj.id

        access_state = get_access_state(request.user, q, active_subcat_id)

        # Explicit data sanitization layer (Frontend is secondary, Backend is authority)
        if access_state in (FULL_ACCESS, PRODUCT_ACCESS):
            visible_profiles = profiles
            full_profiles = profiles
        else:
            visible_profiles = profiles[:2]
            full_profiles = []

        paywall_price = PRODUCT_PRICE if active_subcat_id else HS_CODE_PRICE

        print(f"[HS DASHBOARD DEBUG] q={q} intent={intent} count={total_count} qs.count()={qs.count()} len(raw_profiles)={len(raw_profiles)} len(profiles)={len(profiles)} len(visible_profiles)={len(visible_profiles)} subcat_names={subcat_names}")

        return Response({
            "hs_code":          q,
            "hs_description":   hs_description,
            "total_shipments":  total_count,
            "sidebar_counts":   sidebar_counts,
            # Output security parameters directly to frontend config
            "access_state":     access_state,
            "paywall_price":    paywall_price,
            "visible_profiles": visible_profiles,
            "full_profiles":    full_profiles,
            "total_profiles_count": len(profiles),
        })


    # ----------------------------------------------------------------
    # SUPPLIER DETAIL — GET /api/search/supplier-detail/?name=...&query=...
    # ----------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='supplier-detail')
    def supplier_detail(self, request):
        seller_name  = request.query_params.get('name')
        query        = request.query_params.get('query')
        subcat_id    = request.query_params.get('subcat_id')
        variant_name = request.query_params.get('variant_name')

        if not seller_name or not query:
            return Response({"error": "Params 'name' and 'query' are required"}, status=400)

        scope     = request.query_params.get('scope', 'import').lower()
        orm_scope = 'EXPORT' if scope == 'export' else 'IMPORT'

        # --- Intent resolution (priority order) ---
        # 1. Explicit intent from URL param (most reliable — set by frontend based on active pill tab)
        explicit_intent = request.query_params.get('intent', '').upper()

        if explicit_intent in ('BUY', 'SELL'):
            intent = explicit_intent
            parsed_query = {'intent': intent, 'product': query, 'hs_code': ''}
        else:
            # 2. NLU cache (fast path when user came from a natural-language search)
            import hashlib
            from django.core.cache import cache
            _cache_raw = f"nlu:{query.lower().strip()}:{scope}"
            _cache_key = "nlu_" + hashlib.md5(_cache_raw.encode()).hexdigest()
            parsed_query = cache.get(_cache_key)
            if parsed_query is None:
                # 3. Run NLU only if nothing else resolved
                parsed_query = self.search_service._nlu_engine.parse(query)
            intent = parsed_query.get('intent', 'BUY')
            # For numeric HS-code queries NLU yields UNKNOWN — treat as BUY
            if intent not in ('BUY', 'SELL'):
                intent = 'BUY'

        # Resolve exact subcategory if selected from UI
        hs_code_hint = query if all(c.isdigit() or c == '.' for c in query.strip()) else parsed_query.get("hs_code", "")
        subcat_ids, _, product_item_ids = self.search_service._resolve_subcategories(
            product_keyword=parsed_query.get("product", query),
            hs_code=hs_code_hint,
            intent=intent,
            subcat_id=int(subcat_id) if subcat_id else None,
            variant_name=variant_name,
            scope=orm_scope
        )

        # Route to the correct aggregator
        if intent == 'SELL':
            details = self.aggregator.get_buyer_details(
                seller_name, subcat_ids, product_item_filter=product_item_ids, scope=orm_scope
            )
        else:
            details = self.aggregator.get_supplier_details(
                seller_name, subcat_ids, product_item_filter=product_item_ids, scope=orm_scope
            )

        if not details:
            entity_type = "Buyer" if intent == 'SELL' else "Supplier"
            return Response({"error": f"{entity_type} '{seller_name}' not found in the selected scope."}, status=404)

        return Response({
            "supplier": details,
            "comparables": [],
            "trade_lens_product_id": None,
            "type": "BUYER" if intent == 'SELL' else "SUPPLIER",
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

    # ----------------------------------------------------------------
    # SUPPLIER TRANSACTIONS — GET /api/search/supplier-transactions/
    # ----------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='supplier-transactions')
    def supplier_transactions(self, request):
        seller_name = request.query_params.get('name')
        query = request.query_params.get('query')
        subcat_id = request.query_params.get('subcat_id')
        variant_name = request.query_params.get('variant_name')

        if not seller_name or not query:
            return Response({"error": "Params 'name' and 'query' are required"}, status=400)

        scope = request.query_params.get('scope', 'import').lower()
        orm_scope = 'EXPORT' if scope == 'export' else 'IMPORT'

        try:
            page = int(request.query_params.get('page', 1))
        except ValueError:
            page = 1
        try:
            page_size = int(request.query_params.get('page_size', 15))
        except ValueError:
            page_size = 15

        try:
            # Intent
            explicit_intent = request.query_params.get('intent', '').upper()
            if explicit_intent in ('BUY', 'SELL'):
                intent = explicit_intent
                is_buyer = (intent == 'SELL')
                # Still resolve subcategories using subcat_id/variant_name so the
                # Transactions tab is scoped to the filtered product (e.g. "Dextrose Anhydrous"),
                # not all products under the HS code.
                try:
                    hs_code_hint = query if all(c.isdigit() or c == '.' for c in query.strip()) else ''
                    subcat_ids, _, product_item_ids = self.search_service._resolve_subcategories(
                        product_keyword=query,
                        hs_code=hs_code_hint,
                        intent=intent,
                        subcat_id=int(subcat_id) if subcat_id else None,
                        variant_name=variant_name,
                        scope=orm_scope
                    )
                except Exception:
                    subcat_ids = None
                    product_item_ids = None
            else:
                import hashlib
                from django.core.cache import cache
                _cache_raw = f"nlu:{query.lower().strip()}:{scope}"
                _cache_key = "nlu_" + hashlib.md5(_cache_raw.encode()).hexdigest()
                parsed_query = cache.get(_cache_key)
                if parsed_query is None:
                    parsed_query = self.search_service._nlu_engine.parse(query)
                intent = parsed_query.get('intent', 'BUY')
                if intent not in ('BUY', 'SELL'):
                    intent = 'BUY'
                is_buyer = (intent == 'SELL')

                try:
                    hs_code_hint = query if all(c.isdigit() or c == '.' for c in query.strip()) else parsed_query.get("hs_code", "")
                    subcat_ids, _, product_item_ids = self.search_service._resolve_subcategories(
                        product_keyword=parsed_query.get("product", query),
                        hs_code=hs_code_hint,
                        intent=intent,
                        subcat_id=int(subcat_id) if subcat_id else None,
                        variant_name=variant_name,
                        scope=orm_scope
                    )
                except Exception:
                    # If subcategory resolution fails just load all transactions for entity
                    subcat_ids = None
                    product_item_ids = None

            # Filters
            filters = {}
            if request.query_params.get('start_date'): filters['start_date'] = request.query_params.get('start_date')
            if request.query_params.get('end_date'): filters['end_date'] = request.query_params.get('end_date')
            if request.query_params.get('buyer'): filters['buyer'] = request.query_params.get('buyer')
            if request.query_params.get('seller'): filters['seller'] = request.query_params.get('seller')
            if request.query_params.get('country'): filters['country'] = request.query_params.get('country')
            if request.query_params.get('min_qty'): filters['min_qty'] = float(request.query_params.get('min_qty'))
            if request.query_params.get('max_qty'): filters['max_qty'] = float(request.query_params.get('max_qty'))
            if request.query_params.get('min_price'): filters['min_price'] = float(request.query_params.get('min_price'))
            if request.query_params.get('max_price'): filters['max_price'] = float(request.query_params.get('max_price'))

            data = self.aggregator.get_supplier_transactions(
                entity_name=seller_name,
                is_buyer=is_buyer,
                subcat_ids=subcat_ids,
                product_item_filter=product_item_ids,
                scope=orm_scope,
                filters=filters,
                page=page,
                page_size=page_size
            )
            return Response(data)

        except Exception as exc:
            logger.exception("supplier_transactions error: %s", exc)
            return Response({"error": str(exc)}, status=500)
