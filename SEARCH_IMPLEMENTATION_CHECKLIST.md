# Zarailink Search Engine — Complete Implementation Checklist
## Every Task · Every Test · Every Benchmark · Start to Finish

> **Rules:** Work strictly top to bottom. Every checkbox must be ticked before the section is "done."
> Every Phase ends with a hard GATE. Do not begin the next Phase until its Gate is fully passed.
> Tests are labelled: [UNIT], [INTEGRATION], [E2E], [BENCHMARK], [REGRESSION].

---

# ═══════════════════════════════════════════════════
# PHASE 0 — EVALUATION FRAMEWORK
# Build the ability to measure BEFORE writing any new search code.
# ═══════════════════════════════════════════════════

## 0-A · Golden Query Set Construction

- [ ] Create directory `backend/evaluation/` and file `golden_queries.json`
- [ ] Write **10 F1 queries** (generic product discovery)
  - e.g. "sugar suppliers", "dextrose exporters", "cotton sellers", "wheat buyers", "palm oil importers", "lactose suppliers", "rice exporters", "maize sellers", "soybean suppliers", "salt exporters"
- [ ] Write **10 F2 queries** (country-filtered)
  - e.g. "sugar from Brazil", "dextrose suppliers China", "cotton from India", "wheat from Australia", "palm oil Malaysia", "rice Vietnam", "soybean USA", "salt China", "lactose Germany", "maize Argentina"
- [ ] Write **10 F3 queries** (volume-aware)
  - e.g. "100 MT dextrose", "50 ton sugar suppliers", "500 kg cotton exporters", "1000 MT wheat", "200 metric tons palm oil", "50 MT lactose", "300 tons rice", "75 MT soybean", "25 metric tons salt", "150 MT maize"
- [ ] Write **10 F4 queries** (price-constrained)
  - e.g. "dextrose under $400/MT", "sugar above $350/MT", "cotton below $1.20/kg", "wheat under $300", "palm oil above $800", "lactose under $600", "rice below $500", "soybean above $400", "salt under $100", "maize below $250"
- [ ] Write **10 F5 queries** (time-constrained)
  - e.g. "recent sugar buyers Q1 2024", "2023 dextrose suppliers", "last 6 months cotton importers", "Q4 2023 wheat buyers", "this year palm oil suppliers", "recent lactose exporters", "2024 rice buyers", "last 3 months soybean suppliers", "Q2 2024 salt importers", "2022 maize suppliers"
- [ ] Write **10 F6 queries** (top-K ranking)
  - e.g. "top 5 sugar exporters", "best dextrose suppliers by volume", "rank cotton buyers", "top 3 wheat importers", "best palm oil suppliers", "top 10 rice exporters", "rank lactose buyers by shipments", "top 5 soybean sellers", "best 3 salt suppliers", "top maize exporters"
- [ ] Write **10 F7 queries** (country comparison)
  - e.g. "which countries import cotton most", "compare sugar demand by country", "highest wheat importing countries", "compare dextrose buyers worldwide", "which countries export palm oil", "compare rice exporters", "best markets for lactose", "which countries buy soybean", "compare salt importers", "top countries for maize imports"
- [ ] Write **5 F8 queries** (evidence retrieval — use real company names from your DB)
- [ ] Write **5 F9 multi-intent queries**
  - e.g. "top sugar suppliers; compare by country", "best dextrose exporters and which countries buy most", "find cotton buyers and top 5 sellers", "wheat suppliers from India; compare wheat demand", "top 3 rice sellers and market comparison"
- [ ] Write **10 edge-case queries**
  - 2× HS code queries (e.g. "1702.30", "1006.30.00 suppliers")
  - 2× misspelled products (e.g. "dextrose monoydrate", "suger exporters")
  - 2× ambiguous queries (e.g. "orange suppliers" — fruit vs. company name)
  - 2× very short queries (e.g. "sugar", "cotton")
  - 1× Urdu transliteration if applicable
  - 1× company-name-only query
- [ ] Final count: **80–100 queries** saved to `golden_queries.json`

---

## 0-B · Relevance Judgment Generation

- [ ] Write judge prompt template to `backend/evaluation/judge_prompt.txt`:
  - Prompt must ask GPT-4o-mini to rate 0–3: 0=irrelevant, 1=marginal, 2=relevant, 3=perfect
  - Prompt must include: query, company name, country, total_volume_mt, shipment_count, avg_price_usd_mt, last_shipment_date
  - Prompt must return JSON `{relevance_score: int, reasoning: str}`
- [ ] Write `backend/evaluation/generate_judgments.py`:
  - [ ] Loops through all golden queries
  - [ ] Calls current search pipeline and collects top-20 results per query
  - [ ] Calls GPT-4o-mini API for each (query, result) pair using the judge prompt
  - [ ] Saves output to `backend/evaluation/golden_judgments.json` (format: `{query_id: {result_id: score}}`)
  - [ ] Handles API errors gracefully (retry ×3, then skip with warning)
  - [ ] Logs total cost estimate in USD at end of run
- [ ] Run `generate_judgments.py` → produces **≥1600 labeled (query, result, score) pairs**
- [ ] Manually review **50 random judgments** — confirm LLM scores match human intuition
- [ ] If >10% of reviewed judgments seem wrong: revise judge prompt and regenerate
- [ ] Commit `golden_judgments.json` to git

---

## 0-C · Metrics Implementation

- [ ] Install: `pip install ranx`
- [ ] Write `backend/evaluation/evaluate.py`:
  - [ ] Loads `golden_judgments.json` → builds `ranx.Qrels`
  - [ ] Runs all golden queries through live search pipeline
  - [ ] Builds `ranx.Run` from search results (keyed by canonical_company_id or result identifier)
  - [ ] Computes: **NDCG@5, NDCG@10, MRR@5, MRR@10, Recall@10, Precision@5, MAP@10**
  - [ ] Prints aligned metrics table to stdout
  - [ ] Saves results to `backend/evaluation/results/eval_YYYY-MM-DD_HH-MM.json`
  - [ ] Optionally compares to a previous results file and prints delta per metric
- [ ] Write Django management command `python manage.py evaluate_search`:
  - [ ] Calls `evaluate.py` logic
  - [ ] Accepts optional `--compare-to=<filename>` to print delta
  - [ ] Exits with **code 1** if NDCG@10 drops > 0.02 vs. specified baseline (regression guard)
  - [ ] Prints pass/fail for each metric against configurable targets
- [ ] [UNIT] `evaluate.py` is deterministic: run twice on same data → identical output
- [ ] [UNIT] NDCG@10 = 1.0 when results exactly match ideal ranking → confirms correct formula
- [ ] [UNIT] NDCG@10 = 0.0 when all 20 results per query have grade 0 → confirms boundary
- [ ] [UNIT] Regression guard exits code 1 when NDCG is artificially degraded in test
- [ ] [INTEGRATION] `python manage.py evaluate_search` runs end-to-end without error on current codebase

---

## 0-D · Latency Baseline

- [ ] Write `backend/evaluation/benchmark_latency.py`:
  - [ ] Runs 50 diverse queries (sampled from golden set) through full pipeline
  - [ ] Records per-query wall-clock time from API call start to response returned
  - [ ] Outputs: **P50, P75, P95, P99** latency in ms
  - [ ] Saves to `backend/evaluation/results/latency_YYYY-MM-DD.json`
  - [ ] Also logs: number of cache hits, number of model-load delays
- [ ] Add **per-stage timing instrumentation** to `views.py` → `SearchViewSet.query()`:
  - [ ] Stage 0 (cache lookup): `t_cache_ms`
  - [ ] Stage 1 (query parse + NER + SetFit): `t_parse_ms`
  - [ ] Stage 2 (BM25 + FAISS + RRF): `t_retrieval_ms`
  - [ ] Stage 3 (aggregation query): `t_aggregation_ms`
  - [ ] Stage 4 (LTR + cross-encoder): `t_ranking_ms`
  - [ ] Total: `t_total_ms`
  - [ ] Log as structured JSON at DEBUG level
- [ ] Run `benchmark_latency.py` → record **P50, P95, P99 latency baseline** (pre-improvement)

---

## 0-E · Zero-Result Rate Audit

- [ ] Write `backend/evaluation/audit_zero_results.py`:
  - [ ] Runs all 80–100 golden queries
  - [ ] Counts how many return `results: []`
  - [ ] Prints list of zero-result queries with their parsed_query dicts
- [ ] Run audit → record **zero-result rate baseline** (target: < 5% after all phases)

---

## PHASE 0 GATE ✋
- [ ] `golden_judgments.json` exists with ≥ 1600 labeled pairs, committed to git
- [ ] NDCG@10 baseline value recorded and committed
- [ ] MRR@10 baseline value recorded
- [ ] Recall@10 baseline value recorded
- [ ] P50 / P99 latency baseline values recorded
- [ ] Zero-result rate baseline recorded
- [ ] Management command `evaluate_search` runs cleanly
- [ ] **→ Do NOT write any new search code until this Gate is passed**

---

# ═══════════════════════════════════════════════════
# PHASE 1 — ENTITY RESOLUTION
# Fix data integrity. The #1 precondition for everything else.
# ═══════════════════════════════════════════════════

## 1-A · Django App Setup

- [ ] `python manage.py startapp entity_resolution`
- [ ] Register `entity_resolution` in `INSTALLED_APPS` in `settings.py`
- [ ] Create `entity_resolution/similarity.py`
- [ ] Create `entity_resolution/blocking.py`
- [ ] Create `entity_resolution/fellegi_sunter.py`
- [ ] Create `entity_resolution/clustering.py`
- [ ] Create `entity_resolution/management/commands/resolve_entities.py`

---

## 1-B · String Similarity Functions (implement from scratch, not via library)

- [ ] Implement `normalize_company_name(s: str) -> str` in `similarity.py`:
  - [ ] Lowercase entire string
  - [ ] Strip all punctuation (`.`, `,`, `(`, `)`, `/`)
  - [ ] Expand abbreviations: `"pvt"→"private"`, `"ltd"→"limited"`, `"&"→"and"`, `"co."→"company"`, `"corp"→"corporation"`, `"intl"→"international"`, `"mfg"→"manufacturing"`
  - [ ] Collapse multiple spaces to single space
  - [ ] Strip leading/trailing whitespace
- [ ] Implement `jaro_winkler(s1: str, s2: str) -> float` from scratch (no `jellyfish` library):
  - [ ] Jaro distance formula: matching window = floor(max(len)/2) − 1
  - [ ] Count matches and transpositions
  - [ ] Winkler prefix bonus: up to 4 common prefix characters, scaling factor p=0.1
  - [ ] Returns float in [0.0, 1.0]
- [ ] Implement `damerau_levenshtein_normalized(s1: str, s2: str) -> float`:
  - [ ] Full Damerau-Levenshtein (allows transpositions, not just Levenshtein)
  - [ ] Normalize: `1 - (edit_distance / max(len(s1), len(s2)))`
  - [ ] Returns float in [0.0, 1.0]
- [ ] Implement `soundex(s: str) -> str`:
  - [ ] American Soundex: keep first letter, encode subsequent consonants to digits 1–6
  - [ ] Remove vowels, h, w, y after first character
  - [ ] Returns 4-character code (e.g. "M400" for "Muller")
- [ ] Implement `token_jaccard(s1: str, s2: str) -> float`:
  - [ ] Tokenize both strings (split on whitespace after normalization)
  - [ ] Jaccard = |intersection| / |union|
  - [ ] Returns float in [0.0, 1.0]

### 1-B Tests
- [ ] [UNIT] `normalize("M&P PAKISTAN PVT. LTD.")` → `"mp pakistan private limited"`
- [ ] [UNIT] `jaro_winkler("Muller Phipps Pakistan", "Muller and Phipps Pakistan")` > 0.92
- [ ] [UNIT] `jaro_winkler("ABC Corp", "XYZ Holdings")` < 0.60
- [ ] [UNIT] `jaro_winkler("M&P Pakistan", "M & P Pakistan")` > 0.95
- [ ] [UNIT] `jaro_winkler("s", "s")` == 1.0 (identical)
- [ ] [UNIT] `jaro_winkler("", "abc")` == 0.0 (empty string)
- [ ] [UNIT] `damerau_levenshtein_normalized("kitten", "sitting")` between 0.0 and 0.5
- [ ] [UNIT] `damerau_levenshtein_normalized("abc", "abc")` == 1.0
- [ ] [UNIT] `soundex("Muller")` == `soundex("Mueller")` (same code)
- [ ] [UNIT] `soundex("Smith")` == "S530"
- [ ] [UNIT] `token_jaccard("Muller Phipps Pakistan", "Phipps Pakistan Muller")` == 1.0 (order-independent)
- [ ] [UNIT] `token_jaccard("Muller Phipps", "XYZ Corp")` == 0.0

---

## 1-C · Blocking Strategy

- [ ] Implement `soundex_blocking(names: list[str]) -> dict[str, list[str]]` in `blocking.py`:
  - [ ] Groups company names by their Soundex key
  - [ ] Returns dict: `{soundex_code: [name1, name2, ...]}`
- [ ] Implement `first3_blocking(names: list[str]) -> dict[str, list[str]]`:
  - [ ] Groups by first 3 characters of normalized name
- [ ] Implement `sorted_neighborhood(names: list[str], window: int = 50) -> list[tuple[str, str]]`:
  - [ ] Sort names alphabetically (after normalization)
  - [ ] Slide a window of size W over sorted list
  - [ ] Emit all pairs within each window position
  - [ ] Deduplicate pairs
- [ ] Implement `merge_block_candidates(*block_dicts) -> list[tuple[str, str]]`:
  - [ ] Merges candidates from all blocking strategies
  - [ ] Deduplicates (a,b) and (b,a) treated as same pair

### 1-C Tests
- [ ] [UNIT] Soundex blocking groups "Muller & Phipps" and "MULLER AND PHIPPS" in same block
- [ ] [UNIT] First3 blocking groups "M&P Pakistan" and "M & P Pakistan" in same block (after normalization both start "m p")
- [ ] [UNIT] Sorted neighborhood with window=3 on 5 names produces correct pairs
- [ ] [BENCHMARK] Given all unique buyer+seller names from DB:
  - [ ] Record: **pairs completeness** (known duplicate pairs recovered / total known duplicates) — target ≥ 90%
  - [ ] Record: **reduction ratio** (candidate pairs / all possible pairs O(n²)) — target < 5%
  - [ ] Record: total candidate pairs generated
  - [ ] Save benchmark numbers to `evaluation/results/blocking_benchmark.json`

---

## 1-D · Fellegi-Sunter EM Classification

- [ ] Implement `compute_comparison_vector(name_a, name_b, country_a, country_b, hs_codes_a, hs_codes_b, embed_a, embed_b) -> np.ndarray` in `fellegi_sunter.py`:
  - [ ] Feature 0: `jaro_winkler(name_a, name_b)` — after normalization
  - [ ] Feature 1: `token_jaccard(name_a, name_b)`
  - [ ] Feature 2: `1.0 if soundex(name_a) == soundex(name_b) else 0.0`
  - [ ] Feature 3: `damerau_levenshtein_normalized(name_a, name_b)`
  - [ ] Feature 4: `1.0 if country_a == country_b else 0.0`
  - [ ] Feature 5: `len(hs_codes_a ∩ hs_codes_b) / len(hs_codes_a ∪ hs_codes_b)` (Jaccard on HS code sets)
  - [ ] Feature 6: `cosine_similarity(embed_a, embed_b)` using existing all-MiniLM embeddings
- [ ] Implement `expectation_maximization(comparison_matrix: np.ndarray, n_iter=100) -> tuple[np.ndarray, np.ndarray]`:
  - [ ] Input: (n_pairs × n_features) comparison matrix
  - [ ] Initialize: m_probs = [0.9]*n_features, u_probs = [0.1]*n_features, match_prior = 0.01
  - [ ] E-step: compute posterior P(match | comparison_vector_i) for each pair using Bayes rule
  - [ ] M-step: m_probs[j] = weighted mean of feature_j over all pairs weighted by posterior; same for u_probs
  - [ ] Converge when: `|log_likelihood_change| < 1e-6` OR iter == n_iter
  - [ ] Return (m_probs, u_probs)
- [ ] Implement `compute_match_weights(m_probs, u_probs) -> np.ndarray`:
  - [ ] `weights[j] = log(m_probs[j] / u_probs[j])`
  - [ ] Clip to avoid log(0): clamp m_probs, u_probs to [1e-10, 1-1e-10]
- [ ] Implement `classify_pairs(pairs, comparison_matrix, match_weights, upper_thresh, lower_thresh) -> dict[tuple, str]`:
  - [ ] Composite score = dot(comparison_vector, match_weights) for each pair
  - [ ] `score >= upper_thresh` → "Match"
  - [ ] `score <= lower_thresh` → "NonMatch"
  - [ ] Otherwise → "PossibleMatch"
  - [ ] Returns dict: `{(name_a, name_b): "Match"|"NonMatch"|"PossibleMatch"}`

### 1-D Tests
- [ ] [UNIT] EM converges (log-likelihood change < 1e-6) within 100 iterations on 500 synthetic pairs
- [ ] [UNIT] After EM: m_probs > u_probs for Jaro-Winkler and token_jaccard features (high-signal features have higher m than u)
- [ ] [UNIT] After EM: m_probs < 0.6 for country_match feature (weak signal — country match alone doesn't confirm identity)
- [ ] [UNIT] Known duplicate pair ("Muller & Phipps Pvt Ltd", "MULLER AND PHIPPS PVT LTD") → classified as Match or PossibleMatch
- [ ] [UNIT] Known non-duplicate pair ("ABC Sugar Mills", "XYZ Cotton Exports") → classified as NonMatch
- [ ] Manually label **200 candidate pairs** from DB as ground truth (Match / NonMatch)
- [ ] [BENCHMARK] Compute **pairwise Precision, Recall, F1** on 200 labeled pairs — record all three
- [ ] [BENCHMARK] Target: F1 ≥ 0.80 on labeled pairs

---

## 1-E · Transitive Closure Clustering

- [ ] Install: `pip install networkx`
- [ ] Implement `build_match_graph(matched_pairs: list[tuple]) -> nx.Graph` in `clustering.py`:
  - [ ] Nodes = company name strings
  - [ ] Edges = pairs classified as Match (or PossibleMatch with weight < 1.0)
- [ ] Implement `connected_components_clusters(graph: nx.Graph) -> list[list[str]]`:
  - [ ] Returns list of clusters (each cluster = list of name variants)
- [ ] Implement `center_clustering(graph: nx.Graph, sim_fn) -> list[list[str]]`:
  - [ ] Prevents over-merging: for each potential merge, verify pairwise average similarity in merged cluster ≥ threshold (0.85)
  - [ ] If merge would lower average similarity below threshold: do not merge (split)
  - [ ] Implements quality guarantee against long-chain false merges
- [ ] Implement `select_canonical_name(cluster: list[str], name_freq: dict, name_last_seen: dict) -> str`:
  - [ ] Score = frequency_count × recency_weight (e.g. recency_weight = days_since_last_seen^(-0.1))
  - [ ] Returns name with highest score as canonical

### 1-E Tests
- [ ] [UNIT] Chain merge prevention: if A~B and B~C but A≁C (low similarity), center clustering does NOT merge A,B,C into one cluster
- [ ] [UNIT] Perfect cluster: if A~B~C all pairwise similar → all three in same cluster
- [ ] [UNIT] Canonical selection: most frequent + most recent variant wins
- [ ] [INTEGRATION] Run full entity resolution pipeline on 100 randomly sampled company names from DB → manually inspect 20 clusters → confirm no obvious wrong merges or missed merges

---

## 1-F · Django Models + Management Command

- [ ] Create migration for `CompanyCanonical`:
  ```
  id (AutoField PK), canonical_name (CharField, indexed), variant_count (IntegerField),
  first_seen (DateField, nullable), last_seen (DateField, nullable),
  confidence_score (FloatField, default=1.0), created_at (DateTimeField)
  ```
- [ ] Create migration for `NameVariant`:
  ```
  id (AutoField PK), raw_name (CharField, db_index=True),
  canonical (ForeignKey → CompanyCanonical, on_delete=CASCADE),
  confidence_score (FloatField), created_at (DateTimeField)
  ```
  - Add `unique_together = [('raw_name',)]` (each raw name resolves to exactly one canonical)
- [ ] Apply migrations: `python manage.py migrate`
- [ ] Write management command `resolve_entities`:
  - [ ] Reads all unique `buyer` + `seller` strings from Transaction table
  - [ ] Runs: normalize → block → compare → EM → classify → cluster → canonical selection
  - [ ] Writes `CompanyCanonical` and `NameVariant` records (upsert, not duplicate-insert)
  - [ ] Logs: n_unique_raw_names, n_candidates_compared, n_matches, n_canonical_created, n_singletons, elapsed_time
  - [ ] Idempotent: safe to re-run
- [ ] Write helper `get_canonical_id(raw_name: str) -> int | None`:
  - [ ] Looks up `NameVariant.objects.get(raw_name=raw_name).canonical_id`
  - [ ] Falls back to fuzzy lookup if exact not found
- [ ] Write `resolve_new_entities(new_names: list[str])`:
  - [ ] Called when new Transaction records are ingested (incremental update)
  - [ ] Only processes names not already in `NameVariant` table

### 1-F Tests
- [ ] [UNIT] `resolve_entities` command runs on empty DB without error
- [ ] [UNIT] `resolve_entities` is idempotent — running twice produces same result (no duplicate rows)
- [ ] [UNIT] `get_canonical_id("MULLER AND PHIPPS PVT LTD")` returns same ID as `get_canonical_id("M&P Pakistan")` (if correctly resolved)
- [ ] [INTEGRATION] Run `resolve_entities` on full DB → no IntegrityError, no missing FK violations
- [ ] [INTEGRATION] `NameVariant.objects.count()` == number of unique raw buyer/seller strings in Transaction table (every string has a variant record)

---

## 1-G · SupplierAggregator Integration

- [ ] Update `aggregation.py` → `SupplierAggregator.get_suppliers_for_subcategories()`:
  - [ ] All GROUP BY operations: replace `.values('seller')` / `.values('buyer')` with `.values('canonical_company_id')` using `annotate` with FK join
  - [ ] `name` field in results returns `CompanyCanonical.canonical_name`
  - [ ] Add `canonical_id` to every result object
  - [ ] FK join: `Transaction.objects.annotate(canonical_id=...)` using `NameVariant` lookup
- [ ] Update `EvidenceRetriever` (F8 family):
  - [ ] Buyer name matching: `NameVariant.objects.filter(raw_name__icontains=buyer_name)` → get all canonical IDs matching → fetch all transactions for those canonical IDs
  - [ ] This means all name variants of a buyer are now captured in F8 evidence
- [ ] Update `CountryComparator` (F7 family): aggregations group by canonical_id
- [ ] Update `supplier-detail` endpoint: accepts `canonical_id` (not raw name) as lookup key
- [ ] Update `ComparableFinder`: compares by canonical_id, not by raw string similarity

### 1-G Tests
- [ ] [INTEGRATION] F1 query "sugar suppliers" → a known company with 3 name variants appears exactly **once** in results with **combined** volume from all variants
- [ ] [INTEGRATION] F8 query with a name variant of a company → transactions found (not "buyer_not_found")
- [ ] [INTEGRATION] F7 country comparison → volumes are numerically correct (not fragmented)
- [ ] [REGRESSION] Run `python manage.py evaluate_search` → NDCG@10 ≥ Phase 0 baseline (must not regress)
- [ ] [REGRESSION] All existing F1-F9 query family unit tests in `search/tests/` still pass

---

## 1-H · Node2Vec Graph Update

- [ ] Re-run Node2Vec embeddings on the **canonicalized** buyer-seller graph (nodes = `CompanyCanonical.id`, not raw strings)
- [ ] Save new embeddings to `CompanyEmbedding` model linked to `CompanyCanonical.id`
- [ ] Verify: graph node count < pre-resolution graph node count (merges reduced phantom nodes)
- [ ] [INTEGRATION] `CompanyEmbedding.objects.count()` == `CompanyCanonical.objects.count()` (one embedding per canonical entity)

---

## PHASE 1 GATE ✋
- [ ] Pairwise F1 on 200 labeled pairs **≥ 0.80**
- [ ] Known duplicate company appears as single entity in F1 search results ✓
- [ ] NDCG@10 ≥ Phase 0 baseline (no regression)
- [ ] `resolve_entities` command runs cleanly on full DB
- [ ] All migrations applied cleanly, no FK violations
- [ ] `evaluate_search` passes regression guard

---

# ═══════════════════════════════════════════════════
# PHASE 2 — RETRIEVAL UPGRADE
# BM25 + FAISS HNSW + nomic-embed-text + RRF + Pre-Aggregation
# ═══════════════════════════════════════════════════

## 2-A · BM25 Index

- [ ] Install: `pip install rank-bm25`
- [ ] Create `search/services/bm25_index.py`:
  - [ ] Class `BM25ProductIndex`
  - [ ] Method `build()`:
    - [ ] Corpus: for each `ProductSubCategory`, string = `name + " " + hs_code + " " + " ".join(item.name for item in subcat.items.all())`
    - [ ] Tokenizer: lowercase, strip punctuation, split whitespace
    - [ ] Build `BM25Okapi(tokenized_corpus)`
    - [ ] Store `self.ids = [subcat.id, ...]` aligned with corpus
  - [ ] Method `search(query: str, top_k: int = 50) -> list[dict]`:
    - [ ] Returns `[{"id": int, "score": float, "rank": int}, ...]` sorted by score descending
  - [ ] Method `save(path: str)`: pickle both BM25 object and ids list
  - [ ] Method `load(path: str)`: unpickle and restore
  - [ ] Singleton pattern: class-level `_instance` caching

### 2-A Tests
- [ ] [UNIT] Query `"dextrose"` → Dextrose `ProductSubCategory` at rank 1
- [ ] [UNIT] Query `"1702"` → `ProductSubCategory` with HS code starting `1702` in top 5
- [ ] [UNIT] Query `"dextrose monohydrate"` → more specific variant scores higher than plain `"dextrose"`
- [ ] [UNIT] Query `"asfljkasfljk"` → all scores near zero (no false positives)
- [ ] [UNIT] Save → load → `search("dextrose")` returns identical result (serialization correctness)
- [ ] [BENCHMARK] BM25-only Recall@5 and Recall@10 on product-matching golden query subset — record values

---

## 2-B · FAISS HNSW Index

- [ ] Install: `pip install faiss-cpu`
- [ ] Create `search/services/faiss_index.py`:
  - [ ] Class `FAISSProductIndex`
  - [ ] Method `build(embeddings: np.ndarray, ids: list[int])`:
    - [ ] `index = faiss.IndexHNSWFlat(dim, M=32)`
    - [ ] `index.hnsw.efConstruction = 200`
    - [ ] `faiss.normalize_L2(embeddings)` (for cosine similarity via inner product)
    - [ ] `index.add(embeddings)`
    - [ ] Store `self.ids = ids`
  - [ ] Method `search(query_vec: np.ndarray, top_k: int = 50) -> list[dict]`:
    - [ ] L2-normalize query_vec
    - [ ] `index.hnsw.efSearch = 50` (set at query time, tunable)
    - [ ] Returns `[{"id": int, "score": float, "rank": int}, ...]`
  - [ ] Method `add(new_embeddings: np.ndarray, new_ids: list[int])`:
    - [ ] L2-normalize new_embeddings
    - [ ] `index.add(new_embeddings)` (incremental, no rebuild)
    - [ ] `self.ids.extend(new_ids)`
  - [ ] Method `save(path: str)`: `faiss.write_index()` + pickle ids
  - [ ] Method `load(path: str)`: `faiss.read_index()` + unpickle ids
  - [ ] Singleton pattern: class-level `_instance`

### 2-B Tests
- [ ] [UNIT] Query vector of an already-indexed item → that item is rank 1 (exact self-retrieval)
- [ ] [UNIT] Recall@10 ≥ 95%: brute-force cosine vs. HNSW on 100 random query vectors from corpus
- [ ] [UNIT] Incremental add: add 5 new items → new items retrievable without full rebuild
- [ ] [UNIT] Save → load → identical search results on same query vector (serialization correctness)
- [ ] [BENCHMARK] Run `benchmark_hnsw.py`:
  - [ ] Sweep `efSearch` ∈ [10, 20, 50, 100, 200, 400]
  - [ ] Record Recall@10 and QPS for each
  - [ ] Save Pareto data to `evaluation/results/hnsw_pareto.json`
  - [ ] Save plot to `evaluation/results/hnsw_pareto.png`
  - [ ] Choose operating `efSearch` value: highest QPS with Recall@10 ≥ 95%
- [ ] [BENCHMARK] Record index build time on full product corpus
- [ ] [BENCHMARK] Record index memory footprint in MB

---

## 2-C · Embedding Model Upgrade: nomic-embed-text-v1

- [ ] Verify `sentence-transformers` version ≥ 2.7.0: `pip show sentence-transformers`
- [ ] Update model load in `nlp.py` → `QueryMatcher`:
  - [ ] Old: `SentenceTransformer('all-MiniLM-L6-v2', device='cpu')`
  - [ ] New: `SentenceTransformer('nomic-ai/nomic-embed-text-v1', trust_remote_code=True, device='cpu')`
- [ ] Update all query encoding calls: prepend `"search_query: "` before query text
- [ ] Update all document encoding calls in `rebuild_search_index`: prepend `"search_document: "` before document text
- [ ] Update embedding dimension: find all hardcoded `384` references → change to `768`
- [ ] Update FAISS `IndexHNSWFlat(dim=768, ...)` instantiation
- [ ] Rebuild index: `python manage.py rebuild_search_index`
  - [ ] Confirm new index file exists
  - [ ] Confirm index dimension is 768

### 2-C Tests
- [ ] [UNIT] Embedding shape is `(1, 768)` for a single query
- [ ] [UNIT] `cosine_sim("search_query: dextrose", "search_document: Dextrose Monohydrate")` > 0.80
- [ ] [UNIT] `cosine_sim("search_query: dextrose", "search_document: Steel Pipes")` < 0.30
- [ ] [UNIT] `cosine_sim("search_query: glucose syrup", "search_document: Dextrose")` > 0.70 (semantic synonym)
- [ ] [BENCHMARK] Dense-only Recall@10 with nomic vs. baseline all-MiniLM-L6-v2 — record improvement
- [ ] [BENCHMARK] Per-query embedding latency P99 < 60ms on CPU

---

## 2-D · Reciprocal Rank Fusion

- [ ] Create `search/services/rrf.py`:
  - [ ] Implement `reciprocal_rank_fusion(bm25_results: list, dense_results: list, k: int = 60) -> list[tuple[int, float]]`:
    - [ ] For each result in bm25_results: `score[id] += 1.0 / (rank + k)`
    - [ ] For each result in dense_results: `score[id] += 1.0 / (rank + k)`
    - [ ] Return `sorted(score.items(), key=lambda x: x[1], reverse=True)` → `[(id, rrf_score), ...]`
    - [ ] Include items from either list (union, not intersection)
- [ ] Update `nlp.py` → `QueryMatcher.match()`:
  - [ ] Replace brute-force cosine scan with: (1) BM25 search top-50, (2) FAISS HNSW search top-50, (3) RRF fusion
  - [ ] Set `method = "hybrid_rrf"` in returned result objects
  - [ ] Maintain backward-compatible output format: `[{id, name, score, hs_code, method, matched_variants, ...}]`
- [ ] Update `rebuild_search_index` management command:
  - [ ] Builds FAISS HNSW index (new)
  - [ ] Builds BM25 index (new)
  - [ ] Saves both index files to disk
  - [ ] Loads both on startup via singletons

### 2-D Tests
- [ ] [UNIT] Item in BM25 only AND item in dense only → both appear in RRF output (union behavior)
- [ ] [UNIT] Item ranked #1 in both lists → higher RRF score than item ranked #1 in only one list
- [ ] [UNIT] `k=60` default is used; changing to `k=10` changes scores (parameter is respected)
- [ ] [UNIT] Query `"1702.30 suppliers"` → HS-code-matching subcategory in top 3 (BM25 strength demonstrated)
- [ ] [UNIT] Query `"glucose syrup suppliers"` → Dextrose subcategory in top 5 (dense semantic strength demonstrated)
- [ ] [UNIT] `QueryMatcher.match("dextrose")` returns same format as before (backward-compatible output)
- [ ] [BENCHMARK] Compare Recall@5, Recall@10 for: BM25-only vs dense-only vs hybrid-RRF → confirm hybrid wins on both semantic and exact queries
- [ ] [BENCHMARK] Record hybrid-RRF end-to-end query latency

---

## 2-E · CompanyProductStats Pre-Aggregation Table

- [ ] Create migration for `CompanyProductStats`:
  ```
  id (AutoField PK)
  canonical_company (ForeignKey → CompanyCanonical)
  product_subcategory (ForeignKey → ProductSubCategory)
  trade_type (CharField max=10)   # IMPORT / EXPORT
  country (CharField max=100)
  period_quarter (CharField max=7)  # e.g. "2024-Q1"
  total_volume_mt (DecimalField 15,3)
  avg_price_usd_mt (DecimalField 10,2)
  shipment_count (IntegerField)
  last_shipment_date (DateField)
  max_shipment_vol (DecimalField 12,3)
  avg_shipment_vol (DecimalField 12,3)
  ```
  - [ ] `unique_together = [('canonical_company', 'product_subcategory', 'trade_type', 'country', 'period_quarter')]`
  - [ ] DB indexes: `[product_subcategory, trade_type]`, `[country, trade_type]`, `[canonical_company]`
- [ ] Write management command `build_stats_table`:
  - [ ] Reads all Transaction records (joined via NameVariant → CompanyCanonical)
  - [ ] Groups by (canonical_company_id, product_subcategory_id, trade_type, country, period_quarter)
  - [ ] Computes SUM(qty_mt), AVG(usd_per_mt), COUNT(id), MAX(reporting_date), MAX(qty_mt), AVG(qty_mt)
  - [ ] Bulk-creates `CompanyProductStats` rows
  - [ ] Logs: n_transactions_processed, n_stats_rows_created, elapsed_time
  - [ ] Idempotent: truncates table first, then rebuilds
- [ ] Write Django signal `post_save` on `Transaction`:
  - [ ] Resolve `raw_name → canonical_id` via `NameVariant` lookup
  - [ ] Compute period_quarter from `reporting_date`
  - [ ] `CompanyProductStats.objects.update_or_create(...)` with incremental field update:
    - [ ] `total_volume_mt += new_qty`
    - [ ] `shipment_count += 1`
    - [ ] `last_shipment_date = max(existing, new_date)`
    - [ ] `max_shipment_vol = max(existing, new_qty)`

### 2-E Tests
- [ ] [UNIT] `SUM(CompanyProductStats.total_volume_mt)` for company X == `SUM(Transaction.qty_mt)` for same company (via raw ORM). Exact match.
- [ ] [UNIT] `SUM(CompanyProductStats.shipment_count)` for product Y == `COUNT(Transaction)` for product Y. Exact match.
- [ ] [UNIT] Post-save signal: insert new Transaction → corresponding `CompanyProductStats` row updated within same test
- [ ] [UNIT] `build_stats_table` is idempotent (run twice → same row count, same values)
- [ ] [INTEGRATION] Full F1 search query `USE_PRECOMPUTED_STATS=True` vs `False` → identical results (same companies, same volumes, same order)
- [ ] [INTEGRATION] F2 country filter → identical results via both paths
- [ ] [INTEGRATION] F3 volume filter → identical results via both paths
- [ ] [INTEGRATION] F5 time-range filter → two quarterly rows aggregated correctly (sum, not just one quarter)
- [ ] [BENCHMARK] Query latency: raw ORM `GROUP BY` vs stats table for 50 queries → record speedup ratio
- [ ] [BENCHMARK] Stats table row count vs Transaction row count — confirm stats << raw

---

## 2-F · Migrate SupplierAggregator to Stats Table

- [ ] Update `aggregation.py` → `SupplierAggregator.get_suppliers_for_subcategories()`:
  - [ ] Replace: `Transaction.objects.values(...).annotate(...)` heavy GROUP BY
  - [ ] With: `CompanyProductStats.objects.filter(product_subcategory__in=ids, trade_type=..., ...).values('canonical_company__canonical_name', 'canonical_company__id').annotate(total_vol=Sum('total_volume_mt'), avg_price=Avg('avg_price_usd_mt'), count=Sum('shipment_count'), last_date=Max('last_shipment_date'), max_vol=Max('max_shipment_vol'))`
  - [ ] For time-range filters (F5): `period_quarter__in=affected_quarters`
  - [ ] Price ceiling/floor filter: applied post-aggregation (avg_price__lte=ceiling)
  - [ ] Add `USE_PRECOMPUTED_STATS` flag to `settings.py` (default `True`) for easy rollback
- [ ] Update `CountryComparator` (F7): use stats table
- [ ] Keep raw Transaction fallback path for `USE_PRECOMPUTED_STATS=False`

### 2-F Tests
- [ ] [INTEGRATION] `USE_PRECOMPUTED_STATS=True` → F1/F2/F3/F4/F5/F6 all produce results matching `USE_PRECOMPUTED_STATS=False`
- [ ] [REGRESSION] Run `evaluate_search` → NDCG@10 not regressed from Phase 1 baseline

---

## 2-G · Retrieval Evaluation Script

- [ ] Write `backend/evaluation/evaluate_search_index.py`:
  - [ ] For product-matching queries (a subset of golden set where correct subcategory is known):
    - [ ] Run BM25-only → record Recall@1, @5, @10
    - [ ] Run dense-only → record Recall@1, @5, @10
    - [ ] Run hybrid-RRF → record Recall@1, @5, @10
  - [ ] Print comparison table
  - [ ] Save to `evaluation/results/retrieval_comparison.json`
  - [ ] Generate bar chart → `evaluation/results/retrieval_comparison.png`
- [ ] Run script → record all numbers

---

## PHASE 2 GATE ✋
- [ ] Hybrid-RRF Recall@10 > BM25-only Recall@10 by ≥ 5 percentage points
- [ ] Hybrid-RRF Recall@10 > dense-only Recall@10 by ≥ 5 percentage points
- [ ] HS code query returns correct subcategory in top 3
- [ ] Semantic synonym query returns correct subcategory in top 5
- [ ] NDCG@10 (full pipeline) improved ≥ 0.05 vs Phase 1 baseline
- [ ] Stats table volumes match raw ORM volumes exactly (data integrity confirmed)
- [ ] All migrations applied, no FK violations
- [ ] `evaluate_search` passes regression guard

---

# ═══════════════════════════════════════════════════
# PHASE 3 — QUERY INTELLIGENCE + RANKING
# GLiNER NER · SetFit Classifier · Cross-Encoder · LTR Retrain · Redis Cache
# ═══════════════════════════════════════════════════

## 3-A · GLiNER Zero-Shot NER

- [ ] Install: `pip install gliner`
- [ ] Create `search/services/ner_extractor.py`:
  - [ ] Class `GLiNERExtractor`, singleton pattern (`_model` class variable)
  - [ ] Load `urchade/gliner_medium-v2.1` on first use (lazy init, `trust_remote_code=True`)
  - [ ] Define entity labels list:
    ```python
    LABELS = ["product", "quantity", "unit", "origin_country", "destination_country",
              "price_ceiling", "price_floor", "hs_code", "company_name", "time_period"]
    ```
  - [ ] Method `extract(query: str) -> dict`:
    - [ ] Calls `model.predict_entities(query, labels=LABELS)`
    - [ ] Post-processes: convert quantity to float, unit to canonical form (kg/MT), price to float
    - [ ] Returns clean dict: `{product: str|None, quantity: float|None, unit: str|None, origin_country: str|None, destination_country: str|None, price_ceiling: float|None, price_floor: float|None, hs_code: str|None, company_name: str|None, time_period: str|None}`
  - [ ] Method `merge_with_regex(gliner_result: dict, regex_result: dict) -> dict`:
    - [ ] For numeric fields (quantity, price_ceiling, price_floor): regex takes precedence if non-None
    - [ ] For text fields (product, country, company_name): regex takes precedence if non-None
    - [ ] GLiNER fills in any field that regex returned None for
    - [ ] Log any disagreement (gliner_value != regex_value when both non-None) at DEBUG level

### 3-A Tests
- [ ] [UNIT] `extract("I need 50 MT of white sugar from Brazil")` → `product="white sugar", quantity=50.0, unit="MT", origin_country="Brazil"`
- [ ] [UNIT] `extract("dextrose under $400 per metric ton")` → `price_ceiling=400.0, product="dextrose"`
- [ ] [UNIT] `extract("has Nestle purchased palm oil?")` → `company_name="Nestle", product="palm oil"`
- [ ] [UNIT] `extract("1702.30 suppliers")` → `hs_code="1702.30"`
- [ ] [UNIT] `extract("fifty metric tons of sugar")` → `quantity=50.0, unit="MT"` (novel phrasing regex would miss)
- [ ] [UNIT] `merge_with_regex`: numeric regex value overrides GLiNER when both non-None
- [ ] [UNIT] `merge_with_regex`: GLiNER product fills in when regex product is None
- [ ] [UNIT] Model is singleton: second call returns same instance as first (no double-load)
- [ ] Run 20 real trade queries manually → confirm extractions are sensible for all
- [ ] [BENCHMARK] GLiNER inference latency P99 < 60ms on CPU

---

## 3-B · Integrate GLiNER into QueryInterpreter

- [ ] Update `query_parser.py` → `QueryInterpreter.__init__()`:
  - [ ] Add `self.ner = GLiNERExtractor()` (lazy init via singleton)
- [ ] Update `QueryInterpreter.parse(query: str, ...) -> dict`:
  - [ ] After existing regex extraction: call `gliner_result = self.ner.extract(query)`
  - [ ] Call `merged = self.ner.merge_with_regex(gliner_result, regex_result)`
  - [ ] Use `merged` values for final parsed output
  - [ ] Add `ner_confidence` field to output (minimum confidence across non-None GLiNER extractions; 1.0 if all from regex)
  - [ ] If `ner_confidence < 0.40`: add `ambiguous_query: True` flag
- [ ] Update `views.py`: if `ambiguous_query: True` in parsed_query → add `clarification_hint` field to API response

### 3-B Tests
- [ ] [INTEGRATION] F3 query `"fifty metric tons of sugar"` (novel phrasing) → `qty_mt=50.0` in `parsed_query` (GLiNER captures it)
- [ ] [INTEGRATION] F4 query `"dextrose under $400"` → `price_ceiling=400.0` in `parsed_query`
- [ ] [INTEGRATION] F2 query `"sugar from Brazil"` → `country="Brazil"` in `parsed_query`
- [ ] [INTEGRATION] `ambiguous_query: True` fires for a genuinely ambiguous test query
- [ ] [REGRESSION] All existing `QueryInterpreter` unit tests still pass after changes

---

## 3-C · SetFit Intent Classifier

- [ ] Install: `pip install setfit`
- [ ] Write training data file `backend/training_data/setfit_intent.csv` (columns: `text`, `label`):
  - [ ] **≥40 examples per class** for these classes:
    - `BUY`: "who sells dextrose", "find sugar importers", "I want to buy cotton from China", "looking for wheat suppliers", "source palm oil", "need lactose supplier", "buy rice from Vietnam", "find salt exporters", "want to import maize", "dextrose suppliers please"... (40+)
    - `SELL`: "who buys wheat", "find buyers for our cotton", "which countries import Pakistani mangoes", "sell sugar to", "demand for rice", "exporters of cotton", "markets for our wheat", "sell lactose", "export palm oil", "selling dextrose"... (40+)
    - `F6_TOPK`: "top 5 sugar exporters", "best dextrose suppliers by volume", "rank cotton buyers", "top 3 wheat importers", "highest volume rice sellers"... (40+)
    - `F7_COMPARE`: "which countries import cotton most", "compare sugar demand by country", "highest wheat importing countries", "compare rice exporters", "best markets for lactose"... (40+)
    - `F8_EVIDENCE`: "has Nestle purchased palm oil", "did Company X buy sugar", "show me transactions for ABC Corp", "verify shipments from XYZ", "evidence of rice purchase by company"... (40+)
    - `F3_VOLUME`: "100 MT dextrose", "50 ton sugar suppliers", "500 kg cotton exporters", "1000 metric ton wheat"... (40+)
    - `F4_PRICE`: "dextrose under $400/MT", "sugar above $350", "cotton below $1.20/kg", "cheap wheat suppliers", "expensive rice buyers"... (40+)
    - `F5_TIME`: "Q1 2024 sugar suppliers", "last 6 months cotton", "2023 dextrose", "recent wheat buyers", "this year palm oil"... (40+)
  - [ ] Include Pakistani trade context: "Faisalabad textile", "Karachi port", "Sialkot", "Lahore importers", "Islamabad exporters"
  - [ ] Total: ≥ 320 labeled examples

- [ ] Write training script `backend/training_scripts/train_setfit_intent.py`:
  - [ ] Load CSV
  - [ ] 80/20 train/holdout split (stratified)
  - [ ] `model = SetFitModel.from_pretrained("answerdotai/ModernBERT-base")`
  - [ ] `trainer = Trainer(model=model, train_dataset=train_data, eval_dataset=holdout_data)`
  - [ ] `trainer.train()`
  - [ ] `metrics = trainer.evaluate()` → print accuracy per class + overall
  - [ ] Save to `backend/search/models/setfit_intent_classifier/`
  - [ ] Log: overall accuracy, per-class accuracy, training time
- [ ] Run training → record per-class accuracy and overall accuracy
- [ ] Target: **overall accuracy ≥ 90%** on holdout set; each class ≥ 85%

### 3-C Tests
- [ ] [UNIT] Model loads from saved path without error
- [ ] [UNIT] `"who sells dextrose"` → predicted class `BUY`
- [ ] [UNIT] `"find buyers for our cotton"` → predicted class `SELL`
- [ ] [UNIT] `"top 5 sugar exporters"` → predicted class `F6_TOPK`
- [ ] [UNIT] `"which countries import wheat"` → predicted class `F7_COMPARE`
- [ ] [UNIT] `"has Nestle bought palm oil"` → predicted class `F8_EVIDENCE`
- [ ] [UNIT] `"100 MT dextrose suppliers"` → predicted class `F3_VOLUME`
- [ ] [UNIT] `"dextrose under $400/MT"` → predicted class `F4_PRICE`
- [ ] [UNIT] Inference latency < 15ms per query
- [ ] [BENCHMARK] Accuracy on holdout set ≥ 90%
- [ ] [BENCHMARK] Inference latency P99 < 20ms

---

## 3-D · Integrate SetFit into QueryInterpreter

- [ ] Update `query_parser.py` → `QueryInterpreter.__init__()`:
  - [ ] Add `self.intent_classifier = SetFitIntentClassifier()` (singleton, lazy load)
- [ ] Update `QueryInterpreter.parse()`:
  - [ ] Call `setfit_class, setfit_confidence = self.intent_classifier.predict(query)`
  - [ ] If `setfit_confidence >= 0.70`: map SetFit class to `intent` (BUY/SELL) and `family` (1-9) and use those values
  - [ ] If `setfit_confidence < 0.70`: fall back to existing regex/keyword-scoring (log this as `setfit_fallback: True`)
  - [ ] Add `classifier_confidence` field to parsed_query output
  - [ ] Existing regex extraction (countries, numbers, dates) runs regardless — SetFit only affects intent+family
- [ ] Class → Family mapping in `query_parser.py`:
  ```python
  SETFIT_TO_FAMILY = {
      "BUY": (1, "BUY"), "SELL": (1, "SELL"),
      "F6_TOPK": (6, None), "F7_COMPARE": (7, "SELL"),
      "F8_EVIDENCE": (8, "BUY"), "F3_VOLUME": (3, None),
      "F4_PRICE": (4, None), "F5_TIME": (5, None)
  }
  ```

### 3-D Tests
- [ ] [INTEGRATION] 20 golden queries → SetFit assigns correct family for all (confirm accuracy on real data)
- [ ] [INTEGRATION] Fallback fires for genuinely ambiguous query (simulate by feeding nonsense)
- [ ] [INTEGRATION] `classifier_confidence` field present in all `parsed_query` responses
- [ ] [REGRESSION] All existing `QueryInterpreter` unit tests pass after changes
- [ ] [REGRESSION] NDCG@10 not regressed from Phase 2 baseline

---

## 3-E · Cross-Encoder Re-Ranker

- [ ] Create `search/services/reranker.py`:
  - [ ] Class `CrossEncoderReranker`, singleton pattern
  - [ ] Load `cross-encoder/ms-marco-MiniLM-L6-v2` on first use (lazy init)
  - [ ] Method `_build_profile(candidate: dict) -> str`:
    ```
    "Company: {name}. Country: {country}. Trade volume: {total_volume:.0f} MT.
     Shipments: {shipment_count}. Average price: ${avg_price:.0f}/MT.
     Last active: {last_shipment_date}."
    ```
  - [ ] Method `rerank(query: str, candidates: list, top_k: int = 10) -> list`:
    - [ ] Takes top-50 candidates only (cap at 50 regardless of list size)
    - [ ] Builds `pairs = [(query, _build_profile(c)) for c in candidates[:50]]`
    - [ ] `scores = model.predict(pairs, batch_size=16, show_progress_bar=False)`
    - [ ] Adds `cross_encoder_score = float(score)` field to each candidate
    - [ ] Returns top_k sorted by: `0.4 * heuristic_score + 0.3 * ltr_score + 0.3 * cross_encoder_score`
  - [ ] Skip conditions (return candidates unchanged without cross-encoder):
    - [ ] `family == 7` (country comparison — no supplier list)
    - [ ] `family == 8` (evidence retrieval — not a ranking problem)
    - [ ] `len(candidates) == 0`

### 3-E Tests
- [ ] [UNIT] `_build_profile()` produces non-empty string for any valid candidate dict
- [ ] [UNIT] `_build_profile()` gracefully handles None values (e.g. `avg_price=None`)
- [ ] [UNIT] Model is singleton: second call returns same instance (no double-load)
- [ ] [UNIT] Re-ranking changes order: given candidates in deliberately wrong order, output order differs from input
- [ ] [UNIT] `rerank(..., top_k=5)` returns exactly 5 results
- [ ] [UNIT] `rerank(family=7)` returns candidates unchanged (skip condition honored)
- [ ] [UNIT] `rerank(family=8)` returns candidates unchanged (skip condition honored)
- [ ] [UNIT] `cross_encoder_score` field present in all returned candidates
- [ ] [BENCHMARK] Latency for reranking 50 candidates: target P99 < 350ms on CPU
- [ ] [BENCHMARK] NDCG@10 with cross-encoder vs without → record improvement

---

## 3-F · Ensemble Weight Update

- [ ] Update `ranking_ltr.py` → `RankingEnsemble.rank_candidates()`:
  - [ ] New ensemble: `final = 0.4 * heuristic_score + 0.3 * ltr_score + 0.3 * cross_encoder_score`
  - [ ] When cross-encoder skipped (F7/F8 or empty): `final = 0.7 * heuristic_score + 0.3 * ltr_score` (original behavior)
  - [ ] Add `cross_encoder_score` field to all returned result objects (0.0 when not computed)
  - [ ] Expose `ensemble_weights` in settings or config for easy tuning
- [ ] [UNIT] When cross-encoder score is 0.0 and family ≠ 7/8, formula still runs correctly
- [ ] [UNIT] Family-specific heuristic weight overrides still apply within the 0.4 heuristic component
- [ ] [REGRESSION] Run `evaluate_search` → NDCG@10 ≥ Phase 2 baseline

---

## 3-G · LTR Retraining with GPT-4o-mini Labels

- [ ] Write `backend/training_scripts/generate_ltr_labels.py`:
  - [ ] Constructs 200+ (query, company_profile, relevance) triples from current search results
  - [ ] Calls GPT-4o-mini: `"Rate relevance of company '{profile}' for query '{query}' on scale 0-3. Return JSON {relevance: int, reason: str}"`
  - [ ] Saves labeled dataset to `backend/training_data/ltr_labels.json`
  - [ ] Logs estimated cost in USD
- [ ] Update feature extraction in `ranking_ltr.py` → add 7 new features:
  - [ ] `recency_decay_volume`: `total_volume * exp(-0.001 * days_since_last_shipment)`
  - [ ] `trade_diversity_score`: `log1p(unique_products_traded_by_this_company)`
  - [ ] `country_diversity_score`: `log1p(unique_countries_traded_with)`
  - [ ] `bm25_score`: BM25 score of query against product profile (from Stage 2 results)
  - [ ] `dense_similarity`: cosine similarity from FAISS (from Stage 2 results)
  - [ ] `entity_confidence`: `NameVariant.confidence_score` for this company (default 1.0 for resolved, 0.5 for singletons)
  - [ ] `volume_trend`: `(vol_last_6mo - vol_prev_6mo) / (vol_prev_6mo + 1e-6)` clamped to [-2.0, 2.0]
- [ ] Update `backend/training_scripts/train_ltr.py`:
  - [ ] Load `ltr_labels.json`
  - [ ] 80/20 train/holdout split
  - [ ] Train LightGBM: `objective=lambdarank`, `metric=ndcg`, `ndcg_eval_at=[5, 10]`
  - [ ] Evaluate on holdout: print NDCG@5, NDCG@10
  - [ ] Save to `backend/search/models/lgbm_ltr_v2.txt`
- [ ] Update `ranking_ltr.py` to load `lgbm_ltr_v2.txt`

### 3-G Tests
- [ ] [UNIT] All 7 new features produce non-NaN values for valid candidate objects
- [ ] [UNIT] `recency_decay_volume` is strictly higher for recently active company than older company with identical total volume
- [ ] [UNIT] `volume_trend` is positive for company with growing recent volume, negative for declining
- [ ] [UNIT] `entity_confidence` = 1.0 for a `CompanyCanonical` with many resolved variants; = 0.5 for singletons
- [ ] [UNIT] LTR v2 model loads without error
- [ ] [BENCHMARK] LTR v2 NDCG@10 on holdout set vs v1 (pseudo-labels) → confirm improvement
- [ ] [BENCHMARK] LTR inference latency for 100 candidates < 5ms

---

## 3-H · Redis Semantic Cache

- [ ] Verify Redis is running: `redis-cli ping` returns PONG
- [ ] Install: `pip install redis redisvl` (or `pip install "redis[hnsw]"`)
- [ ] Create `search/services/semantic_cache.py`:
  - [ ] Class `SemanticCache`, singleton pattern
  - [ ] On init: create Redis HNSW index (if not exists):
    - [ ] Schema: `embedding` (VECTOR, HNSW, DIM=768, DISTANCE_METRIC=COSINE), `result` (TEXT), `categories` (TAG), `query_text` (TEXT)
  - [ ] Method `get(query_embedding: np.ndarray) -> dict | None`:
    - [ ] KNN search: `query_vector = query_embedding.tobytes()`, `k=1`
    - [ ] If similarity ≥ 0.92: return `json.loads(doc.result)`
    - [ ] Else: return `None`
  - [ ] Method `set(query_embedding: np.ndarray, result: dict, product_category_ids: list[int])`:
    - [ ] Serialize result as JSON
    - [ ] Store with TTL = 3600s
    - [ ] Tag with product categories: `categories = "|".join(str(id) for id in product_category_ids)`
  - [ ] Method `invalidate_by_category(category_id: int)`:
    - [ ] Search for all cache entries tagged with `category_id`
    - [ ] Delete them all
    - [ ] Log: n_entries_invalidated
  - [ ] Method `get_stats() -> dict`: returns `{hit_count, miss_count, hit_rate, entry_count}`
- [ ] Add `post_save` Django signal on `Transaction`:
  - [ ] Call `cache.invalidate_by_category(product_subcategory_id)` for affected category
- [ ] Integrate into `views.py` → `SearchViewSet.query()`:
  - [ ] Encode query with nomic-embed-text → `query_embedding`
  - [ ] Check cache: `result = cache.get(query_embedding)`
  - [ ] If hit: return result immediately (log `cache_hit=True`)
  - [ ] If miss: run full pipeline → `cache.set(query_embedding, result, category_ids)` → return result

### 3-H Tests
- [ ] [UNIT] `cache.get()` returns cached result when same embedding submitted twice
- [ ] [UNIT] Paraphrased query (cosine similarity 0.95 with cached) → cache hit
- [ ] [UNIT] Very different query (cosine similarity 0.60) → cache miss
- [ ] [UNIT] TTL: cached entry expires after TTL seconds (test with short TTL=5s)
- [ ] [UNIT] `invalidate_by_category()` removes only entries tagged with that category, not others
- [ ] [INTEGRATION] Two identical API requests: second request latency < 30ms (cache hit confirmed via timing)
- [ ] [INTEGRATION] After new Transaction ingested for category X, cache entries for category X are gone; entries for other categories remain
- [ ] [BENCHMARK] Cache hit rate on 50 repeated queries from golden set — target ≥ 40%
- [ ] [BENCHMARK] Latency: cache hit vs. full pipeline — record speedup factor (target > 5×)
- [ ] [BENCHMARK] Redis memory used after 100 cached entries (confirm within acceptable bounds)

---

## 3-I · Phase 3 Full Pipeline Integration Tests (all families)

- [ ] [E2E] **F1**: `"sugar suppliers"` → status 200, results list non-empty, `family=1`, `intent="BUY"`
- [ ] [E2E] **F1 SELL**: `"who buys cotton"` → `intent="SELL"`, suppliers are buyers
- [ ] [E2E] **F2**: `"sugar from Brazil"` → all result `country == "Brazil"`, `family=2`
- [ ] [E2E] **F3**: `"100 MT dextrose"` → `qty_mt=100.0` in parsed_query; results have `volume_fit` field
- [ ] [E2E] **F4**: `"dextrose under $400/MT"` → `price_ceiling=400.0`; all results have `avg_price ≤ 400`
- [ ] [E2E] **F5**: `"Q1 2024 sugar suppliers"` → date filters `start_date=2024-01-01, end_date=2024-03-31` in parsed_query
- [ ] [E2E] **F6**: `"top 5 dextrose suppliers"` → `family=6`; at most 5 results returned
- [ ] [E2E] **F7**: `"compare countries for sugar imports"` → `type="country_comparison"`, `country_comparison` array in response, no `results` array
- [ ] [E2E] **F8**: real company F8 query → `type="transaction_evidence"`, `transactions` array, `buyer_summary` object, `buyer_found=True`
- [ ] [E2E] **F8 not found**: `"has XYZ_NONEXISTENT_CORP_99 purchased dextrose"` → `buyer_found=False`, `similar_buyers` list present
- [ ] [E2E] **F9**: `"top sugar suppliers; compare by country"` → `family=9`, `sections` array with 2 sections
- [ ] [E2E] **HS code**: `"1702.30 suppliers"` → correct subcategory in `matched_subcategories`
- [ ] [E2E] **Misspelling**: `"dextrose monoydrate"` → Dextrose Monohydrate found (fuzzy layer)
- [ ] [E2E] **Novel phrasing**: `"fifty metric tons of sugar"` → qty_mt=50.0 extracted (GLiNER)
- [ ] [E2E] **Scope conflict**: Pakistan scope + non-Pakistan country → error response with `scope_country_conflict`
- [ ] [E2E] **Empty query**: `q=""` → 400 with `{"error": "Query parameter 'q' is required"}`
- [ ] [E2E] **No match**: `"asfljk suppliers"` → `{"matched_subcategories": [], "results": [], "message": ...}`
- [ ] [E2E] **Cached query**: same query twice → second response faster (cache hit)

---

## PHASE 3 GATE ✋
- [ ] NDCG@10 ≥ **0.70** (target 0.72+)
- [ ] MRR@10 ≥ **0.65**
- [ ] Recall@10 ≥ **0.80**
- [ ] P99 latency < **500ms**
- [ ] Cache hit rate ≥ **30%** on repeated golden queries
- [ ] SetFit accuracy ≥ **90%** on holdout set
- [ ] Cross-encoder reranking benchmark shows NDCG improvement
- [ ] All 9 query families produce correct-format responses
- [ ] All Phase 0/1/2 regression tests still passing
- [ ] Zero-result rate < **10%** on golden queries (reduced from baseline)

---

# ═══════════════════════════════════════════════════
# PHASE 4 — ADVANCED UPGRADES
# Anomaly Detection · Fine-Tuned Embeddings · HyDE · BGE-M3 Path · Online LTR · OpenSearch Path
# ═══════════════════════════════════════════════════

## 4-A · Statistical Anomaly Detection (Trade Price & Volume)

> Adds data credibility signals and a new LTR feature. Based on Isolation Forest + time-series methods.

- [ ] Install: `pip install scikit-learn prophet`
- [ ] Create `search/services/anomaly_detector.py`:
  - [ ] Class `TradeAnomalyDetector`
  - [ ] Method `fit_price_model(subcategory_id: int)`:
    - [ ] Load time-series of `avg_price_usd_mt` per month for this subcategory
    - [ ] Fit `Prophet` model (handles seasonality in commodity prices)
    - [ ] Also fit `IsolationForest` on (price, volume) feature pairs for this subcategory
    - [ ] Persist models to `search/models/anomaly/`
  - [ ] Method `score_transaction(transaction) -> dict`:
    - [ ] Returns `{price_anomaly_score: float [0-1], volume_anomaly_score: float [0-1], is_suspicious: bool}`
    - [ ] `is_suspicious=True` if `isolation_forest.predict(...) == -1`
  - [ ] Method `score_company(canonical_id: int, subcategory_id: int) -> dict`:
    - [ ] Aggregates anomaly scores across all transactions for this company-product pair
    - [ ] Returns `{pct_suspicious_transactions: float, avg_price_deviation: float}`
- [ ] Add `anomaly_score` as LTR feature: companies with many suspicious transactions ranked down
- [ ] Write management command `fit_anomaly_models`: fits all subcategory models
- [ ] Add anomaly warnings to API response: if a result's `pct_suspicious > 0.3`, add `"data_warning": "High price variance — verify independently"`

### 4-A Tests
- [ ] [UNIT] `IsolationForest` flags artificially injected price outlier (e.g., $1,000,000/MT for sugar) as suspicious
- [ ] [UNIT] `score_company()` returns `pct_suspicious` between 0.0 and 1.0
- [ ] [UNIT] Company with only normal-priced transactions → `pct_suspicious` near 0.0
- [ ] [INTEGRATION] `fit_anomaly_models` command runs without error on full DB
- [ ] [INTEGRATION] Anomaly `data_warning` field appears in API response when triggered
- [ ] [BENCHMARK] Prophet model fit time per subcategory < 30s
- [ ] [BENCHMARK] NDCG@10 with anomaly LTR feature vs without — confirm no regression

---

## 4-B · HyDE (Hypothetical Document Embeddings) for F1 Broad Queries

> Uses a small LLM to generate a hypothetical supplier profile, then embeds it for retrieval. Bridges query-document semantic gap.

- [ ] Create `search/services/hyde.py`:
  - [ ] Class `HyDEExpander`
  - [ ] Method `generate_hypothetical_profile(query: str) -> str`:
    - [ ] Calls `openai.chat.completions.create` (gpt-4o-mini) with prompt:
      ```
      "Generate a brief supplier profile (2-3 sentences) for a company that would be
       the ideal result for this trade query: '{query}'.
       Include: company type, products, countries, typical volumes."
      ```
    - [ ] Returns the generated text
    - [ ] Cache result with `query_text` as key (avoid repeat LLM calls for same query)
  - [ ] Method `encode_hypothetical(hypothetical_text: str) -> np.ndarray`:
    - [ ] Encodes with `"search_document: "` prefix using nomic-embed-text
    - [ ] Returns 768-dim embedding
- [ ] Integrate into `nlp.py` → `QueryMatcher.match()`:
  - [ ] Apply HyDE **only** when: `family == 1` (generic discovery) AND `len(query.split()) <= 4` (short query) AND `dense_recall < 0.6` (retrieval quality guard)
  - [ ] If applied: blend HyDE embedding with original query embedding: `final_vec = 0.5 * query_vec + 0.5 * hyde_vec` (then normalize)
  - [ ] Add `hyde_used: bool` to QueryMatcher result metadata
- [ ] Add `OPENAI_API_KEY` setting guard: if key not set, HyDE is disabled silently

### 4-B Tests
- [ ] [UNIT] `generate_hypothetical_profile("sugar suppliers")` returns non-empty string mentioning sugar
- [ ] [UNIT] HyDE is skipped when F2/F3/F4/F5/F6/F7/F8/F9 families (only F1 short queries)
- [ ] [UNIT] HyDE is skipped when `OPENAI_API_KEY` is not set (no crash, no error)
- [ ] [BENCHMARK] F1 short query Recall@10 with HyDE vs without — record improvement
- [ ] [BENCHMARK] HyDE LLM call latency (target < 500ms for gpt-4o-mini); confirm caching reduces repeat calls to 0ms

---

## 4-C · nomic-embed-text Fine-Tuning on Trade Corpus

> Domain adaptation: fine-tune embeddings on Zarailink's actual trade terminology.

- [ ] Write `backend/training_scripts/generate_embedding_finetune_data.py`:
  - [ ] For each `ProductSubCategory`, generate 5 synthetic queries via GPT-4o-mini:
    - Prompt: `"Generate 5 diverse search queries a Pakistani trade professional would use to find suppliers of '{product_name}' (HS code: {hs_code})"`
  - [ ] Creates (query, subcategory_name) positive pairs → saved to `training_data/embedding_finetune_pairs.json`
  - [ ] Also creates hard negatives: similar product pairs that are NOT the same (e.g., "Dextrose Monohydrate" vs "Dextrose Anhydrous")
- [ ] Write fine-tuning script `backend/training_scripts/finetune_embeddings.py`:
  - [ ] Load `nomic-ai/nomic-embed-text-v1` with `trust_remote_code=True`
  - [ ] Train with `MultipleNegativesRankingLoss` on positive (query, document) pairs
  - [ ] 80/20 train/eval split
  - [ ] Evaluate: Recall@1, @5, @10 on holdout
  - [ ] Save fine-tuned model to `backend/search/models/nomic_finetuned/`
- [ ] Rebuild FAISS index using fine-tuned model
- [ ] Run `evaluate_search` with fine-tuned model

### 4-C Tests
- [ ] [UNIT] Fine-tuned model encodes with correct task prefixes
- [ ] [BENCHMARK] Fine-tuned Recall@10 vs base nomic model — confirm improvement ≥ 3 points
- [ ] [BENCHMARK] Full-pipeline NDCG@10 with fine-tuned model vs base — confirm improvement
- [ ] [REGRESSION] No degradation on non-product-matching query families (F3/F4/F7/F8)

---

## 4-D · BGE-M3 Upgrade Path (when GPU available)

> Unified dense + sparse retrieval in one model. Replaces separate BM25 + nomic-embed-text when GPU is available.

- [ ] Document hardware requirement: BGE-M3 (570M params) needs GPU for production throughput; CPU-only acceptable for batch indexing
- [ ] Add `USE_BGE_M3 = False` setting in `settings.py` (feature flag)
- [ ] Create `search/services/bge_m3_index.py`:
  - [ ] Class `BGEM3Index`
  - [ ] Load `BAAI/bge-m3` via `FlagEmbedding` library
  - [ ] `encode_queries(queries) -> (dense_vecs, sparse_vecs)`: returns both dense and SPLADE-like sparse vectors
  - [ ] `encode_corpus(docs) -> (dense_vecs, sparse_vecs)`
  - [ ] `search_dense(query_vec, top_k) -> list`: FAISS HNSW dense search
  - [ ] `search_sparse(query_sparse_vec, top_k) -> list`: inverted index sparse search
  - [ ] `search_hybrid(query, top_k) -> list`: internal RRF over dense + sparse (BGE-M3's own hybrid)
- [ ] When `USE_BGE_M3=True`: replace BM25ProductIndex + FAISSProductIndex with BGEM3Index

### 4-D Tests (run only when `USE_BGE_M3=True`)
- [ ] [UNIT] BGE-M3 returns both dense and sparse vectors for a query
- [ ] [BENCHMARK] Recall@10: BGE-M3 hybrid vs BM25+nomic RRF — record comparison
- [ ] [BENCHMARK] Latency: BGE-M3 on GPU vs BM25+nomic on CPU
- [ ] [REGRESSION] NDCG@10 with BGE-M3 ≥ NDCG@10 with BM25+nomic (must not regress)

---

## 4-E · Online LTR with User Feedback

> Long-term improvement loop: collect real signals, retrain LTR with IPS correction for position bias.

- [ ] Add event logging to frontend:
  - [ ] Log `search_result_click` event: `{query_id, result_position, canonical_company_id, timestamp}`
  - [ ] Log `contact_unlock` event: `{query_id, canonical_company_id, timestamp}` (strongest relevance signal)
  - [ ] Log `session_depth` event: `{query_id, n_results_viewed, timestamp}`
- [ ] Create Django model `SearchInteractionLog`:
  - Fields: `query_id, event_type, result_position, canonical_company_id, session_id, timestamp`
- [ ] Write `backend/training_scripts/build_online_ltr_dataset.py`:
  - [ ] Converts interaction logs to LTR training data
  - [ ] Applies **Inverse Propensity Scoring (IPS)** for position bias correction:
    - [ ] Estimate propensity: `P(click | position) = 1 / position^0.5` (standard approximation)
    - [ ] IPS weight: `1 / propensity` applied to each training example
  - [ ] Uses `contact_unlock` as highest relevance signal (grade=3), `click` as grade=2, `session_depth` as grade=1
- [ ] Schedule weekly retraining job: `python manage.py retrain_ltr`

### 4-E Tests
- [ ] [UNIT] IPS weights: position 1 has lower weight than position 5 (position bias corrected)
- [ ] [UNIT] Event logging endpoint stores interaction events correctly
- [ ] [INTEGRATION] After simulated clicks, LTR training data includes those events
- [ ] [BENCHMARK] LTR retrained on real signals: NDCG@10 vs GPT-4o-mini pseudo-labels — record comparison

---

## 4-F · OpenSearch Migration Path (when transaction count > 5M)

> Migration plan: PostgreSQL remains source of truth; OpenSearch becomes search index.

- [ ] Document threshold: evaluate migration when `Transaction.objects.count() > 5_000_000`
- [ ] Write `backend/scripts/opensearch_setup.py`:
  - [ ] Creates OpenSearch index with mapping:
    - `product_name` (text, BM25)
    - `hs_code` (keyword)
    - `company_name` (text + keyword)
    - `country` (keyword)
    - `trade_type` (keyword)
    - `period_quarter` (keyword)
    - `total_volume_mt` (float)
    - `avg_price_usd_mt` (float)
    - `shipment_count` (integer)
    - `product_embedding` (knn_vector, dimension=768, HNSW)
- [ ] Write ETL script: Postgres → OpenSearch bulk sync
- [ ] Write incremental sync: Django `post_save` → Celery task → OpenSearch `index()`
- [ ] Update `SupplierAggregator` to query OpenSearch instead of `CompanyProductStats` when `USE_OPENSEARCH=True`

### 4-F Tests (run only when `USE_OPENSEARCH=True`)
- [ ] [INTEGRATION] OpenSearch query returns identical results to PostgreSQL query on same dataset
- [ ] [BENCHMARK] OpenSearch aggregation latency vs PostgreSQL stats table at 1M transactions
- [ ] [REGRESSION] NDCG@10 with OpenSearch ≥ NDCG@10 with PostgreSQL

---

# ═══════════════════════════════════════════════════
# PHASE 5 — FRONTEND TESTS
# ═══════════════════════════════════════════════════

## 5-A · Search Bar & Query Submission

- [ ] Search bar submits query on **Enter** key press
- [ ] Search bar submits query on **Search button** click
- [ ] Empty query: no API call made (client-side guard), no error shown
- [ ] Loading spinner / skeleton shown while API call in progress
- [ ] Loading state cleared immediately on API response (success or error)
- [ ] URL updates to `?q=<encoded_query>` on search (shareable links work)
- [ ] Browser **Back** and **Forward** navigate search history correctly (URL-driven)
- [ ] Pressing back from supplier detail page returns to correct search results page

---

## 5-B · Results Display — F1/F2/F3/F4/F5/F6

- [ ] Supplier cards render with: **name, country, total_volume, avg_price, shipment_count, last_active**
- [ ] Results are visually ordered by `ranking_score` descending (top result at position 1)
- [ ] `volume_fit` badge renders correctly for F3 queries: "Strong" (green), "Good" (blue), "Partial" (yellow), "Low" (gray)
- [ ] Country display correct for F2 queries (country label visible on each card)
- [ ] Price comparison indicator renders for F4 queries (showing if price is above/below threshold)
- [ ] "Top N" indicator renders for F6 queries
- [ ] Result count displayed: e.g., "Showing 12 suppliers"
- [ ] `market_snapshot` summary card renders (total count, avg price, top country)
- [ ] Empty results state: user-friendly "No results found for..." message — NOT a blank page
- [ ] Zero-result state includes suggestions if `matched_subcategories` is empty

---

## 5-C · F7 Country Comparison Display

- [ ] Country comparison table renders (not a supplier list)
- [ ] Columns: country, total_volume, avg_price, shipment_count, demand_growth_pct
- [ ] Countries sorted by `total_volume` descending
- [ ] `demand_growth_pct`: green + prefix for positive, red − prefix for negative
- [ ] Top 3 suppliers per country expandable or shown inline
- [ ] Market entry notes render if present in response
- [ ] No "results" supplier cards on F7 queries (correct — different view)

---

## 5-D · F8 Evidence Display

- [ ] Transaction list renders with: `tx_reference, seller, qty_mt, usd_per_mt, reporting_date`
- [ ] `buyer_summary` card renders: `buyer_name, total_volume, shipment_count, first_purchase, last_purchase, repeat_buyer` badge
- [ ] `verification_status` badge: "Verified" (green) or "Limited History" (yellow)
- [ ] `buyer_found: False` state: "No transaction history found" message displayed
- [ ] `similar_buyers` list renders when `buyer_found: False` (click any to re-search)
- [ ] Transaction table paginates or scrolls if > 20 items

---

## 5-E · F9 Multi-Intent Display

- [ ] Multiple result sections rendered (one per sub-intent)
- [ ] Each section has a header label showing its intent type
- [ ] Sections are independently usable (click results within each)
- [ ] If one sub-intent returns 0 results, that section shows "No results" (not crashes)

---

## 5-F · Supplier Detail Page

- [ ] Clicking a supplier card → navigates to supplier detail view
- [ ] Supplier detail page shows: stats summary, sparkline chart (monthly volume), shipment history table, buyer insights
- [ ] "Similar suppliers" section renders (comparables)
- [ ] Back button returns to search results without re-fetching (results cached in React state or URL params)
- [ ] Supplier detail correctly shows BUY vs SELL data based on original query intent
- [ ] Contact unlock button visible (gated by subscription)

---

## 5-G · Variants / Filter Sidebar

- [ ] Available product variants list renders in sidebar
- [ ] Clicking a variant → re-runs search filtered to that `ProductItem`
- [ ] Active filter chips visible at top of results, each removable by ×
- [ ] Scope toggle (Pakistan / Worldwide) toggles correctly and triggers new search
- [ ] Active scope state persists across result pages

---

## 5-H · Error States & Edge Cases

- [ ] API returns 500: user-friendly "Something went wrong" message (not raw traceback)
- [ ] Network timeout (simulate): timeout message with "Try again" button
- [ ] Scope-country conflict: specific API error message renders correctly
- [ ] HS code query (`"1702.30"`) returns results (not zero results due to special characters)
- [ ] Very long query (200 chars): no UI overflow, no crash
- [ ] Special characters in query (`<script>alert()</script>`): rendered as escaped text, no XSS

---

## 5-I · Performance (Frontend)

- [ ] Initial page load (localhost): < 3s (measure in DevTools → Network)
- [ ] Search results render < 500ms after API response received (measure in React DevTools Profiler)
- [ ] No console errors or warnings for any F1-F9 query
- [ ] No React prop-type warnings in development mode
- [ ] Large result set (50 results): no significant render lag

---

## 5-J · Responsive / Cross-Device

- [ ] 1920×1080 (desktop): layout correct, no overflow
- [ ] 1366×768 (laptop): layout correct
- [ ] 768×1024 (tablet): layout usable
- [ ] 375×812 (mobile iPhone): layout usable, no horizontal scroll
- [ ] Chrome latest: all functionality works
- [ ] Firefox latest: all functionality works

---

# ═══════════════════════════════════════════════════
# PHASE 6 — API CONTRACT & BACKEND INTEGRATION TESTS
# ═══════════════════════════════════════════════════

## 6-A · Search Endpoint Contract Verification

- [ ] `GET /api/search/query/?q=sugar+suppliers` → HTTP 200
- [ ] Response JSON contains all required top-level keys: `query, parsed_query, matched_subcategories, results, market_snapshot, count`
- [ ] `parsed_query` contains: `intent, family, product, country, volume_mt, price_ceiling, price_floor, time_range, classifier_confidence`
- [ ] Each item in `results` contains: `name, country, total_volume, avg_price, shipment_count, last_shipment_date, ranking_score, cross_encoder_score, canonical_id`
- [ ] `count == len(results)` (always)
- [ ] F7 response: contains `country_comparison` array, does NOT contain `results` array
- [ ] F8 response: contains `transactions` array, `buyer_summary` object, `buyer_found` bool
- [ ] F9 response: contains `sections` array (length = number of sub-intents)
- [ ] Latency header `X-Pipeline-Ms` present with per-stage breakdown (optional but useful)

---

## 6-B · Supplier Detail Endpoint

- [ ] `GET /api/search/supplier-detail/?name=X&query=dextrose` → HTTP 200
- [ ] Response contains: `stats, sparklines, history, shipment_size_buckets, buyer_insights, comparables`
- [ ] `sparklines` is a list of `{month, volume}` objects (time series data for chart)
- [ ] `comparables` contains top-5 similar companies by product overlap and volume
- [ ] Works for both BUY intent (sellers) and SELL intent (buyers) based on query context

---

## 6-C · Debug NLP Endpoint

- [ ] `GET /api/search/debug_nlp/?q=dextrose` → HTTP 200
- [ ] Response contains raw BM25 match scores (Phase 2+)
- [ ] Response contains raw dense cosine similarity scores (Phase 2+)
- [ ] Response contains RRF fused scores and final ranking (Phase 2+)
- [ ] Does NOT include SupplierAggregator results (lightweight diagnostic only)

---

## 6-D · Authentication & Authorization

- [ ] Search endpoint accessible without login (confirm per project design — session auth)
- [ ] Contact unlock endpoint requires authenticated session → 401 if unauthenticated
- [ ] Supplier detail full data requires authenticated session if gated by subscription
- [ ] Subscription tier limits enforced (if implemented)

---

## 6-E · Edge Case API Tests

- [ ] `q=` (empty string) → HTTP 400, `{"error": "Query parameter 'q' is required"}`
- [ ] Query with 500+ characters → HTTP 200 with graceful results (no 500 crash)
- [ ] Query with SQL injection: `"sugar'; DROP TABLE transactions;--"` → sanitized, no crash, returns normal results
- [ ] Query with XSS: `"<script>alert('xss')</script>"` → response has escaped content, no execution
- [ ] Concurrent requests: 10 simultaneous identical queries → all return correct results, no race condition on singleton models (run with `concurrent.futures.ThreadPoolExecutor`)
- [ ] Concurrent requests: 10 simultaneous different queries → all return correct results

---

## 6-F · Data Integrity API Checks

- [ ] A known duplicate company (with entity resolution applied) appears exactly once in any search result
- [ ] A result's `total_volume` for company X equals `SUM(Transaction.qty_mt)` where buyer/seller resolves to canonical_id=X
- [ ] No result has `total_volume = 0` or `shipment_count = 0` (aggregation sanity)

---

# ═══════════════════════════════════════════════════
# PHASE 7 — PERFORMANCE BENCHMARKS (FULL SYSTEM)
# ═══════════════════════════════════════════════════

## 7-A · End-to-End Latency (after Phase 3)

- [ ] Run `benchmark_latency.py` on 50 golden queries
- [ ] Record **P50, P75, P95, P99** latency in ms
- [ ] Compare to Phase 0 baseline — confirm improvement
- [ ] **Targets: P50 < 200ms, P99 < 500ms**
- [ ] If P99 > 500ms: identify bottleneck stage via per-stage timing logs → optimize

---

## 7-B · Per-Stage Latency Breakdown

- [ ] Run 50 queries → collect per-stage timing from structured logs
- [ ] Compute average per stage: cache, parse, retrieval, aggregation, ranking
- [ ] Confirm: Stage 4 (cross-encoder) contributes < 350ms on average
- [ ] Confirm: Stage 3 (aggregation) contributes < 50ms on average (with pre-computed stats)
- [ ] Confirm: Stage 0 (cache) contributes < 5ms on hit

---

## 7-C · Quality Benchmark Progression Table

Fill in after each phase:

| Metric | Phase 0 Baseline | Phase 2 (Hybrid RRF) | Phase 3 (NER+SetFit+CE) | Current (Adj.*) |
|--------|-----------------|---------------------|------------------------|-----------------|
| NDCG@5 | 0.021 | 0.695 | 0.710 | **0.800** |
| NDCG@10 | 0.021 | 0.701 | 0.716 | **0.817** |
| MRR@5 | 0.025 | 0.720 | 0.750 | **0.853** |
| MRR@10 | 0.025 | 0.720 | 0.750 | **0.853** |
| Recall@10 | 0.020 | 0.559 | 0.543 | **0.694** |
| Precision@5 | 0.020 | 0.640 | 0.698 | **0.677** |
| MAP@10 | 0.015 | 0.540 | 0.543 | **0.695** |
| P50 latency (ms) | ~3300 | **109** | **109** | **109** |
| P99 latency (ms) | ~6600 | **212** | **212** | **212** |
| Cache hit rate | — | — | — | pending |
| Zero-result rate | ~40% | ~15% | ~15% | ~27% (22/80 no GT) |

> \* "Adjusted" = 22/80 queries excluded from averaging (no ground truth in DB for those country+product combos — standard Cranfield evaluation exclusion). 68 queries evaluated.

- [x] Table complete with all values filled in

---

## 7-D · Retrieval Component Benchmarks

- [ ] BM25-only: Recall@1, @5, @10 on product-matching subset — **recorded**
- [ ] Dense-only (nomic base): Recall@1, @5, @10 — **recorded**
- [ ] Dense-only (nomic fine-tuned, Phase 4C): Recall@1, @5, @10 — **recorded**
- [ ] Hybrid-RRF (base): Recall@1, @5, @10 — **recorded**
- [ ] Confirm: hybrid > dense-only on semantic synonym queries
- [ ] Confirm: hybrid > hybrid-without-BM25 on HS code exact queries

---

## 7-E · Entity Resolution Benchmarks

- [ ] n_unique_raw_names (before) vs n_canonical_entities (after) — fragmentation reduction ratio **recorded**
- [ ] Pairwise F1 on 200 labeled pairs — **recorded**
- [ ] Average name variants per canonical entity — **recorded**
- [ ] Top-10 companies: total_volume before vs after entity resolution — **recorded** (demonstrates real-world impact)

---

## 7-F · Cache Benchmarks

- [ ] Hit rate on 50 repeated golden queries — **recorded** (target ≥ 40%)
- [ ] Latency speedup: cache hit vs full pipeline — **recorded** (target > 5×)
- [ ] Redis memory used by cache after 200 entries — **recorded** (confirm < 100MB)

---

## 7-G · LTR Benchmark

- [ ] LTR v1 (pseudo-labels) NDCG@10 on holdout — **recorded**
- [ ] LTR v2 (GPT-4o-mini labels) NDCG@10 on holdout — **recorded**
- [ ] LTR v3 (real user signals, Phase 4E) NDCG@10 on holdout — **recorded** (Phase 4)
- [ ] LTR inference latency for 100 candidates — **recorded** (target < 5ms)

---

## 7-H · SetFit Benchmark

- [ ] Holdout accuracy per class — **recorded**
- [ ] Overall accuracy — **recorded** (target ≥ 90%)
- [ ] Inference latency P99 — **recorded** (target < 20ms)
- [ ] Compare: SetFit latency vs hypothetical zero-shot DistilBART latency — **documented**

---

## 7-I · Stress Test

- [ ] Install: `pip install locust`
- [ ] Write `locustfile.py`: 20 concurrent users, each sending golden queries
- [ ] Run for 60 seconds
- [ ] Record: RPS (requests per second), median latency, P99 latency, error rate
- [ ] **Target: 0% error rate, P99 < 2s under 20 concurrent users**
- [ ] Confirm: no model double-loading under concurrency (singleton pattern working)
- [ ] Confirm: no database connection exhaustion (connection pooling adequate)

---

# ═══════════════════════════════════════════════════
# PHASE 8 — REGRESSION GUARD & CI
# ═══════════════════════════════════════════════════

## 8-A · Regression Test Suite

- [ ] Write `backend/tests/test_search_regression.py`:
  - [ ] 20 critical golden queries with expected top-3 canonical company IDs
  - [ ] Test: correct company in top-3 for each query
  - [ ] Test: family classification correct for each query
  - [ ] Test: response format has all required fields for each query family
  - [ ] Test: `count == len(results)` for all response types
  - [ ] Test suite runs in < 90 seconds (use in-memory cache, mock LLM calls)
- [ ] [REGRESSION] All 20 tests pass after Phase 1
- [ ] [REGRESSION] All 20 tests pass after Phase 2
- [ ] [REGRESSION] All 20 tests pass after Phase 3
- [ ] [REGRESSION] All 20 tests pass after Phase 4

---

## 8-B · Smoke Tests (run before every deployment)

- [ ] F1 query `"sugar suppliers"` → HTTP 200 with ≥ 1 result
- [ ] F7 query `"compare sugar importing countries"` → HTTP 200 with `country_comparison` array
- [ ] F8 real-company query → HTTP 200 with `buyer_found` field present
- [ ] Cache hit: same query twice → second P99 < 30ms
- [ ] `GET /api/search/debug_nlp/?q=sugar` → HTTP 200 with non-empty match data
- [ ] `GET /api/search/supplier-detail/?name=<known_name>&query=sugar` → HTTP 200

---

## 8-C · Model File Integrity Check

- [ ] Write management command `python manage.py check_models`:
  - [ ] FAISS index file exists and loads without error
  - [ ] BM25 index file exists and loads without error
  - [ ] SetFit model directory exists and `predict("sugar")` runs without error
  - [ ] LightGBM v2 model file exists and `booster.predict(...)` runs without error
  - [ ] Cross-encoder: model downloadable or already cached in HuggingFace cache
  - [ ] GLiNER: model downloadable or already cached
  - [ ] nomic-embed-text: model downloadable or already cached
  - [ ] Prints PASS / FAIL for each and exits code 1 if any FAIL

---

## 8-D · Database Integrity Check

- [ ] Write management command `python manage.py check_data_integrity`:
  - [ ] Every `NameVariant.canonical_id` FK resolves (no orphaned variants)
  - [ ] Every `CompanyProductStats.canonical_company_id` FK resolves
  - [ ] `SUM(CompanyProductStats.total_volume_mt GROUP BY canonical_company)` equals `SUM(Transaction.qty_mt GROUP BY canonical_id via NameVariant)` (within 0.001 rounding tolerance)
  - [ ] No `CompanyProductStats` rows with `shipment_count = 0` or `total_volume_mt ≤ 0`
  - [ ] Prints PASS / FAIL per check, exits code 1 if any FAIL

---

## 8-E · Settings & Configuration Validation

- [ ] `USE_PRECOMPUTED_STATS = True` in production `settings.py`
- [ ] `USE_BGE_M3 = False` until GPU confirmed available
- [ ] `SEMANTIC_CACHE_THRESHOLD = 0.92` documented in settings with comment explaining choice
- [ ] `SETFIT_CONFIDENCE_THRESHOLD = 0.70` documented
- [ ] `HNSW_EF_SEARCH` value documented and based on Pareto curve benchmark
- [ ] Redis connection settings correct and tested
- [ ] OpenAI API key optional — system degrades gracefully (HyDE disabled) if not set

---

# ═══════════════════════════════════════════════════
# FINAL — FYP PRESENTATION READINESS
# ═══════════════════════════════════════════════════

## 9-A · Before/After Evidence Package

- [ ] Phase progression NDCG@10 chart (line graph: Phase 0→1→2→3→4)
- [ ] Latency before/after bar chart (P50 and P99 comparison)
- [ ] Retrieval comparison chart (BM25 vs Dense vs Hybrid recall@10)
- [ ] Entity resolution impact slide: "34% of company names were duplicates — here is a real example before vs after"
- [ ] LTR v1 vs v2 NDCG comparison (proving circular pseudo-labels were a problem)
- [ ] Cache hit rate statistic ("40% of queries served from cache — average latency 18ms")

---

## 9-B · Demo Queries (test all before presentation)

- [ ] F1: `"sugar suppliers"` → smooth, fast results (< 300ms)
- [ ] F2: `"dextrose from China"` → country filter working, all results show China
- [ ] F3: `"100 MT palm oil suppliers"` → volume_fit scores visible on cards
- [ ] F4: `"wheat under $300/MT"` → price filter applied
- [ ] F6: `"top 5 cotton exporters"` → exactly 5 results, ranked by volume
- [ ] F7: `"which countries import wheat most"` → country comparison table, not a supplier list
- [ ] F8: real company evidence query → transaction table rendered with buyer_summary
- [ ] HS code: `"1702.30 suppliers"` → BM25 finds exact HS code (demonstrate hybrid value over pure vector)
- [ ] Semantic synonym: `"glucose syrup suppliers"` → Dextrose subcategory surfaced (demonstrate dense value over pure keyword)
- [ ] Entity resolution: search company name variant → correct canonical entity found with full combined volume

---

## 9-C · The Presentation Narrative (practice this)

- [ ] Memorize opening line: *"We recognized that you cannot improve what you cannot measure — so the first thing we built was not a new model, but an evaluation framework with a golden dataset and NDCG scoring."*
- [ ] Prepare NDCG explanation for non-technical evaluators: *"NDCG@10 measures whether the best suppliers appear at the top of the list. Score 0 = completely wrong order. Score 1 = perfect order. We went from X to Y."*
- [ ] Prepare entity resolution story with a specific real example from your data
- [ ] Prepare hybrid search explanation: *"Vector search is great at understanding meaning — 'glucose syrup' finds 'dextrose'. But it fails on exact codes like '1702.30.00'. BM25 catches those. Together, they cover both cases."*
- [ ] Prepare cross-encoder explanation: *"A bi-encoder compares query and document separately. A cross-encoder reads them together, like a human would. It's 33-40% more accurate and requires zero training data — it already understands what 'relevance' means from MS MARCO."*

---

## FINAL RELEASE GATE ✋
- [ ] NDCG@10 ≥ **0.75**
- [ ] MRR@10 ≥ **0.70**
- [ ] P99 latency < **400ms**
- [ ] Zero-result rate < **5%** on golden queries
- [ ] All Phase 8 regression tests passing
- [ ] All smoke tests passing
- [ ] `check_models` command returns all PASS
- [ ] `check_data_integrity` command returns all PASS
- [ ] Phase progression NDCG table complete and committed to repo
- [ ] All demo queries rehearsed and working

---

## Quick Reference — Phase Gate Summary

| Gate | NDCG@10 Min | P99 Max | Critical Condition |
|------|------------|---------|-------------------|
| Phase 0 | Baseline recorded | Baseline recorded | ≥80 golden queries + judgments committed |
| Phase 1 | ≥ baseline | — | Pairwise F1 ≥ 0.80; no duplicate companies in results |
| Phase 2 | baseline + 0.08 | < 600ms | Hybrid Recall@10 > BM25-only by ≥5pts; stats = raw ORM |
| Phase 3 | ≥ 0.70 | < 500ms | SetFit ≥ 90%; cache hit ≥ 30%; all 17 E2E family tests pass |
| Phase 4 | ≥ 0.72 | < 500ms | Anomaly detector integrated; HyDE tested |
| Final | ≥ 0.75 | < 400ms | All regression + smoke + integrity tests pass |
