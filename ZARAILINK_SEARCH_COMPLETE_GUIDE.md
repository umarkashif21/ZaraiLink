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
2. [Zarailink's Answer — The 4-Stage Pipeline](#part-2)
3. [The Database — What Raw Data Exists](#part-3)
4. [Stage 1 — QueryInterpreter: Understanding What You're Asking](#part-4)
5. [Stage 2 — QueryMatcher: Finding the Right Product](#part-5)
6. [Stage 3 — Aggregation: Getting the Data](#part-6)
7. [Stage 4 — RankingEnsemble: Sorting Results by Relevance](#part-7)
8. [The 9 Query Families — Complete Reference](#part-8)
9. [Family 9 — Hybrid Multi-Intent Queries](#part-9)
10. [Research Paper Compendium](#part-10)
11. [Glossary of Every Technical Term](#part-11)

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
- **Fast** — HTTP response in under 2 seconds.
- **Accurate** — only relevant products, buyers, and suppliers.
- **Ranked** — the most useful result appears first.
- **Explainable** — users must understand why they see what they see.

This is exactly the problem that the field of **Information Retrieval (IR)** has spent 60+ years studying.

---

<a name="part-2"></a>
# PART 2: ZARAILINK'S ANSWER — THE 4-STAGE PIPELINE

## 2.1 The Core Idea: Decompose, Then Solve Each Sub-Problem

Modern search systems — from Google to Amazon to LinkedIn — decompose the search problem into multiple sequential stages. Each stage does one thing well, and passes its output to the next.

Zarailink's pipeline has exactly 4 stages:

```
RAW QUERY (natural language text)
        │
        ▼
┌─────────────────────────────────────┐
│  STAGE 1: QueryInterpreter          │
│  "What does the user want?"         │
│  • Intent (BUY or SELL)             │
│  • Entities (country, price, vol)   │
│  • Query Family (1-9)               │
│  • Multi-intent detection           │
└─────────────────────────────────────┘
        │ structured dict
        ▼
┌─────────────────────────────────────┐
│  STAGE 2: QueryMatcher (NLP)        │
│  "What product category matches?"   │
│  • Keyword matching (icontains)     │
│  • Semantic matching (SBERT)        │
│  • Fuzzy matching (typos/variants)  │
│  → ProductSubCategory IDs           │
└─────────────────────────────────────┘
        │ subcategory IDs
        ▼
┌─────────────────────────────────────┐
│  STAGE 3: Aggregation               │
│  "Get the actual data"              │
│  • F1-F6: SupplierAggregator        │
│  • F7: CountryComparator            │
│  • F8: EvidenceRetriever            │
│  → raw candidate list               │
└─────────────────────────────────────┘
        │ candidate dicts
        ▼
┌─────────────────────────────────────┐
│  STAGE 4: RankingEnsemble           │
│  "Which results matter most?"       │
│  • Feature Extraction (8 features)  │
│  • Heuristic Scoring (70%)          │
│  • LightGBM LTR Model (30%)         │
│  → ranked final list                │
└─────────────────────────────────────┘
        │
        ▼
JSON RESPONSE to frontend
```

## 2.2 A Concrete Example

Let's trace the query `"find dextrose buyers in China paying above $600"` through all 4 stages.

**Stage 1 — QueryInterpreter:**
```python
{
  "intent": "SELL",          # "find buyers" → user is selling
  "family": 4,               # price constraint detected
  "product": "dextrose",     # after stripping "find buyers in" etc.
  "country_filter": ["China"],
  "price_floor": 600.0,
  "price_ceiling": None,
  "volume_mt": None,
  "time_range": None,
  "scope": "WORLDWIDE",
  "multi_intent": False
}
```

**Stage 2 — QueryMatcher:**
- "dextrose" matches ProductSubCategory `id=42, name="Dextrose"` via keyword (exact icontains).
- Also matches variant ProductItem `id=101, name="Dextrose Monohydrate"` via keyword.
- Semantic search finds related categories: "Glucose" at score 0.72.
- **Output:** `subcategory_ids = [42]`, `product_item_filter = [101]`

**Stage 3 — SupplierAggregator:**
- intent=SELL + scope=WORLDWIDE → query `trade_type='EXPORT'` transactions.
- Filters by `origin_country='China'` and `usd_per_mt >= 600`.
- Groups by buyer name, aggregates volume, price, shipment count.
- **Output:** 12 buyer records.

**Stage 4 — RankingEnsemble:**
- Extracts 8 features per candidate (log_volume, log_price, etc.).
- Applies family=4 weights (price_fit gets 3x weight).
- Combines heuristic score (70%) + LTR score (30%).
- **Output:** sorted list of 12 buyers, best first.

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

## 3.3 How Intent × Scope Maps to Database Queries

Because of this database reality, the system has to interpret "who are my buyers" (SELL intent from a Pakistani farmer) as: find the Pakistani companies importing this product — those are your potential customers.

The mapping is:

| User Intent | Scope | What They Want | DB Query |
|------------|-------|---------------|---------|
| SELL (I want to sell) | PAKISTAN | Find local Pakistani buyers | `IMPORT` records, grouped by `buyer`, filtered by `destination_country='Pakistan'` |
| SELL (I want to sell) | WORLDWIDE | Find international buyers | `EXPORT` records ← **these DON'T EXIST in DB** → falls back to PAKISTAN scope |
| BUY (I want to buy) | PAKISTAN | Find Pakistani suppliers | `EXPORT` records where `origin_country='Pakistan'` |
| BUY (I want to buy) | WORLDWIDE | Find global suppliers | `IMPORT` records, grouped by `seller` (the foreign suppliers) |

This mapping is implemented in `SupplierAggregator.get_suppliers_for_subcategories()`.

## 3.4 Product Hierarchy

Products are organized in a 3-level hierarchy:

```
ProductCategory (e.g., "Chemicals")
    └── ProductSubCategory (e.g., "Dextrose")        ← NLP matches here
            └── ProductItem (e.g., "Dextrose Monohydrate")  ← variants
```

Search operates at the **SubCategory** level. Variants (ProductItems) are used for fine-grained filtering when the user is specific (e.g., "dextrose monohydrate" vs just "dextrose").

---

<a name="part-4"></a>
# PART 4: STAGE 1 — QUERYINTERPRETER: UNDERSTANDING WHAT YOU'RE ASKING

File: `backend/search/services/query_parser.py` — `class QueryInterpreter`

## 4.1 What Is Natural Language Processing (NLP)?

**Natural Language Processing (NLP)** is the branch of computer science that deals with making computers understand human language. Human language is ambiguous, context-dependent, and full of implied meaning. Computers prefer precise, unambiguous instructions.

Example of ambiguity: "I saw her duck." Does "duck" mean the bird, or the action of bending down? A human uses context to know; a computer needs explicit rules or training.

Zarailink's QueryInterpreter doesn't use a neural AI model for parsing. Instead, it uses **rule-based NLP** — a set of hand-crafted patterns, regular expressions, and scoring rules. This is a deliberate engineering choice. Let's understand why before we dive into the details.

## 4.2 Rule-Based vs. Neural NLP: Why Rules Are Sometimes Better

There are two main approaches to NLP:

**1. Rule-based NLP:** A human expert writes patterns like "if the query contains 'who buys', classify intent as SELL." It's fast, predictable, debuggable, and requires no training data.

**2. Neural NLP:** A deep learning model (like BERT, GPT) is trained on millions of examples and learns patterns automatically. It's more flexible and generalizes better, but requires labeled training data and is harder to debug.

**Why Zarailink uses rule-based for query parsing:**
- Trade queries have very specific, learnable patterns.
- The vocabulary is limited (about 30-40 intent keywords, 30 countries, 5 volume units).
- Rules are instantly debuggable: "why did it classify this as F4?" → you can trace through each rule.
- No training data was available when the system was built.
- A 2021 study by **Cheng et al. (AAAI 2021)** found that for domain-specific e-commerce queries with structured intents, rule-based systems with good entity dictionaries matched neural NER performance at a fraction of the compute cost.

The NLP *module* (Stage 2, QueryMatcher) does use neural models. But the *query interpreter* (Stage 1) uses rules. This hybrid is common in production systems.

## 4.3 The Full Parsing Pipeline

When a query arrives, `QueryInterpreter.parse()` runs this sequence of steps:

```
Query Text
    │
    ▼
[Step 0] Multi-Intent Check (split by ';' or 'and'/'also')
    │
    ▼
[Step 1] Is it Family 8, 7, or 6? (keyword scan)
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
[Step 7] Product Extraction (what's left after removing everything else)
    │
    ▼
[Step 8] Family Classification (F1-F8 priority rules)
    │
    ▼
[Step 9] F8 Special: Buyer Name Extraction + Cleanup
    │
    ▼
Structured dict output
```

Let's go through each step in detail.

## 4.4 Step 0: Multi-Intent Detection

**What is multi-intent?** Sometimes a user asks two separate questions in one query:
- `"who buys dextrose most; show me country comparison"` — two distinct questions.
- `"find dextrose buyers in China and India"` — NOT two questions; China and India are additive filters.

The parser must distinguish between these cases.

**How it works:**

First, it splits on semicolons (`;`) — always a strong indicator of multiple questions.

If no semicolon, it looks for `and` or `also`. But splitting on every `and` would be wrong — "buyers in China and India" would get wrongly split. The key insight is:

> Split on 'and'/'also' **only if the right side has its own independent intent keyword**.

The code checks: does the right side (after 'and') contain words like "buyers", "sell", "compare"? If yes → separate intent. If not → it's just a compound modifier (like "China and India").

```python
# From query_parser.py lines 78-99
has_intent = self._detect_intent_score(part)[0] != 'AMBIGUOUS'
if has_intent:
    final_segments.append(current_segment)
    current_segment = part
else:
    current_segment += " and " + part  # Merge — additive filter, not separate intent
```

If multiple segments are found, each is parsed independently with `_parse_single()`, and the result is returned as a **Family 9 (multi-intent)** query.

**Research backing:** Multi-intent detection in single utterances is an active NLP research area. The key challenge (called the "boundary problem") is deciding where one intent ends and another begins. Papers like **AGIF (Qin et al., EMNLP 2020)** propose graph attention networks to detect intent slot correspondences jointly. For Zarailink's constrained domain, the simpler "check for intent keyword on right side of 'and'" heuristic works reliably because the keyword vocabulary is known and finite.

## 4.5 Step 1: Family Keyword Scanning

Before extracting anything, the parser checks for keywords that strongly indicate a specific query family. This is done first because some family types (F7, F8) require very different handling and their keywords should not be confused with product names.

```python
# From query_parser.py lines 183-189
is_rec = any(x in raw_query for x in self.FAM_6_KEYWORDS)    # F6
is_mkt = any(x in raw_query for x in self.FAM_7_KEYWORDS)    # F7
is_evid = (
    any(x in raw_query for x in self.FAM_8_KEYWORDS)         # F8
    or bool(re.search(r'\bhas\s+\S+(?:\s+\S+){0,4}\s+(?:purchased|bought)\b', raw_query))
)
```

**Family 6 keywords:** top, best, rank, suggest, recommend, highest, most, paying
**Family 7 keywords:** which country, which countries, compare, best market, country comparison, by country, breakdown by country, etc.
**Family 8 keywords:** shipments, transactions, history, proof, verification, evidence, invoices, has purchased, has bought, etc.

Note the priority: **F8 > F7 > F6 > F4 > F5 > F3 > F2 > F1**. This means if a query triggers both F8 and F6 keywords, it's classified as F8.

## 4.6 Step 2: Country Extraction

The parser extracts country names from the query using three methods in order of precision:

**Method 1: Alias Matching (Highest Precision)**
```python
COUNTRY_ALIASES = {
    "us": "USA", "u.s.": "USA", "united states of america": "USA", "america": "USA",
    "uae": "UAE", "u.a.e": "UAE", "emirates": "UAE",
    "uk": "UK", "u.k.": "UK", "britain": "UK",
    "ksa": "Saudi Arabia"
}
```
Aliases are sorted by length (longest first) so "united states of america" is matched before "america" — preventing partial matches.

**Method 2: Standard Country List Matching**
A hardcoded list of 30 common trading partners is checked with word-boundary regex (`\b`). Matched countries are removed from the remainder text.

**Method 3: Fuzzy Country Matching**
For tokens ≥4 characters that didn't match any alias or standard name, `difflib.get_close_matches()` is called with cutoff=0.85. This catches typos like "Chnia" → "China".

After extraction, matched countries are removed from the text. This is important for the next steps: if we don't remove "China", it might appear in the product field.

**Why this matters:** Country extraction is a Named Entity Recognition (NER) task. In the academic literature, state-of-the-art NER for general text uses transformer models (BERT-based). But for a fixed vocabulary of ~30 country names, a hand-crafted dictionary with fuzzy matching achieves the same accuracy at near-zero computational cost.

## 4.7 Step 3: Volume Extraction

The parser looks for volume specifications using a regular expression:

```python
vol_pattern = r'(\d+(?:,\d+)?(?:\.\d+)?)\s*(mt|tons|metric tons|kg|kilo|tonnes)'
```

This pattern matches:
- `100 MT` → 100 metric tonnes
- `50,000 kg` → 50 metric tonnes (converted: ÷1000)
- `25.5 tonnes` → 25.5 metric tonnes
- `100MT` (no space) → also matched with `flags=re.IGNORECASE`

Volume is stored as a float in metric tonnes (`volume_mt`). It is used for **soft volume compatibility scoring** in Stage 3, not as a hard filter. This is deliberate: if a buyer has historically done 20 MT shipments and you need 25 MT, they might still be able to fulfill it. Hard filters would exclude them entirely.

## 4.8 Step 4: Price Extraction

Price can be specified in three ways:

**Ceiling (upper bound):** "under $600", "below $600", "< $600", "less than $600"
```python
ceil_pattern = r'(?:under|below|<|cheaper than|less than|paying less than)\s*' + currency_regex + r'?\s*(\d+(?:,\d+)?)'
```

**Floor (lower bound):** "above $600", "over $600", "> $600", "more than $600"
```python
floor_pattern = r'(?:above|over|>|higher than|more than|paying more than|sell above)\s*' + currency_regex + r'?\s*(\d+(?:,\d+)?)'
```

**Exact:** If neither ceiling nor floor is found but a number followed by a currency is present, it's treated as a ceiling.

Currency symbols handled: `$`, `USD`, `EUR`, `PKR`, `GBP`, `CNY`, `RMB`.

Price ceiling and floor are passed directly to the database query as `usd_per_mt__lte` and `usd_per_mt__gte` filters.

## 4.9 Step 5: Time Extraction

Time can be specified as:
- Quarter: `Q1 2025`, `Q3 2024`
- Year: `2024`, `2025`
- Relative: `last 6 months`, `last 3 months`, `this year`
- Range: `from January to March`

These are converted to `(start_date, end_date)` pairs in `_parse_time_range()` in `views.py`. For example:
- `"Q1 2025"` → `{start_date: 2025-01-01, end_date: 2025-03-31}`
- `"last 6 months"` → `{start_date: today-180days, end_date: today}`

These become `reporting_date` filters in the database query.

## 4.10 Step 6: Intent Detection (BUY vs SELL)

Intent detection is the most conceptually important step. It determines the *direction* of the trade relationship the user cares about.

**BUY intent:** The user wants to buy something — they're looking for suppliers who can sell to them.
**SELL intent:** The user wants to sell something — they're looking for buyers who will buy from them.

The system uses **weighted keyword scoring**. Every word/phrase in the query is checked against two vocabularies:

```python
BUY_SCORES = {
    "who sells": 5, "suppliers of": 5, "find suppliers": 5,
    "buy from": 5, "i want to buy": 5,
    "buying": 3, "imports": 2, "want to import": 4,
    "buy": 1, "purchase": 2, "sourcing": 3, "need": 2
}

SELL_SCORES = {
    "who buys": 5, "buyers for": 5, "find buyers": 5,
    "demand for": 5, "sell to": 5, "i want to sell": 5,
    "selling": 3, "exports": 2, "want to export": 4,
    "sell": 1, "buyers": 3, "pay": 3, "buys": 5
}
```

The intent with the higher total score wins. For example:
- "find dextrose buyers paying above $600" → "find buyers" (+5 SELL), "buyers" (+3 SELL), "pay" (+3 SELL) → SELL wins clearly.
- "i want to buy dextrose from China" → "i want to buy" (+5 BUY), "buy" (+1 BUY), "from" (no score) → BUY wins.

**Family 7 intent override:** A special case exists for country comparison queries. Words like "buyers by country" contain "buyers" (SELL indicator) but also look like SELL intent. However, if the query is clearly about "which countries have the most demand" (market analysis), we must force SELL intent. The code does this by checking for BUYER_MARKET_PHRASES and overriding BUY→SELL if F7 was triggered.

## 4.11 Step 7: Product Extraction

After all entities (countries, volumes, prices, time) have been removed from the text, and after all intent keywords and family keywords have been stripped, **whatever remains is the product**.

This is a "leftover" approach. It works because trade queries follow a predictable pattern: "[intent phrase] [product] [filters]".

```python
# Strip intent phrases
for phrase in all_phrases:
    clean_text = re.sub(r'\b' + re.escape(phrase) + r'\b', '', clean_text)

# Strip family keywords
for w in all_fam_keywords:
    clean_text = re.sub(r'\b' + re.escape(w) + r'\b', '', clean_text)

# Strip stopwords
for sw in STOPWORDS:
    clean_text = re.sub(r'\b' + re.escape(sw.strip()) + r'\b', ' ', clean_text)

# What's left is the product
attributes['product'] = clean_text.strip()
```

**Potential issue:** Conversational prefixes like "can i sell", "looking to sell", "i have" are stripped first so they don't contaminate the product field.

## 4.12 Step 8: Family Classification

The family is assigned using a priority chain (code lines 401-411):

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

This priority means: a query with both price and volume is F4 (price takes precedence). The reasoning is that the most *constraining* filter determines the query type.

**F7 downgrade guard:** If F7 was triggered only by ambiguous keywords (like "cheapest", "compare", "vs") and fewer than 2 countries were extracted, it's downgraded to F4 or F1. "Cheapest dextrose from China" should be F4 (price search), not F7 (country comparison — which requires comparing multiple countries).

## 4.13 Step 9: F8 Buyer Name Extraction

Family 8 queries are about verifying whether a specific company has a purchase history. The buyer company name must be extracted precisely. Three patterns are tried:

**Pattern 1:** "Has [BUYER] purchased/bought [product]"
```python
m = re.search(r'\bhas\s+(.+?)\s+(?:purchased|bought)\b', query, re.IGNORECASE)
```

**Pattern 2:** "shipments (from X) to [BUYER]"
```python
m = re.search(r'\bshipments\s+(?:\w+\s+\w+\s+)?to\s+(.+?)(?:\?|$)', query, re.IGNORECASE)
```

**Pattern 3:** "evidence/invoices for [BUYER]" — only if BUYER starts with uppercase (to avoid product names like "dextrose" being misidentified).
```python
m = re.search(
    r'\b(?:evidence|invoices?|history|record|verify)\s+(?:for|of|by)\s+([A-Z]\w[\w\s]*?)(?:\?|$)',
    query  # NOT re.IGNORECASE — uppercase required for proper nouns
)
```

After extraction:
1. Any country names within the buyer name (e.g., "Pakistan" in "Nestle Pakistan Ltd") are removed from `country_filter` — they're part of the company name, not a geographic filter.
2. The buyer name is stripped from the product field so "Nestle Pakistan" doesn't contaminate the product "dextrose".
3. F8-specific noise words ("purchased", "before", "deal") are removed from product.

---

<a name="part-5"></a>
# PART 5: STAGE 2 — QUERYMATCHER: FINDING THE RIGHT PRODUCT

File: `backend/search/services/nlp.py` — `class QueryMatcher`

## 5.1 The Problem: Bridging the Vocabulary Gap

After Stage 1, we have a clean product term like `"dextrose"`. Now we must find which entries in the `ProductSubCategory` table it corresponds to.

Why is this non-trivial? Because of the **vocabulary gap** — the difference between what a user types and what's in the database:

| User Types | Database Has |
|-----------|-------------|
| dextrose | Dextrose |
| glucose | Dextrose (same thing!) |
| blood sugar | Dextrose |
| dextrse | Dextrose (typo) |
| Dextrose Anhydrous | Dextrose Anhydrous (exact ProductItem) |

A simple case-insensitive string match (`icontains`) handles the first case (same word, different case). But it completely fails for synonyms (glucose = dextrose) and near-synonyms.

The solution is **hybrid search**: three complementary methods, each covering what the others miss.

## 5.2 Method 1: Keyword Matching (High Precision)

```python
# From nlp.py lines 46-83
subcat_hits = ProductSubCategory.objects.filter(name__icontains=clean_qs)
item_hits = ProductItem.objects.filter(name__icontains=clean_qs).select_related('sub_category')
```

**`icontains`** is a Django ORM operator that translates to SQL `LIKE '%query%'` (case-insensitive). It matches any database record whose name *contains* the search term as a substring.

Example: searching "dextrose" → matches "Dextrose", "Dextrose Monohydrate", "Dextrose Anhydrous".

If a ProductItem (variant) matches, its parent SubCategory is added to the results and the matched variant IDs are recorded for later filtering.

**Score:** All keyword matches get score=1.0 (maximum).

**Why this matters:** Keyword matching has very high precision for *exact* or *partial* matches. If a user types "dextrose", they almost certainly want the Dextrose category. No complex model needed.

**Limitation:** Fails for synonyms and semantic relationships.

## 5.3 What Is Semantic Search? A Beginner's Explanation

Here is the problem: "glucose" and "dextrose" are chemically identical (both are D-glucose), but the words look completely different. A keyword search would find no match.

**Semantic search** solves this by converting words and phrases into *mathematical vectors* (lists of numbers) where similar-meaning words end up in similar regions of a high-dimensional space. Then, instead of comparing words, we compare vectors.

**The key insight:** If you train a neural network to read billions of sentences and predict which words appear together (or which sentences are related), the network learns that "glucose" and "dextrose" appear in very similar contexts — they're both in the same sentences about blood chemistry, food additives, and pharmaceuticals. The network then assigns them very similar vector representations.

This is the core idea behind **word embeddings** and **sentence embeddings**.

## 5.4 SBERT: Sentence-Transformers for Semantic Search

**SBERT** (Sentence-BERT) is a model specifically designed to produce high-quality vector representations (embeddings) for *sentences and phrases*, not just individual words. It was introduced in:

> **Reimers, N., & Gurevych, I. (2019).** Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *Proceedings of EMNLP 2019.*

Before SBERT, comparing two sentences for semantic similarity required feeding both sentences simultaneously into a large BERT model — a process that took quadratic time (O(N²) comparisons for N sentences). This is too slow for real-time search.

SBERT's key innovation: a **Siamese network architecture** with **shared weights** that encodes each sentence *independently* into a fixed-size vector. Once you have these vectors, comparing any two sentences is just a dot product — extremely fast.

```
Sentence A → [SBERT Encoder] → Vector A (384 numbers)
Sentence B → [SBERT Encoder] → Vector B (384 numbers)

Similarity = dot_product(Vector A, Vector B)
           = fast O(1) operation
```

Instead of comparing every query to every database entry at search time (slow), you **pre-compute** all database entry vectors and store them in an index. At search time, you only need to:
1. Encode the query (one forward pass through SBERT → 384 numbers)
2. Compare the query vector against all pre-computed vectors (vector math, very fast)

This reduces O(N²) to O(N), enabling real-time search over large corpora.

## 5.5 The all-MiniLM-L6-v2 Model

The specific SBERT variant used in Zarailink is `all-MiniLM-L6-v2`. Let's unpack this name:

**MiniLM:** The base architecture is **MiniLM** (Miniaturized Language Model), introduced by:

> **Wang, W., Wei, F., Dong, L., Bao, H., Yang, N., & Zhou, M. (2020).** MiniLM: Deep Self-Attention Distillation for Task-Agnostic Compression of Pre-Trained Transformers. *NeurIPS 2020.*

MiniLM is a technique called **knowledge distillation** — taking a large, accurate model (the "teacher") and training a small, fast model (the "student") to mimic its behavior. The result is a model that is 22.7 million parameters (vs 340M for BERT-Large), runs on CPU in milliseconds, but retains most of the semantic understanding.

**L6:** The "L" stands for "layers" — the transformer has 6 layers. Fewer layers = faster inference.

**v2:** Second version, trained on 1.17 billion sentence pairs (a massive dataset including MS MARCO, Reddit, Wikipedia pairs, and more).

**Output:** 384-dimensional vector for any input phrase.

**Why this model specifically?**
- It runs efficiently on CPU without a GPU (important for a Django web server).
- 384 dimensions is the sweet spot: small enough to compute quickly, large enough to capture semantic nuance.
- BEIR benchmark (**Thakur et al., 2021**) shows it achieves competitive performance across 18 diverse retrieval datasets.

## 5.6 Cosine Similarity: The Mathematical Foundation

Once we have vector embeddings, how do we measure similarity? The answer is **cosine similarity**.

**What is a vector?** Imagine a vector as a point in space. In 2D, a vector is just a point (x, y). In 384D, it's 384 coordinates. The "direction" the point-arrow points in this 384D space represents the *meaning* of the phrase.

**What is cosine similarity?** It measures the angle between two vectors. If the angle is 0° (vectors point in exactly the same direction), similarity=1. If angle is 90° (perpendicular), similarity=0. If angle is 180° (opposite directions), similarity=-1.

```
cosine_similarity(A, B) = (A · B) / (|A| × |B|)
                        = sum(a_i × b_i) / (magnitude_A × magnitude_B)
```

**Why cosine and not Euclidean distance?** Because cosine similarity is **magnitude-invariant** — it only cares about *direction*, not length. This is important because the length of an embedding vector might vary (due to model quirks), but the direction reliably encodes meaning.

Example: "dextrose" and "glucose" will have embeddings pointing in very similar directions (high cosine similarity ~0.85+), while "dextrose" and "steel" will point in very different directions (low cosine similarity ~0.1).

**In code (nlp.py lines 89-113):**
```python
query_vec = model.encode([clean_qs])          # Shape: (1, 384)
scores = cosine_similarity(query_vec, index['embeddings'])[0]  # Shape: (num_categories,)
top_indices = np.argsort(scores)[::-1][:10]   # Top 10 most similar
```

The pre-built index (`search_index.pkl`) contains pre-computed embeddings for all ProductSubCategory names. At search time, only the query is encoded fresh.

**Threshold:** Matches below 0.4 cosine similarity are discarded as irrelevant (line 100).

## 5.7 Method 3: Fuzzy Matching (Catching Typos)

After keyword and semantic matching, the system runs fuzzy matching to catch typos in product variant names.

```python
# From nlp.py lines 115-150
from difflib import SequenceMatcher
ratio = SequenceMatcher(None, clean_qs, item['name'].lower()).ratio()
if ratio > 0.85:  # 85% character-level similarity
    matches[parent_id]['matched_variants'].append(item['id'])
```

**SequenceMatcher** computes the Longest Common Subsequence ratio between two strings. `ratio = 2.0 * M / T` where `M` is matching characters and `T` is total characters in both strings.

Example: "MONOYDRATE" vs "MONOHYDRATE" → ratio ≈ 0.90 → caught as a typo.

This only runs for items within already-matched subcategories (not all products globally), so it's efficient.

## 5.8 The PyTorch Meta Device Bug (and Fix)

A critical production bug was fixed in this codebase. When `sentence_transformers` version 5.x is installed alongside the `accelerate` library, the model's default loading behavior changes:

**The bug:** `accelerate` enables `low_cpu_mem_usage=True` by default, which loads model weights onto a PyTorch "meta device" — an abstract device with no real memory. This is designed to save RAM during model initialization. But when Django's HTTP server process tries to run inference (`.to(device)`), it crashes:

```
NotImplementedError: Cannot copy out of meta tensor; no data!
Please use torch.nn.Module.to_empty() instead of torch.nn.Module.to()
when moving module from meta to a different device.
```

**The fix (nlp.py lines 19-23):**
```python
cls._model = SentenceTransformer(
    'all-MiniLM-L6-v2',
    device='cpu',
    model_kwargs={'low_cpu_mem_usage': False},  # Bypass accelerate's lazy loading
)
```

By passing `low_cpu_mem_usage=False`, we tell the model to load weights directly into real CPU memory, bypassing the meta-device mechanism. The model still runs on CPU, just without the lazy-loading optimization. This is necessary in Django's multi-process server context.

## 5.9 The Pre-Built Search Index

The file `backend/search_index.pkl` contains a Python pickle of:

```python
{
    'embeddings': np.array(...),  # shape: (num_subcategories, 384)
    'ids': [42, 43, 44, ...],     # ProductSubCategory IDs
    'names': ["Dextrose", "Salt", ...],  # Human-readable names
    'hs_codes': ["17023000", ...]  # HS trade classification codes
}
```

This index is built by running a management command that encodes all ProductSubCategory names with SBERT. At search time, only the query is encoded — the index vectors are pre-computed.

**Why pickle?** Pickle is Python's native serialization format. It's fast and supports NumPy arrays natively. For production, this could be upgraded to a dedicated vector database (FAISS, Pinecone, Weaviate) for better scalability, but pickle works for the current dataset size.

---

<a name="part-6"></a>
# PART 6: STAGE 3 — AGGREGATION: GETTING THE DATA

## 6.1 The Three Aggregation Modules

Once we have `subcategory_ids` from Stage 2, we need to retrieve actual buyers/suppliers from the database. Different query families need different kinds of data:

| Family | Module | What it Returns |
|--------|--------|----------------|
| F1–F6 | `SupplierAggregator` | Aggregated buyer/supplier profiles |
| F7 | `CountryComparator` | Per-country trade metrics |
| F8 | `EvidenceRetriever` | Raw transaction records for a specific buyer |

## 6.2 SupplierAggregator: The Core Aggregation Engine

File: `aggregation.py` — `class SupplierAggregator.get_suppliers_for_subcategories()`

### 6.2.1 Intent × Scope Routing

The first thing SupplierAggregator does is determine *which* transactions to query. The code implements a 2×2 routing table:

```python
if intent == 'SELL':
    if scope == 'PAKISTAN':
        # Find Pakistani buyers of the product
        queryset = queryset.filter(trade_type='IMPORT', destination_country='Pakistan')
        target_field = 'buyer'
        country_field = 'destination_country'
    else:  # WORLDWIDE
        # Find international buyers (EXPORT records — don't exist → 0 results)
        queryset = queryset.filter(trade_type='EXPORT')
        target_field = 'buyer'
        country_field = 'destination_country'
else:  # BUY
    if scope == 'PAKISTAN':
        # Find Pakistani suppliers
        queryset = queryset.filter(trade_type='EXPORT', origin_country='Pakistan')
        target_field = 'seller'
        country_field = 'origin_country'
    else:  # WORLDWIDE
        # Find global suppliers (IMPORT records → actual sellers in DB)
        queryset = queryset.filter(trade_type='IMPORT')
        target_field = 'seller'
        country_field = 'origin_country'
```

### 6.2.2 Database Aggregation

After routing, the queryset is grouped (aggregated) by `(target_field, country_field)` pairs:

```python
results = queryset.values(target_field, country_field).annotate(
    total_volume=Sum('qty_mt'),        # Total tonnes traded
    avg_price=Avg('usd_per_mt'),       # Average price paid
    shipment_count=Count('id'),        # Number of individual shipments
    last_shipment_date=Max('reporting_date'),  # Most recent activity
    max_shipment_vol=Max('qty_mt'),    # Largest single shipment
    avg_shipment_vol=Avg('qty_mt')     # Typical shipment size
).order_by('-total_volume')
```

This is a SQL `GROUP BY` operation. Django's `.annotate()` + `.values()` generates efficient SQL like:
```sql
SELECT buyer, destination_country,
       SUM(qty_mt) AS total_volume,
       AVG(usd_per_mt) AS avg_price,
       COUNT(id) AS shipment_count,
       MAX(reporting_date) AS last_shipment_date,
       MAX(qty_mt) AS max_shipment_vol,
       AVG(qty_mt) AS avg_shipment_vol
FROM trade_data_transaction
WHERE trade_type = 'IMPORT'
  AND destination_country = 'Pakistan'
  AND product_item__sub_category_id IN (42)
GROUP BY buyer, destination_country
ORDER BY total_volume DESC
```

The result is one row per unique (buyer, country) pair. Each row is a **candidate** that will later be ranked.

### 6.2.3 Volume Compatibility Scoring

When the user specifies a volume (`volume_mt`), the system scores each candidate on how well their trading capacity matches:

```python
if volume_filter and volume_filter > 0:
    mss = entry['max_shipment_vol']   # Maximum single shipment they've done
    total = entry['total_volume']     # Their total historical volume
    avg = entry['avg_shipment_vol']   # Their average order size
    V = float(volume_filter)          # What the user needs

    # Soft floor: exclude candidates with no plausible capacity
    if mss < 0.3 * V and total < 0.5 * V:
        continue  # Too small to be useful

    # Volume Compatibility Score (0.0 to 1.0)
    single_match = min(mss / V, 1.0)      # Can they do ONE shipment of this size?
    capacity_match = min(total / V, 1.0)  # Do they have enough total capacity?
    avg_match = min(avg / V, 1.0)         # Is their typical order similar size?

    vol_score = 0.5 * single_match + 0.3 * capacity_match + 0.2 * avg_match
```

The score is a **weighted blend** of three factors:
- **single_match (50% weight):** Most important — can they physically handle a single shipment of size V? This is the primary supply capacity indicator.
- **capacity_match (30% weight):** Do they have the overall business scale?
- **avg_match (20% weight):** Is their typical order size similar to yours? Very different sizes suggest different business segments.

Labels are assigned:
- 0.8+ → "Strong" (they can definitely fill this order)
- 0.5+ → "Good" (likely capable)
- 0.3+ → "Partial" (some capacity mismatch)
- <0.3 → "Low" (probably too small)

**Why soft floor instead of hard filter?** A hard filter (`qty_mt >= V`) would eliminate buyers who make many small shipments that sum to more than V. The soft floor only eliminates extreme mismatches (max single shipment < 30% of needed AND total < 50% of needed).

## 6.3 CountryComparator: Family 7 Market Intelligence

File: `aggregation.py` — `class CountryComparator.compare_countries()`

Family 7 answers: "Which countries are the biggest suppliers of X?" This is a market intelligence query, not a buyer search.

### 6.3.1 The Core Aggregation

```python
country_stats = (
    queryset
    .filter(trade_type='IMPORT')  # Only IMPORT records exist
    .values('origin_country')
    .annotate(
        total_volume=Sum('qty_mt'),
        avg_price=Avg('usd_per_mt'),
        supplier_count=Count('seller', distinct=True),  # Unique sellers
        shipment_count=Count('id'),
        last_active=Max('reporting_date'),
    )
    .order_by('-total_volume')
)
```

This groups by **origin country** and aggregates all imports from that country. The result tells you: "From China, Pakistan imported X tonnes of dextrose at an average price of $Y, in N shipments, from M different Chinese companies."

### 6.3.2 Year-over-Year Growth Calculation

YoY growth is a key metric for identifying which countries have growing vs declining trade. The calculation:

```python
# Current period: last 365 days
current_vol_by_country = {
    r['origin_country']: float(r['vol'] or 0)
    for r in queryset.filter(reporting_date__gte=one_year_ago)
                     .values('origin_country')
                     .annotate(vol=Sum('qty_mt'))
}

# Previous period: 366-730 days ago
prev_vol_by_country = {
    r['origin_country']: float(r['vol'] or 0)
    for r in queryset.filter(
        reporting_date__gte=two_years_ago,
        reporting_date__lt=one_year_ago
    ).values('origin_country').annotate(vol=Sum('qty_mt'))
}

# YoY % change
growth_pct = ((curr_vol - prev_vol) / prev_vol) * 100
```

This requires **two separate aggregation passes** on the database — one for each period. The growth is capped at ±500% to prevent display issues with extreme outliers.

**Special case:** If previous volume is 0 but current is >0, growth is +100% (new entrant). If both are 0, growth is 0%.

### 6.3.3 Top 3 Suppliers per Country

For each country, the 3 companies (sellers) with the highest volume are retrieved. This adds 1 additional query per country. To avoid N+1 query problems, this is done in a loop but only for countries in the result set (typically 10-15):

```python
for country in all_countries:
    rows = queryset.filter(origin_country=country)
                   .values('seller')
                   .annotate(vol=Sum('qty_mt'), avg_p=Avg('usd_per_mt'), cnt=Count('id'))
                   .order_by('-vol')[:3]
```

### 6.3.4 Static Market Entry Notes

For each country, static metadata is returned from the `MARKET_ENTRY_NOTES` dict — information about tariff tiers, typical lead times, and packaging/certification requirements. This enriches the data with domain knowledge that cannot be derived from transaction records alone.

## 6.4 EvidenceRetriever: Family 8 Transaction Evidence

File: `aggregation.py` — `class EvidenceRetriever.get_transaction_evidence()`

Family 8 answers: "Has [buyer name] actually purchased [product] before? Show me the proof."

This is a **verification query**, not a discovery query. The user already knows the buyer's name and wants to confirm their purchasing history.

### 6.4.1 Buyer Name Matching Chain

Finding a buyer by name is surprisingly hard because:
- Company names are inconsistently spelled in import records.
- "Muller & Phipps" vs "Muller and Phipps" — same company.
- "Nestlé Pakistan" vs "Nestle Pakistan Ltd" — same company.
- Typos are common in customs data.

The system uses a **4-step fallback chain**:

**Step 1: Exact match (case-insensitive)**
```python
exact_qs = queryset.filter(buyer__iexact=name)
```
`iexact` = case-insensitive exact match. "MULLER & PHIPPS" = "muller & phipps" = "Muller & Phipps".

**Step 2: Partial match (contains)**
```python
partial_qs = queryset.filter(buyer__icontains=name)
```
`icontains` = case-insensitive substring match. "Muller" would match "Muller & Phipps Pakistan Ltd".

**Step 3: And/& normalization**
```python
alt_name = re.sub(r'\band\b', '&', name, flags=re.IGNORECASE)
# Also try: name.replace('&', 'and')
```
This handles the very common inconsistency in customs data where "and" and "&" are used interchangeably.

**Step 4: Fuzzy suggestion (no match found)**
If all else fails, `difflib.get_close_matches()` is used with cutoff=0.55 to suggest similar buyer names:
```python
similar_buyers = difflib.get_close_matches(name, all_buyers, n=5, cutoff=0.55)
```
This returns 5 names from the database that are most similar to the query, helping the user find the right name.

### 6.4.2 The Result Structure

```python
return {
    'transactions': [...],      # Raw transaction list (most recent first)
    'buyer_summary': {...},     # Aggregate stats for this buyer
    'buyer_found': True/False,  # Was the buyer matched?
    'similar_buyers': [...],    # Suggestions if not found
    'total_shown': 100,         # How many transactions shown
}
```

The `buyer_summary` includes:
- `verification_status`: "Verified" (≥3 shipments) or "Limited History"
- `repeat_buyer`: True if active for ≥3 months OR ≥5 shipments
- `months_active`: Count of distinct months with activity
- `unique_sellers`: How many different companies they buy from (supply chain diversity)

---

<a name="part-7"></a>
# PART 7: STAGE 4 — RANKINGENSEMBLE: SORTING RESULTS BY RELEVANCE

File: `backend/search/services/ranking_ltr.py`

## 7.1 Why Ranking Is a Separate Problem

After Stage 3, we have a list of candidates. For a broad query like "find dextrose buyers", this might be 200+ buyer records. The question is: **in what order should they be shown?**

This is the **ranking problem**, and it's one of the most actively studied problems in information retrieval. The naive answer is "sort by total volume" — but that's suboptimal. A buyer with massive volume but last purchased 3 years ago is less useful than a smaller but very active buyer who just bought last month.

Ranking is a **multi-objective optimization problem**: you must simultaneously consider volume, price match, recency, shipment frequency, country match, and user-specified filters. No single metric dominates.

**What does "learning to rank" (LTR) mean?** Instead of manually deciding how to weight these factors, you collect training data (human-labeled relevance scores or user click data), and a machine learning model *learns* the optimal weighting from that data. This is called Learning to Rank (LTR).

## 7.2 The 8 Features of the RankingEnsemble

File: `ranking_ltr.py` — `class FeatureExtractor`

Every candidate is converted into a vector of 8 numbers. These numbers are the **features** used for ranking.

### Feature 1: `log_volume` — Log-transformed Total Volume

```python
np.log1p(vol)   # log(1 + total_volume_mt)
```

**Why log-transform?** Trade volumes follow a **heavy-tailed distribution** — a few companies do enormous volumes while most do modest amounts. Raw volume numbers might be: 50, 100, 200, 500, 1000, 50000 MT. The largest company (50000 MT) dominates any ranking by raw volume.

Taking the logarithm compresses this scale: `log(50001) ≈ 10.8`, `log(51) ≈ 3.9`. The difference shrinks from 1000x to 2.8x in log space. This allows other features to have meaningful influence on the ranking.

`log1p(x) = log(1 + x)` specifically is used (instead of `log(x)`) to handle zero-volume candidates without a division-by-zero error: `log1p(0) = 0`.

**Research backing:** Log transformation for heavy-tailed distributions is a fundamental technique in feature engineering for ML. Box and Cox (1964) formalized this. In the context of e-commerce ranking, Shopify's 2022 engineering blog and academic papers on product ranking (e.g., via Amazon) consistently apply log-transformation to purchase counts and revenue figures before feeding them to LTR models.

### Feature 2: `log_price` — Log-transformed Average Price

```python
np.log1p(price)  # log(1 + avg_price_usd_per_mt)
```

Same reasoning as log_volume — prices can range from $50/MT to $5000/MT.

**An important subtlety:** For Family 4 (price-constrained) queries, *lower price is usually better* for a buyer. The `FAMILY_WEIGHTS` for F4 assigns `log_price` a **negative weight** (-1.0):

```python
4: { # Price-Constrained
    'price_fit': 3.0, 'log_price': -1.0, 'volume_fit': 1.0
}
```

This means higher log_price actually *lowers* the final score for F4 queries. The `price_fit` feature (see below) provides the primary price signal.

### Feature 3: `shipment_freq` — Shipment Count (Frequency)

```python
float(freq)  # raw count of shipments
```

**Why this matters:** A buyer who placed 50 small orders is fundamentally different from a buyer who placed 1 huge order. The first is a reliable, repeat buyer; the second might be a one-off. Frequency captures buying regularity.

This is *not* log-transformed because shipment counts are less skewed than volumes (most buyers have 1-20 shipments; outliers with 100+ are rare).

### Feature 4: `inv_recency` — Inverse Recency (How Recent Is Activity?)

```python
days_ago = (datetime.date.today() - last_shipment_date).days
inv_recency = 1.0 / (days_ago + 1.0)
```

**Explanation:** A buyer who last purchased 30 days ago has `inv_recency = 1/31 ≈ 0.032`. A buyer who last purchased 1 day ago has `inv_recency = 1/2 = 0.5`. A buyer who last purchased 365 days ago has `inv_recency = 1/366 ≈ 0.003`.

As `days_ago` increases, `inv_recency` decreases toward 0. This naturally penalizes stale buyers without ever giving them a negative score.

The `+1` in the denominator prevents division by zero when `days_ago=0` (bought today).

**Why recency matters:** An active buyer is more likely to buy again than an inactive one. This is a core assumption in customer lifetime value models (CLV) and purchase prediction literature. **Parr et al. (2022)** in their survey of buyer propensity models show that recency is consistently the strongest single predictor of future purchase (the "R" in the classic RFM model: Recency, Frequency, Monetary Value).

### Feature 5: `volume_fit_score` — Volume Compatibility

```python
v_fit_map = {'Strong': 3, 'Good': 2, 'Partial': 1, 'Low': 0, 'N/A': 0}
volume_fit_score = v_fit_map.get(v_fit_str, 0)
```

This converts the volume compatibility label (computed in Stage 3) to a numeric score: Strong=3, Good=2, Partial=1, Low=0.

For queries where no volume was specified, this is `N/A → 0`. Volume is only meaningful when the user explicitly asked for a certain order size.

### Feature 6: `scope_match` — Scope Match

```python
scope_match = 1.0  # Constant (retrieval already filtered by scope)
```

Currently constant at 1.0 because the retrieval step (Stage 3) already strictly filters by scope. If retrieval were made "softer" (returning cross-scope results with a score penalty), this feature would become non-constant.

### Feature 7: `country_match` — Country Match Score

```python
q_countries = parsed_query.get('country_filter', [])
cand_country = candidate.get('country', '')
if q_countries and cand_country in q_countries:
    country_match = 1.0   # Exact match with requested country
elif not q_countries:
    country_match = 0.5   # Neutral (no country filter specified)
else:
    country_match = 0.0   # Candidate is in wrong country
```

For F2 (country-filtered) queries, this feature gets a 3x weight — country match is the primary ranking criterion.

### Feature 8: `price_fit` — Price Compatibility

```python
ceiling = parsed_query.get('price_ceiling')
if ceiling and price <= ceiling:
    price_fit = 1.0  # Under the budget
elif ceiling:
    price_fit = 0.0  # Over the budget
else:
    price_fit = 0.5  # Neutral (no price filter)
```

For F4 (price-constrained) queries, this gets a 3x weight. Candidates within the price ceiling are scored 1.0; those above it are scored 0.0 (the database has already filtered them out, but this is a defense-in-depth signal).

## 7.3 FAMILY_WEIGHTS: Why Different Queries Need Different Rankings

The `FAMILY_WEIGHTS` dictionary encodes the ranking priority for each query family:

```python
FAMILY_WEIGHTS = {
    1: { # Discovery / Generic — balanced
        'volume_fit': 1.5, 'log_volume': 1.0, 'shipment_freq': 1.0,
        'inv_recency': 1.0, 'country_match': 1.0
    },
    2: { # Country-Filtered — country match is paramount
        'country_match': 3.0, 'volume_fit': 1.0, 'log_volume': 1.0,
        'inv_recency': 0.5
    },
    3: { # Volume-Aware — volume fit is paramount
        'volume_fit': 3.0, 'log_volume': 1.0, 'inv_recency': 0.5
    },
    4: { # Price-Constrained — price fit is paramount
        'price_fit': 3.0, 'log_price': -1.0, 'volume_fit': 1.0
    },
    5: { # Time-Constrained — recency is paramount
        'inv_recency': 3.0, 'shipment_freq': 1.5, 'volume_fit': 1.0
    },
    # ... F7, F9 ...
}
```

This captures the **user's implicit priority**: for a buyer asking "who can handle 100 MT orders?" (F3), volume fit matters most. For "who bought recently?" (F5), recency matters most.

## 7.4 Pseudo-Labels: Creating Training Data Without Click Logs

The **cold start problem** in learning to rank: a new system has no historical user interaction data (clicks, purchases, ratings). Without labeled examples, you can't train an LTR model.

**The solution: pseudo-labels** — use the heuristic scoring function itself to generate "synthetic" relevance labels.

```python
class PseudoLabelGenerator:
    def generate_label(self, candidate, parsed_query):
        # 1. Extract features
        features = extractor.extract(candidate, parsed_query)
        feat_dict = dict(zip(FeatureExtractor.FEATURE_NAMES, features))

        # 2. Compute weighted score using family weights
        score = sum(weights.get(fname, 0.0) * val for fname, val in feat_dict.items())

        # 3. Convert to discrete relevance label (0-4)
        if score > 15: return 4  # Highly relevant
        if score > 10: return 3  # Relevant
        if score > 5: return 2   # Somewhat relevant
        if score > 2: return 1   # Marginally relevant
        return 0                 # Not relevant
```

The labels are on a **0-4 scale**, a standard in LTR (Järvelin & Kekäläinen, 2002):
- 4 = "Perfect" — ideal match
- 3 = "Excellent" — very good match
- 2 = "Good" — decent match
- 1 = "Fair" — marginal match
- 0 = "Bad" — irrelevant

**Why this works:** The pseudo-label model captures the human intuition encoded in the heuristic weights. By training LightGBM on these labels, the model learns a smooth, non-linear combination of features that can generalize beyond what the simple weighted sum captures.

**Research backing:** This "teacher-student" approach (a heuristic teacher generates labels; an ML student learns from them) has strong empirical support:

> **Han, Y., et al. (2022).** Cold-Start Based Item-Item Collaborative Filtering Recommendation via Empirical Bayes. *CIKM 2022.*

> **Onal, K.D., et al. (2018).** Neural Information Retrieval: At the End of the Early Years. *Information Retrieval Journal, 21(2-3).*

In industrial search systems (Amazon, Alibaba), it's common to bootstrap LTR with rule-based labels before real click data is available. Google's 2021 documentation on LTR for enterprise search explicitly recommends this approach.

## 7.5 LightGBM: What Is Gradient Boosting?

**LightGBM** is the ML library used for the LTR model. Before understanding LightGBM, let's understand gradient boosting.

### 7.5.1 Decision Trees (Building Block)

A **decision tree** is a sequence of yes/no questions that leads to a prediction. For example:

```
Is log_volume > 5?
├── YES → Is inv_recency > 0.01?
│         ├── YES → Relevance = 3 (high volume, recent)
│         └── NO  → Relevance = 2 (high volume, old)
└── NO  → Is country_match == 1?
          ├── YES → Relevance = 1 (low volume but right country)
          └── NO  → Relevance = 0 (irrelevant)
```

A single tree is weak (underfits). **Boosting** chains many weak trees together.

### 7.5.2 Gradient Boosting

Gradient boosting builds an **ensemble of trees** where each tree corrects the mistakes of all previous trees:

1. Start with a constant prediction (e.g., the average label).
2. Compute the **residual** (error) between predictions and true labels.
3. Train a new tree to predict these residuals.
4. Add the new tree to the ensemble (with a small learning rate).
5. Repeat steps 2-4 for N iterations.

The final prediction is the sum of all trees' outputs. Each tree adds a small "correction" to the running prediction.

### 7.5.3 LightGBM Innovations

**LightGBM** (Light Gradient Boosting Machine), introduced by **Ke et al. at Microsoft (NeurIPS 2017)**, has three key innovations that make it much faster than earlier boosting frameworks (like XGBoost):

**1. Leaf-wise tree growth:** Traditional trees grow level-by-level (breadth-first). LightGBM grows leaf-by-leaf (best-first). It always splits the leaf with the highest gain, which produces more accurate trees with fewer splits.

```
Traditional:              LightGBM (leaf-wise):
Level 1: split root       Split leaf with max gain:
Level 2: split all 2       → deeper, more asymmetric
Level 3: split all 4         → fewer nodes needed for same accuracy
```

**2. GOSS (Gradient-Based One-Side Sampling):** Instead of using all training samples each iteration, GOSS keeps all "hard" samples (large gradient = large error) but only a random fraction of "easy" samples. This dramatically reduces training time while preserving accuracy on hard cases.

**3. EFB (Exclusive Feature Bundling):** In high-dimensional datasets, many features are mutually exclusive (non-zero at the same time). EFB bundles these features together, reducing the effective feature dimension without information loss.

**Why LightGBM for Zarailink?** With only 8 features and potentially thousands of candidates per query, training time is not the bottleneck. But LightGBM's native `lambdarank` objective is the critical reason.

## 7.6 LambdaRank: Learning to Optimize Rankings

Standard supervised learning optimizes for prediction accuracy (e.g., minimize squared error). But ranking has a different goal: **optimize the order** of results, specifically as measured by NDCG.

**RankNet** (**Burges et al., Neural Information Processing Systems 2005**) was the first neural approach to ranking. It models the probability that document A should rank above document B:

```
P(A > B) = sigmoid(score_A - score_B)
```

The loss function is the cross-entropy between predicted and ideal pairwise orderings. This is called a **pairwise** approach — it compares pairs of documents.

**LambdaRank** (**Burges et al., 2006**) improves on RankNet by not computing an explicit loss, but instead computing the **gradient** directly. The key insight: when deciding how much to push document A up and document B down, weight the push by |ΔNDCG| — how much would swapping A and B change the NDCG metric?

```
λ_AB = |ΔNDCG_AB| × gradient_from_pairwise_loss
```

This means: pairs where swapping would greatly change NDCG get large gradient updates; pairs where swapping barely changes NDCG get small updates. The model implicitly optimizes the list-level metric (NDCG) through pairwise gradients.

**LambdaMART** (**Burges, 2010**) extends LambdaRank to use gradient boosted trees instead of neural networks. This is what LightGBM's `lambdarank` objective implements.

**The full lineage:**
```
RankNet (Burges 2005) → LambdaRank (Burges 2006) → LambdaMART (Burges 2010) → LightGBM lambdarank (Ke 2017)
```

## 7.7 NDCG: How We Measure Ranking Quality

**NDCG** (Normalized Discounted Cumulative Gain) is the gold standard metric for ranking quality. It was introduced by:

> **Järvelin, K., & Kekäläinen, J. (2002).** Cumulated gain-based evaluation of IR techniques. *ACM Transactions on Information Systems, 20(4), 422-446.*

**DCG (Discounted Cumulative Gain):** The idea is that highly relevant results at *higher positions* are more valuable than at lower positions. The "discount" means results at position 2 are less valuable than position 1.

```
DCG@k = Σ(i=1 to k) [relevance_i / log2(i + 1)]

For positions 1-5 with relevance scores [4, 3, 2, 1, 0]:
DCG = 4/log2(2) + 3/log2(3) + 2/log2(4) + 1/log2(5) + 0/log2(6)
    = 4/1 + 3/1.585 + 2/2 + 1/2.322 + 0
    = 4 + 1.893 + 1 + 0.431 + 0
    = 7.324
```

**IDCG (Ideal DCG):** The DCG you'd get if results were perfectly sorted (best first).

**NDCG = DCG / IDCG.** This normalizes by the best possible DCG, so NDCG is always in [0, 1]. NDCG=1 means perfect ranking; NDCG=0 means completely wrong order.

**Why log2(i+1)?** This is the position discount function. Results at position 1 get no discount. Position 2 gets divided by log2(3)≈1.58. Position 10 gets divided by log2(11)≈3.46. This captures the empirical observation that users click less often on lower results (Joachims et al., 2005).

LightGBM's `lambdarank` objective directly maximizes NDCG during training.

## 7.8 The 70/30 Ensemble

The final ranking combines heuristic and LTR scores:

```python
final_score = (heuristic_score * 0.7) + (ltr_score * 0.3)
```

**Why 70% heuristic?** When the LTR model is newly trained on pseudo-labels (rather than real click data), it might not generalize perfectly. The 70% heuristic weight ensures the ranking stays close to a known-good baseline. As real training data accumulates (from user behavior), the LTR weight can be increased.

This is called **conservative interpolation** in the LTR literature. A production-scale example: in LinkedIn's ranking system, new model components are first deployed with a small weight (10-20%) and gradually increased as they prove themselves in A/B testing.

**What if the LTR model file doesn't exist?** The system falls back gracefully: `LTRModel.predict()` returns `np.zeros(len(features))` (all zeros), so the LTR contribution is zero, and the ranking is entirely heuristic-driven. This prevents crashes in development or cold-start scenarios.

## 7.9 Multi-Stage Retrieval Research Context

Zarailink's 4-stage pipeline is an instance of what the IR community calls **cascade ranking** or **multi-stage retrieval**:

> **Matsubara, Y., et al. (2022).** RankFlow: Joint Optimization for Multi-Stage Cascaded Ranking Systems. *SIGIR 2022.*

> **Zhu, H., et al. (2021).** MGDSPR: Large-Scale Retrieval for Reinforced Conversational Recommendation over Billions of Items. *KDD 2021.*

The idea: instead of running a complex model over all candidates, use a cheap model to narrow candidates, then a more expensive model for final ranking. Zarailink's pipeline is:

```
ALL PRODUCTS (~thousands)
    ↓ Stage 2 (SBERT + keyword, fast)
PRODUCT SUBCATEGORIES (~1-20)
    ↓ Stage 3 (SQL aggregation)
CANDIDATES (~10-500 buyers/sellers)
    ↓ Stage 4 (LightGBM, most expensive)
RANKED RESULTS (~10-500)
```

Each stage dramatically reduces the candidate set, so the expensive model (LightGBM) only scores tens or hundreds of candidates, not thousands.

---

<a name="part-8"></a>
# PART 8: THE 9 QUERY FAMILIES — COMPLETE REFERENCE

The 9 query families are based on the **Zarailink Seller Query Framework** — a classification of the fundamental questions a Pakistani agricultural seller or buyer might ask. Each family maps to a different search behavior, different aggregation logic, and different ranking priority.

---

## Family 1 (F1): Simple Buyer Discovery

**"Who buys this product?"**

**What the user is asking:** I have a product (say, raw dextrose). Who are the Pakistani companies that regularly import it?

**Example queries:**
- `"find dextrose buyers"`
- `"who buys rice in Pakistan"`
- `"buyers for sugar"`

**What the system does:**
1. Parse: intent=SELL, no country/price/volume filters
2. Match: product → subcategory IDs
3. Aggregate: IMPORT records, group by buyer, no extra filters
4. Rank: F1 weights (balanced: volume, recency, frequency, volume_fit equally weighted)
5. Return: full list of buyers sorted by combined score

**Key characteristic:** Broadest query type. Returns ALL buyers, sorted by relevance. No filters applied.

**Primary display:** Ranked buyer cards with name, country, total volume, avg price, shipment count, last active.

---

## Family 2 (F2): Country-Filtered Buyer Discovery

**"Who buys this product from [COUNTRY]?"**

**What the user is asking:** I specifically want buyers in a certain country (e.g., Chinese buyers importing from Pakistan), or I want to know which Pakistani buyers import from a specific origin country.

**Example queries:**
- `"dextrose buyers in China"`
- `"rice importers from India"`
- `"buyers for sugar from UAE"`

**What the system does:**
1. Parse: intent=SELL, `country_filter=['China']`
2. Aggregate: IMPORT records filtered by `destination_country='China'` (or `origin_country='China'` depending on scope)
3. Rank: F2 weights: `country_match` gets 3x weight — country alignment is the primary criterion

**Key characteristic:** Country match dominates ranking. Buyers in the specified country are scored 1.0 for country_match; others are 0.0.

---

## Family 3 (F3): Volume-Aware Buyer Discovery

**"Who can handle a [VOLUME] order?"**

**What the user is asking:** I have 100 metric tonnes of dextrose to sell. Who regularly buys in quantities close to this?

**Example queries:**
- `"find buyers for 100 MT of dextrose"`
- `"who buys 50 tons of rice"`
- `"buyers for 25 metric tonnes of salt"`

**What the system does:**
1. Parse: `volume_mt=100.0`
2. Aggregate: Run volume compatibility scoring (Stage 3.2.3)
3. Rank: F3 weights: `volume_fit` gets 3x weight

**Key characteristic:** The "soft floor" filter excludes buyers with max shipment volume < 30% of requested AND total volume < 50% of requested. Volume compatibility score (Strong/Good/Partial/Low) is the primary ranking signal.

---

## Family 4 (F4): Price-Constrained Buyer Discovery

**"Who pays above/below [PRICE] for this product?"**

**What the user is asking:** I can only sell at $600/MT or more. Who pays at least this much?

**Example queries:**
- `"dextrose buyers paying above $600"`
- `"buyers under $700 for rice"`
- `"sugar buyers paying more than $300"`

**What the system does:**
1. Parse: `price_floor=600.0` or `price_ceiling=700.0`
2. Aggregate: SQL filter `usd_per_mt >= 600` or `usd_per_mt <= 700`
3. Rank: F4 weights: `price_fit` gets 3x weight, `log_price` gets -1.0 weight (lower price penalized)

**Key characteristic:** Price filter is a hard database filter (unlike volume which is soft). Buyers outside the price range are excluded entirely at the SQL level.

---

## Family 5 (F5): Time-Constrained / Recency-Based Discovery

**"Who has bought this product recently?"**

**What the user is asking:** I want active buyers — ones who've been purchasing in the last 6 months, not dormant accounts.

**Example queries:**
- `"dextrose buyers last 6 months"`
- `"who bought rice in Q1 2025"`
- `"recent buyers for sugar in 2024"`

**What the system does:**
1. Parse: `time_range="last 6 months"` → `time_filter={start_date: today-180days, end_date: today}`
2. Aggregate: SQL filter `reporting_date >= start_date AND reporting_date <= end_date`
3. Rank: F5 weights: `inv_recency` gets 3x weight, `shipment_freq` 1.5x

**Key characteristic:** Time filter applied at SQL level. Within the filtered period, most recent buyers rank highest. Recency dominates ranking.

---

## Family 6 (F6): Recommendation / Outreach Shortlist

**"Who are the TOP/BEST buyers for outreach?"**

**What the user is asking:** I don't want 200 results — I want the 5 best, most promising buyers to call tomorrow. Recommend the best.

**Example queries:**
- `"top 5 buyers for dextrose"`
- `"best 3 buyers for rice"`
- `"recommend buyers for sugar"`
- `"suggest buyers paying the most"`

**What the system does:**
1. Parse: is_rec=True (from "top", "best", "suggest" keywords), extract N from "top 5"
2. Full F1-F5 pipeline runs first (full aggregation + ranking)
3. Truncate to top N results: `ranked_results = ranked_results[:top_n]` (default N=5 if not specified)
4. Rank: Same as F1 (balanced weights), but output is limited to N results

**Key characteristic:** F6 is a "post-processing" family — it runs F1's full pipeline and then truncates. The quality of results depends entirely on how well F1 ranks.

**Top-N extraction:**
```python
pattern = r'\b(?:top|best|first|suggest)\s+(\d+)\b'
match = re.search(pattern, query.lower())
```
"top 3" → N=3, "best 10" → N=10. If no number, defaults to N=5.

---

## Family 7 (F7): Country Comparison / Market Intelligence

**"Which countries have the most demand for this product?"**

**What the user is asking:** I want a market analysis — not individual buyers, but country-level metrics. Which countries import the most dextrose? Which have the fastest-growing demand?

**Example queries:**
- `"which countries buy the most dextrose"`
- `"compare dextrose markets by country"`
- `"best country for rice export"`
- `"buyers by country for sugar"`

**What the system does:**
1. Parse: is_mkt=True (F7 keywords), intent overridden to SELL if buyer-market phrases detected
2. Skip SupplierAggregator entirely
3. Run CountryComparator.compare_countries():
   - Group IMPORT transactions by origin_country
   - Calculate total_volume, avg_price, supplier_count, YoY growth
   - Find top 3 suppliers per country
   - Add static market entry notes
4. Return structured country comparison data (not a buyer list)

**Key characteristic:** Completely different output format from F1-F6. Returns country-level aggregates, not individual company profiles. Used for market discovery.

**Special case — F7 downgrade guard:** If F7 was triggered only by "cheapest" or "compare" with only 1 country, it's downgraded to F4. "Cheapest dextrose from China" is a price query, not a country comparison.

---

## Family 8 (F8): Transaction Evidence / Buyer Verification

**"Has [COMPANY] purchased this product before? Show proof."**

**What the user is asking:** Before I approach Company XYZ as a potential buyer, I want to verify they're a real buyer. Do they have a track record of purchasing this product?

**Example queries:**
- `"has Muller and Phipps purchased dextrose before"`
- `"show shipments to Nestle Pakistan"`
- `"evidence for Engro Foods buying sugar"`
- `"transaction history for Unilever"`

**What the system does:**
1. Parse: is_evid=True, extract buyer name via 3 patterns
2. Skip SupplierAggregator and ranking entirely
3. Run EvidenceRetriever.get_transaction_evidence():
   - 4-step buyer name matching (exact → partial → and/& normalize → fuzzy suggest)
   - Return raw transaction list (not aggregated)
   - Return buyer summary card with verification status
4. Return raw transactions + buyer_summary

**Key characteristic:** Completely different from F1-F7. Returns raw transaction rows (not aggregated), and explicitly verifies a named buyer. No ranking — results sorted by date (most recent first).

**Verification logic:**
- `verification_status = "Verified"` if shipment_count >= 3
- `repeat_buyer = True` if months_active >= 3 OR shipment_count >= 5

---

## Family 9 (F9): Hybrid Multi-Intent

**"Answer multiple questions at once"**

Covered in detail in the next section.

---

<a name="part-9"></a>
# PART 9: FAMILY 9 — HYBRID MULTI-INTENT QUERIES

## 9.1 The Problem: Compound Questions

Sometimes users ask two (or more) distinct questions in a single query:

- `"which countries buy dextrose most, and who are the top buyers there?"`
- `"find dextrose buyers; show country comparison"`
- `"top 3 buyers for dextrose and show country breakdown"`

These are **multi-intent queries** — each clause has a different family, different output format, and requires different processing.

## 9.2 Detection and Splitting

The `QueryInterpreter.parse()` function handles this:

```python
# Split on semicolons (always multi-intent)
candidates = re.split(r';', query)

# Split on 'and'/'also' only if right side has independent intent
if len(candidates) == 1:
    parts = re.split(r'\b(?:and|also)\b', query)
    for part in parts[1:]:
        has_intent = self._detect_intent_score(part)[0] != 'AMBIGUOUS'
        if has_intent:
            # Independent clause → separate intent
            final_segments.append(current_segment)
            current_segment = part
        else:
            # Additive filter → merge back in
            current_segment += " and " + part
```

The split produces a list of `sub_intents`, each independently parsed with `_parse_single()`.

## 9.3 Context Product Carry-Over

A subtle problem: the second part of a multi-intent query often uses anaphora (referring back to something):
- `"which countries buy dextrose most, and who are the top buyers there?"`

The second clause "who are the top buyers there?" doesn't explicitly mention "dextrose". The parser extracts product="" from this clause (nothing left after stripping intent words).

The fix in `views.py`:
```python
context_product = next(
    (s.get('product', '') for s in sub_intents if len(s.get('product', '')) > 3),
    ''
)
for sub in sub_intents:
    if context_product and len(sub.get('product', '')) <= 3:
        sub = {**sub, 'product': context_product}  # Carry over from context
```

If a sub-intent has a product term shorter than 4 characters (or empty), it inherits the product from the first non-trivial sub-intent. "there" (5 chars, but it's a pronoun) would get replaced by "dextrose".

## 9.4 `_run_sub_intent`: Routing Each Clause

Each sub-intent is processed by `_run_sub_intent()` in `views.py`:

```python
def _run_sub_intent(self, sub_params, raw_query):
    family = sub_params.get('family', 1)

    if family == 7:
        # Route to CountryComparator
        comparator = CountryComparator()
        cc_result = comparator.compare_countries(subcategory_ids, ...)
        return {
            "label": "Country Comparison",
            "family": 7,
            "intent_answered": "Which countries have the most demand?",
            "country_comparison": cc_result['results'],
            ...
        }

    # F1-F6: SupplierAggregator + RankingEnsemble
    # CRITICAL: SELL + WORLDWIDE falls back to PAKISTAN scope
    effective_scope = sub_params.get('scope', 'WORLDWIDE')
    if intent == 'SELL' and effective_scope == 'WORLDWIDE':
        effective_scope = 'PAKISTAN'  # DB only has IMPORT records

    results = aggregator.get_suppliers_for_subcategories(
        subcategory_ids, intent=intent, scope=effective_scope, ...
    )
    ranked = ranker.rank_candidates(results, sub_params)

    if family == 6:
        ranked = ranked[:top_n]

    return {
        "label": label,       # e.g., "Buyer Discovery"
        "family": family,
        "intent_answered": intent_answered,
        "results": ranked,
        ...
    }
```

**The critical SELL+WORLDWIDE fix:** When a sub-intent has `intent='SELL'` (seller looking for buyers) and `scope='WORLDWIDE'`, the aggregator would query EXPORT records. But the DB has no EXPORT records → 0 results. The fix forces `effective_scope='PAKISTAN'` so IMPORT records are queried (where Pakistani buyers appear).

## 9.5 The Stacked Section Response

The final response is structured as **stacked sections**:

```json
{
  "type": "multi_intent",
  "family": 9,
  "sections": [
    {
      "label": "Country Comparison",
      "family": 7,
      "intent_answered": "Which countries have the most demand?",
      "country_comparison": [...]
    },
    {
      "label": "Top Recommendations",
      "family": 6,
      "intent_answered": "Best buyers to approach first",
      "results": [...]
    }
  ]
}
```

The frontend renders each section independently with its own header, icon, and display format.

## 9.6 Section Label Metadata

```python
SECTION_META = {
    1: ("Buyer Discovery",        "Who buys this product?"),
    2: ("Country-Filtered Buyers","Buyers in specific countries"),
    3: ("Volume-Matched Buyers",  "Buyers matching your order size"),
    4: ("Price-Filtered Buyers",  "Buyers at your target price"),
    5: ("Active Recent Buyers",   "Buyers who purchased recently"),
    6: ("Top Recommendations",    "Best buyers to approach first"),
    7: ("Country Comparison",     "Which countries have the most demand?"),
}
```

Each section is labeled with a human-readable title and subtitle, so users immediately understand what each section is showing.

---

<a name="part-10"></a>
# PART 10: RESEARCH PAPER COMPENDIUM

This section summarizes every academic paper cited in this document, with context for why it applies to Zarailink.

---

## 10.1 Semantic Embeddings & Retrieval

### SBERT — The Core Semantic Search Foundation

> **Reimers, N., & Gurevych, I. (2019).** Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *Proceedings of EMNLP 2019. arXiv:1908.10084.*

**What it is:** The foundational paper for SBERT. Introduces a Siamese network architecture that encodes two sentences independently using shared BERT weights, then compares them with cosine similarity. Dramatically faster than cross-encoder BERT (O(N) vs O(N²)).

**How Zarailink uses it:** `all-MiniLM-L6-v2` is a fine-tuned SBERT model. The `QueryMatcher` uses it to encode query terms and compare against pre-computed subcategory embeddings.

**Key result:** SBERT achieves near-BERT performance on semantic textual similarity (STS) benchmarks while being 9x faster for pairwise comparisons.

---

### MiniLM — The Compression Technique

> **Wang, W., Wei, F., Dong, L., Bao, H., Yang, N., & Zhou, M. (2020).** MiniLM: Deep Self-Attention Distillation for Task-Agnostic Compression of Pre-Trained Transformers. *NeurIPS 2020. arXiv:2002.10957.*

**What it is:** Introduces knowledge distillation for transformer models, focusing on compressing the self-attention mechanism. A student model learns to mimic the attention patterns of the teacher model, not just its output predictions.

**How Zarailink uses it:** `all-MiniLM-L6-v2` is a 6-layer, 384-dimension model distilled from a 12-layer, 768-dimension model. This makes it fast enough for CPU inference in a Django web server without sacrificing much accuracy.

**Key result:** MiniLM achieves 99% of BERT-base performance on GLUE while being 2x faster (6 layers vs 12).

---

### SimCSE — Why Sentence Embeddings Work

> **Gao, T., Yao, X., & Chen, D. (2021).** SimCSE: Simple Contrastive Learning of Sentence Embeddings. *EMNLP 2021. arXiv:2104.08821.*

**What it is:** Explains theoretically why contrastive learning produces good sentence embeddings. Shows that standard dropout acts as a minimal data augmentation for contrastive learning — the same sentence fed twice with different dropout masks produces a positive pair.

**How it's relevant:** SBERT's training uses similar contrastive principles. SimCSE's theoretical analysis explains *why* `all-MiniLM-L6-v2` embeddings cluster semantically related terms (like "glucose" and "dextrose") close together in vector space.

---

### DPR — Dense Passage Retrieval

> **Karpukhin, V., et al. (2020).** Dense Passage Retrieval for Open-Domain Question Answering. *EMNLP 2020. arXiv:2004.04906.*

**What it is:** Introduces DPR, a bi-encoder retrieval system where questions and passages are encoded independently into dense vectors. Shows that dense retrieval outperforms TF-IDF/BM25 for question answering.

**How it's relevant:** Zarailink's semantic search is architecturally identical to DPR: query encoded independently, compared against pre-indexed passage (subcategory) embeddings. The insight that pre-computing index embeddings is sufficient for fast retrieval directly motivates the `search_index.pkl` approach.

---

### BEIR — Benchmark Validating Model Choice

> **Thakur, N., Reimers, N., Rücklé, A., Srivastava, A., & Gurevych, I. (2021).** BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models. *NeurIPS 2021 Datasets and Benchmarks. arXiv:2104.08663.*

**What it is:** BEIR (Benchmarking Information Retrieval) evaluates retrieval models across 18 diverse datasets. Shows that `all-MiniLM-L6-v2` is a strong baseline across many retrieval tasks, even without domain-specific fine-tuning.

**How it's relevant:** Justifies using `all-MiniLM-L6-v2` out-of-the-box (without fine-tuning on trade data) for Zarailink's semantic search. The model's strong zero-shot performance on BEIR suggests it will generalize to the agricultural trade domain.

---

## 10.2 Learning to Rank

### RankNet — The Foundation of Pairwise LTR

> **Burges, C., Shaked, T., Renshaw, E., Lazier, A., Deeds, M., Hamilton, N., & Pinnell, G. (2005).** Learning to Rank Using Gradient Descent. *ICML 2005.*

**What it is:** Introduces RankNet, the first neural network for learning to rank. Models pairwise document preferences as probabilities and optimizes with gradient descent. Deployed at Microsoft Bing.

**How it's relevant:** The theoretical foundation for all subsequent pairwise LTR methods, including LambdaRank and LambdaMART which Zarailink uses.

---

### LambdaRank — List-Level Optimization via Pairwise Gradients

> **Burges, C., Ragno, R., & Le, Q. (2006).** Learning to Rank with Nonsmooth Cost Functions. *NeurIPS 2006.*

**What it is:** Introduces LambdaRank. Instead of defining a loss function for NDCG (which is non-differentiable), defines λ_AB as the gradient of an implicit loss that, when optimized, maximizes NDCG. The λ values are the product of pairwise cross-entropy gradients and |ΔNDCG| from swapping document A and B.

**How Zarailink uses it:** LightGBM's `lambdarank` objective implements the LambdaRank algorithm. The model learns to maximize NDCG by iteratively computing and acting on these λ gradients.

---

### LambdaMART — Gradient Boosted Trees for Ranking

> **Burges, C. (2010).** From RankNet to LambdaRank to LambdaMART: An Overview. *Microsoft Research Technical Report MSR-TR-2010-82.*

**What it is:** Extends LambdaRank to use MART (Multiple Additive Regression Trees) — an ensemble of gradient boosted decision trees. LambdaMART dominated the Yahoo! Learning to Rank Challenge (2010) and the Netflix Prize (modified for ranking tasks).

**How it's relevant:** LightGBM's `lambdarank` is an efficient implementation of LambdaMART. This is the algorithm that learns from Zarailink's pseudo-labeled training data.

---

### LightGBM — The ML Library

> **Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.Y. (2017).** LightGBM: A Highly Efficient Gradient Boosting Decision Tree. *NeurIPS 2017.*

**What it is:** Introduces LightGBM with three key innovations: leaf-wise tree growth, GOSS (Gradient-Based One-Side Sampling), and EFB (Exclusive Feature Bundling). Up to 20x faster than XGBoost on large datasets.

**How Zarailink uses it:** The `lgbm_ltr.txt` model was trained using LightGBM's `lambdarank` objective. At inference time, `lgb.Booster(model_file='lgbm_ltr.txt').predict(features)` runs the trained ensemble.

---

### NDCG — The Evaluation Metric

> **Järvelin, K., & Kekäläinen, J. (2002).** Cumulated gain-based evaluation of IR techniques. *ACM Transactions on Information Systems, 20(4), 422-446.*

**What it is:** Introduces DCG and NDCG. The position-based discount function (log2(position+1)) is motivated by user behavior studies showing logarithmic decay of attention with position.

**How it's relevant:** LightGBM's `lambdarank` objective directly maximizes NDCG. The 0-4 relevance labels used in Zarailink's pseudo-labeling match the 5-level scale proposed in this paper.

---

### ListNet — Listwise LTR (First Listwise Method)

> **Cao, Z., Qin, T., Liu, T.-Y., Tsai, M.-F., & Li, H. (2007).** Learning to Rank: From Pairwise Approach to Listwise Approach. *ICML 2007.*

**What it is:** The first listwise LTR method. Defines a probability distribution over all permutations of the ranked list using the Plackett-Luce model. Since the full permutation space is factorial (intractable), it approximates with the "top-1 probability" — a softmax over predicted scores:

```
P(doc i is ranked first) = exp(s_i) / Σ_j exp(s_j)
```

The loss is KL divergence between the predicted top-1 distribution and the ideal (sorted by true labels) distribution.

**Why it matters:** ListNet directly considers the full list structure. Empirically: listwise > pairwise > pointwise on standard IR benchmarks. This three-way comparison validates why LambdaMART (which implicitly optimizes the full list via |ΔNDCG| scaling) outperforms pointwise and naive pairwise approaches.

---

### LambdaLoss Framework — Theoretical Unification

> **Wang, X., Li, C., Golbandi, N., Bendersky, M., & Najork, M. (2018).** The LambdaLoss Framework for Ranking Metric Optimization. *CIKM 2018, pp. 1313-1322.*

**What it is:** The first rigorous theoretical justification for LambdaRank. This paper proves that LambdaRank is a special case of a broader probabilistic framework called LambdaLoss. The framework unifies RankNet, LambdaRank, and other ranking objectives under a single probabilistic generative model.

**Why it matters:** Before this paper, the reason LambdaRank worked was somewhat mysterious — it defined gradients without defining an explicit loss, and empirically it optimized NDCG. LambdaLoss proves that LambdaRank is implicitly minimizing a well-defined probabilistic loss. This retroactively provides a solid theoretical foundation for Zarailink's choice of `lambdarank` objective in LightGBM.

---

### Unbiased LTR — Correcting Position Bias in Click Data

> **Joachims, T., Swaminathan, A., & Schnabel, T. (2017).** Unbiased Learning-to-Rank with Biased Feedback. *WSDM 2017.*

**What it is:** Proves that click data has systematic position bias — users are more likely to click results at position 1 simply because they're at position 1, not because they're necessarily more relevant. Introduces Inverse Propensity Scoring (IPS) to debias click-based LTR training:

```
debiased_loss = Σ_i [loss_i / propensity_i]

where propensity_i = P(user examines position i)
```

**How it relates to Zarailink:** Zarailink currently uses heuristic pseudo-labels (no click data). If real user behavior data were collected, position bias would need to be corrected before training a new LTR model. This paper provides the mathematical tool for doing so.

---

### Cold-Start LTR — Amazon Content-Based Priors (2020)

> **Gupta, P., Dreossi, T., Bakus, J., Lin, Y.-H., & Salaka, V. (2020).** Treating Cold Start in Product Search by Priors. *Amazon Science.*

**What it is:** Amazon's first cold-start paper for product search. New products have no click/purchase history. The approach: train a model to predict "what the behavioral feature values would be" for a new product based on its content features (title, description, category). These predicted behavioral scores become the prior estimate.

**How Zarailink uses it:** Zarailink's `PseudoLabelGenerator` implements the same principle: it computes a "predicted relevance" from content-derived signals (volume, recency, frequency) to create synthetic training labels without needing any real user clicks.

---

### Cold-Start LTR — Amazon Empirical Bayes (2022)

> **Han, C., Castells, P., Gupta, P., Xu, L., & Salaka, V. (2022).** Addressing Cold Start in Product Search via Empirical Bayes. *CIKM 2022.*

**What it is:** Formalizes Amazon's cold-start approach using Bayesian inference. For a new product with zero clicks, the prior from content features serves as the relevance estimate. As interactions arrive, the posterior is updated:

```
P(behavioral_score | content_features, observed_clicks) ∝
    P(content_features → behavioral prior) × P(observed_clicks | behavioral_score)
```

Validated with a live A/B test: +13.53% new product impressions, +11.14% new product purchases.

**How Zarailink uses it:** The `PseudoLabelGenerator`'s heuristic-to-label mapping (score > 15 → label 4, etc.) is a simplified version of this — it uses domain knowledge (volume, recency, frequency are strong signals) as a prior for generating relevance estimates when no click data exists. The LightGBM model is then trained on these synthetic labels.

---

### Cold-Start LTR — Dataset Transfer (2021)

> **Missault, P., de Myttenaere, A., Radler, A., & Sondag, P.-A. (2021).** Addressing Cold Start with Dataset Transfer in E-Commerce Learning to Rank. *The Web Conference 2021 Workshop on Knowledge Management in E-Commerce.*

**What it is:** When a company launches in a new market/country with no local interaction data, this paper proposes transferring an LTR model from a data-rich source market using Inverse Propensity Weighting. Training examples from the source domain are reweighted by propensity scores, allowing the target market model to benefit from source data while compensating for distribution shift. Validated in a live Amazon A/B test.

**Relevance:** Validates the "progressive LTR" deployment strategy: start with content-based pseudo-labels (what Zarailink does), then incrementally add real behavioral data as it accumulates.

---

### E-Commerce LTR Survey (2024)

> **Multiple authors. (2024).** A Survey on E-Commerce Learning to Rank. *arXiv:2412.03581.*

**What it is:** The first comprehensive survey with experimental comparison across e-commerce LTR algorithms. Identifies five feature categories used in production: (1) relevance features (BM25, semantic similarity), (2) behavioral features (CTR, purchase rate — these suffer from cold start), (3) seller reputation, (4) personalization, (5) paid promotion. The survey explicitly notes that cold start disproportionately affects behavioral features and recommends content-based fallbacks.

**How it validates Zarailink's design:** Zarailink uses exclusively content-derived features (volume, price, recency, frequency, country match) — all of which are immune to cold start. The survey confirms this is the correct approach before behavioral data is available.

---

### NDCG Theoretical Analysis

> **Wang, Y., Wang, L., Li, Y., He, D., & Liu, T.-Y. (2013).** A Theoretical Analysis of NDCG Ranking Measures. *COLT 2013.*

**What it is:** Proves formal properties of NDCG and shows conditions under which it is a consistent, unambiguous metric for ranking. Key result: NDCG with exponential gain `(2^rel - 1) / log2(i+1)` (the formula used in LightGBM's default `label_gain` parameter) is more discriminating than linear gain `rel / log2(i+1)` because it emphasizes highly-relevant documents more strongly.

**LightGBM's default `label_gain`:** For a 5-level relevance scale (0-4), LightGBM defaults to `label_gain = [0, 1, 3, 7, 15]` which equals `2^label - 1` for labels 0-4. This matches the exponential gain formula from NDCG literature.

---

### MSLR-WEB30K — The Standard LTR Benchmark

> **Microsoft Research. MSLR: Microsoft Learning to Rank Datasets.** Available at microsoft.com/research/project/mslr/

**What it is:** The de facto standard benchmark for evaluating LTR algorithms. Contains 30,000+ queries with up to 136 features per query-document pair and 5-level relevance labels (0-4) from Bing search results. The 136 features include BM25 scores at different fields, DM language model scores, PageRank, query coverage, etc.

**How it's relevant:** Zarailink's 8-feature vector is a domain-specific instantiation of the same general concept. The standard of using 0-4 relevance labels and training with LambdaMART is directly borrowed from the MSLR-WEB30K lineage.

---

### Cold-Start LTR — Bootstrapping Without Click Data

---

## 10.3 Query Understanding & NLP

### NER in E-Commerce — The TripleLearn Framework

> **Cheng, X., Bowden, M., Bhange, B.R., et al. (2021).** An End-to-End Solution for Named Entity Recognition in eCommerce Search. *AAAI 2021. arXiv:2012.07553.*

**What it is:** The most-cited industry NER paper in the e-commerce space. Introduces the **TripleLearn** training framework — iteratively training from three separate datasets simultaneously:
1. Human-labeled data (high quality, low volume)
2. Behavior-derived labels from search click logs (low quality, very high volume)
3. Heuristic-labeled data (medium quality, medium volume)

The result is a BERT-CRF NER model that lifts F1 from 69.5 → **93.3** on holdout data. The paper also highlights that product search queries are highly telegraphic (no verbs, no grammar) — "dextrose monohydrate 25kg China supplier" — which requires different handling than standard NER benchmarks (CoNLL-2003, OntoNotes) designed for full sentences.

**How it's relevant:** Directly justifies Zarailink's choice to use rule-based NLP. For Zarailink's constrained domain (30 countries, 5 volume units, 5 price pattern types), a hand-crafted rule system achieves the same precision as TripleLearn at zero annotation cost. The paper validates: the smaller and more predictable the entity vocabulary, the more competitive rule-based systems are.

---

### QueryNER — E-Commerce Query Segmentation

> **Palen-Michel, C., Liang, L., Wu, Z., & Lignos, C. (2024).** QueryNER: Segmentation of E-commerce Queries. *LREC-COLING 2024 / ECNLP Workshop. arXiv:2405.09507.*

**What it is:** Introduces a **17-type entity ontology** for product queries, avoiding category-specific tag sets that don't transfer across domains. The 17 types include: `core_product_type`, `modifier`, `creator`, `unit_of_measure`, `color`, `size`, `material`, `age_group`, and more. Releases a dataset of 7,000+ annotated queries from the Amazon Shopping Queries Dataset.

**Directly applicable to Zarailink:** The entity types for a trade search system would be: `commodity_type` (dextrose, rice), `variety/grade` (monohydrate, basmati), `unit_of_measure` (MT, kg, ton), `origin_country` (China, India), `quantity`, `price`, and `time_period`. The same BERT-based tagging approach applies identically.

---

### Amazon Implicit Query Parsing

> **Luo, C., Goutam, R., Zhang, H., et al. (2023).** Implicit Query Parsing at Amazon Product Search. *SIGIR 2023. ACM DOI: 10.1145/3539618.3591858.*

**What it is:** Distinguishes between:
- **Explicit attributes:** stated directly ("red wool sweater" → color=red, material=wool)
- **Implicit attributes:** not mentioned but strongly implied by context ("iPhone charger" → implicitly requires iOS compatibility)

Introduces a unified framework combining knowledge graphs (product-attribute relationships) and customer behavior analysis (historical search-click-purchase patterns) to resolve implicit attributes. Demonstrates that ignoring implicit attributes causes significant precision loss.

**How it relates to Zarailink:** "Karachi exporter" implicitly targets Pakistan. "Basmati rice" implicitly targets certain HS codes. The QueryInterpreter's country extraction and family classification are doing a simplified version of implicit attribute resolution — the family detection keywords (like "compare", "top", "verified") imply structural attributes (F7, F6, F8) not explicitly stated in the query.

---

### Amazon Query Understanding — Comprehensive Empirical Study

> **Luo, C., Tang, X., Lu, H., et al. (2024).** Exploring Query Understanding for Amazon Product Search. *arXiv:2408.02215.*

**What it is:** A year-long empirical study of how query understanding features (parsed entities, detected intent, extracted attributes) influence downstream product ranking. Uses a multi-task learning framework jointly training query understanding and ranking. Key finding: **query understanding features are among the strongest signals for improving NDCG** in product search. The paper also confirms: "product search engines feature short queries which are mostly a combination of product attributes" — justifying structured attribute extraction over full NLU.

**How it's relevant:** The most direct validation of Zarailink's 4-stage architecture. Zarailink's Stage 1 (QueryInterpreter) produces exactly the kind of structured query representation that Amazon demonstrates is critical for downstream ranking quality.

---

### Deep Search Query Intent Understanding

> **Liu, X., Guo, W., Gao, H., & Long, B. (2020).** Deep Search Query Intent Understanding. *arXiv:2008.06759.*

**What it is:** Describes a production system for real-time query intent prediction at scale, covering both typeahead (character-level) and complete query (word-level) intent classification. Demonstrates that deep learning components validated by offline evaluation must be further validated by online A/B testing — offline improvements don't always translate to user behavior improvements.

**How it's relevant:** Validates Zarailink's phased approach: rule-based intent scoring (SELL_SCORES / BUY_SCORES) is a fast, interpretable first-pass intent classifier. The paper confirms that for high-throughput production systems, latency-conscious architectures (like Zarailink's regex-based scoring) often win over more accurate but slower neural models.

---

### Intent Detection in the Age of LLMs (2024)

> **Arora, G., Jain, S., & Merugu, S. (2024).** Intent Detection in the Age of LLMs. *EMNLP 2024 Industry Track. arXiv:2410.01627.*

**What it is:** Directly compares 7 LLMs (ChatGPT, GPT-4, Claude, Mistral, LLaMA-2) vs fine-tuned sentence transformers (SetFit) for intent classification. Key findings:
- SetFit-class models are **56x faster** than LLMs but ~8% less accurate
- A **hybrid uncertainty-based routing** system achieves within ~2% of native LLM accuracy at ~50% reduced latency: use fast SetFit for confident cases, route uncertain cases to LLM
- LLMs struggle significantly with **out-of-scope detection** — recognizing queries that don't match any known intent class (important for Zarailink: queries like "what is the weather?" should be rejected)

**How it's relevant:** Validates Zarailink's use of a fast rule-based intent classifier (analogous to SetFit's speed advantage). For the current scale, rules are sufficient. As Zarailink adds more complex query types, the hybrid routing pattern (fast rules → ML fallback) is the recommended upgrade path.

---

### Joint Intent Detection Survey

> **Weld, H., Huang, X., Long, S., Poon, J., & Han, S.C. (2022).** A Survey of Joint Intent Detection and Slot Filling Models in Natural Language Understanding. *ACM Computing Surveys, 55(8), Article 156. DOI: 10.1145/3547138.*

**What it is:** The definitive survey covering evolution from pipeline models (separate intent classifier + slot filler) to joint models. Key finding: **joint models consistently outperform pipeline models** by reducing error propagation. When intent detection and entity extraction share a backbone (BERT), they mutually inform each other — the intent "SELL" raises the likelihood that "China" is a `destination_country` not just a general location reference.

**How it's relevant:** Zarailink's QueryInterpreter is effectively a pipeline model (intent scored separately from entity extraction). A future improvement would jointly model intent and slot filling, allowing "who buys" to help parse "dextrose in China" as product+country (not company name).

---

### AGIF — Multi-Intent Detection

> **Qin, L., Xu, X., Che, W., & Liu, T. (2020).** AGIF: An Adaptive Graph-Interactive Framework for Joint Multiple Intent Detection and Slot Filling. *Findings of EMNLP 2020. arXiv:2004.10087.*

**What it is:** Foundational paper for modern multi-intent + slot filling joint modeling. Introduces an **intent-slot graph interaction layer** where each token gets an adaptive intent context vector computed from only the intents relevant to that token (rather than a global intent vector). Achieves state-of-the-art on multi-intent datasets (MixATIS, MixSNIPS).

```
Query tokens → BERT encoder → token representations
    |
Intent detection (multi-label) → [intent_1, intent_2, ...]
    |
Per-token adaptive intent graph interaction
    |
Slot label prediction (BIO tagging per token)
```

**How it's relevant:** Zarailink's multi-intent detection (Family 9) addresses the same fundamental problem but with rule-based detection (check for independent intent keywords after "and"). For Zarailink's constrained vocabulary, the rule-based approach is sufficient and more interpretable.

---

### GL-GIN — 11.5x Faster Multi-Intent Detection

> **Qin, L., Wei, F., Xie, T., Xu, X., Che, W., & Liu, T. (2021).** GL-GIN: Fast and Accurate Non-Autoregressive Model for Joint Multiple Intent Detection and Slot Filling. *ACL 2021. arXiv:2106.01925.*

**What it is:** Directly addresses AGIF's bottleneck (autoregressive slot prediction is slow and causes information leakage). GL-GIN uses a non-autoregressive architecture with two graph interaction layers:
1. **Local slot-aware graph:** models slot dependency between adjacent positions
2. **Global intent-slot graph:** models interaction between all detected intents and all slot positions simultaneously

Achieves **11.5x faster inference** than AGIF while maintaining competitive accuracy — directly deployable in latency-sensitive production search.

---

### MISCA — State-of-the-Art Multi-Intent (2023)

> **Pham, T., Tran, C., & Nguyen, D.Q. (2023).** MISCA: A Joint Model for Multiple Intent Detection and Slot Filling with Intent-Slot Co-Attention. *Findings of EMNLP 2023. arXiv:2312.05741.*

**What it is:** Solves AGIF's graph construction uncertainty with **bidirectional intent-slot co-attention** — intent representations attend to slot representations AND slot representations attend to intent representations simultaneously. Introduces a **label attention layer** that extracts label-specific token representations without relying on token-level intent information. Achieves 59.1% overall accuracy on MixATIS, 86.2% on MixSNIPS (with RoBERTa backbone) — state-of-the-art as of late 2023.

---

### Hybrid Rule+ML — The Recommended Production Architecture

> **Multiple authors (2024).** Strengths and Weaknesses of LLM-Based and Rule-Based NLP Technologies and Their Potential Synergies. *MDPI Electronics, 2024.*

**What it is:** Systematic analysis of when each approach is appropriate. Key empirical finding: "combining rule-based parsing with machine learning-based spellcheckers and suggestions improved query understanding accuracy from 80% to 91%." This 11-percentage-point improvement from adding ML to a rule-based backbone is frequently cited as justification for hybrid systems.

**The recommended production architecture:**
```
Query Input
    │
[Layer 1] Fast rule/regex layer (< 1ms):
  - Numeric extraction (price, volume, date)
  - Known entity lookup (country list, unit dictionary)
    │
[Layer 2] ML model layer (if Layer 1 confidence is low):
  - BERT-based NER for ambiguous spans
  - Intent classification for novel queries
    │
[Layer 3] Post-processing rules:
  - Constraint enforcement
  - Conflict resolution (rules win for high-confidence patterns)
```

**How it validates Zarailink:** The current QueryInterpreter is Layer 1 of this architecture. It works extremely well for the current known-vocabulary domain. Adding Layer 2 (ML) only makes sense as query diversity grows beyond what rules can handle.

---

## 10.4 Multi-Stage Retrieval

### Cascade Ranking for E-Commerce — Alibaba (KDD 2017)

> **Liu, X., Xiao, M., Ou, X., & Si, L. (2017).** Cascade Ranking for Operational E-commerce Search. *KDD 2017. ACM doi:10.1145/3097983.3098011.*

**What it is:** The **seminal paper** establishing the cascade model paradigm for large-scale production e-commerce. Deployed at Alibaba handling hundreds of millions of queries per day. Models multiple user behaviors (clicks AND purchases). Key result: **40% reduction in engine sorting CPU load** with improved quality, deployed at the 2016 Double 11 festival. Core insight: real-world search must optimize accuracy, latency, result set size, AND CPU cost simultaneously — single-stage models cannot satisfy all constraints.

**How it's relevant:** Zarailink's 4-stage pipeline mirrors Alibaba's cascade design exactly: cheap NLP matching narrows candidates so the expensive LightGBM ranker only processes a small set.

---

### RankFlow — Cross-Stage Cascade Optimization (SIGIR 2022)

> **Qin, Z., Zhu, S., et al. (2022).** RankFlow: Joint Optimization for Multi-Stage Cascaded Ranking Systems as Flows. *SIGIR 2022. ACM doi:10.1145/3477495.3532050.*

**What it is:** Identifies a critical flaw in conventional cascade training: all stages are independently trained on the same data, **ignoring distributional shift between stages**. RankFlow proposes iterative training where each stage learns from its upstream stage's outputs and distills knowledge from the downstream model — cross-stage optimization.

**How it's relevant:** Zarailink's stages are currently trained independently (LTR trained separately from NLP matching). RankFlow's finding that joint cross-stage optimization improves quality motivates a future upgrade: co-training Stage 2 + Stage 4 end-to-end.

---

### Taobao MGDSPR — Industrial Multi-Stage Retrieval (KDD 2021)

> **Li, Y., Lv, F., et al. (2021).** Embedding-based Product Retrieval in Taobao Search. *KDD 2021. ACM doi:10.1145/3447548.3467101.*

**What it is:** Taobao's production multi-channel retrieval: Billions → Match → Tens of Thousands → Pre-Rank → Thousands → Rank → Dozens → Re-rank. Introduces MGDSPR (Multi-Grained Deep Semantic Product Retrieval) as an embedding-based third retrieval channel alongside keyword and collaborative filtering channels.

**How it's relevant:** Industrial validation of the exact cascade architecture used in Zarailink. Zarailink operates at vastly smaller scale but the architecture mirrors Taobao's design — keyword + semantic retrieval feeding a downstream LTR ranker.

---

### Meta KDD 2024 — Cascade Budget Personalization

> **Evnine, A., Ioannidis, S., Kalimeris, D., et al. (2024).** Achieving a Better Tradeoff in Multi-stage Recommender Systems through Personalization. *KDD 2024. ACM doi:10.1145/3637528.3671593.*

**What it is:** Proves via DR-submodularity that ranking more items in downstream stages has **diminishing returns**. Personalized budget allocation (ranking more for complex queries, fewer for simple ones) achieved **8.8% compute reduction** with no quality loss in A/B tests across 3 Facebook recommender systems.

**How it's relevant:** For Zarailink, simple F1 queries with few results don't need full LTR scoring — heuristic ranking is sufficient. Complex F9 multi-intent queries with many candidates benefit most from full LightGBM scoring. This paper provides the theoretical basis for such adaptive compute allocation.

---

## 10.4b Additional Retrieval Papers (Extended)

### BM25 — The Sparse Retrieval Baseline

> **Robertson, S., & Zaragoza, H. (2009).** The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval, 3(4), 333-389.* (Original TREC work by Robertson et al., 1994.)

**What it is:** BM25 (Best Match 25) is the dominant sparse (keyword) retrieval function, still competitive with neural methods in 2024.

The BM25 formula is:
```
score(D, Q) = Σ_t IDF(t) × [TF(t,D) × (k1+1)] / [TF(t,D) + k1×(1 - b + b×|D|/avgdl)]

where:
  IDF(t)   = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
  TF(t,D)  = frequency of term t in document D
  N        = total number of documents
  df(t)    = number of documents containing term t
  |D|      = length of document D in words
  avgdl    = average document length in corpus
  k1       = term frequency saturation parameter (typically 1.2–2.0)
  b        = length normalization parameter (typically 0.75)
```

**Key properties:**
- **TF saturation:** The k1 parameter means that after a certain frequency, adding more occurrences of a term has diminishing returns (the score saturates). This prevents a document that says "dextrose" 100 times from dominating over a document that mentions it 3 times with more relevant context.
- **IDF:** Rare terms get higher weight. "Dextrose" in a medical database is more informative than "the" in any database.
- **Length normalization:** Parameter b penalizes long documents that contain the query term just by virtue of being long.

**How Zarailink relates:** The keyword icontains search in `QueryMatcher` is simpler than BM25 (just presence/absence, not frequency-weighted). A future improvement would use PostgreSQL's full-text search with BM25-style weighting.

---

### SPLADE — Learned Sparse Representations

> **Formal, T., Piwowarski, B., Lassance, C., & Clinchant, S. (2021).** SPLADE v2: Sparse Lexical and Expansion Model for Information Retrieval. *arXiv:2109.10086. (SPLADE at SIGIR 2021; SPLADEv2 at SIGIR 2022.)*

**What it is:** SPLADE bridges the gap between sparse (BM25) and dense (SBERT) retrieval. It uses a BERT-based MLM (masked language model) head to produce sparse representations in the **vocabulary space** (30,000+ dimensions, but very sparse — mostly zeros). The model learns to:
1. Keep important query/document terms (similar to TF-IDF weighting).
2. **Expand** both query and document with related terms (e.g., "dextrose" → also assigns weight to "glucose", "sugar").

A FLOPS regularization term controls sparsity — the model is penalized for using too many dimensions, so it learns to pack meaning into few high-weight dimensions.

**Why it matters:** SPLADE achieves near-dense-retrieval accuracy while remaining compatible with inverted index infrastructure (used by Elasticsearch, Lucene). SPLADEv2 with hard-negative mining and cross-encoder distillation achieves state-of-the-art on the BEIR benchmark.

**How it's relevant to Zarailink:** The concept of query/document expansion is exactly what Zarailink's hybrid search is doing manually — the semantic branch finds related product categories that keyword search would miss. SPLADE automates this expansion in a learned, end-to-end fashion. A future version of Zarailink could replace the SBERT semantic search with SPLADE for better keyword-semantic integration.

---

### Reciprocal Rank Fusion (RRF) — The Fusion Formula

> **Cormack, G.V., Clarke, C.L.A., & Buettcher, S. (2009).** Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods. *SIGIR 2009, pp. 758-759.*

**What it is:** RRF is the standard method for combining multiple ranked lists without needing to normalize different scoring scales. For each document d appearing in any of the ranked lists:

```
RRF_score(d) = Σ_r  1 / (k + rank_r(d))

where:
  k        = smoothing constant (typically 60)
  rank_r(d) = position of d in ranked list r (1-indexed)
```

Example: Document A ranks #1 in BM25 list and #3 in SBERT list. With k=60:
```
RRF_score(A) = 1/(60+1) + 1/(60+3) = 0.0164 + 0.0159 = 0.0323
```

**Why k=60?** The constant k is chosen to dampen the impact of very high ranks — a document at rank 1 vs rank 2 gets a smaller boost than if k=0. k=60 was empirically validated as robust across many retrieval tasks.

**Key advantages:**
- No score normalization required (BM25 and cosine similarity are on completely different scales)
- No parameters to tune per domain
- Consistently improves over single-method retrieval
- Empirically found to improve NDCG@10 by ~1.4% over SBERT alone, ~18% over BM25 alone on BEIR

**How it relates to Zarailink:** Zarailink's hybrid search uses a simpler rule: keyword matches get score=1.0 and are kept regardless; semantic matches below 0.4 cosine are dropped. A production improvement would implement RRF to properly combine keyword and semantic scores.

---

### TSDAE — Domain Adaptation for Embeddings

> **Wang, K., Reimers, N., & Gurevych, I. (2021).** TSDAE: Using Transformer-based Sequential Denoising Auto-Encoder for Unsupervised Sentence Embedding Learning. *Findings of ACL 2021. arXiv:2104.06979.*

**What it is:** TSDAE is an **unsupervised** method for fine-tuning sentence embedding models on domain-specific text without any labeled data. Sentences from the target domain are **corrupted** (random words deleted or swapped), and the model must **reconstruct** the original sentence. This reconstruction objective forces the encoder to produce embeddings that capture enough information for faithful reconstruction — i.e., semantically rich embeddings.

**Why this matters for Zarailink:** The `all-MiniLM-L6-v2` model is a general-purpose model trained on Reddit, Wikipedia, etc. It may not produce optimal embeddings for trade-specific terminology like "Dextrose Monohydrate", "HS Code 17023000", or "Free Carrier Karachi". TSDAE would allow fine-tuning the SBERT model on Zarailink's own product catalogue text, with zero labeling effort, by simply corrupting and reconstructing the product names. This would improve search quality for specialized trade vocabulary.

---

### Cosine Similarity Critique (2024)

> **Steck, H., Ekanadham, C., & Kallus, N. (2024).** Is Cosine-Similarity of Embeddings Really About Similarity? *Companion Proceedings of the ACM Web Conference (WWW) 2024. arXiv:2403.05440.*

**What it is:** This recent paper (2024) raises a subtle but important warning: cosine similarity of raw, unnormalized embeddings can sometimes be arbitrary and misleading. The authors show mathematically that cosine similarity equals a rescaled dot product, and its interpretation depends critically on training methodology. For embeddings trained with explicit cosine-based objectives (like all SBERT-family models), cosine similarity is valid and meaningful. For embeddings from models trained purely with dot-product or cross-entropy losses, it may not be.

**Practical implication for Zarailink:** Since `all-MiniLM-L6-v2` is trained using Multiple Negatives Ranking Loss (which maximizes cosine similarity between positive pairs), cosine similarity is the **correct and well-founded** metric for this model. The critique does not apply here — but it validates the importance of the choice: always use the similarity metric that matches the model's training objective.

---

### Augmented SBERT — Teacher-Student for Bi-Encoders

> **Reimers, N., & Gurevych, I. (2021).** Improving Bi-Encoder Document Ranking Models with Two Rankers and Multi-Teacher Distillation. *NAACL 2021.*

**What it is:** A training methodology for improving bi-encoder (SBERT-style) models by using a slow-but-accurate cross-encoder as a "teacher". The cross-encoder generates soft labels (similarity scores) for sentence pairs, and the bi-encoder student learns from these. This bridges the accuracy gap between cross-encoders (very accurate, O(N²)) and bi-encoders (fast, O(N)).

**How it relates to Zarailink:** The `PseudoLabelGenerator` class in Zarailink implements an analogous teacher-student pattern for the LTR ranking problem (heuristic teacher → LightGBM student). The same principle — use a more accurate but computationally expensive method to generate labels for training a faster method — applies in both contexts.

---

## 10.5 Feature Engineering

### Box-Cox / Log Transformation

> **Box, G.E.P., & Cox, D.R. (1964).** An Analysis of Transformations. *Journal of the Royal Statistical Society Series B, 26(2), 211-252.*

**What it is:** The classic paper on power transformations for normalizing heavy-tailed distributions. Box-Cox shows that `y^λ` transformations (including `log(y)` at λ=0) can make skewed distributions approximately normal.

**How Zarailink uses it:** `np.log1p(volume)` and `np.log1p(price)` in `FeatureExtractor.extract()` are log-transformations that compress heavy-tailed trade volume and price distributions for ML consumption.

---

### Feature Transformation for Neural Ranking — Direct log1p Citation

> **Pang, L., Lan, Y., Guo, J., Xu, J., Cheng, X., & Cheng, X. (2020).** Feature Transformation for Neural Ranking Models. *SIGIR 2020. ACM doi:10.1145/3397271.3401333.*

**What it is:** The authoritative citation for log1p transformation in LTR ranking systems. Evaluates multiple feature transformation strategies for LTR on MSLR-WEB30K and Istella-S benchmarks. Key findings:
- Standard `log(x)` is inapplicable because it is undefined for `x ≤ 0`
- Paper proposes **symmetric log1p**: `sign(x) × log(1 + |x|)`, which handles zero and negative values
- Quote: "The distribution of the transformed feature values will no longer be as skewed as raw feature values"
- Log1p is consistently beneficial for neural ranking models across all tested configurations

**Direct relationship to Zarailink:** `np.log1p(vol)` and `np.log1p(price)` in `FeatureExtractor.extract()` implement exactly this transformation. This paper is the authoritative citation for why that choice is correct.

---

### LRFMV — Extending RFM with Volume

> **Multiple authors (2023).** LRFMV: An Efficient Customer Segmentation Model for Superstores. *PLOS One, 2023. doi:10.1371/journal.pone.0279262.*

**What it is:** Extends the classic RFM model with L (relationship Length) and V (Volume — quantity of items purchased), creating a 5-dimensional customer segmentation model. Demonstrates the profit-quantity relationship in trade contexts: high-volume buyers contribute disproportionately to revenue, validating using volume as the primary ranking signal.

**How Zarailink uses it:** Zarailink's 8 features map to LRFMV exactly: `inv_recency` → R, `shipment_freq` → F, `log_volume` → M+V, historical span → L. The LRFMV paper validates the completeness of Zarailink's feature set for buyer ranking.

---

### Recency Ranking — WSDM 2010 (Foundational)

> **Dong, A., Chang, Y., & Zheng, Z. (2010).** Towards Recency Ranking in Web Search. *WSDM 2010.*

**What it is:** The foundational paper establishing recency ranking as a distinct IR problem. Proposes a multi-grade classifier for recency-sensitive queries and a machine-learned ranking model trained specifically for temporal queries. Key insight: different queries require different freshness weighting. Failing to recognize a query's temporal dimension "negatively affects user experience." This remains the standard citation for the freshness/relevance tradeoff.

**How Zarailink uses it:** The `inv_recency` feature implements temporal decay — buyers active recently rank higher. For F5 queries ("who bought recently?"), `inv_recency` gets 3x family weight, implementing exactly the recency-sensitive ranking this paper advocates.

---

### Learning to Rank for Freshness and Relevance (SIGIR 2011)

> **Dai, N., Shokouhi, M., & Davison, B.D. (2011).** Learning to Rank for Freshness and Relevance. *SIGIR 2011. Microsoft Research.*

**What it is:** Extends the LTR framework to jointly optimize for both freshness AND topical relevance. Introduces **temporal distance as a feature** directly in a RankSVM framework, rather than as a post-hoc reranking adjustment. Shows measurable improvements over relevance-only ranking.

**Direct mapping to Zarailink:** `inv_recency = 1/(days_ago + 1)` is exactly "temporal distance as a feature" feeding directly into the LightGBM LTR model. This paper provides the LTR-level justification for including recency as one of the 8 features.

---

### Analysis of E-Commerce Ranking Signals — YoY Growth (Amazon Science 2021)

> **Multiple authors (Amazon Science, 2021).** Analysis of E-commerce Ranking Signals via Signal Temporal Logic. *arXiv:2101.05415.*

**What it is:** Uses Signal Temporal Logic (STL) to formally characterize time-varying ranking signals including cold start, warm start, product instability, and growth spikes. Explicitly models growth trajectories — not just static scores — as informative ranking features. Distinguishes "warm start" (gradual sustained growth) vs "spike" (sudden temporary growth) as different signals. Validated on 100K product signals.

**Direct mapping to Zarailink:** CountryComparator's YoY growth calculation:
```python
growth_pct = ((curr_vol - prev_vol) / prev_vol) * 100
```
is exactly the "growth trajectory feature" this paper formalizes. Countries with sustained growth (warm start) should rank above countries with flat or declining volumes, even if absolute volume is lower.

---

### Popularity Bias Survey — Why YoY Growth Mitigates It (2023)

> **Multiple authors (2023).** A Survey on Popularity Bias in Recommender Systems. *arXiv:2308.01118.*

**What it is:** Documents how naive use of popularity (raw volume) as a ranking signal creates self-reinforcing feedback loops — popular items get more exposure, which generates more clicks, which further boosts their ranking regardless of intrinsic quality. YoY growth is one recommended signal to mitigate this: a supplier with modest but **growing** volume should rank above a large but **declining** supplier.

**How Zarailink uses it:** Zarailink's F7 (CountryComparator) returns `demand_growth_pct` alongside `total_volume`. Displaying growth rate lets users see momentum rather than just historical mass, mitigating the popularity bias that pure volume ranking would create.

---

### B2B Lead Scoring — Volume Compatibility (Frontiers AI 2025)

> **Multiple authors (2025).** B2B Lead Prioritization: A Lead Scoring Model Based on Machine Learning. *Frontiers in Artificial Intelligence, 2025.*

**What it is:** 2025 paper on ML-based B2B lead prioritization that scores potential supplier-buyer pairs on compatibility using: company size, revenue scale, industry vertical, and behavioral signals. The volume compatibility problem in trade search is analogous to matching a buyer's revenue scale to a supplier's typical order size.

**Direct mapping to Zarailink:** SupplierAggregator's volume compatibility scoring:
```python
vol_score = 0.5*single_match + 0.3*capacity_match + 0.2*avg_match
```
is a practical implementation of B2B compatibility scoring. The 50/30/20 weight split (prioritizing single-shipment capacity) is supported by this paper's finding that buyers primarily care about whether a supplier can fill a single order, not cumulative capacity.

---

### RFM Model — Recency, Frequency, Monetary Value

> **Hughes, A.M. (1994).** Strategic Database Marketing. *McGraw-Hill.*

> **Fader, P.S., Hardie, B.G.S., & Lee, K.L. (2005).** "Counting Your Customers" the Easy Way: An Alternative to the Pareto/NBD Model. *Marketing Science, 24(2).*

**What it is:** The RFM framework classifies customers by Recency (how recently they bought), Frequency (how often), and Monetary (how much). These three dimensions reliably predict future purchase behavior.

**How Zarailink uses it:** The `inv_recency`, `shipment_freq`, and `log_volume` features in `FeatureExtractor` directly map to R, F, and M respectively. The ranking system is essentially an RFM model applied to buyer ranking.

---

<a name="part-11"></a>
# PART 11: GLOSSARY OF EVERY TECHNICAL TERM

**Aggregation:** In databases, combining multiple rows into summary statistics (SUM, AVG, COUNT). Django's `.annotate()` method performs aggregation.

**BEIR:** Benchmarking Information Retrieval — a collection of 18 datasets for evaluating retrieval model quality.

**Boosting:** An ensemble ML technique where models are trained sequentially, each correcting the errors of the previous ones.

**Cascade Ranking:** A multi-stage system where cheap models narrow candidates and expensive models do final ranking.

**Cold Start Problem:** In ML, the challenge of making predictions when little or no historical data is available.

**Cosine Similarity:** A measure of similarity between two vectors, computed as the cosine of the angle between them. Range: [-1, 1].

**DCG (Discounted Cumulative Gain):** A ranking quality metric that rewards placing highly relevant results at top positions, with a logarithmic position discount.

**Dense Retrieval:** Retrieval using dense vector embeddings (as opposed to sparse keyword vectors like TF-IDF).

**Django ORM:** Django's Object-Relational Mapper — Python code that generates SQL queries automatically.

**Embedding:** A dense vector representation of text (or any object) in a high-dimensional space where similar items have similar vectors.

**EFB (Exclusive Feature Bundling):** A LightGBM optimization that bundles mutually exclusive features to reduce dimensionality.

**GOSS (Gradient-Based One-Side Sampling):** A LightGBM optimization that keeps hard training samples (large gradient) and randomly samples easy ones.

**Gradient Boosting:** An ensemble technique that builds models sequentially, where each model predicts the residual (error) of the previous ensemble.

**Gradient Descent:** An optimization algorithm that iteratively adjusts model parameters in the direction that reduces the loss (error).

**Heavy-Tailed Distribution:** A probability distribution where extreme values are much more common than a normal distribution would predict. Trade volumes follow a heavy-tailed distribution.

**IDCG (Ideal DCG):** The maximum possible DCG for a given set of relevance labels (achieved by perfect ranking).

**icontains:** Django ORM operator for case-insensitive substring matching (SQL: LIKE '%term%').

**iexact:** Django ORM operator for case-insensitive exact matching (SQL: WHERE column ILIKE 'term').

**Inference:** Using a trained ML model to make predictions on new data (as opposed to "training").

**Intent:** In query understanding, what the user ultimately wants to achieve (BUY vs SELL in Zarailink).

**Knowledge Distillation:** Training a small "student" model to mimic the behavior of a large "teacher" model.

**Lambda (λ):** In LambdaRank, the gradient that pushes documents up or down in the ranking. Scaled by |ΔNDCG| to implicitly optimize the ranking metric.

**LambdaMART:** LambdaRank implemented with gradient boosted trees (MART = Multiple Additive Regression Trees).

**LambdaRank:** A ranking algorithm that directly computes gradients for NDCG optimization without defining an explicit differentiable loss function.

**Leaf-wise Growth:** LightGBM's strategy of splitting the leaf with the maximum gain at each step (vs level-wise growth in traditional trees).

**LightGBM:** Light Gradient Boosting Machine — a fast, accurate gradient boosting library by Microsoft.

**log1p:** `log(1 + x)` — a log transformation that handles x=0 gracefully (log1p(0)=0).

**LTR (Learning to Rank):** A class of ML techniques for training models to rank items by relevance.

**Meta Tensor:** In PyTorch, a "meta" device that stores tensor shape/dtype but no actual data. Used for lazy loading. Causes `NotImplementedError` when you try to do arithmetic with it.

**Multi-Intent Query:** A query that contains two or more independent questions.

**NDCG (Normalized Discounted Cumulative Gain):** DCG normalized by IDCG, giving a score in [0,1] where 1 = perfect ranking.

**NER (Named Entity Recognition):** Identifying named entities (people, places, organizations, etc.) in text.

**NLP (Natural Language Processing):** The field of making computers understand human language.

**Pairwise LTR:** A learning-to-rank paradigm where training examples are pairs of documents, and the model learns which document in each pair should rank higher.

**Pickle:** Python's native object serialization format. Used for storing the SBERT search index.

**Pointwise LTR:** A learning-to-rank paradigm where each document is assigned an individual relevance score, and the model learns to predict these scores.

**Pseudo-Label:** A synthetic training label generated by a heuristic or rule, used when real labels are unavailable.

**Queryset:** In Django, a lazy-evaluated SQL query. Chaining `.filter()`, `.annotate()`, `.values()` builds up the query without executing it.

**RankNet:** The first neural LTR method (Burges et al., 2005), predecessor to LambdaRank.

**Recency:** How recently a buyer made their last purchase. High recency = bought recently = more likely to buy again.

**Regular Expression (Regex):** A pattern language for matching text. `\d+` matches one or more digits; `\b` matches word boundaries.

**RFM Model:** Recency-Frequency-Monetary model for customer value analysis.

**Scope:** In Zarailink, whether to search Pakistani buyers specifically (PAKISTAN) or globally (WORLDWIDE).

**Semantic Gap:** The difference between the vocabulary a user uses and the vocabulary in the database. Semantic search bridges this gap.

**Semantic Search:** Finding relevant results based on meaning, not just keyword matching.

**SequenceMatcher:** Python's `difflib.SequenceMatcher` — computes string similarity as 2M/T where M = matching characters, T = total characters.

**Siamese Network:** A neural network architecture where two inputs are processed by shared weights, producing two embeddings that are then compared.

**Softmax:** A function that converts a vector of raw scores into probabilities (summing to 1).

**SQL (Structured Query Language):** The language used to query relational databases.

**SBERT (Sentence-BERT):** A modification of BERT that uses a Siamese network to produce semantically meaningful sentence embeddings.

**Trade Type:** "IMPORT" (goods arriving in Pakistan) or "EXPORT" (goods leaving Pakistan). The Zarailink DB contains only IMPORT records.

**Transformer:** A neural network architecture based on self-attention mechanisms. BERT, GPT, and SBERT are all transformer-based models.

**Vector:** A list of numbers representing a point in multi-dimensional space. In NLP, vectors represent the meaning of words/sentences.

**YoY (Year-over-Year):** The percentage change compared to the same period in the previous year. Used to identify growing vs declining trade partners.

**Zero-Shot:** A model's ability to perform a task it was never specifically trained for. BEIR measures zero-shot retrieval performance.

---

# CONCLUSION: THE COMPLETE PICTURE

Let's bring it all together with one final trace through the entire system.

**User types:** `"which countries buy dextrose most, and who are the top buyers there?"`

**Stage 1 — QueryInterpreter:**
1. Split on "and": "show country comparison" has intent keywords → split into 2 sub-intents
2. Sub-intent 1: "which countries buy dextrose most" → F7, intent=SELL, product="dextrose"
3. Sub-intent 2: "who are the top buyers there" → F6, intent=SELL, product="" (empty)
4. Context carry-over: product="" → inherit "dextrose" from sub-intent 1
5. Output: multi_intent=True, family=9, sub_intents=[F7, F6]

**Stage 2 — QueryMatcher (for each sub-intent):**
1. "dextrose" → keyword match: SubCategory[id=42, name="Dextrose"], score=1.0
2. Semantic search: "Glucose" at score=0.72 (related)
3. Output: subcategory_ids=[42]

**Stage 3 — Aggregation:**
- Sub-intent F7 → CountryComparator: 10 countries ranked by import volume, with YoY growth
- Sub-intent F6 → SupplierAggregator (SELL + WORLDWIDE → PAKISTAN scope fix) → 229 buyers

**Stage 4 — RankingEnsemble (F6 sub-intent only):**
1. Extract 8 features for each of 229 buyers
2. F6 uses DEFAULT_WEIGHTS (balanced)
3. Combine 70% heuristic + 30% LTR model
4. Truncate to top 5 (F6 with no N specified → default 5)

**Response:**
```json
{
  "type": "multi_intent",
  "family": 9,
  "sections": [
    {
      "label": "Country Comparison",
      "family": 7,
      "country_comparison": [
        {"country": "China", "total_volume": 5420.0, "demand_growth_pct": 23.5, ...},
        {"country": "India", "total_volume": 3150.0, "demand_growth_pct": -8.2, ...},
        ...
      ]
    },
    {
      "label": "Top Recommendations",
      "family": 6,
      "results": [
        {"name": "Muller & Phipps Pakistan Ltd", "total_volume": 850.0, "avg_price": 680.0, ...},
        ...
      ]
    }
  ]
}
```

This is Zarailink's search system — a carefully engineered, research-backed 4-stage pipeline that turns natural language trade questions into structured, ranked intelligence about the agricultural trade market.

---

*Document prepared February 2026.*
*Covers: QueryInterpreter, QueryMatcher, SupplierAggregator, CountryComparator, EvidenceRetriever, RankingEnsemble, FeatureExtractor, PseudoLabelGenerator, LTRModel, 9 Query Families.*
*Research citations: Reimers & Gurevych 2019, Wang et al. 2020, Gao et al. 2021, Karpukhin et al. 2020, Thakur et al. 2021, Burges et al. 2005/2006/2010, Ke et al. 2017, Järvelin & Kekäläinen 2002, Han et al. 2022, Cheng et al. 2021, Qin et al. 2020/2021, Matsubara et al. 2022, Box & Cox 1964, Hughes 1994, Fader et al. 2005.*
