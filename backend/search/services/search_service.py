import logging
import hashlib
from typing import Optional
from django.core.cache import cache

logger = logging.getLogger(__name__)

OPENSEARCH_HOST = "http://localhost:9200"
INDEX_NAME      = "trade_index"

# Threshold: if the product keyword matches more than this many distinct
# subcategories, ask the user to narrow down first.
DISAMBIGUATION_THRESHOLD = 1


class SearchService:
    _os_client      = None
    _os_ok          = None   # None = unknown, True = up, False = down
    _nlu_engine     = None
    _embed_model    = None
    _reranker       = None
    _product_catalog = None

    @classmethod
    def _get_product_catalog(cls):
        if cls._product_catalog is None:
            from trade_data.models import ProductSubCategory, ProductItem
            names = list(ProductSubCategory.objects.values_list('name', flat=True))
            names += list(ProductItem.objects.values_list('name', flat=True))
            cls._product_catalog = list(set(names))
            logger.info(f"[PASS5] Product catalog loaded: {len(cls._product_catalog)} entries")
        return cls._product_catalog

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
        # Ping result cached for process lifetime.
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

    def _log_perf(self, query, cache_status, timings, nlu_result=None):
        print(f'\n[QUERY] "{query}"')
        print(f"[CACHE] {cache_status}")
        print(f"[TIMING] NLU: {timings.get('nlu', 0.0):.2f}s")

        if nlu_result and "timings" in nlu_result:
            nt = nlu_result["timings"]
            print("\n[NLU]")
            print(f"  intent={nlu_result.get('intent')} product={nlu_result.get('product')!r} keyword={nlu_result.get('product_keyword')!r}")

            country  = nlu_result.get("country")
            quantity = nlu_result.get("quantity")
            if country or quantity:
                print(f"  country={country!r} quantity={quantity!r}")

            pf = nlu_result.get("price_filter") or {}
            rng = (pf.get("range") or {}).get("usd_per_mt") or {}
            hint = pf.get("ranking_hint") or nlu_result.get("ranking_hint")
            if rng or hint:
                bits = []
                if "lte" in rng: bits.append(f"<= {rng['lte']}")
                if "gte" in rng: bits.append(f">= {rng['gte']}")
                if hint:         bits.append(f"hint={hint}")
                print(f"  price: {' '.join(bits)}")

            print(f"  SetFit={int(nt.get('setfit', 0)*1000)}ms | GLiNER={int(nt.get('gliner', 0)*1000)}ms | RapidFuzz={int(nt.get('rapidfuzz', 0)*1000)}ms | PickProduct={int(nt.get('pick_product', 0)*1000)}ms | LLM={int(nt.get('llm', 0)*1000)}ms")
            print(f"  TOTAL={int(nt.get('total', 0)*1000)}ms\n")

        print(f"[TIMING] Subcategory: {timings.get('subcat', 0.0):.2f}s")
        print(f"[TIMING] DB: {timings.get('db', 0.0):.2f}s")
        print(f"[TIMING] TOTAL: {timings.get('total', 0.0):.2f}s\n")

    def execute_search(
        self,
        raw_query: str,
        ui_context: str = "worldwide",
        top_k: int = 100,
        hs_code: str = None,
        subcat_id: int = None,
        variant_name: str = None,
        explicit_intent: str = None,
        already_switched: bool = False,  # Loop-breaker for scope-mismatch switching.
    ) -> dict:
        import time
        t_total = time.perf_counter()

        t_nlu = 0.0
        t_subcat = 0.0
        t_db = 0.0
        cache_status = "MISS"

        t0 = time.perf_counter()

        # Safe default — prevents UnboundLocalError when the 'multiple same-name
        # subcats' branch hits `pass` and falls through to extraction below.
        nlu_result = {
            "intent":          explicit_intent or "UNKNOWN",
            "product_keyword": raw_query,
        }

        is_numeric = all(c.isdigit() or c == '.' for c in raw_query.strip())

        if is_numeric:
            logger.warning(f"[NLU] Bypassing LLM NLU for numeric HS Code query: '{raw_query}'")
            hs_code_candidate = raw_query.strip()
            nlu_result = {
                "intent": explicit_intent or "UNKNOWN",
                "product_keyword": hs_code_candidate
            }
            if not hs_code:
                hs_code = hs_code_candidate

            t_nlu = time.perf_counter() - t0

        else:
            rq = raw_query.strip()
            # Fast path: exact DB match skips NLU entirely. Check BEFORE cache so
            # stale cached NLU results can't interfere.
            from trade_data.models import ProductCategory, ProductSubCategory
            cats = list(ProductCategory.objects.filter(name__iexact=rq))
            subcats = list(ProductSubCategory.objects.filter(name__iexact=rq))
            all_matches = cats + subcats
            
            if all_matches:
                hs_codes = list(set(m.hs_code for m in all_matches))
                if len(hs_codes) == 1 and len(hs_codes[0].replace('.', '')) >= 7:
                    logger.warning(f"[NLU] Bypassing NLU for exact DB matched Category: '{rq}', directing to leaf HS {hs_codes[0]}")

                    subcat_id = subcats[0].id if subcats and not cats else None
                    variant_name = subcats[0].name if subcats and not cats else None
                    
                    t_total_s = time.perf_counter() - t_total
                    self._log_perf(raw_query, "BYPASS", {"nlu": time.perf_counter() - t0, "total": t_total_s}, nlu_result)
                    return {
                        "is_category_bridge": True,
                        "hs_code": hs_codes[0],
                        "subcat_id": subcat_id,
                        "variant_name": variant_name
                    }
                elif cats:
                    # Broad category match — let SummaryView handle it.
                    t_total_s = time.perf_counter() - t_total
                    self._log_perf(raw_query, "BYPASS", {"nlu": time.perf_counter() - t0, "total": t_total_s}, nlu_result)
                    return {
                        "is_category_bridge": True,
                        "hs_code": rq,
                    }
                else:
                    # Multiple subcategories share the same name under different HS codes.
                    # Fall through to NLU/disambig so user can pick the exact variant.
                    pass
            else:
                _cache_raw = f"nlu:{raw_query.lower().strip()}:{ui_context.lower()}"
                _cache_key = "nlu_" + hashlib.md5(_cache_raw.encode()).hexdigest()
                nlu_result = cache.get(_cache_key)
                if nlu_result is not None:
                    cache_status = "HIT"
                else:
                    cache_status = "MISS"
                    nlu_result = self._nlu_engine.parse(raw_query, ui_context=ui_context)
                    cache.set(_cache_key, nlu_result, timeout=86400)
            t_nlu = time.perf_counter() - t0

        intent  = explicit_intent or nlu_result.get("intent", "UNKNOWN")
        country = nlu_result.get("country")

        product_keyword = (
            nlu_result.get("product")
            or nlu_result.get("product_keyword")
            or raw_query
        )

        orm_scope  = self._map_scope(ui_context)
        orm_intent = intent

        # Reset per-request state on the singleton before resolution. The subcat_id
        # fast-path returns early before _resolve_subcategories runs its own reset,
        # so without this line a stale scope_mismatch from a previous request poisons
        # the disambiguation-click call and returns 0 results.
        self._scope_mismatch = None

        t0 = time.perf_counter()
        subcat_ids, variant_list, product_item_ids = self._resolve_subcategories(
            product_keyword, hs_code, country=country, intent=intent,
            subcat_id=subcat_id, variant_name=variant_name, scope=orm_scope
        )
        t_subcat = time.perf_counter() - t0


        # Scope mismatch early exit: product only exists in the opposite trade direction.
        scope_info = getattr(self, '_scope_mismatch', None)

        if scope_info:
            t_total_s = time.perf_counter() - t_total
            self._log_perf(raw_query, cache_status, {"nlu": t_nlu, "subcat": t_subcat, "total": t_total_s}, nlu_result)
            # If user already clicked Switch and we're still mismatched, data exists
            # in both directions — break the loop with a no-data message.
            if already_switched:
                logger.warning(f"[LOOP-BREAK] already_switched=True, suppressing second scope_mismatch for '{raw_query}'")
                return {
                    "nlu":                  nlu_result,
                    "profiles":             [],
                    "total_raw_hits":       0,
                    "needs_disambiguation": False,
                    "is_broad_search":      False,
                    "variants":             [],
                    "search_engine":        "none",
                    "scope_mismatch":       None,
                    "no_data_message":      f"No trade data found for '{scope_info.get('product', raw_query)}' in the selected scope. Try a broader search or remove the country filter.",
                }
            return {
                "nlu":                  nlu_result,
                "profiles":             [],
                "total_raw_hits":       0,
                "needs_disambiguation": False,
                "is_broad_search":      False,
                "variants":             [],
                "search_engine":        "none",
                "scope_mismatch":       scope_info,
            }

        # Same-name rule: if all matched subcats share the query's name (e.g. 4x
        # "Refined Sugar" under different HS codes), aggregate them instead of
        # showing a picker. Only disambiguate when variants have genuinely
        # different names ("Dextrose Anhydrous" vs "Dextrose Ball").
        needs_disambig = False
        import re
        def _clean(name):
            return re.sub(r'\(.*?\)', '', name).lower().strip()

        pk_clean = _clean(product_keyword)
        all_same_name = bool(variant_list) and all(
            _clean(v.get('name', '')) == pk_clean
            for v in variant_list
        )
        if not all_same_name:
            if len(subcat_ids) > DISAMBIGUATION_THRESHOLD:
                needs_disambig = True

        if needs_disambig:
            t_total_s = time.perf_counter() - t_total
            self._log_perf(raw_query, cache_status, {"nlu": t_nlu, "subcat": t_subcat, "total": t_total_s}, nlu_result)
            return {
                "nlu":                  nlu_result,
                "profiles":             [],
                "total_raw_hits":       0,
                "needs_disambiguation": True,
                "is_broad_search":      False,
                "variants":             variant_list,
                "search_engine":        "none",
            }

        # OpenSearch BM25 path — currently disabled.
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
        t_db = time.perf_counter() - t0

        t_total_s = time.perf_counter() - t_total
        self._log_perf(raw_query, cache_status, {"nlu": t_nlu, "subcat": t_subcat, "db": t_db, "total": t_total_s}, nlu_result)

        is_broad = False
        if not hs_code and not subcat_ids and (not product_keyword or len(product_keyword) < 2):
            is_broad = True

        active_subcat_id = subcat_ids[0] if len(subcat_ids) == 1 else None
        active_hs_code_resolved = variant_list[0].get("hs_code") if len(variant_list) == 1 and isinstance(variant_list[0], dict) else None

        _RANKING_LABELS = {
            "price_asc":   "Sorted by: Lowest Price",
            "price_desc":  "Sorted by: Highest Quality / Price",
            "volume_desc": "Sorted by: Highest Volume",
            "reliability": "Sorted by: Most Shipments (Reliability)",
        }
        _rh = nlu_result.get("ranking_hint") or ""
        ranking_applied = _RANKING_LABELS.get(_rh) or None

        return {
            "nlu":                  nlu_result,
            "profiles":             profiles,
            "total_raw_hits":       total_hits,
            "needs_disambiguation": False,
            "is_broad_search":      is_broad,
            "variants":             [],
            "search_engine":        "orm",
            "active_subcat_id":     active_subcat_id,
            "active_hs_code":       active_hs_code_resolved,
            "ranking_applied":      ranking_applied,
        }

    def _resolve_subcategories(
        self,
        product_keyword: str,
        hs_code: str = None,
        country: str = None,
        intent: str = "BUY",
        subcat_id: int = None,
        variant_name: str = None,
        scope: str = "WORLDWIDE",
    ):
        """
        Returns (subcat_ids, variant_list, product_item_ids).
        product_item_ids is non-empty only when user picked an exact item via hs_code.
        """
        from trade_data.models import ProductSubCategory, ProductItem, Transaction, ProductCategory
        from django.db.models import Q

        def _get_display_name(obj, is_item=False):
            name = obj.name
            if name.lower().strip() in ['other', 'others']:
                if is_item:
                    sc = obj.sub_category if hasattr(obj, 'sub_category') else None
                    cat = sc.category if sc and hasattr(sc, 'category') else None
                    hs = sc.hs_code if sc else ''
                else:
                    cat = obj.category if hasattr(obj, 'category') else None
                    hs = obj.hs_code
                cat_name = cat.name if cat else ''
                name = f"Other (HS {hs}) - {cat_name}" if cat_name else f"Other (HS {hs})"
            return name

        # Fast path: user clicked an exact product. Resolve item IDs so the aggregator
        # filters to the specific variant, not all variants sharing the HS code prefix.
        if subcat_id:
            item_ids = list(
                ProductItem.objects.filter(sub_category_id=subcat_id)
                .values_list('id', flat=True)
            )
            return [subcat_id], [], item_ids

        if hs_code:
            scs = list(ProductSubCategory.objects.filter(hs_code__startswith=hs_code)
                        .select_related('category').order_by('hs_code', 'name'))

            if not scs:
                # hs_code refers to a ProductItem — unpack to subcategory
                items = list(ProductItem.objects.filter(
                    sub_category__hs_code=hs_code
                ).select_related('sub_category'))
                if items:
                    sc_id = items[0].sub_category.id
                    item_ids = [i.id for i in items]
                    return [sc_id], [], item_ids
                return [], [], []

            if subcat_id:
                return [subcat_id], [], []

            if len(scs) == 1:
                return [scs[0].id], [], []

            if variant_name:
                vn_lower = variant_name.lower().strip()
                for sc in scs:
                    if sc.name.lower().strip() == vn_lower:
                        return [sc.id], [], []

            # Hierarchical grouping: short HS prefixes bucket into the next
            # meaningful level (chapter -> heading -> subheading).
            clean_q = hs_code.replace('.', '')

            if len(clean_q) <= 4:
                if len(clean_q) <= 3:
                    groups = {}
                    for sc in scs:
                        raw = sc.hs_code or ''
                        parts = raw.split('.')
                        bucket = parts[0][:4] if parts else raw[:4]
                        if len(bucket) >= 4 and bucket not in groups:
                            cat_name = sc.category.name if hasattr(sc, 'category') and sc.category else bucket
                            groups[bucket] = {
                                'id': None,
                                'hs_code': bucket,
                                'name': cat_name,
                                'category': '',
                                'is_drill_down': True,
                            }
                    variant_list = list(groups.values())
                else:
                    groups = {}
                    for sc in scs:
                        raw = sc.hs_code or ''
                        bucket = raw[:7] if len(raw) >= 7 else raw
                        if bucket not in groups:
                            groups[bucket] = {
                                'id': None,
                                'hs_code': bucket,
                                'name': sc.category.name if hasattr(sc, 'category') and sc.category else sc.name,
                                'category': '',
                                'is_drill_down': len(ProductSubCategory.objects.filter(hs_code__startswith=bucket)) > 1,
                            }
                    variant_list = list(groups.values())

                if len(variant_list) == 1 and variant_list[0].get('is_drill_down'):
                    return [sc.id for sc in scs], [], []

                return [sc.id for sc in scs], variant_list, []

            if len(scs) > 10:
                # Group by unique name to avoid hiding distinct items with same hs_code
                seen = {}
                for sc in scs:
                    key = sc.name.lower().strip()
                    if key not in seen:
                        seen[key] = {
                            'id': sc.id,
                            'hs_code': sc.hs_code,
                            'name': sc.name,
                            'category': sc.category.name if hasattr(sc, 'category') and sc.category else '',
                            'is_drill_down': False,
                        }
                variant_list = list(seen.values())
                return [sc.id for sc in scs], variant_list, []

            variant_list = [
                {
                    'id': sc.id,
                    'hs_code': sc.hs_code,
                    'name': sc.name,
                    'category': sc.category.name if hasattr(sc, 'category') and sc.category else '',
                    'is_drill_down': False,
                }
                for sc in scs
            ]
            return [sc.id for sc in scs], variant_list, []

        if not product_keyword or len(product_keyword) < 2:
            return [], [], []

        # PASS 0: Category icontains match
        cat_qs = list(ProductCategory.objects.filter(
            name__icontains=product_keyword
        ))
        cat_sc_ids = set()
        if cat_qs:
            cat_sc_qs = list(ProductSubCategory.objects.filter(
                category__in=cat_qs
            ).select_related("category"))
            cat_sc_ids = {sc.id for sc in cat_sc_qs}
        else:
            cat_sc_qs = []

        # PASS 1: Prefix match on subcategory names
        pass1 = list(ProductSubCategory.objects.filter(
            name__istartswith=product_keyword
        ).select_related("category"))
        sc_map_pre = {sc.id: sc for sc in cat_sc_qs}
        for sc in pass1:
            sc_map_pre.setdefault(sc.id, sc)
        sc_qs = list(sc_map_pre.values())

        # PASS 2: Prefix match on product item names
        item_qs = list(ProductItem.objects.filter(
            name__istartswith=product_keyword
        ).select_related("sub_category__category"))

        # PASS 3: pg_trgm fuzzy fallback (0.45 threshold cuts false positives)
        if not sc_qs and not item_qs:
            from django.contrib.postgres.search import TrigramSimilarity
            sc_qs = list(ProductSubCategory.objects.annotate(
                similarity=TrigramSimilarity('name', product_keyword)
            ).filter(similarity__gt=0.45).order_by('-similarity')[:5].select_related("category"))
            item_qs = list(ProductItem.objects.annotate(
                similarity=TrigramSimilarity('name', product_keyword)
            ).filter(similarity__gt=0.45).order_by('-similarity')[:5].select_related("sub_category__category"))

        # PASS 4: Word-by-word search for garbled queries and single-word typos.
        if not sc_qs and not item_qs:
            words = sorted([w for w in product_keyword.split() if len(w) > 2], key=len, reverse=True)
            if not words:
                words = [product_keyword]
            for word in words:
                sc_qs = list(ProductSubCategory.objects.filter(name__istartswith=word).select_related("category"))
                item_qs = list(ProductItem.objects.filter(name__istartswith=word).select_related("sub_category__category"))
                if sc_qs or item_qs:
                    break
                from django.contrib.postgres.search import TrigramSimilarity
                sc_qs = list(ProductSubCategory.objects.annotate(
                    similarity=TrigramSimilarity('name', word)
                ).filter(similarity__gt=0.45).order_by('-similarity')[:5].select_related("category"))
                item_qs = list(ProductItem.objects.annotate(
                    similarity=TrigramSimilarity('name', word)
                ).filter(similarity__gt=0.45).order_by('-similarity')[:5].select_related("sub_category__category"))
                if sc_qs or item_qs:
                    break

        # PASS 5: RapidFuzz full-catalog fuzzy match for severe typos.
        if not sc_qs and not item_qs:
            try:
                from rapidfuzz import process, fuzz
                catalog = SearchService._get_product_catalog()
                match = process.extractOne(
                    product_keyword,
                    catalog,
                    scorer=fuzz.WRatio,
                    score_cutoff=75,
                )
                if match:
                    corrected = match[0]
                    logger.info(f"[PASS5] RapidFuzz: '{product_keyword}' → '{corrected}' (score={match[1]:.1f})")
                    sc_qs = list(ProductSubCategory.objects.filter(
                        name__iexact=corrected
                    ).select_related("category"))
                    item_qs = list(ProductItem.objects.filter(
                        name__iexact=corrected
                    ).select_related("sub_category__category"))
            except Exception as _e:
                logger.warning(f"[PASS5] RapidFuzz fallback failed: {_e}")

        sc_map = {}
        for sc in sc_qs:
            sc_map[sc.id] = {
                "id":       sc.id,
                "hs_code":  sc.hs_code,
                "name":     _get_display_name(sc),
                "category": sc.category.name if hasattr(sc, 'category') and sc.category else ''
            }
        for item in item_qs:
            sc = item.sub_category
            if sc.id not in sc_map:
                sc_map[sc.id] = {
                    "id":       sc.id,
                    "hs_code":  sc.hs_code,
                    "name":     _get_display_name(sc),
                    "category": sc.category.name if hasattr(sc, 'category') and sc.category else ''
                }

        variant_list = list(sc_map.values())
        subcat_ids   = list(sc_map.keys())

        # Scope-aware availability filter — skipped for HS-code searches because
        # the frontend's 4-tab pill UI lets the user pick direction; applying a
        # scope filter here would kill half the results.
        self._scope_mismatch = None

        if subcat_ids and not hs_code:
            target_trade_type = scope

            filters = {
                "trade_type": target_trade_type,
                "product_item__sub_category_id__in": subcat_ids,
            }

            if country:
                country_field = None
                if target_trade_type == 'IMPORT':
                    country_field = 'origin_country' if intent == 'BUY' else 'destination_country'
                elif target_trade_type == 'EXPORT':
                    country_field = 'destination_country' if intent == 'SELL' else 'origin_country'
                
                if country_field:
                    filters[country_field] = country

            availability_qs = Transaction.objects.filter(**filters)

            active_ids = set(
                availability_qs.values_list(
                    "product_item__sub_category_id", flat=True
                ).distinct()
            )

            if active_ids:
                variant_list = [v for v in variant_list if v["id"] in active_ids]
                subcat_ids   = [sid for sid in subcat_ids if sid in active_ids]
            else:
                opposite_type = "EXPORT" if target_trade_type == "IMPORT" else "IMPORT"
                from django.db.models import Min, Max
                opposite_qs = Transaction.objects.filter(
                    trade_type=opposite_type,
                    product_item__sub_category_id__in=subcat_ids,
                )
                opposite_count = opposite_qs.count()

                if opposite_count > 0:
                    # Re-check opposite scope filtered by the requested country, so we
                    # don't surface a mismatch about Brazil when only China data exists.
                    opposite_filters = {
                        "trade_type": opposite_type,
                        "product_item__sub_category_id__in": subcat_ids,
                    }
                    if country:
                        opp_country_field = None
                        if opposite_type == 'IMPORT':
                            opp_country_field = 'origin_country' if intent == 'BUY' else 'destination_country'
                        elif opposite_type == 'EXPORT':
                            opp_country_field = 'destination_country' if intent == 'SELL' else 'origin_country'
                        if opp_country_field:
                            opposite_filters[opp_country_field] = country
                    
                    opposite_qs = Transaction.objects.filter(**opposite_filters)
                    opposite_count = opposite_qs.count()
                    
                    if opposite_count > 0:
                        date_range = opposite_qs.aggregate(
                            min_date=Min("reporting_date"),
                            max_date=Max("reporting_date"),
                        )
                        product_display = product_keyword or "this product"
                        current_label = "exported" if target_trade_type == "EXPORT" else "imported"
                        alt_label     = "imported" if target_trade_type == "EXPORT" else "exported"
                        alt_scope     = "import" if target_trade_type == "EXPORT" else "export"

                        min_year = date_range["min_date"].year if date_range["min_date"] else "?"
                        max_year = date_range["max_date"].year if date_range["max_date"] else "?"

                        self._scope_mismatch = {
                            "product": product_display,
                            "current_scope": target_trade_type.lower(),
                            "alt_scope": alt_scope,
                            "current_label": current_label,
                            "alt_label": alt_label,
                            "alt_records": opposite_count,
                            "year_min": min_year,
                            "year_max": max_year,
                        }
                        # Clear variants so disambiguation picker doesn't show.
                        variant_list = []
                        subcat_ids = []
                    else:
                        variant_list = []
                        subcat_ids = []

        return subcat_ids, variant_list, []

    def _opensearch_search(
        self, product_keyword, intent, ui_context, subcat_ids, hs_code, top_k, nlu_result
    ) -> dict:
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

    def _orm_search(self, subcat_ids, intent, scope, nlu_result, top_k=100, product_item_ids=None, raw_query=""):
        """
        product_item_ids pins to an exact item so e.g. 'Dextrose Anhydrous' and
        'Dextrose Ball' never share supplier lists when sharing an HS code.
        """
        from search.services.aggregation import SupplierAggregator
        aggregator = SupplierAggregator()

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

        raw_results = aggregator.get_suppliers_for_subcategories(
            subcategory_ids=subcat_ids,
            intent=intent,
            scope=scope,
            country_filter=country_filter,
            price_filter=price_filter,
            product_item_filter=product_item_ids or None,
        )

        # Ranking: explicit hint sorts directly on the relevant field
        # ("cheapest dextrose" -> ORDER BY price ASC, not a composite).
        # Default = balanced composite (volume + shipments + price + recency).
        if raw_results:
            ranking_hint  = nlu_result.get("ranking_hint") or (nlu_result.get("price_filter") or {}).get("ranking_hint") or ""
            signal_text   = nlu_result.get("product_keyword", "").lower() + " " + raw_query.lower()

            if ranking_hint == "price_asc" or any(
                w in signal_text for w in ["cheap", "affordable", "low price", "best price",
                                            "cheapest", "under", "inexpensive", "bargain"]
            ):
                preset_name = "price_asc"
            elif ranking_hint == "price_desc":
                preset_name = "price_desc"
            elif ranking_hint == "volume_desc" or any(
                w in signal_text for w in ["biggest", "largest", "bulk", "leading",
                                            "most active", "highest volume", "large scale"]
            ):
                preset_name = "volume_desc"
            elif ranking_hint == "reliability" or any(
                w in signal_text for w in ["reliable", "trusted", "established", "serious", "verified"]
            ):
                preset_name = "reliability"
            else:
                preset_name = "default"

            logger.info(
                f"[Ranking] Preset='{preset_name}' ranking_hint={ranking_hint!r}"
            )

            if preset_name == "price_asc":
                # No-price suppliers sink to the bottom.
                raw_results.sort(key=lambda r: r.get("avg_price") or float("inf"))
                for r in raw_results:
                    r["composite_score"] = 0.0
                    r["ranking_preset"]  = preset_name

            elif preset_name == "price_desc":
                raw_results.sort(key=lambda r: r.get("avg_price") or 0.0, reverse=True)
                for r in raw_results:
                    r["composite_score"] = 0.0
                    r["ranking_preset"]  = preset_name

            elif preset_name == "volume_desc":
                raw_results.sort(key=lambda r: r.get("total_volume") or 0.0, reverse=True)
                for r in raw_results:
                    r["composite_score"] = 0.0
                    r["ranking_preset"]  = preset_name

            elif preset_name == "reliability":
                # Shipment count is the reliability proxy.
                raw_results.sort(key=lambda r: r.get("shipment_count") or 0, reverse=True)
                for r in raw_results:
                    r["composite_score"] = 0.0
                    r["ranking_preset"]  = preset_name

            else:
                w1, w2, w3, w4 = 0.4, 0.3, 0.2, 0.1

                vols   = [r["total_volume"] for r in raw_results]
                counts = [r["shipment_count"] for r in raw_results]

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

                    score = w1 * vol_norm + w2 * cnt_norm + w4 * rec_norm
                    if r.get("avg_price"):
                        p_norm = minmax(1.0 / r["avg_price"], min_inv_p, max_inv_p)
                        score += w3 * p_norm

                    r["composite_score"] = score
                    r["ranking_preset"]  = preset_name

                raw_results.sort(key=lambda x: x.get("composite_score", 0), reverse=True)

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

    @staticmethod
    def _map_scope(ui_context: str) -> str:
        return "EXPORT" if ui_context.lower() == "export" else "IMPORT"

    def autocomplete_products(self, partial_query: str, limit: int = 8) -> list:
        """
        Strips intent stop-words before the DB lookup so "i want to buy dex"
        matches "Dextrose". Ranked by total transaction volume.
        """
        from django.db.models import Sum, Count
        from trade_data.models import ProductCategory, ProductSubCategory, ProductItem, Transaction
        from search.services.nlu_engine import extract_product_keyword

        if not partial_query or len(partial_query) < 2:
            return []

        raw = partial_query.strip()
        is_numeric = bool(raw) and all(c.isdigit() or c == '.' for c in raw)

        if is_numeric:
            keyword = raw
        else:
            keyword = extract_product_keyword(raw)
            if len(keyword) < 2:
                keyword = raw
            if len(keyword) < 2:
                return []

        if is_numeric:
            sc_matches = ProductSubCategory.objects.filter(
                hs_code__startswith=keyword
            ).select_related("category")
            cat_matches = ProductCategory.objects.filter(
                hs_code__startswith=keyword
            )
        else:
            sc_matches = ProductSubCategory.objects.filter(
                name__icontains=keyword
            ).select_related("category")
            cat_matches = ProductCategory.objects.filter(
                name__icontains=keyword
            )

        seen_names = set()
        suggestions = []

        for sc in sc_matches[:30]:
            name_lower = sc.name.lower().strip()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                suggestions.append({
                    "hs_code":  sc.hs_code,
                    "name":     sc.name,
                    "category": sc.category.name if getattr(sc, 'category', None) else "Category",
                    "is_leaf":  True,
                })

        for cat in cat_matches[:30]:
            name_lower = cat.name.lower().strip()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                suggestions.append({
                    "hs_code":  cat.hs_code,
                    "name":     cat.name,
                    "category": "Broad Category",
                    "is_leaf":  False,
                })

        if not suggestions:
            return []

        results = []
        for meta in suggestions:
            vol = Transaction.objects.filter(
                hs_code__startswith=meta["hs_code"]
            ).aggregate(total=Sum("qty_mt"), count=Count("id"))

            results.append({
                "hs_code":      meta["hs_code"],
                "name":         meta["name"],
                "category":     meta["category"],
                "total_volume": float(vol["total"] or 0),
                "tx_count":     vol["count"] or 0,
                "is_final":     meta["is_leaf"],
            })

        results.sort(key=lambda x: x["total_volume"], reverse=True)
        return results[:limit]

    @classmethod
    def _get_embed_model(cls):
        if cls._embed_model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: all-MiniLM-L6-v2")
            cls._embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._embed_model

    @classmethod
    def _get_reranker(cls):
        if cls._reranker is None:
            from sentence_transformers import CrossEncoder
            logger.info("Loading BGE-Reranker: BAAI/bge-reranker-base")
            cls._reranker = CrossEncoder("BAAI/bge-reranker-base")
        return cls._reranker

    def semantic_search(self, query: str, top_k: int = 10) -> list:
        if not self._opensearch_available():
            return []
        model        = self._get_embed_model()
        query_vector = model.encode(query).tolist()
        os_query     = {
            "size": top_k,
            "query": {"knn": {"combined_vector": {"vector": query_vector, "k": top_k}}},
        }
        try:
            response = self._os_client.search(index=INDEX_NAME, body=os_query)
            return [hit["_source"] for hit in response.get("hits", {}).get("hits", [])]
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def rerank_results(self, query: str, profiles: list, max_rerank: int = 15) -> list:
        if not profiles:
            return profiles
        reranker    = self._get_reranker()
        to_rerank   = profiles[:max_rerank]
        the_rest    = profiles[max_rerank:]
        sentence_pairs = [
            [query, f"Company: {p.get('company_name')}. Volume: {p.get('total_volume')} MT. "
                    f"Shipments: {p.get('transaction_count')}. Last active: {p.get('last_shipped')}."]
            for p in to_rerank
        ]
        try:
            scores = reranker.predict(sentence_pairs)
            for i, p in enumerate(to_rerank):
                p["relevance_score"] = float(scores[i])
            reranked = sorted(to_rerank, key=lambda x: x["relevance_score"], reverse=True)
            for p in the_rest:
                p["relevance_score"] = 0.0
            return reranked + the_rest
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return profiles
