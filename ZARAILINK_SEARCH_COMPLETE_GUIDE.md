# ZARAILINK SEARCH SYSTEM: THE COMPLETE BEGINNER'S GUIDE

## Everything You Need to Know — How It Works, Why It Works, and What Research Backs Every Decision

---

> **Who is this document for?**
> This guide is written for someone who has never studied information retrieval, machine learning, or natural language processing. Every concept is explained from the very ground up, with analogies, examples from real life, and references to published research papers. By the end of this document, you will understand *every single line* of Zarailink's search system as deeply as the engineers who built it.

> **How long is this?**
> Long. Very long. That is intentional. The request was for extreme granular detail, and that is what this document delivers. Use the table of contents to navigate.

---

# TABLE OF CONTENTS

1. [The Problem — Why Trade Search Is Hard](#part-1)
2. [Zarailink's Answer — The Multi-Stage Pipeline](#part-2)
3. [The Database — What Raw Data Exists](#part-3)
4. [Stage 1 — QueryInterpreter: Understanding What You're Asking](#part-4)
5. [Stage 1B — SetFit Intent Classifier](#part-5)
6. [Stage 1C — GLiNER Named Entity Recognition](#part-6)
7. [Stage 2 — Hybrid Retrieval: BM25 + FAISS-HNSW + RRF](#part-7)
8. [Stage 2B — Cross-Encoder Re-Ranking](#part-8)
9. [Stage 2C — HyDE: Hypothetical Document Embeddings](#part-9)
10. [Stage 3 — Aggregation: Getting the Data](#part-10)
11. [Stage 4 — RankingEnsemble: LightGBM LTR v2](#part-11)
12. [The 9 Query Families — Complete Reference](#part-12)
13. [Family 9 — Hybrid Multi-Intent Queries](#part-13)
14. [Supporting Infrastructure](#part-14)
15. [Evaluation Framework](#part-15)
16. [Management Commands & Operations](#part-16)
17. [Current Metrics & Performance](#part-17)
18. [Research Paper Compendium](#part-18)
19. [Glossary of Every Technical Term](#part-19)

---

<a name="part-1"></a>
# PART 1: THE PROBLEM — WHY TRADE SEARCH IS HARD

## 1.1 What Is Zarailink Trying to Do?

Zarailink is a trade intelligence platform for Pakistani agricultural businesses. It collects real government import/export transaction records and lets users search through them. The users are mostly **sellers** — people or companies that grow or manufacture a product (say, dextrose, rice, or salt) and want to know:

- **Who** is buying this product in Pakistan?
- **How much** do buyers typically pay?
- **Which countries** supply this product the most?
- **Is company XYZ a real buyer?** Do they have a transaction history?

These questions seem simple. But making a computer understand and answer them is surprisingly complex. Here is why.

## 1.2 Why This Is Not Like Googling Something

When you Google "dextrose," Google's job is to find *web pages* that mention the word dextrose. The pages already contain text that Google can read and index. The results are ranked by a mix of popularity (links pointing to the page) and text relevance.

Zarailink's problem is fundamentally different:

1. **The data is structured, not a web page.** A transaction record looks like this:
   ```
   seller = "Roquette Frères"
   buyer = "Muller & Phipps Pakistan Ltd"
   product = "Dextrose Monohydrate"
   qty_mt = 25.0
   usd_per_mt = 680.0
   date = 2024-03-15
   origin_country = "France"
   destination_country = "Pakistan"
   trade_type = "IMPORT"
   ```
   There is no body of text to search through — just numbers and proper nouns.

2. **The user's query is free-form natural language.** Users type things like:
   - `"find dextrose buyers in China paying above $600"`
   - `"who buys dextrose most, and which countries supply it"`
   - `"has Muller & Phipps purchased dextrose before"`
   - `"top 3 buyers for dextrose"`

   Each of these questions requires a *completely different* database operation.

3. **Trade product names are highly technical and have many synonyms.** "Dextrose" is the same as "Glucose," "D-glucose," "Blood sugar." "Dextrose Monohydrate" is a specific form. Users might type any of these. A simple text match fails.

4. **The user's vocabulary often differs from database vocabulary.** A user searches "sugar substitute" — the database has "Sucralose" and "Aspartame." A keyword search finds nothing; a *semantic* search understands the relationship.

5. **Queries contain many different *types* of intent embedded in one sentence.** "Find buyers in China for dextrose who pay above $600 and have bought in the last 6 months" contains: product (dextrose), geography (China), price constraint ($600), time constraint (6 months), and the fundamental intent (find buyers). The system must extract all of these simultaneously.

## 1.3 The Scale of the Problem

The Zarailink transaction database contains thousands of import records across hundreds of products, dozens of countries, and thousands of buyer/seller company names. A naive search that scans every record for every query would be:
- **Slow** — full table scans on large tables are expensive.
- **Inaccurate** — keyword match misses synonyms and catches unrelated matches.
- **Undifferentiated** — returning 10,000 results with no ranking is useless.

The system must be:
- **Fast** — P50 latency under 200ms, P99 under 400ms.
- **Accurate** — only relevant products, buyers, and suppliers.
- **Ranked** — the most useful result appears first (NDCG@10 ≥ 0.75).
- **Explainable** — users must understand why they see what they see.

This is exactly the problem that the field of **Information Retrieval (IR)** has spent 60+ years studying.

---

<a name="part-2"></a>
# PART 2: ZARAILINK'S ANSWER — THE MULTI-STAGE PIPELINE

## 2.1 The Core Idea: Decompose, Then Solve Each Sub-Problem

Modern search systems — from Google to Amazon to LinkedIn — decompose the search problem into multiple sequential stages. Each stage does one thing well, and passes its output to the next.

Zarailink's pipeline has 4 main stages with multiple ML-augmented sub-stages:

```
RAW QUERY (natural language text)
        │
        ▼
┌──────────────────────────────────────────────┐
│  STAGE 1: QueryInterpreter (Rule-based)      │
│  "What does the user want?"                  │
│  • Intent (BUY or SELL) via weighted scoring  │
│  • Entities: country, price, volume, time    │
│  • Query Family (F1-F9) classification       │
│  • Multi-intent detection (F9 splitting)     │
│                                              │
│  ┌─── 1B: SetFit Classifier ──────────┐     │
│  │  Overrides intent/family when       │     │
│  │  classifier confidence ≥ 0.70       │     │
│  │  Preserves SELL intent for F3-F8    │     │
│  └─────────────────────────────────────┘     │
│                                              │
│  ┌─── 1C: GLiNER NER ─────────────────┐     │
│  │  Fills gaps from regex extraction    │     │
│  │  Cleans quantity-polluted products   │     │
│  │  Zero-shot: no fine-tuning needed    │     │
│  └─────────────────────────────────────┘     │
└──────────────────────────────────────────────┘
        │ structured dict
        ▼
┌──────────────────────────────────────────────┐
│  STAGE 2: QueryMatcher (NLP / Hybrid)        │
│  "What product category matches?"            │
│                                              │
│  ┌─── 2A: HybridRetriever ────────────┐     │
│  │  BM25 (rank_bm25) keyword recall    │     │
│  │  + FAISS-HNSW (nomic-embed-text-v1) │     │
│  │  + Keyword icontains exact match     │     │
│  │  + Fuzzy trigram/edit-distance       │     │
│  │  + HS code prefix match             │     │
│  │  → RRF (k=60) fusion                │     │
│  └─────────────────────────────────────┘     │
│                                              │
│  ┌─── 2B: Cross-Encoder Re-Ranker ────┐     │
│  │  cross-encoder/ms-marco-MiniLM-L6-v2│     │
│  │  Re-scores top 15 → returns top 5   │     │
│  │  Blend: 60% CE + 40% RRF            │     │
│  └─────────────────────────────────────┘     │
│                                              │
│  ┌─── 2C: HyDE (optional) ────────────┐     │
│  │  Short F1 queries (≤4 words):       │     │
│  │  Generate hypothetical doc → blend   │     │
│  │  50% query vec + 50% HyDE vec        │     │
│  └─────────────────────────────────────┘     │
│  → ProductSubCategory IDs                    │
└──────────────────────────────────────────────┘
        │ subcategory IDs
        ▼
┌──────────────────────────────────────────────┐
│  STAGE 3: Aggregation                        │
│  "Get the actual data"                       │
│  • F1-F6: SupplierAggregator (ORM agg)       │
│  • F7: CountryComparator (country metrics)   │
│  • F8: EvidenceRetriever (raw transactions)  │
│  • OpenSearch fast path (if configured)      │
│  • CompanyProductStats table fast path        │
│  → raw candidate list                        │
└──────────────────────────────────────────────┘
        │ candidate dicts
        ▼
┌──────────────────────────────────────────────┐
│  STAGE 4: RankingEnsemble                    │
│  "Which results matter most?"                │
│  • Feature Extraction (15 features, v2)      │
│  • Heuristic Scoring (70%) per-family weights│
│  • LightGBM LTR v2 LambdaRank (30%)         │
│  • Supplier cross-encoder re-ranking         │
│  • Anomaly detection warnings                │
│  → ranked final list                         │
└──────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────┐
│  STAGE 5: Response & Caching                 │
│  • Semantic cache (Redis) write-through      │
│  • Market snapshot metadata                  │
│  • Clarification hints for ambiguous queries │
│  → JSON response to frontend                 │
└──────────────────────────────────────────────┘
```

## 2.2 A Concrete Example

Let's trace the query `"find dextrose buyers in China paying above $600"` through all stages.

**Stage 1 — QueryInterpreter (regex + scoring):**
```python
{
  "intent": "SELL",          # "find buyers" → user is selling
  "family": 4,               # price constraint detected (above $600)
  "product": "dextrose",     # after stripping "find buyers in" etc.
  "country_filter": ["China"],
  "price_floor": 600.0,
  "price_ceiling": None,
  "volume_mt": None,
  "time_range": None,
  "scope": "WORLDWIDE",
  "multi_intent": False,
  "classifier_confidence": 0.82,  # SetFit confirms F4_PRICE
  "ner_confidence": 0.95,         # GLiNER agrees on entities
  "ambiguous_query": False
}
```

**Stage 1B — SetFit:** Classifies as `F4_PRICE` with confidence 0.82 (≥ 0.70 threshold). Maps to `('BUY', 4)`, but because regex detected SELL intent, the SELL intent preservation fix keeps `intent='SELL'`.

**Stage 1C — GLiNER:** Extracts `product="dextrose"`, `origin_country="China"`, `price_floor=600`. All match regex — no gaps to fill.

**Stage 2A — HybridRetriever:**
- BM25: "dextrose" → `Dextrose` (rank 1, score 4.2)
- FAISS: nomic-embed-text-v1 encodes `"search_query: dextrose"` → cosine similarity 0.92 with `Dextrose`
- Keyword: `ProductSubCategory.objects.filter(name__icontains='dextrose')` → exact match, score=1.0
- RRF fusion: `Dextrose` gets score from all 3 lists = 3/(60+1) = 0.049, boosted 20x for exact match = 0.98

**Stage 2B — Cross-Encoder:** `cross-encoder/ms-marco-MiniLM-L6-v2` scores `("dextrose", "Dextrose")` → logit 8.5 (very high relevance). Top 5 returned.

**Stage 3 — SupplierAggregator:**
- intent=SELL + scope=WORLDWIDE → query `trade_type='IMPORT'` transactions
- Filter by `origin_country__in=['China']` and `usd_per_mt >= 600`
- Groups by buyer name, aggregates volume, price, shipment count
- **Output:** 12 buyer records with volume_fit scores

**Stage 4 — RankingEnsemble:**
- Extracts 15 features per candidate (8 original + 7 new)
- Applies family=4 weights: `price_fit` gets 3x, `log_price` gets -1.0
- Combines heuristic score (70%) + LTR v2 score (30%)
- Supplier cross-encoder re-ranks if enabled
- **Output:** sorted list of 12 buyers, best first

---

<a name="part-3"></a>
# PART 3: THE DATABASE — WHAT RAW DATA EXISTS

## 3.1 The Transaction Table

The foundation of everything is the `Transaction` Django model. Every search eventually turns into one or more queries against this table. Understanding its structure is essential.

Each row represents **one shipment** — a single consignment of goods. The key columns are:

| Column | Type | Example | What it means |
|--------|------|---------|---------------|
| `seller` | text | "Roquette Frères" | Who sent the goods |
| `buyer` | text | "Muller & Phipps Pakistan Ltd" | Who received the goods |
| `product_item` | FK | → ProductItem | What was shipped |
| `qty_mt` | decimal | 25.0 | Quantity in Metric Tonnes |
| `usd_per_mt` | decimal | 680.0 | Price per Metric Tonne in USD |
| `reporting_date` | date | 2024-03-15 | When the shipment was recorded |
| `origin_country` | text | "France" | Where goods came from |
| `destination_country` | text | "Pakistan" | Where goods went |
| `trade_type` | text | "IMPORT" | "IMPORT" or "EXPORT" |
| `tx_reference` | text | "TXN-2024-001" | Unique shipment ID |
| `shipping_agent` | text | "Maersk" | Freight forwarder (optional) |

## 3.2 The Critical Database Reality: IMPORT Records Only

**This is the single most important thing to understand about the database.**

The Zarailink database contains **only IMPORT records** — i.e., shipments where Pakistan was the *destination* (buying from the world). There are **no EXPORT records** (Pakistan selling to other countries).

This means:
- `origin_country` tells you **where the supplier is** (China, India, France, etc.)
- `destination_country` is always "Pakistan"
- `seller` is always the foreign supplier
- `buyer` is always a Pakistani company

This is not a bug — this is the nature of the government import data that Zarailink collected.

## 3.3 How Intent x Scope Maps to Database Queries

Because of this database reality, the system has to interpret "who are my buyers" (SELL intent from a Pakistani farmer) as: find the Pakistani companies importing this product — those are your potential customers.

The mapping is:

| User Intent | Scope | What They Want | DB Query |
|------------|-------|---------------|---------|
| SELL (I want to sell) | PAKISTAN | Find local Pakistani buyers | `IMPORT` records, grouped by `buyer`, filtered by `destination_country='Pakistan'` |
| SELL (I want to sell) | WORLDWIDE | Find international buyers | `EXPORT` records — **DON'T EXIST** → auto-fallback to PAKISTAN scope |
| BUY (I want to buy) | PAKISTAN | Find Pakistani suppliers | `EXPORT` records where `origin_country='Pakistan'` |
| BUY (I want to buy) | WORLDWIDE | Find global suppliers | `IMPORT` records, grouped by `seller` (the foreign suppliers) |

This mapping is implemented in `SupplierAggregator.get_suppliers_for_subcategories()`.

**SELL + WORLDWIDE fallback:** In `views.py`, when `intent='SELL'` and `scope='WORLDWIDE'`, the effective scope is forced to `'PAKISTAN'` before calling the aggregator. This prevents the aggregator from querying non-existent EXPORT records and returning 0 results.

## 3.4 Product Hierarchy

Products are organized in a 3-level hierarchy:

```
ProductCategory (e.g., "Chemicals")
    └── ProductSubCategory (e.g., "Dextrose")        ← NLP matches here
            └── ProductItem (e.g., "Dextrose Monohydrate")  ← variants
```

Search operates at the **SubCategory** level. Variants (ProductItems) are used for fine-grained filtering when the user is specific (e.g., "dextrose monohydrate" vs just "dextrose").

## 3.5 Current Database Coverage

The current database primarily contains food-grade ingredients: dextrose, lactose, maltodextrin, refined sugar, and related sugar derivatives. This means queries about products like palm oil, cotton, or wheat will return 0 results — not because the pipeline is broken, but because those products have no transaction data.

---

<a name="part-4"></a>
# PART 4: STAGE 1 — QUERYINTERPRETER: UNDERSTANDING WHAT YOU'RE ASKING

File: `backend/search/services/query_parser.py` — `class QueryInterpreter`

## 4.1 Rule-Based vs. Neural NLP: Why Rules Come First

There are two main approaches to NLP:

**1. Rule-based NLP:** A human expert writes patterns like "if the query contains 'who buys', classify intent as SELL." It's fast, predictable, debuggable, and requires no training data.

**2. Neural NLP:** A deep learning model is trained on examples and learns patterns automatically. More flexible, but harder to debug.

**Why Zarailink uses a hybrid approach:** The query interpreter starts with rule-based regex extraction (fast, predictable), then overlays two ML models:
- **SetFit** (Stage 1B): overrides intent/family when confident
- **GLiNER** (Stage 1C): fills entity gaps that regex missed

This layered approach means regex handles the 90% of queries that follow predictable patterns, while ML handles edge cases and novel phrasings.

## 4.2 The Full Parsing Pipeline

When a query arrives, `QueryInterpreter.parse()` runs this sequence:

```
Query Text
    │
    ▼
[Step 0] Multi-Intent Check (split by ';' or 'and'/'also')
    │
    ▼
[Step 1] Family Keyword Scanning (F6/F7/F8 detection)
    │
    ▼
[Step 2] Country Extraction (aliases + standard list + fuzzy)
    │
    ▼
[Step 3] Volume Extraction (regex: "100 MT", "50 kg")
    │
    ▼
[Step 4] Price Extraction (ceiling, floor, exact)
    │
    ▼
[Step 5] Time Extraction (quarter, year, relative)
    │
    ▼
[Step 6] Intent Scoring (BUY vs SELL phrase matching)
    │
    ▼
[Step 7] Product Extraction (what's left after removing everything)
    │
    ▼
[Step 8] Family Classification (F1-F8 priority rules)
    │
    ▼
[Step 9] F8 Special: Buyer Name Extraction + Cleanup
    │
    ▼
[Step 10] GLiNER NER: fill entity gaps (Stage 1C)
    │
    ▼
[Step 11] F7 Downgrade Guard + F7 Intent Override
    │
    ▼
[Step 12] SetFit Override (Stage 1B) — only for single-intent queries
    │
    ▼
Structured dict output
```

## 4.3 Step 0: Multi-Intent Detection

**What is multi-intent?** Sometimes a user asks two separate questions in one query:
- `"who buys dextrose most; show me country comparison"` — two distinct questions.
- `"find dextrose buyers in China and India"` — NOT two questions; China and India are additive filters.

**How it works:**

First, it splits on semicolons (`;`) — always a strong indicator of multiple questions.

If no semicolon, it looks for `and` or `also`. But splitting on every `and` would be wrong — "buyers in China and India" would get wrongly split. The rule:

> Split on 'and'/'also' **only if the right side has its own independent intent keyword** OR has a structural family keyword (F6/F7/F8).

```python
# From query_parser.py lines 98-116
has_intent = self._detect_intent_score(part)[0] != 'AMBIGUOUS'
has_structural_intent = (
    any(kw in part_lower for kw in self.FAM_7_KEYWORDS) or
    any(kw in part_lower for kw in self.FAM_8_KEYWORDS) or
    any(kw in part_lower for kw in self.FAM_6_KEYWORDS)
)
if has_intent or has_structural_intent:
    final_segments.append(current_segment)
    current_segment = part
else:
    current_segment += " and " + part  # Merge — additive filter
```

If multiple segments are found, each is parsed independently with `_parse_single()`, and the result is returned as a **Family 9 (multi-intent)** query.

## 4.4 Step 1: Family Keyword Scanning

Before extracting anything, the parser checks for keywords that strongly indicate a specific query family:

```python
is_rec = any(x in raw_query for x in self.FAM_6_KEYWORDS)    # F6
is_mkt = any(x in raw_query for x in self.FAM_7_KEYWORDS)    # F7
is_evid = (
    any(x in raw_query for x in self.FAM_8_KEYWORDS)         # F8
    or bool(re.search(r'\bhas\s+\S+(?:\s+\S+){0,4}\s+(?:purchased|bought)\b', raw_query))
)
```

**Family 6 keywords:** top, best, rank, suggest, recommend, highest, most, paying
**Family 7 keywords:** cheapest, lowest price, highest demand, compare, vs, which country, which countries, best market, country comparison, by country, etc.
**Family 8 keywords:** shipments, transactions, history, proof, verification, evidence, invoices, has purchased, has bought, etc.

## 4.5 Step 2: Country Extraction

The parser extracts country names using three methods in order of precision:

**Method 1: Alias Matching (Highest Precision)**
```python
COUNTRY_ALIASES = {
    "us": "USA", "u.s.": "USA", "united states of america": "USA", "america": "USA",
    "uae": "UAE", "u.a.e": "UAE", "emirates": "UAE",
    "uk": "UK", "u.k.": "UK", "britain": "UK",
    "ksa": "Saudi Arabia"
}
```
Aliases are sorted by length (longest first) so "united states of america" is matched before "america".

**Method 2: Standard Country List Matching**
A hardcoded list of 30 common trading partners is checked with word-boundary regex. Matched countries are removed from the remainder text.

**Method 3: Fuzzy Country Matching**
For tokens ≥ 4 characters that didn't match, `difflib.get_close_matches()` is called with cutoff=0.85. This catches typos like "Chnia" → "China".

## 4.6 Steps 3-5: Volume, Price, Time Extraction

**Volume:** Regex pattern `(\d+(?:,\d+)?(?:\.\d+)?)\s*(mt|tons|metric tons|kg|kilo|tonnes)`. Converts kg to MT by dividing by 1000. Used as a soft compatibility score, not a hard filter.

**Price Ceiling:** Patterns like "under $600", "below $600", "< $600", "less than $600"
**Price Floor:** Patterns like "above $600", "over $600", "> $600", "more than $600"
**Price Exact:** A number with currency symbol, treated as ceiling if no direction specified.

**Time:** Supports Q1-Q4, year ranges, "last N months", "from January to March". Converted to `(start_date, end_date)` pairs in `views.py`.

## 4.7 Step 6: Intent Detection (BUY vs SELL)

Uses **weighted keyword scoring**. Every word/phrase is checked against two vocabularies:

```python
BUY_SCORES = {
    "who sells": 5, "suppliers of": 5, "find suppliers": 5,
    "buy from": 5, "i want to buy": 5, "buying": 3, "imports": 2,
    "buy": 1, "purchase": 2, "sourcing": 3, "need": 2,
    "exporters": 3, "sellers": 3,  # foreign suppliers = BUY intent
}

SELL_SCORES = {
    "who buys": 5, "buyers for": 5, "find buyers": 5,
    "demand for": 5, "i want to sell": 5, "selling": 3,
    "sell": 1, "buyers": 3, "pay": 3, "buys": 5,
    "importers": 2,  # Pakistani companies that import = buyers = SELL intent
}
```

The intent with the higher total score wins. If tied, defaults to `BUY`.

## 4.8 Step 7: Product Extraction

After all entities have been removed from the text, and after intent/family/stopwords are stripped, **whatever remains is the product**.

```python
# Strip intent phrases (sorted longest-first)
for phrase in all_phrases:
    clean_text = re.sub(r'\b' + re.escape(phrase) + r'\b', '', clean_text)

# Strip family keywords (sorted longest-first to avoid fragmentation)
for w in all_fam_keywords:
    clean_text = re.sub(r'\b' + re.escape(w) + r'\b', '', clean_text)

# Strip stopwords
for sw in STOPWORDS:
    clean_text = re.sub(r'\b' + re.escape(sw.strip()) + r'\b', ' ', clean_text)

attributes['product'] = clean_text.strip()
```

**Corporate entity detection:** If tokens like "Ltd", "Inc", "Co", "Corp" are present, the text is split into company name (→ `counterparty_name`) and product.

## 4.9 Step 8: Family Classification

The family is assigned using a priority chain:

```python
if is_evid: f = 8           # Evidence keywords → always F8
elif is_mkt: f = 7          # Market keywords → F7
elif is_rec: f = 6          # Recommendation keywords → F6
elif price_ceiling or price_floor: f = 4  # Price filter → F4
elif time_range: f = 5      # Time filter → F5
elif volume_mt: f = 3       # Volume filter → F3
elif country_filter: f = 2  # Country filter → F2
else: f = 1                 # Nothing special → F1
```

**Priority:** F8 > F7 > F6 > F4 > F5 > F3 > F2 > F1. The most constraining filter determines the family.

## 4.10 Step 9: F8 Buyer Name Extraction

Family 8 queries need the buyer company name extracted precisely. Three patterns are tried on the **original-case** query:

**Pattern 1:** `"Has [BUYER] purchased/bought [product]"`
**Pattern 2:** `"shipments (from X) to [BUYER]"`
**Pattern 3:** `"evidence/invoices/history for [BUYER]"` — only matches if BUYER starts with uppercase (proper noun protection).

After extraction:
1. Countries within the buyer name (e.g., "Pakistan" in "Nestle Pakistan Ltd") are removed from `country_filter`
2. The buyer name is stripped from the product field
3. F8 noise words ("purchased", "before", "deal") are removed from product

## 4.11 Step 11: F7 Downgrade Guard + Intent Override

**Downgrade Guard:** If F7 was triggered only by ambiguous keywords ("cheapest", "compare", "vs") and fewer than 2 countries were extracted AND the query doesn't mention "country/countries", it's downgraded:
- Has price filter → F4
- Has country filter → F2
- Otherwise → F1

**Intent Override:** Phrases like "which country buys", "buyers by country" contain "buy/buys" (BUY indicator), but the user is actually asking about buyer *markets* — SELL intent. The code checks `BUYER_MARKET_PHRASES` and overrides `BUY → SELL` for F7 queries.

---

<a name="part-5"></a>
# PART 5: STAGE 1B — SETFIT INTENT CLASSIFIER

File: `backend/search/services/setfit_classifier.py`

## 5.1 What Is SetFit?

SetFit (Sentence Transformer Fine-tuning) is a framework for few-shot text classification. Unlike traditional classifiers that need thousands of labeled examples, SetFit can learn from as few as 8 examples per class using contrastive learning on sentence embeddings.

> **Tunstall, L., et al. (2022).** Efficient Few-Shot Learning Without Prompts. *arXiv:2209.11055.*

**Why SetFit for Zarailink?** When the system was built, only ~50 labeled query examples existed. SetFit's few-shot capability made it the ideal choice for intent classification without a large training set.

## 5.2 The Classification Labels

SetFit maps queries to 8 labels:

| Label | Intent | Family | Example Query |
|-------|--------|--------|--------------|
| BUY | BUY | 1 | "find sugar suppliers" |
| SELL | SELL | 2 | "who buys dextrose" |
| F3_VOLUME | BUY | 3 | "buyers for 100 MT rice" |
| F4_PRICE | BUY | 4 | "sugar under $500" |
| F5_TIME | BUY | 5 | "buyers last 6 months" |
| F6_TOPK | BUY | 6 | "top 5 exporters" |
| F7_COMPARE | BUY | 7 | "compare countries for sugar" |
| F8_EVIDENCE | BUY | 8 | "has Nestle purchased sugar" |

## 5.3 When SetFit Fires

SetFit only overrides the regex result when:
1. The model is loaded and ready (`clf.is_ready()`)
2. Confidence ≥ 0.70 (`CONFIDENCE_THRESHOLD`)
3. The label maps to a known family (`sf_label in SETFIT_TO_FAMILY`)
4. Query is single-intent (not F9)

## 5.4 The SELL Intent Preservation Fix

**The bug:** SetFit's filter-only classes (F3-F8) all default to `intent='BUY'` in the mapping table. This means a query like `"I want to sell 500 MT of refined sugar"` would be:
1. Regex: detects SELL intent (sell_score=6)
2. SetFit: classifies as F3_VOLUME with confidence 0.82
3. **Without fix:** SetFit maps F3_VOLUME → `('BUY', 3)`, overriding the correct SELL intent

**The fix (query_parser.py lines 164-168):**
```python
if sf_label not in ('BUY', 'SELL') and result.get('intent') == 'SELL':
    sf_intent = 'SELL'
```

For filter-only classes (F3-F8), SetFit only classifies the *structure* of the query (volume, price, time, etc.), not the buy/sell direction. When regex confidently detected SELL, the fix preserves it.

## 5.5 Model Details

- **Base model:** Sentence-BERT fine-tuned on trade query pairs
- **Model directory:** `backend/search/models/setfit_intent_classifier/`
- **Required files:** `config.json`, `model_head.pkl`, `metadata.json`
- **Lazy-loaded singleton:** First prediction takes ~2s (model load), subsequent predictions ~5ms
- **Failure is non-fatal:** If SetFit crashes or is unavailable, the pipeline continues with regex-only parsing

---

<a name="part-6"></a>
# PART 6: STAGE 1C — GLINER NAMED ENTITY RECOGNITION

File: `backend/search/services/ner_extractor.py`

## 6.1 What Is GLiNER?

GLiNER is a **zero-shot Named Entity Recognition** model. Traditional NER systems (like spaCy's) recognize fixed entity types (PERSON, ORG, LOCATION). GLiNER can recognize *any* entity type — you just provide the label names at inference time.

Model: `urchade/gliner_medium-v2.1` (~450 MB, ~30ms per query on CPU)

## 6.2 Entity Labels

GLiNER extracts 10 entity types from trade queries:

| Label | Example | What it captures |
|-------|---------|-----------------|
| product | "dextrose anhydrous" | Commodity/ingredient name |
| quantity | "50", "hundred" | Numeric amount |
| unit | "MT", "metric tons" | Measurement unit |
| origin_country | "China", "Brazil" | Country of origin |
| destination_country | "Pakistan" | Import destination |
| price_ceiling | "$400" | Upper price bound |
| price_floor | "above $300" | Lower price bound |
| hs_code | "1702.11" | HS trade classification code |
| company_name | "Nestle", "Al Khaleej" | Organization name |
| time_period | "Q1 2024", "last 6 months" | Temporal reference |

## 6.3 How GLiNER Fills Gaps

GLiNER runs **after** all regex extraction steps. It only fills fields that regex left as None:

```python
regex_aligned = {
    'product':        None if _prod_is_qty_polluted else _raw_prod,
    'quantity':       attributes.get('volume_mt'),
    'origin_country': attributes['country_filter'][0] if attributes['country_filter'] else None,
    # ... etc
}
merged = extractor.merge_with_regex(gliner_result, regex_aligned)
```

Regex results **always take precedence** when both sources produce a value.

## 6.4 The Quantity-Polluted Product Fix

**The bug:** When a user says "fifty metric tons dextrose monohydrate", regex extracts `volume_mt=50` correctly but leaves the full text "fifty metric tons dextrose monohydrate" as the product. GLiNER would extract a clean `product="dextrose monohydrate"`, but since `regex_aligned['product']` was non-None, GLiNER couldn't override it.

**The fix (query_parser.py lines 532-541):**
```python
_QUANTITY_WORDS_SET = {'zero','one','two','three','four','five','six','seven',
                       'eight','nine','ten','twenty','thirty','forty','fifty',
                       'sixty','seventy','eighty','ninety','hundred','thousand',
                       'million','dozen','metric','tons','ton','mt','kg','kgs'}

_raw_prod = attributes.get('product') or None
_prod_is_qty_polluted = bool(
    _raw_prod and _raw_prod.lower().split()[0] in _QUANTITY_WORDS_SET
)
regex_aligned = {
    'product': None if _prod_is_qty_polluted else _raw_prod,
    ...
}
```

If the first word of the extracted product is a quantity word (like "fifty", "metric", "tons"), the product is treated as None in the regex alignment, allowing GLiNER's cleaner extraction to take over.

## 6.5 NER Confidence and Ambiguity

GLiNER returns a confidence score per extraction. If overall NER confidence drops below 0.40, the query is flagged as `ambiguous_query=True`, and the response includes a `clarification_hint` suggesting the user be more specific.

---

<a name="part-7"></a>
# PART 7: STAGE 2 — HYBRID RETRIEVAL: BM25 + FAISS-HNSW + RRF

File: `backend/search/services/retrieval.py` — `class HybridRetriever`

## 7.1 The Problem: Bridging the Vocabulary Gap

After Stage 1, we have a clean product term like `"dextrose"`. Now we must find which entries in the `ProductSubCategory` table it corresponds to.

This is non-trivial because of the **vocabulary gap**:

| User Types | Database Has |
|-----------|-------------|
| dextrose | Dextrose |
| glucose | Dextrose (same thing!) |
| blood sugar | Dextrose |
| dextrse | Dextrose (typo) |
| 17023000 | Dextrose (HS code match) |

The solution is **hybrid retrieval**: five complementary methods, fused using Reciprocal Rank Fusion (RRF).

## 7.2 The Five Retrieval Methods

### Method 1: BM25 Keyword Search

BM25 (Best Match 25) is a probabilistic ranking function that extends TF-IDF:

```
BM25(q, d) = Σ IDF(qi) × (f(qi, d) × (k1 + 1)) / (f(qi, d) + k1 × (1 - b + b × |d|/avgdl))
```

Where:
- `IDF(qi)` = Inverse Document Frequency (rare terms matter more)
- `f(qi, d)` = Term frequency in document
- `k1` = Saturation parameter (default 1.5)
- `b` = Length normalization (default 0.75)
- `|d|/avgdl` = Document length relative to average

**Implementation:** Uses `rank_bm25.BM25Okapi` library. Documents are tokenized ProductSubCategory names + ProductItem names + HS codes. Top 20 results, filtered by `MIN_BM25_SCORE = 0.1` (relative to max score).

> **Robertson, S. E., & Zaragoza, H. (2009).** The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval.*

### Method 2: FAISS-HNSW Dense Retrieval

**FAISS** (Facebook AI Similarity Search) provides efficient nearest-neighbor search for dense vectors.

**HNSW** (Hierarchical Navigable Small World) is a graph-based index that provides approximately nearest-neighbor search in O(log N) time:

```python
faiss_idx = faiss.IndexHNSWFlat(dim, 32)    # M=32 neighbors per node
faiss_idx.hnsw.efConstruction = 200          # build-time precision
faiss_idx.hnsw.efSearch = 50                 # query-time precision
```

**Embedding model: nomic-embed-text-v1** (768-dimensional)

nomic-embed-text-v1 is a modern sentence embedding model that requires **task-type prefixes**:
- Index documents: `"search_document: Dextrose Monohydrate 17023000"`
- Query encoding: `"search_query: dextrose"`

This asymmetric encoding allows the model to optimize differently for queries (short, interrogative) vs documents (descriptive, longer).

```python
class _NomicModel:
    @classmethod
    def get(cls):
        if cls._instance is None:
            from sentence_transformers import SentenceTransformer
            cls._instance = SentenceTransformer(
                'nomic-ai/nomic-embed-text-v1',
                trust_remote_code=True,
                device='cpu',
                model_kwargs={'low_cpu_mem_usage': False},
            )
        return cls._instance
```

**Fallback:** If nomic-embed-text-v1 is unavailable, falls back to `all-MiniLM-L6-v2` (384-dimensional).

**Threshold:** Cosine similarity < 0.35 is discarded (`MIN_FAISS_SCORE`).

> **Johnson, J., Douze, M., & Jégou, H. (2019).** Billion-scale similarity search with GPUs. *IEEE Transactions on Big Data.*

### Method 3: Keyword Exact Match

Direct Django ORM `icontains` lookup for high-precision:

```python
subcat_hits = ProductSubCategory.objects.filter(name__icontains=query)
item_hits = ProductItem.objects.filter(name__icontains=query)
```

Scoring:
- Exact match (name == query): score = 1.0
- Prefix match: score = 0.98
- Substring: score = 0.95 × length_ratio

### Method 4: Fuzzy Trigram + Edit Distance

Fires only when BM25 and keyword both return nothing (typos like "suag" → "sugar"). Uses:
- **Trigram Jaccard similarity:** Compare character trigrams of query and each product name
- **Levenshtein edit distance:** Catch single-character transpositions
- **Prefix bonus:** +0.3 if a product token starts with the query

Threshold: combined score > 0.25.

### Method 5: HS Code Prefix Matching

If the query looks like an HS code (`^\d{4}[\.\d]*$`), directly look up subcategories by `hs_code__startswith`.

## 7.3 Reciprocal Rank Fusion (RRF)

RRF combines multiple ranked lists without needing score normalization:

```
RRF_score(d) = Σ_i  1 / (k + rank_i(d))
```

Where `k=60` (bias constant) and `rank_i(d)` is the rank of document d in list i. If a document doesn't appear in a list, it contributes 0.

**Why RRF?** Different retrieval methods produce scores on incompatible scales (BM25 scores range 0-50, cosine similarity 0-1). RRF only uses ranks, not scores, so no normalization is needed.

> **Cormack, G. V., Clarke, C. L., & Buettcher, S. (2009).** Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods. *SIGIR 2009.*

**Exact-match boost:** After RRF, any keyword exact match (score=1.0) gets its RRF score multiplied by 20x. This ensures exact matches always rank above partial/semantic matches.

## 7.4 The Pre-Built Index (search_index_v2.pkl)

The index is a pickled dict containing:

```python
{
    'ids': [42, 43, ...],           # ProductSubCategory IDs
    'names': ["Dextrose", ...],     # Human-readable names
    'hs_codes': ["17023000", ...],  # HS codes
    'documents': [...],             # Full text (name + HS + item names)
    'bm25': BM25Okapi(...),         # Fitted BM25 index
    'faiss_idx': faiss.IndexHNSWFlat(...),  # HNSW index
    'embeddings': np.ndarray(...),  # (n, 768) nomic embeddings
    'model_name': 'nomic',          # Which model was used
    'embedding_dim': 768,
    'n_docs': n,
}
```

Built by `build_index()` or `python manage.py build_index`. Persisted at `backend/search_index_v2.pkl`. Loaded lazily as a class-level singleton in `HybridRetriever`.

---

<a name="part-8"></a>
# PART 8: STAGE 2B — CROSS-ENCODER RE-RANKING

File: `backend/search/services/cross_encoder.py`

## 8.1 Why a Cross-Encoder After Retrieval?

The hybrid retriever uses **bi-encoder** models — query and document are encoded independently, then compared with dot product/cosine similarity. This is fast but less accurate than models that see both texts together.

A **cross-encoder** concatenates query + document and processes them through a single transformer. It can model fine-grained interactions (word-level attention) between query and document, at the cost of being slower.

```
Bi-encoder:    encode(query) ⊙ encode(document)     → fast, O(1)
Cross-encoder: classify(query + [SEP] + document)    → slow, O(n²)
```

The strategy: retrieve broadly with bi-encoder (cheap), then re-rank top candidates with cross-encoder (expensive but accurate).

## 8.2 The Model

**Model:** `cross-encoder/ms-marco-MiniLM-L6-v2`
- 6-layer MiniLM fine-tuned on MS MARCO passage ranking dataset
- ~22 MB model, ~5ms to score 15 pairs on CPU
- Output: unbounded logits (higher = more relevant)

## 8.3 How Re-Ranking Works

```python
TOP_K_RETRIEVE = 15   # get 15 from hybrid retriever
TOP_K_RETURN = 5      # return top 5 after CE re-ranking
BLEND_ALPHA = 0.6     # 60% CE score + 40% RRF score
```

1. HybridRetriever returns 15 candidates
2. Cross-encoder scores each (query, subcategory_name) pair
3. CE scores are clamped to [-10, 10] and min-max normalized to [0, 1]
4. Final score = `0.6 * ce_normalized + 0.4 * rrf_normalized`
5. Top 5 by final score are returned

**Feature flag:** `SEARCH_USE_CROSS_ENCODER` in settings.py (default True). If disabled, hybrid retriever's order is used as-is.

---

<a name="part-9"></a>
# PART 9: STAGE 2C — HYDE: HYPOTHETICAL DOCUMENT EMBEDDINGS

File: `backend/search/services/hyde.py`

## 9.1 The Short Query Problem

Short queries like "sugar" or "dextrose" produce generic embeddings — the vector space can't distinguish between "sugar as a commodity" and "sugar in a medical context." This leads to poor FAISS recall for F1 discovery queries.

## 9.2 How HyDE Works

HyDE generates a **hypothetical document** — what an ideal search result would look like — and uses its embedding to enhance the query vector.

> **Gao, L., Ma, X., Lin, J., & Callan, J. (2022).** Precise Zero-Shot Dense Retrieval without Relevance Labels. *arXiv:2212.10496.*

```
Query: "sugar"
    ↓
HyDE generates: "ABC Trading Co. is a major sugar supplier based in Brazil.
                  They export 5000 MT of refined cane sugar annually to
                  Pakistan and the Middle East at competitive prices."
    ↓
Encode hypothetical doc with nomic-embed-text-v1
    ↓
final_vec = 0.5 * query_vec + 0.5 * hyde_vec   (L2-normalized)
```

## 9.3 When HyDE Fires

HyDE is applied **only** when:
- `family == 1` (generic discovery, no structural constraints)
- Query has ≤ 4 words
- `SEARCH_USE_HYDE = True` in settings

## 9.4 Generation Sources

1. **GPT-4o-mini** via OpenAI API (if `OPENAI_API_KEY` is set)
2. **Template-based fallback** (no API key needed) — fills a template with the query product name

Results are cached in-memory (query_text → hypothetical_text) to avoid repeat LLM calls.

---

<a name="part-10"></a>
# PART 10: STAGE 3 — AGGREGATION: GETTING THE DATA

File: `backend/search/services/aggregation.py`

## 10.1 The Three Aggregation Modules

Once we have `subcategory_ids` from Stage 2, different query families need different data:

| Family | Module | What it Returns |
|--------|--------|----------------|
| F1-F6 | `SupplierAggregator` | Aggregated buyer/supplier profiles |
| F7 | `CountryComparator` | Per-country trade metrics |
| F8 | `EvidenceRetriever` | Raw transaction records for a specific buyer |

## 10.2 SupplierAggregator: The Core Engine

### 10.2.1 Fast Paths

Before running the full ORM aggregation, two fast paths are checked:

1. **OpenSearch fast path** (`SEARCH_USE_OPENSEARCH=True`): If OpenSearch is configured, queries are run against the pre-indexed OpenSearch cluster. This avoids hitting PostgreSQL for read-heavy aggregation queries.

2. **CompanyProductStats table**: A pre-computed materialized view containing per-(company, subcategory) aggregate statistics. If the stats table has data for the requested subcategories, it's used instead of running live aggregation.

### 10.2.2 Intent x Scope Routing

```python
if intent == 'SELL':
    if scope == 'PAKISTAN':
        queryset = queryset.filter(trade_type='IMPORT', destination_country='Pakistan')
        target_field = 'buyer'
    else:  # WORLDWIDE — auto-downgraded to PAKISTAN in views.py
        queryset = queryset.filter(trade_type='EXPORT')
        target_field = 'buyer'
else:  # BUY
    if scope == 'PAKISTAN':
        queryset = queryset.filter(trade_type='EXPORT', origin_country='Pakistan')
        target_field = 'seller'
    else:  # WORLDWIDE
        queryset = queryset.filter(trade_type='IMPORT')
        target_field = 'seller'
```

### 10.2.3 Database Aggregation

```python
results = queryset.values(target_field, country_field).annotate(
    total_volume=Sum('qty_mt'),
    avg_price=Avg('usd_per_mt'),
    shipment_count=Count('id'),
    last_shipment_date=Max('reporting_date'),
    max_shipment_vol=Max('qty_mt'),
    avg_shipment_vol=Avg('qty_mt')
).order_by('-total_volume')
```

### 10.2.4 Volume Compatibility Scoring

When the user specifies a volume, candidates are scored:

```python
single_match = min(mss / V, 1.0)      # Can they handle one shipment of size V?
capacity_match = min(total / V, 1.0)   # Total business scale
avg_match = min(avg / V, 1.0)          # Typical order similarity

vol_score = 0.5 * single_match + 0.3 * capacity_match + 0.2 * avg_match
```

Labels: Strong (0.8+), Good (0.5+), Partial (0.3+), Low (<0.3)

**Soft floor:** Candidates with `max_shipment < 0.3*V AND total < 0.5*V` are excluded. This prevents extreme mismatches while keeping borderline candidates.

## 10.3 CountryComparator: Family 7 Market Intelligence

Groups IMPORT transactions by `origin_country` and aggregates:
- `total_volume`, `avg_price`, `supplier_count`, `shipment_count`, `last_active`
- Year-over-Year growth (comparing last 365 days vs 366-730 days ago)
- Top 3 suppliers per country
- Static `MARKET_ENTRY_NOTES` (tariff tiers, lead times, packaging requirements)

## 10.4 EvidenceRetriever: Family 8 Transaction Verification

Uses a **4-step buyer name matching chain**:

1. **Exact match** (`iexact`): Case-insensitive exact
2. **Partial match** (`icontains`): Substring
3. **And/& normalization**: "Muller and Phipps" ↔ "Muller & Phipps"
4. **Fuzzy suggestion** (`difflib.get_close_matches`, cutoff=0.55): Suggests 5 similar names

Returns:
- `transactions`: Raw transaction list (most recent first)
- `buyer_summary`: Aggregate stats with `verification_status` ("Verified" if ≥3 shipments) and `repeat_buyer` flag (months_active ≥ 3 OR shipment_count ≥ 5)
- `similar_buyers`: Fuzzy suggestions if buyer not found

---

<a name="part-11"></a>
# PART 11: STAGE 4 — RANKINGENSEMBLE: LIGHTGBM LTR V2

File: `backend/search/services/ranking_ltr.py`

## 11.1 Why Ranking Is a Separate Problem

After Stage 3, we have a list of candidates. The question is: **in what order should they be shown?**

A buyer with massive volume but last purchased 3 years ago is less useful than a smaller but active buyer. Ranking is a **multi-objective optimization** balancing volume, price match, recency, frequency, country match, and more.

## 11.2 The 15 Features (v2)

The `FeatureExtractor` converts each candidate into a vector of 15 numbers:

### Original 8 Features

| # | Feature | Computation | Why |
|---|---------|------------|-----|
| 1 | `log_volume` | `log1p(total_volume_mt)` | Log-compresses heavy-tailed distribution |
| 2 | `log_price` | `log1p(avg_price_usd_mt)` | Same compression for prices |
| 3 | `shipment_freq` | Raw shipment count | Captures buying regularity |
| 4 | `inv_recency` | `1 / (days_since_last + 1)` | Penalizes stale buyers |
| 5 | `volume_fit_score` | Strong=3, Good=2, Partial=1, Low=0 | Volume compatibility |
| 6 | `scope_match` | 1.0 (constant) | Retrieval already filtered by scope |
| 7 | `country_match` | 1.0 exact / 0.5 neutral / 0.0 mismatch | Country alignment |
| 8 | `price_fit` | 1.0 under ceiling / 0.5 neutral / 0.0 over | Price compatibility |

### New 7 Features (Phase 3-G)

| # | Feature | Computation | Why |
|---|---------|------------|-----|
| 9 | `recency_decay_volume` | `volume * exp(-0.001 * days_ago)` | Penalizes dormant high-volume companies |
| 10 | `trade_diversity_score` | `log1p(unique_subcategories)` | Multi-product traders are more established |
| 11 | `country_diversity_score` | `log1p(unique_countries)` | International reach indicator |
| 12 | `bm25_score` | BM25 score from retrieval | Product relevance signal from Stage 2 |
| 13 | `dense_similarity` | Cosine similarity from FAISS | Semantic relevance signal from Stage 2 |
| 14 | `entity_confidence` | 1.0 resolved / 0.5 singleton | Entity resolution quality |
| 15 | `volume_trend` | `(vol_6mo - vol_prev_6mo) / prev` clamped ±2 | Growing vs declining buyers |

## 11.3 FAMILY_WEIGHTS: Per-Family Ranking Priorities

```python
FAMILY_WEIGHTS = {
    1: {'volume_fit': 1.5, 'log_volume': 1.0, 'shipment_freq': 1.0, 'inv_recency': 1.0, 'country_match': 1.0},
    2: {'country_match': 3.0, 'volume_fit': 1.0, 'log_volume': 1.0, 'inv_recency': 0.5},
    3: {'volume_fit': 3.0, 'log_volume': 1.0, 'inv_recency': 0.5},
    4: {'price_fit': 3.0, 'log_price': -1.0, 'volume_fit': 1.0},
    5: {'inv_recency': 3.0, 'shipment_freq': 1.5, 'volume_fit': 1.0},
    7: {'log_volume': 1.0, 'inv_recency': 1.0, 'country_match': 2.0, 'shipment_freq': 1.0},
    9: {'volume_fit': 1.0, 'log_volume': 1.0, 'inv_recency': 1.0, 'shipment_freq': 1.0, 'country_match': 1.0},
}
```

F1 = balanced, F2 = country dominates, F3 = volume dominates, F4 = price dominates (and `log_price` gets negative weight — higher price hurts), F5 = recency dominates.

## 11.4 LightGBM LambdaRank

**LightGBM** is an efficient gradient boosting framework by Microsoft.

> **Ke, G., et al. (2017).** LightGBM: A Highly Efficient Gradient Boosting Decision Tree. *NeurIPS 2017.*

The `lambdarank` objective directly optimizes NDCG by computing gradient updates weighted by |ΔNDCG| — how much would swapping two items change NDCG?

**LTR v2 model** (`lgbm_ltr_v2.txt`):
- Trained on 62 queries with 460 labeled pairs
- 15 features (expanded from 8 in v1)
- Holdout performance: **NDCG@5 = 0.987, NDCG@10 = 0.992**
- Falls back to `lgbm_ltr.txt` (v1, 8 features) if v2 not found

**Lineage:**
```
RankNet (Burges 2005) → LambdaRank (Burges 2006) → LambdaMART (Burges 2010) → LightGBM lambdarank (Ke 2017)
```

## 11.5 The 70/30 Ensemble

```python
final_score = (heuristic_score * 0.7) + (ltr_score * 0.3)
```

When the LTR model is trained on pseudo-labels (not real click data), the 70% heuristic weight ensures stability. As real training data accumulates, the LTR weight can be increased.

If the model file doesn't exist, `LTRModel.predict()` returns all zeros → ranking is entirely heuristic-driven.

## 11.6 Pseudo-Labels for Cold Start

Without click data, the heuristic scoring function generates synthetic relevance labels:

```python
if score > 15: return 4  # Highly relevant
if score > 10: return 3  # Relevant
if score > 5:  return 2  # Somewhat relevant
if score > 2:  return 1  # Marginally relevant
return 0                  # Not relevant
```

This "teacher-student" approach bootstraps the LTR model until real user interaction data is available.

## 11.7 Supplier Cross-Encoder Re-Ranking

After LTR ranking, an optional supplier-level cross-encoder (`SEARCH_USE_SUPPLIER_RERANKER`) can re-rank the final results by scoring (query, supplier_profile) pairs.

## 11.8 Anomaly Detection

After ranking, each result is checked against an anomaly detector that flags companies with suspicious price/volume patterns (> 30% suspicious transactions → adds `data_warning: "High price variance — verify independently"`).

---

<a name="part-12"></a>
# PART 12: THE 9 QUERY FAMILIES — COMPLETE REFERENCE

The 9 query families are based on the **Zarailink Seller Query Framework** — a classification of the fundamental questions a Pakistani agricultural seller or buyer might ask.

---

## Family 1 (F1): Simple Buyer Discovery

**"Who buys this product?"**

**Example queries:**
- `"find dextrose buyers"`
- `"who buys rice in Pakistan"`
- `"buyers for sugar"`

**Pipeline:** Parse → Match product → Aggregate all IMPORT buyers → Rank with balanced F1 weights → Return full list.

**Key:** Broadest query type. No filters. Ranking balances volume, recency, frequency equally.

---

## Family 2 (F2): Country-Filtered Buyer Discovery

**"Who buys this product from [COUNTRY]?"**

**Example queries:**
- `"dextrose buyers in China"`
- `"rice importers from India"`

**Pipeline:** Same as F1 but `country_filter` applied. Ranking: `country_match` gets 3x weight.

**Note:** If query says "sugar importers Pakistan" — `country_filter=['Pakistan']` but Pakistan is the destination, not origin. This can return 0 results with IMPORT-only data. Known limitation.

---

## Family 3 (F3): Volume-Aware Buyer Discovery

**"Who can handle a [VOLUME] order?"**

**Example queries:**
- `"find buyers for 100 MT of dextrose"`
- `"who buys 50 tons of rice"`

**Pipeline:** Same as F1 but soft volume floor applied + volume compatibility scoring. Ranking: `volume_fit` gets 3x weight.

---

## Family 4 (F4): Price-Constrained Buyer Discovery

**"Who pays above/below [PRICE]?"**

**Example queries:**
- `"dextrose buyers paying above $600"`
- `"buyers under $700 for rice"`

**Pipeline:** Price filter is a **hard** SQL filter (`usd_per_mt >= 600` or `<= 700`). Ranking: `price_fit` gets 3x, `log_price` gets -1.0 (lower price penalized for F4).

---

## Family 5 (F5): Time-Constrained / Recency-Based

**"Who has bought recently?"**

**Example queries:**
- `"dextrose buyers last 6 months"`
- `"who bought rice in Q1 2025"`

**Pipeline:** Time filter at SQL level (`reporting_date BETWEEN`). Ranking: `inv_recency` gets 3x, `shipment_freq` 1.5x.

---

## Family 6 (F6): Recommendation / Shortlist

**"Who are the TOP/BEST buyers?"**

**Example queries:**
- `"top 5 buyers for dextrose"`
- `"best 3 buyers for rice"`

**Pipeline:** Full F1 pipeline runs first, then truncated to top N results. Default N=5 if not specified. Ranking: same as F1.

**Top-N extraction:** `re.search(r'\b(?:top|best|first|suggest)\s+(\d+)\b', query)`

---

## Family 7 (F7): Country Comparison / Market Intelligence

**"Which countries have the most demand?"**

**Example queries:**
- `"which countries buy the most dextrose"`
- `"compare dextrose markets by country"`

**Pipeline:** Skips SupplierAggregator entirely. Routes to `CountryComparator.compare_countries()`. Returns country-level aggregates, YoY growth, top 3 suppliers per country, market entry notes.

**Output format:** Completely different from F1-F6 — returns countries, not company profiles.

**F7 downgrade guard:** If triggered only by "cheapest"/"compare" with only 1 country and no "country/countries" word, downgrades to F4/F2/F1.

**F7 intent override:** "which country buys" contains "buys" (BUY signal) but user is asking about buyer *markets* (SELL perspective). Override: BUY → SELL when `BUYER_MARKET_PHRASES` detected.

---

## Family 8 (F8): Transaction Evidence / Buyer Verification

**"Has [COMPANY] purchased this product before?"**

**Example queries:**
- `"has Muller and Phipps purchased dextrose before"`
- `"show shipments to Nestle Pakistan"`

**Pipeline:** Skips aggregator + ranking. Routes to `EvidenceRetriever.get_transaction_evidence()`. Returns raw transaction rows sorted by date.

**Key details:**
- 3 buyer name extraction patterns (Step 9)
- 4-step fuzzy buyer name matching
- `verification_status = "Verified"` if ≥ 3 shipments
- F8 with buyer name but no product: searches across all products for that buyer

---

## Family 9 (F9): Hybrid Multi-Intent

**"Answer multiple questions at once"**

Covered in the next section.

---

<a name="part-13"></a>
# PART 13: FAMILY 9 — HYBRID MULTI-INTENT QUERIES

## 13.1 Detection and Splitting

Queries are split on:
1. Semicolons (`;`) — always split
2. `"and"` / `"also"` — only if the right side has an independent intent keyword OR a structural F6/F7/F8 keyword

## 13.2 Context Product Carry-Over

The second clause often uses anaphora: "who are the top buyers **there**?" The parser inherits the product from the first non-trivial sub-intent when `len(sub.product) <= 3`.

```python
context_product = next(
    (s.get('product', '') for s in sub_intents if len(s.get('product', '')) > 3), ''
)
for sub in sub_intents:
    if context_product and len(sub.get('product', '')) <= 3:
        sub = {**sub, 'product': context_product}
```

## 13.3 Section Routing

Each sub-intent is processed by `_run_sub_intent()`:
- F7 → `CountryComparator.compare_countries()`
- F8 → `EvidenceRetriever.get_transaction_evidence()`
- F1-F6 → `SupplierAggregator` + `RankingEnsemble`

The SELL+WORLDWIDE fallback is applied per sub-intent.

## 13.4 Response Structure

```json
{
  "type": "multi_intent",
  "family": 9,
  "sections": [
    {"label": "Country Comparison", "family": 7, "country_comparison": [...]},
    {"label": "Top Recommendations", "family": 6, "results": [...]}
  ]
}
```

Each section has a human-readable label and is rendered independently by the frontend.

---

<a name="part-14"></a>
# PART 14: SUPPORTING INFRASTRUCTURE

## 14.1 Semantic Cache (Redis)

File: `backend/search/services/semantic_cache.py`

**Purpose:** Cache search responses to avoid re-running the full pipeline for repeated or semantically similar queries.

- **Backend:** Redis (127.0.0.1:6379) when available, in-memory dict fallback otherwise
- **Key:** Query text (normalized lowercase)
- **TTL:** Configurable, typically 1 hour
- **Invalidation:** Cache is bypassed with `?no_cache=1` query parameter
- **Semantic matching:** Uses embedding similarity to match queries like "dextrose buyers" and "find buyers for dextrose" to the same cached result

## 14.2 Entity Resolution Infrastructure

Files: `backend/search/services/entity_resolution.py`, `backend/trade_data/models.py` (`CanonicalCompanyLink`)

**Purpose:** Company names in customs data are inconsistent. "Muller & Phipps", "M&P Pakistan Ltd", "Muller and Phipps Pk" may all be the same company. Entity resolution groups these into canonical entities.

**Infrastructure ready:**
- `CanonicalCompanyLink` model stores (raw_name → canonical_name) mappings
- Entity confidence feature (1.0 resolved, 0.5 singleton) feeds into LTR ranking
- Not yet fully populated — requires running the entity resolution pipeline

## 14.3 OpenSearch Integration

**Feature flag:** `SEARCH_USE_OPENSEARCH` in settings.py

When enabled, the `SupplierAggregator` attempts to query an OpenSearch cluster before falling back to PostgreSQL. OpenSearch provides faster aggregation for read-heavy workloads.

## 14.4 CompanyProductStats Materialized View

A pre-computed table containing per-(company, subcategory) aggregate statistics. Updated periodically via management command. Provides a fast path for aggregation queries without hitting the full Transaction table.

---

<a name="part-15"></a>
# PART 15: EVALUATION FRAMEWORK

File: `backend/evaluation/evaluate.py`

## 15.1 Metrics Computed

| Metric | What it Measures | Current Value |
|--------|-----------------|---------------|
| **NDCG@10** | Ranking quality (position-aware) | **0.9325** |
| **NDCG@5** | Ranking quality (top 5 only) | 0.92+ |
| **MRR@10** | How quickly first relevant result appears | **0.9853** |
| **Recall@10** | % of all relevant items found in top 10 | **0.7798** |
| **Precision@5** | % of top 5 results that are relevant | 0.85+ |
| **MAP@10** | Average precision across rank positions | 0.80+ |

## 15.2 Golden Judgments

The evaluation uses **Cranfield-style evaluation**: a fixed set of queries with manually-judged relevance labels.

- **Golden queries:** `backend/evaluation/golden_queries.json` — 90 queries across all 9 families
- **Golden judgments:** `backend/evaluation/golden_judgments.json` — per-query relevance scores (0-3) for each result
- **Queries evaluated:** 68 (22 excluded due to no ground truth — standard Cranfield practice)

## 15.3 Evaluation Targets

```python
TARGETS = {
    'ndcg@5':      0.40,
    'ndcg@10':     0.38,
    'mrr@5':       0.45,
    'mrr@10':      0.43,
    'recall@10':   0.45,
    'precision@5': 0.40,
    'map@10':      0.35,
}
```

All current targets: **PASSED**.

## 15.4 Regression Guard

NDCG@10 must not drop more than 0.02 between successive evaluations. If it does, the evaluation exits with code 1 (failing the quality gate).

## 15.5 Phase Progression

| Phase | NDCG@10 | MRR@10 | Recall@10 | Key Change |
|-------|---------|--------|-----------|------------|
| Phase 0 (Baseline) | 0.021 | 0.025 | 0.020 | Simple keyword icontains |
| Phase 1 (Entity Res.) | 0.43 | 0.45 | 0.31 | Entity resolution + basic ranking |
| Phase 2 (Hybrid RRF) | 0.701 | 0.720 | 0.559 | BM25 + FAISS + RRF |
| Phase 3 (NER+SetFit+CE) | 0.716 | 0.750 | 0.543 | GLiNER + SetFit + cross-encoder |
| **Current** | **0.933** | **0.985** | **0.780** | SetFit SELL fix + GLiNER qty fix + LTR v2 |

---

<a name="part-16"></a>
# PART 16: MANAGEMENT COMMANDS & OPERATIONS

## 16.1 Search Commands

| Command | What it Does |
|---------|-------------|
| `python manage.py build_index` | Rebuilds BM25 + FAISS search index (search_index_v2.pkl) |
| `python manage.py evaluate_search` | Runs full evaluation against golden judgments |
| `python manage.py evaluate_search --compare-to=eval_2024-01-01.json` | Compare against baseline |
| `python manage.py check_models` | Verifies all 7 ML models are loadable |
| `python manage.py check_data_integrity` | Verifies FK integrity, volume sanity, OpenSearch sync |

## 16.2 check_models (7 checks)

1. **FAISS HNSW index** — `search_index_v2.pkl` exists and loads correctly
2. **BM25 product index** — BM25Okapi present in index, has corpus_size > 0
3. **SetFit intent classifier** — Model directory exists, `config.json` + `model_head.pkl` present, predict() works
4. **LightGBM LTR model** — `lgbm_ltr_v2.txt` (or `lgbm_ltr.txt`) loads, predict() works
5. **Cross-encoder re-ranker** — `cross-encoder/ms-marco-MiniLM-L6-v2` loads
6. **nomic-embed-text-v1** — Model loads, embedding dimension = 768
7. **GLiNER NER model** — `urchade/gliner_medium-v2.1` loads, extract() works

All 7: **PASS** on current codebase.

## 16.3 check_data_integrity (7 checks)

1. **Transaction table basics** — Records exist, has valid seller/buyer/product_item
2. **ProductItem FK integrity** — All transactions have valid product_item references
3. **SubCategory FK integrity** — All ProductItems have valid sub_category references
4. **Non-zero volumes** — Volume and price fields are non-zero/non-null
5. **CanonicalCompanyLink** — Entity resolution mappings exist (WARN if not run yet)
6. **CompanyProductStats** — Pre-computed stats table is populated
7. **OpenSearch sync** — OpenSearch index count matches PostgreSQL count (WARN if opensearch-py not installed)

## 16.4 Cold Start Procedure

First query after server restart takes 23-60 seconds (all models load lazily):
1. nomic-embed-text-v1 (~768MB) — ~15s
2. FAISS index load — ~2s
3. SetFit classifier — ~2s
4. GLiNER NER — ~5s
5. Cross-encoder — ~2s
6. LightGBM LTR — ~0.1s

Subsequent (warm) queries: **100-200ms P50, 200-400ms P99**.

**Recommendation:** Run `python manage.py check_models` after deployment to warm all models before serving traffic.

---

<a name="part-17"></a>
# PART 17: CURRENT METRICS & PERFORMANCE

## 17.1 Search Quality (as of March 2026)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| NDCG@10 | **0.9325** | ≥ 0.75 | PASS |
| MRR@10 | **0.9853** | ≥ 0.70 | PASS |
| Recall@10 | **0.7798** | ≥ 0.80 | CLOSE (0.02 below) |
| Precision@5 | **0.85+** | ≥ 0.40 | PASS |
| MAP@10 | **0.80+** | ≥ 0.35 | PASS |

## 17.2 Recall@10 by Query Family

| Family | Recall@10 | Status |
|--------|-----------|--------|
| F1 Generic | 0.709 | Acceptable |
| F2 Country | 0.875 | Strong |
| F3 Volume | 0.775 | Good |
| F4 Price | 0.749 | Acceptable |
| F5 Time | 0.711 | Acceptable |
| F6 Top-K | 0.647 | Below target |
| F7 Compare | 0.528 | Weak (data gaps) |
| F8 Evidence | 0.768 | Good |
| F9 Multi | 0.654 | Acceptable |
| EDGE Cases | 0.758 | Good |

## 17.3 Latency

| Stage | P50 (ms) | P99 (ms) |
|-------|----------|----------|
| Parse | 2 | 9 |
| Retrieval | 92 | 194 |
| Aggregation | 6 | 15 |
| Ranking | 6 | 33 |
| **Total** | **109** | **212** |

Before optimization (Phase 0): P50 ~3300ms, P99 ~6600ms. **~30x improvement.**

## 17.4 LTR Model Performance

| Metric | LTR v1 | LTR v2 |
|--------|--------|--------|
| NDCG@5 (holdout) | 0.910 | **0.987** |
| NDCG@10 (holdout) | 0.930 | **0.992** |
| Training queries | 25 | 62 |
| Labeled pairs | 200 | 460 |
| Features | 8 | 15 |

---

<a name="part-18"></a>
# PART 18: RESEARCH PAPER COMPENDIUM

## 18.1 Semantic Embeddings & Retrieval

### SBERT — The Core Semantic Search Foundation
> **Reimers, N., & Gurevych, I. (2019).** Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *EMNLP 2019. arXiv:1908.10084.*

Introduces Siamese architecture for encoding sentences independently into fixed-size vectors. Enables O(N) comparison vs O(N²) for cross-encoder BERT. Zarailink uses nomic-embed-text-v1 (a modern successor) as primary and all-MiniLM-L6-v2 as fallback.

### MiniLM — Knowledge Distillation
> **Wang, W., et al. (2020).** MiniLM: Deep Self-Attention Distillation for Task-Agnostic Compression of Pre-Trained Transformers. *NeurIPS 2020. arXiv:2002.10957.*

Compresses large transformers by distilling self-attention patterns into smaller student models. Powers both `all-MiniLM-L6-v2` (fallback embeddings) and `cross-encoder/ms-marco-MiniLM-L6-v2` (re-ranker).

### nomic-embed-text — Primary Embedding Model
> **Nussbaum, Z., et al. (2024).** nomic-embed: Training a Reproducible Long Context Text Embedder. *arXiv:2402.01613.*

768-dimensional embeddings with task-type prefixes (search_query/search_document). Outperforms MiniLM on retrieval benchmarks while supporting longer contexts. Used as Zarailink's primary embedding model.

### BM25 — Probabilistic Keyword Retrieval
> **Robertson, S. E., & Zaragoza, H. (2009).** The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval.*

The industry-standard keyword retrieval function. Zarailink uses BM25Okapi as one component of the hybrid retrieval pipeline, combined with dense retrieval via RRF.

### FAISS — Efficient Similarity Search
> **Johnson, J., Douze, M., & Jégou, H. (2019).** Billion-scale similarity search with GPUs. *IEEE Transactions on Big Data.*

Facebook's library for efficient nearest-neighbor search. Zarailink uses IndexHNSWFlat (M=32, efConstruction=200, efSearch=50) for approximate nearest-neighbor search in O(log N) time.

### RRF — Reciprocal Rank Fusion
> **Cormack, G. V., Clarke, C. L., & Buettcher, S. (2009).** Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods. *SIGIR 2009.*

Combines multiple ranked lists using `RRF(d) = Σ 1/(k + rank_i(d))`. Avoids score normalization issues between BM25 and dense retrieval. Zarailink uses k=60.

### HyDE — Hypothetical Document Embeddings
> **Gao, L., Ma, X., Lin, J., & Callan, J. (2022).** Precise Zero-Shot Dense Retrieval without Relevance Labels. *arXiv:2212.10496.*

Generates hypothetical "ideal" documents for short queries, then uses their embeddings to enhance retrieval. Applied to F1 queries with ≤4 words in Zarailink.

### SimCSE — Contrastive Learning for Embeddings
> **Gao, T., Yao, X., & Chen, D. (2021).** SimCSE: Simple Contrastive Learning of Sentence Embeddings. *EMNLP 2021. arXiv:2104.08821.*

Explains why contrastive learning produces good sentence embeddings. Standard dropout acts as minimal data augmentation for positive pairs.

### DPR — Dense Passage Retrieval
> **Karpukhin, V., et al. (2020).** Dense Passage Retrieval for Open-Domain Question Answering. *EMNLP 2020. arXiv:2004.04906.*

Bi-encoder retrieval for QA. Zarailink's FAISS retrieval path is architecturally identical to DPR.

### BEIR — Benchmark Validation
> **Thakur, N., et al. (2021).** BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models. *NeurIPS 2021. arXiv:2104.08663.*

Validates that embedding models generalize across diverse retrieval tasks without domain-specific fine-tuning.

## 18.2 Learning to Rank

### RankNet — Pairwise LTR Foundation
> **Burges, C., et al. (2005).** Learning to Rank Using Gradient Descent. *ICML 2005.*

First neural ranking model. Models P(A > B) = sigmoid(score_A - score_B).

### LambdaRank — NDCG-Optimal Gradients
> **Burges, C., Ragno, R., & Le, Q. (2006).** Learning to Rank with Nonsmooth Cost Functions. *NeurIPS 2006.*

Defines λ_AB = |ΔNDCG_AB| × pairwise gradient. Implicitly optimizes NDCG through pairwise comparisons.

### LambdaMART — Trees for Ranking
> **Burges, C. (2010).** From RankNet to LambdaRank to LambdaMART: An Overview. *MSR-TR-2010-82.*

Extends LambdaRank to gradient boosted trees. Dominated Yahoo Learning to Rank Challenge (2010).

### LightGBM — The ML Library
> **Ke, G., et al. (2017).** LightGBM: A Highly Efficient Gradient Boosting Decision Tree. *NeurIPS 2017.*

Three innovations: leaf-wise growth, GOSS, EFB. Up to 20x faster than XGBoost. Zarailink uses `lambdarank` objective.

### NDCG — The Evaluation Metric
> **Järvelin, K., & Kekäläinen, J. (2002).** Cumulated gain-based evaluation of IR techniques. *ACM TOIS, 20(4), 422-446.*

Introduces position-discounted relevance scoring. DCG@k = Σ (2^rel_i - 1) / log2(i+1). NDCG = DCG / IDCG.

### ListNet — Listwise LTR
> **Cao, Z., et al. (2007).** Learning to Rank: From Pairwise Approach to Listwise Approach. *ICML 2007.*

First listwise method. Uses top-1 probability via Plackett-Luce model.

### LambdaLoss — Theoretical Unification
> **Wang, X., et al. (2018).** The LambdaLoss Framework for Ranking Metric Optimization. *CIKM 2018.*

Proves LambdaRank is a special case of a broader probabilistic framework.

## 18.3 NER & Classification

### SetFit — Few-Shot Classification
> **Tunstall, L., et al. (2022).** Efficient Few-Shot Learning Without Prompts. *arXiv:2209.11055.*

Sentence transformer fine-tuning for few-shot text classification. Used for Zarailink's intent/family classification.

### GLiNER — Zero-Shot NER
> **Zaratiana, U., et al. (2023).** GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer. *arXiv:2311.08526.*

Zero-shot NER where entity types are specified as label strings. Used for extracting product, quantity, country, price, company, and time entities.

## 18.4 Cross-Encoders

### MS MARCO — Training Data for Cross-Encoders
> **Nguyen, T., et al. (2016).** MS MARCO: A Human Generated MAchine Reading COmprehension Dataset. *arXiv:1611.09268.*

The dataset that `cross-encoder/ms-marco-MiniLM-L6-v2` is fine-tuned on. 1M query-passage relevance pairs from Bing search logs.

## 18.5 Multi-Stage Retrieval Architecture

### Cascade Ranking
> **Matsubara, Y., et al. (2022).** RankFlow: Joint Optimization for Multi-Stage Cascaded Ranking Systems. *SIGIR 2022.*

The theoretical justification for Zarailink's pipeline: cheap retrieval → expensive re-ranking → even more expensive final ranking.

---

<a name="part-19"></a>
# PART 19: GLOSSARY OF EVERY TECHNICAL TERM

| Term | Definition |
|------|-----------|
| **BM25** | Best Match 25 — probabilistic keyword retrieval function. Extends TF-IDF with length normalization and saturation. |
| **Bi-encoder** | A model architecture where query and document are encoded independently, then compared with dot product/cosine. Fast but less accurate than cross-encoder. |
| **Cross-encoder** | A model that concatenates query + document and processes them jointly. More accurate but slower than bi-encoder. |
| **Cosine similarity** | Measures the angle between two vectors. `cos(A,B) = A·B / (|A|×|B|)`. Range [-1, 1]. |
| **DCG** | Discounted Cumulative Gain. Sum of relevance scores weighted by position discount `1/log2(i+1)`. |
| **FAISS** | Facebook AI Similarity Search. Library for efficient nearest-neighbor search on dense vectors. |
| **GLiNER** | Generalist Liner — zero-shot NER model that recognizes entity types specified as label strings. |
| **HNSW** | Hierarchical Navigable Small World. Graph-based approximate nearest-neighbor index. O(log N) search. |
| **HyDE** | Hypothetical Document Embeddings. Generates a hypothetical "ideal result" to improve retrieval for short queries. |
| **icontains** | Django ORM operator. Case-insensitive substring match. Translates to SQL `LIKE '%query%'`. |
| **IDCG** | Ideal DCG — the DCG score of a perfectly ranked list. Used to normalize DCG into NDCG. |
| **Intent** | Whether the user wants to BUY (find suppliers) or SELL (find buyers). |
| **LambdaMART** | LambdaRank applied to MART (gradient boosted trees). The algorithm behind LightGBM's `lambdarank` objective. |
| **LambdaRank** | Ranking algorithm that computes gradients weighted by |ΔNDCG| to implicitly optimize NDCG. |
| **LightGBM** | Light Gradient Boosting Machine. Microsoft's efficient GBDT library with leaf-wise growth, GOSS, and EFB. |
| **LTR** | Learning to Rank. ML approach to ranking where a model learns optimal result ordering from labeled data. |
| **MAP** | Mean Average Precision. Average of precision values computed at each relevant result position. |
| **MRR** | Mean Reciprocal Rank. 1/position of the first relevant result, averaged across queries. |
| **NDCG** | Normalized DCG. `DCG / IDCG`. Range [0, 1]. The gold standard for ranking quality. |
| **NER** | Named Entity Recognition. Extracting structured entities (product, country, price) from unstructured text. |
| **nomic-embed-text-v1** | A 768-dimensional sentence embedding model by Nomic AI. Requires task-type prefixes. Zarailink's primary embedding model. |
| **Pseudo-labels** | Synthetic relevance labels generated by a heuristic scoring function, used to bootstrap LTR training when no click data exists. |
| **Query Family** | One of 9 categories (F1-F9) that determines how a query is processed. Each family has different aggregation logic and ranking weights. |
| **Recall@K** | Of all relevant items in the judgment set, what fraction appears in the top K results. |
| **RRF** | Reciprocal Rank Fusion. Combines multiple ranked lists using `1/(k + rank)`. Score-agnostic. |
| **SBERT** | Sentence-BERT. Siamese BERT networks that encode sentences into fixed-size vectors for efficient similarity comparison. |
| **Scope** | PAKISTAN (domestic) or WORLDWIDE (international). Determines which side of the trade relationship is queried. |
| **SetFit** | Sentence Transformer Fine-tuning. Few-shot classification framework that learns from ~8 examples per class. |
| **all-MiniLM-L6-v2** | A 384-dimensional SBERT model. 6-layer MiniLM distilled from BERT. Zarailink's fallback embedding model. |

---

# APPENDIX: DEMO QUERIES

These queries demonstrate the full pipeline capability with products that exist in the current database:

| # | Query | Family | Expected Behavior |
|---|-------|--------|------------------|
| 1 | `"find dextrose buyers"` | F1 | Returns all Pakistani dextrose importers ranked by volume+recency |
| 2 | `"dextrose buyers in China"` | F2 | Filters to buyers importing from China |
| 3 | `"find buyers for 100 MT of lactose"` | F3 | Volume-matched buyers with compatibility scores |
| 4 | `"maltodextrin buyers paying above $500"` | F4 | Hard price floor filter applied |
| 5 | `"who bought refined sugar last 6 months"` | F5 | Time-filtered, recency-ranked |
| 6 | `"top 5 lactose exporters"` | F6 | Full pipeline → truncated to 5 results |
| 7 | `"which countries buy the most dextrose"` | F7 | Country comparison with YoY growth |
| 8 | `"has Muller and Phipps purchased dextrose"` | F8 | Buyer verification with transaction evidence |
| 9 | `"find dextrose buyers; show country comparison"` | F9 | Multi-intent: F1 + F7 stacked sections |
| 10 | `"I want to sell 50 MT refined sugar from Germany"` | F3 | SELL intent preserved despite SetFit F3_VOLUME |
| 11 | `"fifty metric tons dextrose monohydrate"` | F3 | GLiNER cleans quantity-polluted product |
| 12 | `"compare dextrose vs lactose markets by country"` | F7 | Complex F7 with implicit product comparison |

---

*Last updated: March 2026. Based on codebase at commit `ac6eb8a1` (salman_v2 branch).*
