"""
search_service.py — Revamped v3
================================
Resilient, correct, production-ready search.

Main search path:
  1. NLU        → intent (BUY/SELL) + product_keyword extraction
  2. OpenSearch → BM25 fast path (skipped gracefully if OS is down)
  3. ORM Fallback → Django DB aggregation via SupplierAggregator
  4. Disambiguation → if keyword matches 2+ subcategories, return variant picker

Autocomplete:
  - Strips stop words from query → icontains DB lookup → rank by volume

When OpenSearch IS running, it is used for the main result ranking.
When it's NOT running (ConnectionError), falls back to ORM silently.
"""

import logging
import hashlib
from typing import Optional
from django.core.cache import cache

logger = logging.getLogger(__name__)

OPENSEARCH_HOST = "http://localhost:9200"
INDEX_NAME      = "trade_index"

# Only force the variant picker when the user's keyword is so broad that it
# matches more than this many distinct subcategories. Below the threshold we
# merge results across all matching variants so the user sees something.
DISAMBIGUATION_THRESHOLD = 20


class SearchService:
    """
    Revamped Search Service — resilient (OS + ORM fallback).
    """

    _os_client   = None
    _os_ok       = None   # None = unknown, True = up, False = down
    _nlu_engine  = None

    # =========================================================================
    # Init
    # =========================================================================

    @classmethod
    def _init_clients(cls):
        if cls._nlu_engine is None:
            from search.services.nlu_engine import ModernNLUEngine
            logger.info("Initializing ModernNLUEngine...")
            cls._nlu_engine = ModernNLUEngine()

        if cls._os_client is None:
            try:
                from opensearchpy import OpenSearch
                cls._os_client = OpenSearch(
                    hosts=[OPENSEARCH_HOST],
                    use_ssl=False,
                    verify_certs=False,
                    ssl_show_warn=False,
                    timeout=3,           # short timeout so fallback is fast
                    max_retries=1,
                    retry_on_timeout=False,
                )
                logger.info(f"OpenSearch client configured at {OPENSEARCH_HOST}")
            except Exception as e:
                logger.warning(f"Could not create OpenSearch client: {e}")

    @classmethod
    def _opensearch_available(cls) -> bool:
        """Ping OpenSearch. Result is cached for the lifetime of the process."""
        if cls._os_ok is True:
            return True
        if cls._os_client is None:
            return False
        try:
            cls._os_client.ping()
            if cls._os_ok is not True:
                logger.info("OpenSearch is UP — using BM25 fast path.")
            cls._os_ok = True
            return True
        except Exception:
            if cls._os_ok is not False:
                logger.info("OpenSearch is DOWN — using ORM fallback.")
            cls._os_ok = False
            return False

    def __init__(self):
        self._init_clients()

    # =========================================================================
    # PUBLIC API — MAIN SEARCH
    # =========================================================================

    def execute_search(
        self,
        raw_query: str,
        ui_context: str = "worldwide",
        top_k: int = 100,
        hs_code: str = None,
        subcat_id: int = None,       # Exact DB subcategory id (from disambiguation click)
        variant_name: str = None,   # Exact product name user clicked (e.g., "Dextrose Anhydrous")
    ) -> dict:
        """
        Execute search. Returns:
        {
            "nlu":                 structured NLU result,
            "profiles":            list of company profile dicts (may be empty),
            "total_raw_hits":      int,
            "needs_disambiguation": bool,
            "variants":            list of product variant dicts (when disambig needed),
            "search_engine":       "opensearch" | "orm",
        }
        """
        import time
        t_total = time.perf_counter()

        # ------------------------------------------------------------------
        # Step 1: NLU  (SetFit + KeyBERT + OpenRouter)
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        # ------- NLU CACHE -------
        # Build a stable cache key from (query, context) — 24h TTL
        _cache_raw = f"nlu:{raw_query.lower().strip()}:{ui_context.lower()}"
        _cache_key = "nlu_" + hashlib.md5(_cache_raw.encode()).hexdigest()
        nlu_result = cache.get(_cache_key)
        if nlu_result is not None:
            logger.debug(f"[CACHE] NLU cache HIT for query='{raw_query[:40]}' — skipping LLM call")
        else:
            logger.debug(f"[CACHE] NLU cache MISS for query='{raw_query[:40]}' — running full NLU")
            nlu_result = self._nlu_engine.parse(raw_query, ui_context=ui_context)
            cache.set(_cache_key, nlu_result, timeout=86400)  # 24 hours
        logger.debug(f"[TIMING] NLU parse: {time.perf_counter() - t0:.3f}s")

        intent  = nlu_result.get("intent", "BUY")
        country = nlu_result.get("country")

        product_keyword = (
            nlu_result.get("product")
            or nlu_result.get("product_keyword")
            or raw_query
        )

        # HS code fast path: NLU detected query is a raw HS code string.
        # Pass it directly so _resolve_subcategories uses hs_code-based lookup.
        if nlu_result.get("is_hs_query") and not hs_code:
            hs_code = product_keyword
            logger.info(f"[Search] HS code query detected, using hs_code={hs_code!r}")

        # ------------------------------------------------------------------
        # Step 2: Determine scope for ORM aggregator
        # NLU may have inferred a different scope from query signals (e.g. "pakistan sugar"
        # auto-switches to PAKISTAN scope). Use the NLU's ui_context if it changed.
        # ------------------------------------------------------------------
        nlu_ui_context = nlu_result.get("ui_context", ui_context)
        orm_scope  = self._map_scope(nlu_ui_context)
        orm_intent = intent

        # ------------------------------------------------------------------
        # Step 3: Resolve product subcategories from DB
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        subcat_ids, variant_list, product_item_ids = self._resolve_subcategories(
            product_keyword, hs_code, country=country, intent=intent,
            subcat_id=subcat_id, variant_name=variant_name, scope=orm_scope,
            price_filter=nlu_result.get("price_filter"),
        )
        logger.debug(f"[TIMING] Subcategory resolve: {time.perf_counter() - t0:.3f}s")

        # Disambiguation policy:
        #   1. If any variant name exactly matches the keyword (case-insensitive),
        #      pick that one and run the search — no picker.
        #   2. If price_filter or country filter is set, skip disambiguation and show
        #      results — user has explicit constraints, merging all variants is correct.
        #   3. Else if the number of matches is small (≤ DISAMBIGUATION_THRESHOLD),
        #      merge results across all matching variants. User sees real data.
        #   4. Only force the variant picker when the keyword is truly ambiguous
        #      (>DISAMBIGUATION_THRESHOLD variants) AND no specific filters are set.
        has_specific_filters = bool(
            nlu_result.get("price_filter") or nlu_result.get("country")
        )
        # SELL intent: user wants buyers — show all matching products, never ask them to disambiguate.
        # Disambiguation for BUY makes sense ("which dextrose variant?") but for SELL it's noise.
        _is_sell = (intent == "SELL")
        needs_disambig = False
        if not hs_code and variant_list:
            kw_lower = (product_keyword or "").lower().strip()
            exact = [v for v in variant_list if v['name'].lower().strip() == kw_lower]
            # Exact match shortcut: only activate when there is NO more-specific variant.
            # Example: "dextrose" matches both "Dextrose" (exact) and "Dextrose Anhydrous"
            # (more specific). In that case keep all variants so users see Anhydrous results too.
            # If keyword is multi-word and exact, it IS specific — use it alone.
            more_specific = [v for v in variant_list if v['name'].lower().strip() != kw_lower
                             and v['name'].lower().startswith(kw_lower)]
            if exact and not more_specific:
                # Exact match wins and no more-specific variants exist — lock in that variant
                subcat_ids   = [exact[0]['id']]
                variant_list = exact
            elif has_specific_filters or _is_sell:
                # Filters or SELL intent: merge all matching subcategories, never show picker
                pass
            elif len(subcat_ids) > DISAMBIGUATION_THRESHOLD:
                needs_disambig = True
            # else: keep all matches, let aggregation merge them

        if needs_disambig:
            logger.debug(f"[TIMING] Total (disambig early-exit): {time.perf_counter() - t_total:.3f}s")
            return {
                "nlu":                  nlu_result,
                "profiles":             [],
                "total_raw_hits":       0,
                "needs_disambiguation": True,
                "is_broad_search":      False,
                "variants":             variant_list,
                "search_engine":        "none",
            }

        # Company name fallback: if no product subcategories matched, treat the
        # keyword as a company name and search transactions directly.
        if not subcat_ids and product_keyword and len(product_keyword) >= 3:
            logger.info(f"[Search] No product match for '{product_keyword}' — trying company name search")
            company_profiles = self._company_name_fallback(
                product_keyword, orm_intent, orm_scope, nlu_result, top_k
            )
            if company_profiles:
                logger.debug(f"[TIMING] Total (company fallback): {time.perf_counter() - t_total:.3f}s")
                return {
                    "nlu":                  nlu_result,
                    "profiles":             company_profiles,
                    "total_raw_hits":       len(company_profiles),
                    "needs_disambiguation": False,
                    "is_broad_search":      False,
                    "variants":             [],
                    "search_engine":        "orm",
                }

        # ------------------------------------------------------------------
        # Step 4a: Try OpenSearch (fast BM25 path) - DISABLED TEMPORARILY
        # ------------------------------------------------------------------
        if False and self._opensearch_available() and subcat_ids:
            try:
                result = self._opensearch_search(
                    product_keyword, intent, ui_context, subcat_ids, hs_code, top_k, nlu_result
                )
                result["nlu"]                  = nlu_result
                result["needs_disambiguation"] = False
                result["is_broad_search"]      = False
                result["variants"]             = []
                result["search_engine"]        = "opensearch"
                return result
            except Exception as e:
                logger.warning(f"OpenSearch query failed, falling back to ORM: {e}")
                self.__class__._os_ok = False

        # ------------------------------------------------------------------
        # Step 4b: ORM Fallback — DB aggregation + ranking
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        profiles, total_hits = self._orm_search(
            subcat_ids=subcat_ids,
            intent=orm_intent,
            scope=orm_scope,
            nlu_result=nlu_result,
            top_k=top_k,
            product_item_ids=product_item_ids,
            raw_query=raw_query,
        )
        db_elapsed = time.perf_counter() - t0
        logger.debug(f"[TIMING] DB aggregation: {db_elapsed:.3f}s")
        # Ranking is embedded inside _orm_search; estimate remainder as < 30 ms

        logger.debug(f"[TIMING] Total: {time.perf_counter() - t_total:.3f}s")

        is_broad = False
        if not hs_code and not subcat_ids and len(product_keyword) > 1:
            is_broad = True

        return {
            "nlu":                  nlu_result,
            "profiles":             profiles,
            "total_raw_hits":       total_hits,
            "needs_disambiguation": False,
            "is_broad_search":      is_broad,
            "variants":             [],
            "search_engine":        "orm",
        }

    # =========================================================================
    # INTERNAL — Product Resolution
    # =========================================================================

    def _resolve_subcategories(
        self,
        product_keyword: str,
        hs_code: str = None,
        country: str = None,
        intent: str = "BUY",
        subcat_id: int = None,
        variant_name: str = None,
        scope: str = "WORLDWIDE",
        price_filter: dict = None,  # if set, expands icontains search to find more variants
    ):
        """
        Find matching ProductSubCategory IDs for the keyword.

        Returns:
            (subcat_ids: list[int], variant_list: list[dict], product_item_ids: list[int])
            - subcat_ids: DB IDs for ORM aggregator
            - variant_list: metadata for disambiguation display (country-filtered if country given)
            - product_item_ids: non-empty only when user picked an exact product item (via hs_code)
        """
        from trade_data.models import ProductSubCategory, ProductItem, Transaction
        from django.db.models import Q

        # ------------------------------------------------------------------
        # FAST PATH: subcat_id provided — user clicked an exact product
        # Return immediately, no fuzzy matching needed
        # ------------------------------------------------------------------
        if subcat_id:
            return [subcat_id], [], []

        if hs_code:
            # Multiple subcategories can share the same hs_code (e.g., 1702.3 is shared by
            # Dextrose Ball, Dextrose Anhydrous, Dextrose Monohydrate, etc.)
            # Priority: variant_name (exact) > product_keyword (fuzzy) > first alphabetical
            scs = list(ProductSubCategory.objects.filter(hs_code=hs_code).order_by('name'))

            # Fallback 1: input is a prefix of stored hs_codes (e.g. "1702" → "1702.3", "1702.111")
            if not scs:
                scs = list(ProductSubCategory.objects.filter(
                    hs_code__startswith=hs_code + "."
                ).order_by('name'))
                if not scs:
                    # Also try without dot (e.g. "1702" → startswith "1702")
                    scs = list(ProductSubCategory.objects.filter(
                        hs_code__startswith=hs_code
                    ).order_by('name'))

            # Fallback 2: stored hs_code (normalized) is a prefix of input (normalized)
            # e.g. "17023090" should match hs_code "1702.3" (norm "17023") or "1702.30" (norm "170230")
            if not scs:
                import re as _re
                _hs_norm = _re.sub(r'[\.\s\-]', '', hs_code)
                _all_scs = list(ProductSubCategory.objects.exclude(hs_code__isnull=True).exclude(hs_code='').only('id', 'name', 'hs_code'))
                scs = [sc for sc in _all_scs
                       if _hs_norm.startswith(_re.sub(r'[\.\s\-]', '', sc.hs_code))]
                scs = sorted(scs, key=lambda x: x.name)
            
            if len(scs) == 1:
                return [scs[0].id], [], []
            
            if scs:
                # 1. Exact match on variant_name (most reliable — comes from frontend click)
                if variant_name:
                    vn_lower = variant_name.lower().strip()
                    for sc in scs:
                        if sc.name.lower().strip() == vn_lower:
                            return [sc.id], [], []
                
                # 2. Unique-word match — ONLY when keyword is specific enough (>= 5 chars)
                # e.g. "dex ball" -> "ball" uniquely identifies Dextrose Ball ✓
                # e.g. "dex" -> too short, skip ("dex" won't match unique words anyway)
                if product_keyword and len(product_keyword) >= 5:
                    kw_lower = product_keyword.lower()
                    all_name_words = []
                    for sc in scs:
                        all_name_words.extend(sc.name.lower().split())
                    word_counts = {}
                    for w in all_name_words:
                        word_counts[w] = word_counts.get(w, 0) + 1
                    unique_words = {w for w, c in word_counts.items() if c == 1 and len(w) > 3}

                    for sc in scs:
                        for word in sc.name.lower().split():
                            if word in unique_words and word in kw_lower:
                                return [sc.id], [], []
            
            # 3. SAFE FALLBACK: return ALL subcategories sharing this hs_code.
            # Better to show combined results (all dextrose suppliers) than pick the
            # alphabetically-first wrong subcategory and show 0 suppliers.
            # The user will see accurate results once the frontend sends subcat_id/variant_name.
            if scs:
                return [sc.id for sc in scs], [], []
            
            # hs_code refers to a ProductItem — unpack to subcategory
            items = list(ProductItem.objects.filter(
                sub_category__hs_code=hs_code
            ).select_related("sub_category"))
            if items:
                sc_id = items[0].sub_category.id
                item_ids = [i.id for i in items]
                return [sc_id], [], item_ids
            return [], [], []

        if not product_keyword or len(product_keyword) < 2:
            return [], [], []

        # ------------------------------------------------------------------
        # PASS 1: Prefix match on subcategory names
        # ------------------------------------------------------------------
        sc_qs = list(ProductSubCategory.objects.filter(
            name__istartswith=product_keyword
        ).select_related("category"))

        # PASS 2: Prefix match on product item names
        item_qs = list(ProductItem.objects.filter(
            name__istartswith=product_keyword
        ).select_related("sub_category__category"))

        # PASS 2.5: Contains match (catches "palm oil" → "Crude Palm Oil").
        # Default behavior: fallback-only (runs when PASS 1 finds nothing).
        # Extended behavior: when specific filters are present (price or country),
        # MERGE with PASS 1 results so "sugar under $500" searches ALL sugar variants
        # (e.g. "Refined Sugar", "Invert Sugar") not just subcategories starting with "sugar".
        _has_specific_filters = bool(country or price_filter)
        if not sc_qs and not item_qs:
            sc_qs = list(ProductSubCategory.objects.filter(
                name__icontains=product_keyword
            ).select_related("category"))
            item_qs = list(ProductItem.objects.filter(
                name__icontains=product_keyword
            ).select_related("sub_category__category"))
        elif _has_specific_filters:
            # Merge icontains results with PASS 1 results (union by ID)
            sc_qs_contains = list(ProductSubCategory.objects.filter(
                name__icontains=product_keyword
            ).select_related("category"))
            item_qs_contains = list(ProductItem.objects.filter(
                name__icontains=product_keyword
            ).select_related("sub_category__category"))
            sc_seen = {s.id for s in sc_qs}
            sc_qs = list(sc_qs) + [s for s in sc_qs_contains if s.id not in sc_seen]
            item_seen = {i.id for i in item_qs}
            item_qs = list(item_qs) + [i for i in item_qs_contains if i.id not in item_seen]

        # PASS 3: Fuzzy fallback via pg_trgm
        if not sc_qs and not item_qs:
            from django.contrib.postgres.search import TrigramSimilarity
            sc_qs = list(ProductSubCategory.objects.annotate(
                similarity=TrigramSimilarity('name', product_keyword)
            ).filter(similarity__gt=0.3).order_by('-similarity')[:5].select_related("category"))
            item_qs = list(ProductItem.objects.annotate(
                similarity=TrigramSimilarity('name', product_keyword)
            ).filter(similarity__gt=0.3).order_by('-similarity')[:5].select_related("sub_category__category"))

        # PASS 4: Needle-in-haystack — word-by-word search for garbled queries.
        # Guard removed: previously required a space in product_keyword, which meant
        # single-word garbled queries ("dextrozz") could never reach this pass.
        # Pass 3 trigram already handles most single-word typos, but removing the
        # guard makes Pass 4 available as an additional safety net.
        if not sc_qs and not item_qs and product_keyword:
            words = sorted([w for w in product_keyword.split() if len(w) > 2], key=len, reverse=True)
            for word in words:
                sc_qs = list(ProductSubCategory.objects.filter(name__istartswith=word).select_related("category"))
                item_qs = list(ProductItem.objects.filter(name__istartswith=word).select_related("sub_category__category"))
                if sc_qs or item_qs:
                    break
                from django.contrib.postgres.search import TrigramSimilarity
                sc_qs = list(ProductSubCategory.objects.annotate(
                    similarity=TrigramSimilarity('name', word)
                ).filter(similarity__gt=0.3).order_by('-similarity')[:5].select_related("category"))
                item_qs = list(ProductItem.objects.annotate(
                    similarity=TrigramSimilarity('name', word)
                ).filter(similarity__gt=0.3).order_by('-similarity')[:5].select_related("sub_category__category"))
                if sc_qs or item_qs:
                    break

        # Build a unified map: subcat_id → metadata
        sc_map = {}
        for sc in sc_qs:
            sc_map[sc.id] = {
                "id":       sc.id,
                "hs_code":  sc.hs_code,
                "name":     sc.name,
                "category": sc.category.name,
            }
        for item in item_qs:
            sc = item.sub_category
            if sc.id not in sc_map:
                sc_map[sc.id] = {
                    "id":       sc.id,
                    "hs_code":  sc.hs_code,
                    "name":     sc.name,
                    "category": sc.category.name,
                }

        variant_list = list(sc_map.values())
        subcat_ids   = list(sc_map.keys())

        # ------------------------------------------------------------------
        # SCOPE-AWARE AVAILABILITY FILTER
        # Map (Intent, Scope) → the trade_type that has real data for the
        # current user context. This prevents showing product variants that
        # will return 0 results when clicked.
        #
        # Intent | Scope     | Trade Type | Reasoning
        # -------|-----------|------------|------------------------------
        # BUY    | PAKISTAN  | EXPORT     | User wants a Pak seller
        # SELL   | PAKISTAN  | IMPORT     | User wants a Pak buyer
        # BUY    | WORLDWIDE | IMPORT     | User wants a foreign seller
        # SELL   | WORLDWIDE | EXPORT     | User wants a foreign buyer
        # ------------------------------------------------------------------
        if subcat_ids:
            if intent == "BUY" and scope == "PAKISTAN":
                target_trade_type = "EXPORT"
            elif intent == "SELL" and scope == "PAKISTAN":
                target_trade_type = "IMPORT"
            elif intent == "BUY" and scope == "WORLDWIDE":
                target_trade_type = "IMPORT"
            else:  # SELL + WORLDWIDE — dataset has only IMPORT, buyers are in IMPORT records
                target_trade_type = "IMPORT"

            # Cache the availability check — product availability changes
            # only when new transactions are ingested, not between searches.
            _avail_parts = f"avail:{sorted(subcat_ids)}:{target_trade_type}:{country or ''}"
            _avail_key = "avail_" + hashlib.md5(_avail_parts.encode()).hexdigest()
            active_ids = cache.get(_avail_key)
            if active_ids is None:
                availability_qs = Transaction.objects.filter(
                    trade_type=target_trade_type,
                    product_item__sub_category_id__in=subcat_ids,
                )
                if country:
                    country_field = "origin_country" if target_trade_type == "IMPORT" else "destination_country"
                    availability_qs = availability_qs.filter(
                        **{country_field + "__icontains": country}
                    )
                active_ids = set(
                    availability_qs.values_list(
                        "product_item__sub_category_id", flat=True
                    ).distinct()
                )
                cache.set(_avail_key, active_ids, timeout=3600)  # 1 hour

            if active_ids:
                variant_list = [v for v in variant_list if v["id"] in active_ids]
                subcat_ids   = [sid for sid in subcat_ids if sid in active_ids]

        return subcat_ids, variant_list, []

    # =========================================================================
    # INTERNAL — OpenSearch Path
    # =========================================================================

    def _opensearch_search(
        self, product_keyword, intent, ui_context, subcat_ids, hs_code, top_k, nlu_result
    ) -> dict:
        """Run BM25 aggregation query via OpenSearch."""
        agg_company_field = "seller.keyword" if intent == "BUY" else "buyer.keyword"
        country_field     = "origin_country" if intent == "BUY" else "destination_country"

        bm25_query = {
            "multi_match": {
                "query":     product_keyword,
                "fields":    ["clean_product_name^9", "product_item_name^5", "sub_category_name^7"],
                "type":      "best_fields",
                "fuzziness": "AUTO",
            }
        }

        filter_clauses = []

        os_filter = nlu_result.get("os_filter", {})
        nlu_must  = os_filter.get("bool", {}).get("must", [])
        filter_clauses.extend(nlu_must)

        if hs_code:
            filter_clauses.append({"term": {"hs_code": hs_code}})

        price_filter = nlu_result.get("price_filter")
        if price_filter and price_filter not in filter_clauses:
            filter_clauses.append(price_filter)

        os_query = {
            "size": 0,
            "query": {
                "bool": {
                    "must":   [bm25_query],
                    "filter": filter_clauses,
                }
            },
            "aggs": {
                "companies": {
                    "terms": {
                        "field": agg_company_field,
                        "size":  top_k,
                        "order": {"total_volume": "desc"},
                    },
                    "aggs": {
                        "total_volume": {"sum": {"field": "qty_mt"}},
                        "avg_price":    {"avg": {"field": "usd_per_mt"}},
                        "last_shipped": {"max": {"field": "reporting_date"}},
                        "country":      {"terms": {"field": country_field, "size": 1}},
                        "hs_codes":     {"terms": {"field": "hs_code", "size": 5}},
                    },
                }
            },
        }

        response = self._os_client.search(index=INDEX_NAME, body=os_query)
        total_hits = response.get("hits", {}).get("total", {}).get("value", 0)
        buckets    = response.get("aggregations", {}).get("companies", {}).get("buckets", [])

        profiles = []
        for b in buckets:
            last_shipped_val   = b["last_shipped"].get("value_as_string", b["last_shipped"].get("value"))
            country_buckets    = b.get("country", {}).get("buckets", [])
            country_val        = country_buckets[0]["key"] if country_buckets else "N/A"
            hs_codes_list      = [h["key"] for h in b.get("hs_codes", {}).get("buckets", [])]

            profiles.append({
                "company_name":     b["key"],
                "type":             "SELLER" if intent == "BUY" else "BUYER",
                "transaction_count": b["doc_count"],
                "total_volume":     b["total_volume"]["value"] or 0.0,
                "avg_price":        b["avg_price"].get("value") or 0.0,
                "last_shipped":     last_shipped_val,
                "country":          country_val,
                "hs_codes":         hs_codes_list,
                "relevance_score":  0.0,
            })

        return {"profiles": profiles, "total_raw_hits": total_hits}

    # =========================================================================
    # INTERNAL — ORM Fallback Path
    # =========================================================================

    def _orm_search(self, subcat_ids, intent, scope, nlu_result, top_k=100, product_item_ids=None, raw_query=""):
        """
        Use SupplierAggregator (pure Django ORM) to get company profiles.
        This is the guaranteed-to-work fallback path.

        product_item_ids: if provided, the aggregator will filter by exact product item
        (ensures 'Dextrose Anhydrous' and 'Dextrose Ball' never share supplier lists).
        """
        from search.services.aggregation import SupplierAggregator
        aggregator = SupplierAggregator()

        # Build optional filters from NLU
        price_filter = None
        if nlu_result.get("price_filter"):
            pf   = nlu_result["price_filter"]
            rng  = pf.get("range", {}).get("usd_per_mt", {})
            price_filter = {
                "ceiling": rng.get("lte"),
                "floor":   rng.get("gte"),
            }

        country_filter = None
        country = nlu_result.get("country")
        if country:
            country_filter = [country]

        if not subcat_ids:
            return [], 0

        # ── Aggregation-level cache (1 hour TTL) ──────────────────────────
        # The DB aggregation is the heaviest part of search. Cache it so
        # repeat queries for the same product/intent/scope skip the DB.
        _agg_parts = [
            "agg",
            str(sorted(subcat_ids)),
            intent,
            scope,
            str(country_filter or ""),
            str(price_filter or ""),
            str(sorted(product_item_ids) if product_item_ids else ""),
        ]
        _agg_key = "agg_" + hashlib.md5(":".join(_agg_parts).encode()).hexdigest()
        raw_results = cache.get(_agg_key)
        if raw_results is not None:
            logger.debug(f"[CACHE] Aggregation cache HIT — skipping DB query")
        else:
            raw_results = aggregator.get_suppliers_for_subcategories(
                subcategory_ids=subcat_ids,
                intent=intent,
                scope=scope,
                country_filter=country_filter,
                price_filter=price_filter,
                product_item_filter=product_item_ids or None,
            )
            cache.set(_agg_key, raw_results, timeout=3600)  # 1 hour

        # ------------------------------------------------------------------
        # INTENT-AWARE COMPOSITE RANKING
        # ------------------------------------------------------------------
        # Replaces raw total_volume sorting with a multi-factor score.
        #
        # Signal detection priority:
        #   1. ranking_hint from LLM price extractor (most explicit)
        #   2. product_keyword scan (catches residual words after stopword stripping)
        #
        # NOTE: 'cheap', 'affordable' etc. are stop-words and get stripped from
        # product_keyword before it reaches here. Therefore we must check
        # ranking_hint (from the LLM price call) as the primary signal for
        # price-preference intents.
        #
        # Weight presets (tune here):
        #   "price_asc" (cheap)  → w3 (1/price) = 0.5, w1 (volume) = 0.2
        #   "bulk"               → w1 (volume)  = 0.5, w2 (count)  = 0.3
        #   default              → balanced (w1=0.4, w2=0.3, w3=0.2, w4=0.1)
        if raw_results:
            ranking_hint  = (nlu_result.get("price_filter") or {}).get("ranking_hint") or ""
            signal_text   = nlu_result.get("product_keyword", "").lower() + " " + raw_query.lower()

            # Determine weight preset
            # FIX: Increased recency weight (w4) from 0.1 to 0.25 so stale suppliers
            # don't dominate results. Adjusted other weights proportionally.
            if ranking_hint == "price_asc" or any(
                w in signal_text for w in ["cheap", "affordable", "low price", "best price", "cheapest", "under", "inexpensive", "bargain"]
            ):
                w1, w2, w3, w4 = 0.15, 0.15, 0.5, 0.2
                preset_name = "price_asc"
            elif ranking_hint == "price_desc" or any(
                w in signal_text for w in ["bulk", "large quantity", "reliable", "established", "premium", "top supplier", "biggest"]
            ):
                w1, w2, w3, w4 = 0.45, 0.25, 0.05, 0.25
                preset_name = "bulk/premium"
            else:
                w1, w2, w3, w4 = 0.35, 0.25, 0.15, 0.25
                preset_name = "default"

            logger.info(
                f"[Ranking] Preset='{preset_name}' ranking_hint={ranking_hint!r} "
                f"signal_text={signal_text!r} "
                f"weights=(vol={w1}, cnt={w2}, price={w3}, rec={w4})"
            )


            vols = [r["total_volume"] for r in raw_results]
            counts = [r["shipment_count"] for r in raw_results]
            
            # Convert dates to ordinals for normalized recency
            from datetime import datetime, date
            recencies = []
            for r in raw_results:
                lsd = r["last_shipment_date"]
                if isinstance(lsd, (datetime, date)):
                    recencies.append(lsd.toordinal())
                elif isinstance(lsd, str):
                    try:
                        recencies.append(datetime.strptime(lsd[:10], "%Y-%m-%d").toordinal())
                    except ValueError:
                        recencies.append(0)
                else:
                    recencies.append(0)
                    
            valid_prices = [r["avg_price"] for r in raw_results if r.get("avg_price")]
            
            min_vol, max_vol = min(vols), max(vols)
            min_cnt, max_cnt = min(counts), max(counts)
            min_rec, max_rec = min(recencies), max(recencies)
            
            if valid_prices:
                inv_prices = [1.0 / p for p in valid_prices]
                min_inv_p, max_inv_p = min(inv_prices), max(inv_prices)
            else:
                min_inv_p, max_inv_p = 0.0, 0.0

            def minmax(val, mi, ma):
                return (val - mi) / (ma - mi) if ma > mi else 0.0

            for i, r in enumerate(raw_results):
                vol_norm = minmax(r["total_volume"], min_vol, max_vol)
                cnt_norm = minmax(r["shipment_count"], min_cnt, max_cnt)
                rec_norm = minmax(recencies[i], min_rec, max_rec)
                
                # Price component: use inverted price when data is available.
                # When avg_price is 0/null:
                #   - price_asc mode: skip (0 contribution) — we don't know if cheap, rank lower
                #   - other modes: assign neutral 0.5 so no-price-data suppliers land in middle,
                #     not unfairly at the bottom of results that have nothing to do with price.
                score = w1 * vol_norm + w2 * cnt_norm + w4 * rec_norm
                if r.get("avg_price"):
                    p_norm = minmax(1.0 / r["avg_price"], min_inv_p, max_inv_p)
                    score += w3 * p_norm
                elif preset_name != "price_asc":
                    score += w3 * 0.5
                    
                r["composite_score"] = score

            # Sort by the new intent-aware composite score
            raw_results.sort(key=lambda x: x.get("composite_score", 0), reverse=True)

        # Normalise to the same shape the rest of the code expects
        profiles = []
        for r in raw_results[:top_k]:
            profiles.append({
                "company_name":      r["name"],
                "type":              "SELLER" if intent == "BUY" else "BUYER",
                "transaction_count": r["shipment_count"],
                "total_volume":      r["total_volume"],
                "avg_price":         r["avg_price"],
                "last_shipped":      r["last_shipment_date"],
                "country":           r["country"],
                "hs_codes":          [],
                "relevance_score":   round(r.get("composite_score", 0.0), 4),
                "volume_score":      r.get("volume_score"),
                "volume_fit":        r.get("volume_fit", "N/A"),
            })

        return profiles, len(profiles)

    # =========================================================================
    # INTERNAL — Company Name Fallback
    # =========================================================================

    def _company_name_fallback(self, keyword: str, intent: str, scope: str, nlu_result: dict, top_k: int) -> list:
        """
        Fallback search path when no product subcategory matched the keyword.
        Searches Transaction.seller (BUY) or Transaction.buyer (SELL) directly by name.
        Enables queries like 'SEAWALL' (company name) to return meaningful results.
        """
        from trade_data.models import Transaction
        from django.db.models import Sum, Count, Max, ExpressionWrapper, F, FloatField, Case, When, Value

        company_field = 'seller' if intent == 'BUY' else 'buyer'
        country_field = 'origin_country' if intent == 'BUY' else 'destination_country'

        qs = Transaction.objects.filter(**{f'{company_field}__icontains': keyword})

        if scope == 'PAKISTAN':
            if intent == 'BUY':
                qs = qs.filter(trade_type='EXPORT', origin_country='Pakistan')
            else:
                qs = qs.filter(trade_type='IMPORT', destination_country='Pakistan')
        else:
            if intent == 'BUY':
                qs = qs.filter(trade_type='IMPORT').exclude(origin_country='Pakistan')
            else:
                # SELL+WORLDWIDE: dataset only has IMPORT records; buyers are in those records
                qs = qs.filter(trade_type='IMPORT')

        results = qs.values(company_field, country_field).annotate(
            total_volume=Sum('qty_mt'),
            weighted_price_sum=Sum(ExpressionWrapper(
                Case(
                    When(usd_per_mt__isnull=False, then=F('qty_mt') * F('usd_per_mt')),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                output_field=FloatField(),
            )),
            priced_volume=Sum(Case(
                When(usd_per_mt__isnull=False, then=F('qty_mt')),
                default=Value(0.0),
                output_field=FloatField(),
            )),
            shipment_count=Count('tx_reference', distinct=True),
            last_shipment_date=Max('reporting_date'),
        ).order_by('-total_volume')[:top_k]

        profiles = []
        for r in results:
            tv = float(r['total_volume'] or 0)
            wps = float(r.get('weighted_price_sum') or 0)
            pv = float(r.get('priced_volume') or 0)
            avg_price = round(wps / pv, 2) if pv > 0 else 0.0
            profiles.append({
                "company_name":      r[company_field],
                "type":              "SELLER" if intent == "BUY" else "BUYER",
                "transaction_count": r['shipment_count'],
                "total_volume":      tv,
                "avg_price":         avg_price,
                "last_shipped":      r['last_shipment_date'],
                "country":           r[country_field],
                "hs_codes":          [],
                "relevance_score":   0.0,
                "volume_score":      None,
                "volume_fit":        "N/A",
            })

        return profiles

    # =========================================================================
    # INTERNAL — helpers
    # =========================================================================

    @staticmethod
    def _map_scope(ui_context: str) -> str:
        """Map 'worldwide' / 'pakistan' to aggregator scope strings."""
        return "PAKISTAN" if ui_context.lower() == "pakistan" else "WORLDWIDE"

    # =========================================================================
    # AUTOCOMPLETE
    # =========================================================================

    def autocomplete_products(self, partial_query: str, limit: int = 8) -> list:
        """
        Returns ranked product subcategory matches for the autocomplete dropdown.

        Key fix: strips intent stop-words from the query BEFORE the DB lookup,
        so "i want to buy dex" correctly matches "Dextrose", "Dextrose Anhydrous", etc.

        Ranked by total transaction volume (most traded first).
        """
        from django.db.models import Sum, Count, Q, Subquery, OuterRef
        from trade_data.models import ProductSubCategory, ProductItem, Transaction
        from search.services.nlu_engine import extract_product_keyword

        if not partial_query or len(partial_query) < 2:
            return []

        # Strip intent noise → get the actual product keyword
        keyword = extract_product_keyword(partial_query)

        # Edge case: if keyword is shorter than 2 chars after stripping, use original
        if len(keyword) < 2:
            keyword = partial_query.strip()

        if len(keyword) < 2:
            return []

        # Collect matching subcategory IDs from both SubCategory and Item names
        sc_direct = set(
            ProductSubCategory.objects.filter(
                name__icontains=keyword
            ).values_list("id", flat=True)[:30]
        )
        sc_via_item = set(
            ProductItem.objects.filter(
                name__icontains=keyword
            ).values_list("sub_category_id", flat=True)[:30]
        )
        sc_ids = sc_direct | sc_via_item

        if not sc_ids:
            return []

        # Single annotated query — replaces the N+1 per-subcategory loop
        sc_qs = (
            ProductSubCategory.objects
            .filter(id__in=sc_ids)
            .select_related("category")
            .annotate(
                total_volume=Sum("items__transaction__qty_mt"),
                tx_count=Count("items__transaction__id"),
            )
            .order_by("-total_volume")
            [:limit]
        )

        results = []
        for sc in sc_qs:
            results.append({
                "hs_code":      sc.hs_code,
                "name":         sc.name,
                "category":     sc.category.name,
                "total_volume": float(sc.total_volume or 0),
                "tx_count":     sc.tx_count or 0,
            })

        return results
