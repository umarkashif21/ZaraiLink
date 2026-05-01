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
      GET /api/search/?q=...&scope=worldwide&hs_code=1702.4  → supplier list
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
        scope_param  = request.query_params.get('scope', 'worldwide').lower()
        hs_code      = request.query_params.get('hs_code', None)
        subcat_id    = request.query_params.get('subcat_id', None)   # Exact subcategory DB id
        variant_name = request.query_params.get('variant_name', None) # Exact product name user clicked

        if not query:
            return Response({"error": "Query parameter 'q' is required"}, status=400)

        ui_context = "pakistan" if scope_param == "pakistan" else "worldwide"
        logger.info(f"[SEARCH] q={query!r} scope={ui_context} hs_code={hs_code} subcat_id={subcat_id}")
        top_k = self._extract_top_n(query) or 100

        search_result = self.search_service.execute_search(
            raw_query=query,
            ui_context=ui_context,
            top_k=top_k,
            hs_code=hs_code,
            subcat_id=int(subcat_id) if subcat_id else None,
            variant_name=variant_name,
        )

        parsed_query = search_result['nlu']
        raw_profiles = search_result['profiles']

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

        # Volume-weighted average price: high-volume suppliers dominate, tiny outliers get near-zero weight.
        _vw_num = sum(r["avg_price"] * r["total_volume"] for r in mapped_results if r["avg_price"] > 0 and r["total_volume"] > 0)
        _vw_den = sum(r["total_volume"] for r in mapped_results if r["avg_price"] > 0 and r["total_volume"] > 0)
        vw_avg_price = round(_vw_num / _vw_den, 2) if _vw_den > 0 else 0

        # Top country: by total volume across all results (not just first result's country)
        from collections import defaultdict
        _country_vols = defaultdict(float)
        for r in mapped_results:
            if r.get("country") and r["country"] not in ("N/A", "Unknown", ""):
                _country_vols[r["country"]] += r["total_volume"]
        top_country = max(_country_vols, key=_country_vols.get) if _country_vols else (mapped_results[0]["country"] if mapped_results else "N/A")

        market_snapshot = {
            "total_count":      len(mapped_results),
            "avg_price_global": vw_avg_price,
            "top_country":      top_country,
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

        scope = request.query_params.get('scope', 'worldwide').lower()
        orm_scope = 'PAKISTAN' if scope == 'pakistan' else 'WORLDWIDE'

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
        # FIX: hs_code comes from request params, NOT from NLU result (NLU has no 'hs_code' key)
        subcat_ids, _, product_item_ids = self.search_service._resolve_subcategories(
            product_keyword=parsed_query.get("product", ""),
            hs_code=request.query_params.get('hs_code', '') or '',
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
        scope = request.query_params.get('scope', 'WORLDWIDE').lower()

        if not suppliers_param or not query:
            return Response({"error": "Params 'suppliers' and 'query' are required"}, status=400)

        seller_names = [s.strip() for s in suppliers_param.split(',')]
        orm_scope = 'PAKISTAN' if scope == 'pakistan' else 'WORLDWIDE'

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

        # FIX: hs_code comes from request params, NOT from NLU result (NLU has no 'hs_code' key)
        subcat_ids, _, product_item_ids = self.search_service._resolve_subcategories(
            product_keyword=parsed_query.get("product", ""),
            hs_code=request.query_params.get('hs_code', '') or '',
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
