# ZaraiLink Search Engine — Exhaustive Bug Tracker

**Total: 60 bugs** | Critical: 5 | Significant: 20 | Moderate: 35
**Audit date:** 2026-02-15
**ALL 60 BUGS FIXED:** 2026-02-15
**Files audited:**
- `backend/search/services/query_parser.py`
- `backend/search/services/nlp.py`
- `backend/search/services/aggregation.py`
- `backend/search/services/ranking_ltr.py`
- `backend/search/services/ranking.py`
- `backend/search/services/train_ltr.py`
- `backend/search/services/ltr_dataset_builder.py`
- `backend/search/services/ltr_evaluation.py`
- `backend/search/views.py`
- `backend/search/urls.py`
- `backend/trade_data/models.py`

---

## TIER 1: CRITICAL (5) — System fundamentally broken

### BUG-001: Feature key mismatch — 5 of 8 ranking features are dead
- **Status:** OPEN
- **File:** `ranking_ltr.py:64-66,69,80` vs `aggregation.py:98-105`
- **Description:** FeatureExtractor reads keys that don't exist in the candidate dict returned by SupplierAggregator. All 5 features silently default to 0.
- **Impact:** Ranking is nonfunctional across ALL queries. All candidates get near-identical scores.

| FeatureExtractor reads | Aggregator provides | Feature value |
|---|---|---|
| `total_volume_mt` (line 64) | `total_volume` | Always 0 |
| `avg_price_usd_per_mt` (line 65) | `avg_price` | Always 0 |
| `num_shipments` (line 66) | `shipment_count` | Always 0 |
| `last_trade_date` as string (line 69) | `last_shipment_date` as datetime.date | Always 0 (wrong key + wrong type) |
| `volume_fit` (line 80) | never set at inference time | Always 'N/A' → 0 |

- **Fix:** Align FeatureExtractor keys to match aggregator output. Handle datetime.date for recency. Enrich candidates with volume_fit before ranking.

---

### BUG-002: LTR model trained on garbage — same key mismatch in training
- **Status:** OPEN
- **File:** `ltr_dataset_builder.py:121` → calls `extractor.extract(cand, parsed_q)`
- **Description:** The dataset builder calls FeatureExtractor with candidates from SupplierAggregator. Same key mismatch as BUG-001. The LightGBM model was trained on 5 zero-valued features. It has never learned from real volume, price, frequency, recency, or volume_fit data.
- **Impact:** Trained model is useless. The 30% LTR weight in the ensemble contributes noise or zeros.
- **Fix:** Fix BUG-001 first, then retrain the model.

---

### BUG-003: `get_supplier_details` hardcoded to seller — SELL intent detail pages return 404
- **Status:** OPEN
- **File:** `aggregation.py:119`
- **Description:** `queryset = Transaction.objects.filter(seller=seller_name, ...)`. When intent=SELL, search results list buyers (`target_field='buyer'`). If user clicks a buyer name, the detail view passes that buyer name, but queries `seller=buyer_name` → no matching transactions → returns None → 404 error.
- **Impact:** Supplier detail page is completely broken for all SELL-intent queries.
- **Fix:** Accept an `intent` parameter. If SELL, filter on `buyer=name` instead of `seller=name`. Also fix hardcoded `origin_country` references (lines 158, 165) to use the correct country field per intent.

---

### BUG-004: Empty clean query matches ALL products in database
- **Status:** OPEN
- **File:** `nlp.py:40`
- **Description:** If all words in the query are stopwords (e.g., "I want to buy"), `_clean_query` returns `""`. Then `ProductSubCategory.objects.filter(name__icontains='')` matches every row — ILIKE on empty string is universally true.
- **Impact:** User sees the entire product catalog dumped back as results. Potentially thousands of subcategories, leading to a massive aggregation query that could time out.
- **Fix:** Check for empty `clean_qs` before running the DB query. Return empty matches if clean_qs is empty or below a minimum length.

---

### BUG-005: `parsed_query` passed to ranker instead of `active_params` for multi-intent
- **Status:** OPEN
- **File:** `views.py:168`
- **Description:** For multi-intent queries, views.py merges sub_intents into `active_params` (line 78). But `ranker.rank_candidates(results, parsed_query)` passes the raw `parsed_query` which has `family=9` and the first sub-intent's unmerged attributes. The ranker uses wrong family weights and potentially wrong country_filter/price attributes.
- **Impact:** Multi-intent queries (Family 9) get wrong ranking behavior. Merged filters are applied in aggregation but not reflected in ranking scores.
- **Fix:** Pass `active_params` instead of `parsed_query` to the ranker.

---

## TIER 2: SIGNIFICANT (20) — Wrong results for specific scenarios

### BUG-006: `price_floor` ignored in ranking features
- **Status:** OPEN
- **File:** `ranking_ltr.py:104-110`
- **Description:** `price_fit` feature only checks `price_ceiling`. If user says "sell above $500" (price_floor), it's extracted by the parser and applied as a hard filter in aggregation, but the ranking feature `price_fit` is 0.5 (neutral) instead of scoring candidates against the floor.
- **Fix:** Add floor check: `if floor and price >= floor: price_fit = 1.0`.

---

### BUG-007: Scope conflict check missing for SELL intent
- **Status:** OPEN
- **File:** `views.py:113-123`
- **Description:** Only checks `active_scope == 'PAKISTAN' and country_filter` generically. For SELL+PAKISTAN, the hard filter is `destination_country='Pakistan'`. A non-Pakistan country filter on destination silently returns zero results with no error message.
- **Fix:** Extend the conflict check to consider intent. For SELL+PAKISTAN, check country_filter against destination_country.

---

### BUG-008: "Korea" extracted instead of "South Korea" — iteration order bug
- **Status:** OPEN
- **File:** `query_parser.py:198-203`, COUNTRIES list order
- **Description:** COUNTRIES list has "Korea" at index 26, "South Korea" at index 27. Pattern `\bkorea\b` matches first inside "south korea", extracts "Korea" and removes it from remainder. Then `\bsouth korea\b` can't match. User gets wrong country.
- **Fix:** Sort COUNTRIES by length descending before iterating (longest first), so "South Korea" matches before "Korea".

---

### BUG-009: "Dubai" is a city — zero DB matches
- **Status:** OPEN
- **File:** `query_parser.py:13`
- **Description:** "Dubai" in COUNTRIES list. Database likely stores "UAE" for Dubai-based entities. Country filter `["Dubai"]` matches no transactions.
- **Fix:** Remove "Dubai" from COUNTRIES. Add "dubai" → "UAE" to COUNTRY_ALIASES.

---

### BUG-010: SELL+WORLDWIDE has no `origin_country='Pakistan'` filter
- **Status:** OPEN
- **File:** `aggregation.py:42`
- **Description:** `queryset.filter(trade_type='EXPORT')` returns ALL exports in DB, not just Pakistan's. If DB contains multi-country export data, results include non-Pakistan exporters.
- **Fix:** Add `origin_country='Pakistan'` to the filter for SELL+WORLDWIDE.

---

### BUG-011: BUY+WORLDWIDE has no `destination_country='Pakistan'` filter
- **Status:** OPEN
- **File:** `aggregation.py:57`
- **Description:** `queryset.filter(trade_type='IMPORT')` returns ALL imports, not just imports to Pakistan. Same issue as BUG-010 for the import side.
- **Fix:** Add `destination_country='Pakistan'` to the filter for BUY+WORLDWIDE.

---

### BUG-012: Families 6, 7, 8 have no FAMILY_WEIGHTS
- **Status:** OPEN
- **File:** `ranking_ltr.py:26-46`
- **Description:** FAMILY_WEIGHTS dict only has entries for 1, 2, 3, 4, 5, 9. Families 6 (Recommendation), 7 (Comparison), 8 (Evidence) fall back to Family 9 generic weights via `FAMILY_WEIGHTS.get(family_id, DEFAULT_WEIGHTS)`.
- **Fix:** Add specific weight profiles for families 6, 7, 8.

---

### BUG-013: `_parse_time_range` hardcoded to 2024/2025 quarters only
- **Status:** OPEN
- **File:** `views.py:315-326`
- **Description:** Quarter parsing uses literal if/elif for "q1" + "2025", "q2" + "2025", etc. "Q1 2023", "Q3 2026", or any other year silently returns None. The time filter is dropped.
- **Fix:** Parse quarter number and year dynamically.

---

### BUG-014: `_parse_time_range` can't handle generic "last N months/years"
- **Status:** OPEN
- **File:** `views.py:333-338`
- **Description:** Only handles literal "last 6 months" and "last 3 months". "last 12 months", "last 2 years", "last 1 month" all return None. The parser DOES extract these correctly (line 274-278), but _parse_time_range drops them.
- **Fix:** Parse the number and unit dynamically from the string.

---

### BUG-015: `_parse_time_range` can't handle "from X to Y" date ranges
- **Status:** OPEN
- **File:** `views.py:298-346`
- **Description:** Parser extracts `"january to march"` as time_range (line 269-272), but _parse_time_range has no handler for month-name ranges. Returns None.
- **Fix:** Add month-name parsing (map "january"→1, etc.) and construct date range.

---

### BUG-016: Quarter default year hardcoded to 2025
- **Status:** OPEN
- **File:** `query_parser.py:265`
- **Description:** `year = q_match.group(2) or "2025"`. If user says "Q1" without a year, defaults to 2025 instead of current year.
- **Fix:** Use `str(datetime.date.today().year)` or `import datetime; str(datetime.datetime.now().year)`.

---

### BUG-017: `supplier_detail` comparables always use BUY+WORLDWIDE defaults
- **Status:** OPEN
- **File:** `views.py:226`
- **Description:** `all_suppliers = aggregator.get_suppliers_for_subcategories(subcategory_ids)` uses default parameters (intent='BUY', scope='WORLDWIDE'). If the original search was SELL intent, comparables show sellers instead of fellow buyers.
- **Fix:** Pass the original intent and scope to the comparables query. Accept these as query params from the frontend.

---

### BUG-018: `supplier_detail` passes raw query to QueryMatcher
- **Status:** OPEN
- **File:** `views.py:213`
- **Description:** `matcher.match(query)` where query is the raw user string (e.g., "buy sugar from China"). The matcher's _clean_query removes some words but "china" survives and may match China-related subcategories. Subcategory IDs become overly broad.
- **Fix:** Parse the query first and pass only the extracted product term to the matcher.

---

### BUG-019: Volume unit case sensitivity — "KG" not converted to MT
- **Status:** OPEN
- **File:** `query_parser.py:227,230`
- **Description:** `unit = vol_match.group(2)` preserves original case (regex is case-insensitive). Then `if unit in ['kg', 'kilo']` — fails for "KG", "Kg", "KILO". Volume stays in kg-scale instead of dividing by 1000.
- **Fix:** `unit = vol_match.group(2).lower()`.

---

### BUG-020: Volume regex only handles one comma group
- **Status:** OPEN
- **File:** `query_parser.py:222`
- **Description:** Pattern `(\d+(?:,\d+)?)` matches "1,000" but not "1,000,000". A 1-million-MT query is parsed as 1,000 MT.
- **Fix:** Change to `(\d+(?:,\d{3})*)` to handle multiple comma groups.

---

### BUG-021: Multi-intent with mixed BUY/SELL loses second intent
- **Status:** OPEN
- **File:** `query_parser.py:103`, `views.py:89`
- **Description:** Top-level `intent` is always from `sub_intents[0]`. If first sub-intent is BUY and second is SELL, aggregation runs with BUY intent only. The SELL part of the query is completely ignored.
- **Fix:** For truly mixed intents, either run two separate aggregations and merge, or clearly communicate to the user that only the first intent is processed.

---

### BUG-022: `counterparty_name` extracted but never used
- **Status:** OPEN
- **File:** `query_parser.py:346`, `views.py` (never reads it)
- **Description:** Parser extracts company names (e.g., "Al-Amin Ltd") into `counterparty_name`, but views.py never applies any counterparty filter. Queries like "sugar from Al-Amin Ltd" are treated identically to "sugar".
- **Fix:** If counterparty_name is set, add a filter on `target_field__icontains=counterparty_name` in aggregation.

---

### BUG-023: URL routing mismatch — frontend may get 404
- **Status:** OPEN (needs frontend verification)
- **File:** `search/urls.py:22`
- **Description:** Router registers ViewSet at `r''`, making the list endpoint `/api/search/`. Comments on lines 9-11 say the frontend called `/api/search/query/?q=...`. With current routing, `/api/search/query/` is interpreted as `/{pk}/` with pk="query" → 405/404.
- **Fix:** Verify frontend URL. Either update frontend to call `/api/search/?q=...` or register router at `r'query'`.

---

### BUG-024: "Pakistan" country filter on BUY+WORLDWIDE silently returns empty
- **Status:** OPEN
- **File:** `views.py:112-123`, `aggregation.py:52-57`
- **Description:** If user types "buy sugar from Pakistan" with WORLDWIDE scope, aggregation runs BUY+WORLDWIDE: `trade_type='IMPORT'` + `origin_country__in=['Pakistan']`. Imports INTO Pakistan have foreign origin — so `origin_country='Pakistan'` finds zero results. No error message shown.
- **Fix:** Detect when "Pakistan" is in the country filter with WORLDWIDE scope and either auto-switch to PAKISTAN scope or show a helpful message.

---

### BUG-025: `avg_price = 0.0` for suppliers with all-NULL prices — misleading
- **Status:** OPEN
- **File:** `aggregation.py:102`
- **Description:** `float(r['avg_price'] or 0)`. When all transactions have `usd_per_mt=NULL`, Avg() returns NULL → converted to 0.0. Looks like free goods instead of "no price data".
- **Fix:** Use `None` instead of 0 when avg_price is NULL. Let frontend display "N/A".

---

## TIER 3: MODERATE (35) — Degraded experience or minor logic flaws

### BUG-026: "importers" scores BUY(+1), "exporters" scores SELL(+1) — inverted for standalone use
- **Status:** OPEN
- **File:** `query_parser.py:32,39`
- **Description:** "sugar exporters" → SELL(1) → SELL intent. But user likely wants to find suppliers (BUY). Low score (1) means easily overridden, but wrong for queries with no other intent signals.

---

### BUG-027: FAM_6/7/8 keyword detection uses substring `in`, not word boundary
- **Status:** OPEN
- **File:** `query_parser.py:168-170`
- **Description:** `any(x in raw_query for x in ...)`. "vs" matches inside "canvas". "top" matches inside "stoppage". "rank" matches inside "ranking". "record" matches inside "recorded".
- **Fix:** Use regex `\b` word boundary check instead of substring `in`.

---

### BUG-028: `scope_match` feature is always 1.0 — dead feature
- **Status:** OPEN
- **File:** `ranking_ltr.py:87`
- **Description:** Hardcoded `scope_match = 1.0`. Adds constant to all scores. Zero discriminative value.
- **Fix:** Either implement real scope matching logic or remove the feature.

---

### BUG-029: `country_match` effectively binary (0.5 or 1.0) — minimal signal
- **Status:** OPEN
- **File:** `ranking_ltr.py:93-100`
- **Description:** Aggregation hard-filters by country, so all returned candidates match (→1.0). When no filter, all get 0.5. The 0.0 path is unreachable.
- **Fix:** Remove hard country filter from aggregation and let ranking handle it as a soft preference, OR accept this as intentional and document it.

---

### BUG-030: `match_features` in response always shows null
- **Status:** OPEN
- **File:** `ranking_ltr.py:257-260`
- **Description:** `candidates[i].get('total_volume_mt')` → None. `candidates[i].get('volume_fit')` → None. Frontend sees `{vol: null, fit: null}`.
- **Fix:** Use correct keys (`total_volume`, etc.) after fixing BUG-001.

---

### BUG-031: RankingEnsemble reinstantiated per request — LTR model reloaded from disk
- **Status:** OPEN
- **File:** `views.py:166-167`
- **Description:** `ranker = RankingEnsemble()` creates a new instance per search request. The constructor calls `self.ltr_model.load()` which reads `lgbm_ltr.txt` from disk every time.
- **Fix:** Cache the RankingEnsemble as a module-level singleton or class variable.

---

### BUG-032: `PseudoLabelGenerator` instantiated but unused in rank_candidates
- **Status:** OPEN
- **File:** `ranking_ltr.py:231`
- **Description:** `h_gen = PseudoLabelGenerator()` constructed, never called. Dead code.
- **Fix:** Remove the line.

---

### BUG-033: `distinct_intents` set computed but never used
- **Status:** OPEN
- **File:** `query_parser.py:88`
- **Description:** `distinct_intents = set()` populated with each sub-intent's intent, but never referenced for any logic.
- **Fix:** Remove or use it to detect mixed intent conflicts.

---

### BUG-034: Debug print statements in production code
- **Status:** OPEN
- **File:** `aggregation.py:62-64`
- **Description:** Two `print()` calls with `queryset.count()` — the `.count()` executes an extra DB query on every request with a country filter.
- **Fix:** Remove or convert to `logging.debug()`.

---

### BUG-035: `SupplierRanker` imported but never used
- **Status:** OPEN
- **File:** `views.py:10`
- **Description:** `from .services.ranking import SupplierRanker, ComparableFinder` — SupplierRanker is dead code. Only ComparableFinder is used.
- **Fix:** Remove the SupplierRanker import.

---

### BUG-036: POST body fallback in list() is unreachable
- **Status:** OPEN
- **File:** `views.py:30-32`
- **Description:** The `list` action is GET-only via DRF router. `request.method == 'POST'` never fires.
- **Fix:** Remove the dead code block.

---

### BUG-037: Stale search index — no invalidation mechanism
- **Status:** OPEN
- **File:** `nlp.py:21-27`, `build_search_index.py`
- **Description:** Pickle index is loaded once and cached forever via class variable. If subcategories are added/deleted, index is stale. Keyword matching (line 40) hits live DB, creating inconsistency between keyword and semantic results.
- **Fix:** Add index rebuild on subcategory change, or check index freshness periodically.

---

### BUG-038: Fuzzy match uses `str.replace()` — not word-boundary-aware
- **Status:** OPEN
- **File:** `query_parser.py:216`
- **Description:** `remainder = remainder.replace(token, '')`. If a fuzzy-matched token appears as a substring of another word, it strips from inside that word. E.g., "industrial" contains "india" (after lowercase) — though "india" would already be removed by standard list check, other tokens could have this issue.
- **Fix:** Use `re.sub(r'\b' + re.escape(token) + r'\b', '', remainder)`.

---

### BUG-039: Price filter distorts aggregated stats silently
- **Status:** OPEN
- **File:** `aggregation.py:67-70`
- **Description:** Price ceiling/floor applied at transaction level before aggregation. A supplier with transactions at $400 and $800, with ceiling=$500, shows avg_price=$400, shipment_count=1 (not 2), and reduced total_volume. Stats are distorted without indication.
- **Fix:** Document this behavior or apply price filter post-aggregation on avg_price.

---

### BUG-040: `get_supplier_details` hardcodes `origin_country` for history/filters
- **Status:** OPEN
- **File:** `aggregation.py:158,165`
- **Description:** Transaction history shows `tx.origin_country` and country filter lists `origin_country` regardless of intent. For SELL queries, the relevant country is `destination_country`.
- **Fix:** Accept intent parameter and use correct country field.

---

### BUG-041: Entity extraction regex too greedy — eats product name
- **Status:** OPEN
- **File:** `query_parser.py:343`
- **Description:** `[\w\s]+ (?:ltd|inc|co|corp)` — the `[\w\s]+` is greedy and consumes everything before the corporate suffix. "sugar amin co" → entity="sugar amin co", product="".
- **Fix:** Use a non-greedy or more constrained pattern, e.g., `(\S+(?:\s+\S+){0,3})\s+(?:ltd|inc|co|corp)`.

---

### BUG-042: Bare `except:` catches all exceptions including SystemExit
- **Status:** OPEN
- **File:** `ltr_dataset_builder.py:158`
- **Description:** `except:` catches everything including KeyboardInterrupt and SystemExit.
- **Fix:** Use `except Exception:`.

---

### BUG-043: LTR dataset builder only generates 5 of 36 possible query combos
- **Status:** OPEN
- **File:** `ltr_dataset_builder.py:41-65`
- **Description:** Only generates Family 1/3/4 × BUY+WORLDWIDE, Family 1 × SELL+WORLDWIDE, Family 1 × BUY+PAKISTAN. No coverage for Family 2/5/6/7/8/9, no SELL+PAKISTAN. Model has extremely narrow training coverage.
- **Fix:** Generate synthetic queries for all families and all intent×scope combinations.

---

### BUG-044: NDCG returns 1.0 for empty result lists — inflates evaluation
- **Status:** OPEN
- **File:** `ltr_evaluation.py:13`
- **Description:** `return 1.0 if len(y_true) == 0`. Perfect score for empty list inflates the average NDCG metric, making the model appear better than it is.
- **Fix:** Return 0.0 for empty lists, or exclude them from the average.

---

### BUG-045: Family classification is single-winner — no compound families
- **Status:** OPEN
- **File:** `query_parser.py:352-360`
- **Description:** A query with BOTH price AND time (e.g., "chocolate under $500 in Q1 2025") gets Family 4 (price wins). Time constraint is applied as hard filter but not reflected in ranking weights. Same for any multi-constraint query.
- **Fix:** Consider a compound family or adjust family weights to include secondary constraints.

---

### BUG-046: "from X to Y" time pattern can match non-time contexts
- **Status:** OPEN
- **File:** `query_parser.py:269`
- **Description:** `r'from\s+(\w+)\s+to\s+(\w+)'` matches any "from X to Y" structure. If a country wasn't removed (e.g., typo), "from chyna to buy" produces time_range="chyna to buy".
- **Fix:** Validate that captured groups are month names or dates.

---

### BUG-047: `recency_score` in SupplierRanker is hardcoded placeholder
- **Status:** OPEN
- **File:** `ranking.py:24`
- **Description:** `recency_score = 1.0` — never computed from actual date. (SupplierRanker itself is unused, but if ever re-enabled, this is broken.)
- **Fix:** Remove SupplierRanker entirely or implement recency calculation.

---

### BUG-048: `u.s.a` (with dots) not recognized as USA
- **Status:** OPEN
- **File:** `query_parser.py:178-216`
- **Description:** Alias "u.s." fails on "u.s.a" (next char is word char). Standard list "USA" doesn't match "u.s.a". Fuzzy match "Usa" vs "USA" = 0.33 ratio (case-sensitive) — below 0.85 cutoff.
- **Fix:** Add "u.s.a" and "u.s.a." to COUNTRY_ALIASES.

---

### BUG-049: Dead imports across multiple files
- **Status:** OPEN
- **Files/Imports:**
  - `query_parser.py:2` — `import math`
  - `ranking_ltr.py:5` — `import json`
  - `ranking_ltr.py:6` — `import pickle`
  - `ltr_dataset_builder.py:3` — `import random`
  - `aggregation.py:2` — `F` from django.db.models
  - `views.py:2` — `status` from rest_framework
  - `views.py:5` — `IsAuthenticated`
  - `views.py:12` — `ProductSubCategory`

---

### BUG-050: Double router instantiation in urls.py
- **Status:** OPEN
- **File:** `search/urls.py:5,18`
- **Description:** `router = DefaultRouter()` created twice. Line 5 is immediately overwritten.
- **Fix:** Remove line 5.

---

### BUG-051: `limit_per_product` parameter accepted but never used
- **Status:** OPEN
- **File:** `ltr_dataset_builder.py:12`
- **Description:** `build_dataset(self, limit_per_product=50)` — parameter in signature, passed from train_ltr.py:15, but body never references it. No candidate count limit is enforced.
- **Fix:** Implement the limit or remove the parameter.

---

### BUG-052: Inner function `time_to_label` redefined on every loop iteration
- **Status:** OPEN
- **File:** `ltr_dataset_builder.py:150`
- **Description:** `def time_to_label(p):` defined inside inner loop body. Recreated on every iteration.
- **Fix:** Move to class level or outside the loop.

---

### BUG-053: `q12` could falsely match `q1` in _parse_time_range
- **Status:** OPEN
- **File:** `views.py:315`
- **Description:** `if "q1" in tr` — substring check. "q12" contains "q1". Parser regex prevents "q12" from being extracted normally, but the check is fragile.
- **Fix:** Use `re.search(r'\bq1\b', tr)` for word boundary.

---

### BUG-054: `import datetime` inside function body
- **Status:** OPEN
- **File:** `views.py:303`
- **Description:** `import datetime` inside `_parse_time_range`. Python caches it, but it's unconventional. Module-level import is cleaner.
- **Fix:** Move to top of file.

---

### BUG-055: `from django.db.models import Case, When, Value, CharField` inside function body
- **Status:** OPEN
- **File:** `aggregation.py:171`
- **Description:** Import inside `get_supplier_details`. Re-imported on every call.
- **Fix:** Move to top of file.

---

### BUG-056: ComparableFinder name comparison is case/whitespace sensitive
- **Status:** OPEN
- **File:** `ranking.py:48`
- **Description:** `s['name'] != current_supplier` — if DB stores "AL AMIN TRADING" but clicked name is "Al Amin Trading" (title-cased), the supplier isn't excluded from its own comparables.
- **Fix:** Normalize both names (`.strip().upper()`) before comparison.

---

### BUG-057: `volume_filter` uses max single shipment as capacity proxy
- **Status:** OPEN
- **File:** `aggregation.py:90-91`
- **Description:** `max_shipment_vol__gte=volume_filter` checks largest SINGLE shipment. A supplier doing 50MT × 20 times (1000MT total) but never a single 100MT shipment is excluded from "100MT" queries despite clear capacity.
- **Fix:** Consider using `total_volume__gte` as an alternative or combined capacity check.

---

### BUG-058: Missing common trading countries
- **Status:** OPEN
- **File:** `query_parser.py:12-17`
- **Description:** COUNTRIES list is missing: Afghanistan, Iran, Iraq, Mexico, South Africa, Nigeria, Netherlands, Belgium, Italy, Spain, Philippines, Myanmar, Oman, Qatar, Bahrain, Kuwait, Jordan, Lebanon, etc.
- **Fix:** Expand the list or load from DB.

---

### BUG-059: `price_fit` always 1.0 when ceiling set (due to BUG-001)
- **Status:** OPEN (dependent on BUG-001)
- **File:** `ranking_ltr.py:105`
- **Description:** `price` is always 0 due to key mismatch. So `0 <= ceiling` is always True → `price_fit = 1.0` for every candidate when ceiling is set. No price discrimination in ranking.
- **Fix:** Resolves automatically when BUG-001 is fixed.

---

### BUG-060: `_clean_query` stopwords may break multi-word product queries
- **Status:** OPEN
- **File:** `nlp.py:87-90`
- **Description:** Stopwords include "for", "to", "i". Applied via whitespace split, not regex. If product name from parser is a clean term like "dextrose", this is fine. But if the NLP search term falls back to raw query (when parser product is empty), aggressive stopword removal can break the search term. E.g., "looking for suppliers" → "" (all words stripped) → triggers BUG-004.
- **Fix:** Guard against empty result after stopword removal (related to BUG-004 fix).

---

## Summary by Component

| Component | Critical | Significant | Moderate | Total |
|---|---|---|---|---|
| `ranking_ltr.py` (FeatureExtractor, Ensemble) | 2 | 2 | 5 | 9 |
| `aggregation.py` (SupplierAggregator) | 1 | 4 | 5 | 10 |
| `query_parser.py` (QueryInterpreter) | 0 | 4 | 9 | 13 |
| `views.py` (SearchViewSet) | 1 | 5 | 5 | 11 |
| `nlp.py` (QueryMatcher) | 1 | 0 | 2 | 3 |
| `ltr_dataset_builder.py` | 0 | 0 | 5 | 5 |
| `ltr_evaluation.py` | 0 | 0 | 1 | 1 |
| `ranking.py` (dead code) | 0 | 0 | 2 | 2 |
| `urls.py` | 0 | 1 | 1 | 2 |
| Cross-file | 0 | 4 | 0 | 4 |
| **Total** | **5** | **20** | **35** | **60** |

## Fix Priority Order

1. **BUG-001 + BUG-002** — Fix key mismatch (unlocks ranking for all queries)
2. **BUG-004** — Guard empty query (prevents catalog dump)
3. **BUG-003** — Fix seller-only detail page (enables SELL flow)
4. **BUG-005** — Pass active_params to ranker (fixes multi-intent)
5. **BUG-010 + BUG-011** — Add Pakistan country filter (data integrity)
6. **BUG-006** — Add price_floor to ranking
7. **BUG-008 + BUG-009** — Fix country list issues
8. **BUG-013 + BUG-014 + BUG-015 + BUG-016** — Fix time parsing
9. **BUG-012** — Add family 6/7/8 weights
10. **BUG-007 + BUG-024** — Fix scope conflict detection
11. Everything else in numerical order
