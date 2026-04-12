# Zarailink Search Engine — Accuracy Analysis

Generated: 2026-03-23

The pipeline has 4 stages. Each is audited individually, followed by cross-cutting issues and a summary table.

---

## Stage 1 — QueryInterpreter (`query_parser.py`)

### 1.1 Intent Detection
The system uses a weighted phrase-score approach (BUY_SCORES / SELL_SCORES dictionaries + regex). When scores are equal it defaults to BUY without asking for clarification. A SetFit classifier can override the regex result, but only at ≥0.70 confidence — if it consistently scores below that threshold or is not trained/ready, the system silently falls back to the regex scoring.

**Accuracy risk:** Conversational queries like "can you show me who buys rice?" that lack exact scoring phrases will score AMBIGUOUS → default to BUY, returning suppliers instead of buyers.

---

### 1.2 Country Extraction — Critical Flaw
The country list is **hardcoded at 29 countries**:
Pakistan, China, India, Brazil, USA, UAE, Vietnam, Thailand, Indonesia, Germany, France, UK, Russia, Turkey, Egypt, Saudi Arabia, Canada, Australia, Malaysia, Kenya, Bangladesh, Sri Lanka, Japan, Korea, South Korea, Afghanistan, Dubai.

Missing: Italy, Spain, Iran, Iraq, Netherlands, Mexico, Argentina, Nigeria, Singapore, Switzerland, Ukraine, Ethiopia, Myanmar, Philippines, and ~150 others. Any query mentioning an unlisted country is silently ignored — the country filter is not applied and the user gets unfiltered worldwide results.

**Alias list is also minimal:** only US / UAE / UK / KSA covered. "Holland", "PRC", "ROC", "Bharat", "Persia" etc. are not handled.

---

### 1.3 Year Hardcoded to 2025
When a quarter is detected without an explicit year (e.g., "Q1 dextrose"), the code sets:

```python
year = q_match.group(2) or "2025"
```

The current year is 2026. Any "Q1" query without a year resolves to **Q1 2025 instead of Q1 2026**, silently fetching stale data.

---

### 1.4 Price Filter Currency Mismatch
The regex accepts `PKR`, `EUR`, `GBP`, `CNY`, `RMB` as valid currency indicators but the database stores prices in USD only. No conversion is performed. A query like "dextrose under PKR 70,000/MT" sets `price_ceiling=70000`, applied directly to `usd_per_mt` — returning zero results since typical dextrose trades at ~$300–$600/MT.

---

### 1.5 Family Priority Creates Wrong Ranking Weights
The family classification priority is: F8 > F7 > F6 > F4 (price) > **F5 (time) > F3 (volume)** > F2 (country) > F1.

A query like "Import 100 MT of dextrose from last year" has both a volume and a time constraint. It is classified as **F5** (time-constrained), applying weights `{inv_recency: 3.0, shipment_freq: 1.5, volume_fit: 1.0}`. Volume is treated as secondary even though it is the primary constraint. The correct family for this query is F3 (`volume_fit: 3.0`).

---

### 1.6 Product Extraction — Overly Aggressive Stopword Removal
After stripping countries, volumes, prices, time, intent keywords, and family keywords, a long stopword list is applied. This is mostly correct but has several failure modes:

- **Hyphens stripped:** `re.sub(r'[^\w\s\.]', '', clean_text)` — "iso-propyl alcohol" becomes "isopropyl alcohol"
- **Descriptors not stripped:** "bulk", "grade", "refined", "technical", "food grade" survive and pollute the product term, reducing BM25/FAISS precision
- **Country names in company names (F1–F6):** "Nestle Pakistan sugar" → `country_filter=['Pakistan']`, `product='nestle sugar'`. The user gets sugar suppliers filtered to Pakistan origin instead of a company search. This issue is handled for F8 but not F1–F6.

---

### 1.7 Multi-Intent Splitting — Product Name False Splits
The splitter splits on `"and"` only if the right side has explicit intent or family keywords. This is a good heuristic but fails for compound product names containing "and":

> "Sodium Hydroxide and Soda Ash prices from China"

This gets split at "and", treating "Soda Ash prices from China" as a separate sub-intent, resulting in two queries instead of one.

---

### 1.8 GLiNER NER (Gap-Filler) — Does Not Expand Country Coverage
Model: `urchade/gliner_medium-v2.1` (~450MB, ~30ms CPU). It runs after regex and only fills empty slots. Countries extracted by GLiNER are validated against the same 29-country hardcoded list, so GLiNER does **not** solve the country coverage gap.

---

## Stage 2 — QueryMatcher / HybridRetriever (`nlp.py` + `retrieval.py`)

### 2.1 BM25 — Vocabulary Limited to 5 Items Per Subcategory
When building the BM25 index, only **up to 5 ProductItem names** per subcategory are included in the document text:

```python
item_names = list(ProductItem.objects.filter(...).values_list('name', flat=True)[:5])
```

If a subcategory has 50 product variants, 45 of them are invisible to BM25. A query for a specific variant not in the top 5 fails BM25 and relies entirely on FAISS and keyword matching.

BM25 also has **no stemming or lemmatization**. "Refined sugar" and "refining sugar" are treated as different tokens.

---

### 2.2 Cross-Encoder Hard Cap of 5 Subcategories
The cross-encoder (`cross_encoder.py`) retrieves 15 candidates from hybrid retrieval and returns **only 5** after re-ranking (`TOP_K_RETURN = 5`). For a broad query like "chemicals from China", the matcher might legitimately match 10+ relevant subcategories, but only 5 are passed downstream. The remaining subcategories — and all the suppliers trading them — are permanently dropped.

---

### 2.3 MS-MARCO Cross-Encoder Domain Mismatch
Both the subcategory cross-encoder and the supplier re-ranker use `cross-encoder/ms-marco-MiniLM-L6-v2`, which was trained on **web page relevance** (MS MARCO is a Bing search benchmark). It scores pairs like:

> `("dextrose anhydrous from China", "Dextrose Monohydrate (HS 1702.11)")`

It has never been fine-tuned on agricultural commodity taxonomy. Its relevance judgments for short product names vs short subcategory names are unreliable — it may prefer longer or more semantically familiar names even when a shorter, exact match is more correct.

---

### 2.4 FAISS Dimension Mismatch on Fallback
The FAISS index is built with nomic-embed-text-v1 (**768 dimensions**). If nomic fails to load, the code falls back to all-MiniLM-L6-v2 (**384 dimensions**) for query encoding. The 384-dim query vector against a 768-dim index causes FAISS to crash. This is caught by `try/except` in `_match_hybrid`, which falls back to `_match_legacy` (old `search_index.pkl`). The user gets results, but from the old index, silently, with no indication of degraded quality.

---

### 2.5 HyDE Expansion Requires OpenAI API
HyDE (Hypothetical Document Embedding) in `_faiss_retrieve` calls an OpenAI API to generate a hypothetical product description and blend its embedding with the query vector. If the API key is absent or rate-limited, HyDE silently fails (`except Exception: pass`) and the original query vector is used. No degradation signal reaches the user.

---

### 2.6 Fuzzy Retrieval Skipped When BM25 Returns Anything
The `_fuzzy_retrieve` (trigram + Levenshtein) only runs when both BM25 and keyword match return nothing. If BM25 returns any result (even a poor one from a coincidental token overlap), fuzzy is skipped. A typo like "sucrouse" may get a poor BM25 result rather than the correct fuzzy match for "sucrose".

---

## Stage 3 — SupplierAggregator (`aggregation.py`)

### 3.1 Database Is Import-Only — BUY+PAKISTAN Always Returns 0
The DB contains Pakistan import records only. For `intent=BUY, scope=PAKISTAN`, the aggregator runs:

```python
queryset = queryset.filter(trade_type='EXPORT', origin_country='Pakistan')
```

Export records (Pakistani companies selling abroad) do not exist in this DB. This query **always returns zero results**. A user searching "sugar suppliers in Pakistan" with scope=PAKISTAN gets nothing.

---

### 3.2 SELL+WORLDWIDE Country Filter Silently Cleared
```python
if intent == 'SELL' and _scope == 'WORLDWIDE' and country_filter:
    country_filter = None
```

A user asking "who in Germany buys dextrose?" (SELL intent, country=Germany) has their Germany filter silently discarded. They receive all worldwide buyers with no indication that the country constraint was ignored.

---

### 3.3 SELL+WORLDWIDE Data Is a Proxy, Not Ground Truth
For SELL intent worldwide, buyers are proxied by Pakistan import records — i.e., who has shipped this product *to* Pakistan. This is not "who worldwide buys this product" — it is "who has shipped this product to Pakistan." A Pakistani exporter asking "who buys wheat worldwide?" receives a list of foreign companies that ship wheat *into* Pakistan, which is the wrong commercial direction entirely.

---

### 3.4 No Company Name Deduplication
Raw Transaction records contain company names as strings. "Al-Khaleej Sugar", "Al Khaleej Sugar", "AL KHALEEJ SUGAR CO.", "Al Khaleej Sugars Ltd" appear as 4 separate suppliers, each with a fraction of the real total volume. The entity resolution GNN outputs an `entity_confidence` score used as a ranking feature, but it does **not** merge the duplicate rows before aggregation. The user sees the same supplier listed multiple times at artificially reduced volumes.

---

### 3.5 Stats Table Fast Path — Volume Inflation Across Subcategories
`_get_from_stats_table` aggregates across all matched subcategory IDs simultaneously. A supplier that trades 3 of the 5 matched subcategories has their volumes, shipment counts, and average prices combined across all 3. This inflates their apparent market position relative to a specialist supplier who only trades one subcategory. The blended average price is also meaningless when it spans multiple product types with different price ranges.

---

### 3.6 Volume Filter Thresholds Are Not Empirically Calibrated
The soft floor excludes a supplier only if `max_single_shipment < 0.3*V AND total_volume < 0.5*V`. A supplier who shipped 5 MT total but had one 35 MT shipment 5 years ago passes the filter for a `V=100 MT` query. The 30%/50% thresholds are arbitrary and were not derived from real trade data analysis.

---

## Stage 4 — Ranking (`ranking_ltr.py` + `reranker.py`)

### 4.1 LTR Trained on Its Own Heuristic — Circular Reference
The LightGBM LambdaRank model is trained using `PseudoLabelGenerator`, which generates relevance labels from the **same heuristic scoring formula** used by `RankingEnsemble`. At inference time:

```python
final_score = heuristic * 0.7 + ltr_score * 0.3
```

The LTR was trained to reproduce heuristic output. Its 30% contribution captures no independent signal. If the LTR model file is missing, the formula degrades to `heuristic * 0.7`, which sorts identically to pure heuristic. **The LTR provides zero practical uplift in either case.**

---

### 4.2 Seven New Features Are Almost Always Zero
The `FeatureExtractor` extracts 15 features. The 7 "Phase 3-G" additions include:

| Feature | Source field | Populated by aggregator? |
|---|---|---|
| `bm25_score` | `candidate.get('bm25_score')` | No |
| `dense_similarity` | `candidate.get('dense_similarity')` | No |
| `trade_diversity_score` | `candidate.get('trade_diversity')` | No |
| `country_diversity_score` | `candidate.get('country_diversity')` | No |
| `volume_trend` | `candidate.get('volume_6mo')` | No |
| `recency_decay_volume` | computed from `days_ago` + `vol` | Yes (partial) |
| `entity_confidence` | `candidate.get('entity_confidence')` | No |

None of these fields are populated by `get_suppliers_for_subcategories()` or `_get_from_stats_table()`. **All 7 new features default to 0.0 for every supplier candidate.** The LTR model is effectively an 8-feature model in production despite being trained as a 15-feature model.

---

### 4.3 Supplier Reranker — MS-MARCO on Company Profiles
After LTR ranking, the supplier reranker scores `(query, company_profile)` pairs where the profile is:

```
"Company: XYZ. Country: China. Trade volume: 5000 MT. Shipments: 42. Average price: $320/MT. Last active: 2024-06-15."
```

MS-MARCO is designed to rank web passages for factual queries. Applied here, it scores based on term overlap between the query and this structured profile. A query for "dextrose" would not match any company name (no supplier is named "Dextrose"), so the CE scores are effectively random with respect to product relevance — they reflect statistical artefacts of MS-MARCO's training distribution. This adds **noise, not signal**, to the final ranking.

Furthermore, `ltr_score` is never populated in the candidate dicts (`c.get('ltr_score') or 0.0` is always 0.0), so the reranker ensemble degrades to `0.7 * heuristic + 0.3 * MS-MARCO noise`.

---

### 4.4 Dead Code: Old SupplierRanker with Hardcoded Recency
`ranking.py:SupplierRanker` is imported in `views.py` but never called in the main search path. It contains:

```python
recency_score = 1.0  # Simple recency score (...) For now, just placeholder
```

This assigns full recency score to every supplier regardless of when they last shipped. It is dead code, but its presence is misleading and it remains imported, creating confusion about which ranker is active.

---

## Cross-Cutting Issues

### C.1 Cache Key Ignores All Filter Parameters
The semantic cache at Stage 0 uses only the raw query string as the cache key. `subcategory_id`, `country`, and `scope` query parameters are read **after** the cache lookup. Any filtered re-query (`?q=dextrose&subcategory_id=5`) returns the unfiltered cached result for `?q=dextrose`. This renders subcategory pill selection and country filtering **non-functional** when Redis is running.

---

### C.2 No User Feedback Loop — Ranking Is Permanently Static
There is no click-through logging, relevance feedback, or online learning. The LTR model is static and trained once on pseudo-labels. Queries that produce bad results today will produce the same bad results indefinitely.

---

### C.3 No Null-Result Explanation or Suggestions
When no matching subcategories are found, the response is:
```json
{"message": "No matching products found."}
```
There is no "did you mean X?", no related product suggestions, and no indication of which filter caused the zero-result outcome.

---

### C.4 F6 Shortlist Defaults to 5 Without Quality Threshold
For family 6 queries ("top 3 dextrose suppliers"), if no number is extracted the result is truncated to 5. There is no quality gate — a market with only 2 active suppliers returns 5 entries including dormant or low-activity ones.

---

## Summary Table

| # | Area | Issue | Severity |
|---|---|---|---|
| 1 | Country extraction | Only 29 hardcoded countries; ~150 missing | High |
| 2 | Time extraction | Q without year → 2025, current year is 2026 | High |
| 3 | Price filter | PKR/EUR applied to USD DB without conversion | High |
| 4 | Family priority | F5 > F3: time beats volume in compound queries | Medium |
| 5 | Subcategory cap | Cross-encoder returns max 5; broader queries truncated | Medium |
| 6 | CE domain mismatch | MS-MARCO model used for agricultural product names | Medium |
| 7 | FAISS dimension | nomic/MiniLM mismatch on fallback → silent quality drop | Medium |
| 8 | Company deduplication | None; same supplier appears multiple times at reduced volume | High |
| 9 | BUY+PAKISTAN | Export records absent in DB; always 0 results | High |
| 10 | SELL+WORLDWIDE country | Filter silently cleared; no user warning | High |
| 11 | SELL+WORLDWIDE data | Pakistan importers proxied as world buyers (wrong direction) | High |
| 12 | Stats table multi-subcat | Volume/price averaged across unrelated subcategories | Medium |
| 13 | LTR training | Pseudo-labels = circular; LTR adds zero independent signal | High |
| 14 | New LTR features (7) | All default to 0.0; 15-feature model is effectively 8-feature | High |
| 15 | Supplier reranker | MS-MARCO on structured profile strings adds noise | Medium |
| 16 | Cache filter bypass | subcategory_id/country ignored when Redis is running | High |
| 17 | Country names in companies | Extracted as geo-filter for F1–F6 queries | Medium |
| 18 | Product stopwords | Descriptors like "bulk", "food grade" pollute product term | Low |
| 19 | Multi-intent "and" split | Splits on "and" inside compound product names | Low |
| 20 | No feedback loop | Ranking cannot improve over time | High |
| 21 | No null-result guidance | Zero results give no suggestions or explanation | Medium |
| 22 | HyDE OpenAI dependency | Silently degrades when API key absent | Low |
| 23 | Fuzzy skipped early | Good fuzzy match missed when BM25 returns any result | Low |
| 24 | Volume threshold arbitrary | 30%/50% soft floor not calibrated to real trade data | Low |

---

## Overall Assessment

**Strongest part:** The retrieval layer (BM25 + FAISS + RRF + keyword boost) is well-designed and will find the correct product subcategory for most well-formed English queries about common commodities.

**Where accuracy breaks down:**
- Queries involving countries not in the 29-country list (country filter silently dropped)
- Time-constrained queries without an explicit year (wrong year applied)
- Price queries in non-USD currencies (zero results)
- SELL intent worldwide (wrong data direction; country filter ignored)
- Pakistan-scoped BUY queries (always zero results)
- Any supplier present under multiple name variants in the DB (volume split across duplicates)
- Broad queries matching more than 5 subcategories (rest permanently dropped)

**Ranking quality:** The heuristic sort-by-volume baseline is the dominant signal throughout. The LTR model and supplier cross-encoder add no independently measurable improvement and in the supplier reranker's case actively introduce noise. The practical ranking accuracy is equivalent to a simple multi-factor sort on (volume, shipment_count, recency).
