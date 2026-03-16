# Zarailink — Complete Project Overview

**Last Updated:** March 2026
**Branch:** `salman_v2`
**Status:** MVP-complete; production-ready with noted caveats

---

## Table of Contents

1. [What Is Zarailink?](#1-what-is-zarailink)
2. [Purpose & Problem Statement](#2-purpose--problem-statement)
3. [System Architecture](#3-system-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Backend — Django Applications](#5-backend--django-applications)
   - [accounts](#51-accounts-app)
   - [companies](#52-companies-app)
   - [subscriptions](#53-subscriptions-app)
   - [trade_data](#54-trade_data-app)
   - [search](#55-search-app--the-core)
   - [trade_ledger](#56-trade_ledger-app)
   - [market_intel](#57-market_intel-app)
   - [trade_lens](#58-trade_lens-app)
6. [The 4-Stage Search Pipeline](#6-the-4-stage-search-pipeline)
7. [ML Pipeline In Depth](#7-ml-pipeline-in-depth)
8. [Frontend — React Application](#8-frontend--react-application)
9. [Authentication & Authorization System](#9-authentication--authorization-system)
10. [Token Economy](#10-token-economy)
11. [Database Schema Summary](#11-database-schema-summary)
12. [API Endpoints Reference](#12-api-endpoints-reference)
13. [Data Flow Examples](#13-data-flow-examples)
14. [What Has Been Built & Accomplished](#14-what-has-been-built--accomplished)
15. [Configuration & Dev Setup](#15-configuration--dev-setup)
16. [Known Gaps & Next Steps](#16-known-gaps--next-steps)

---

## 1. What Is Zarailink?

Zarailink is a **Pakistani agricultural trade intelligence SaaS platform**. It aggregates real government import/export transaction data and exposes it through intelligent search, analytics, and a business directory — enabling agricultural businesses to discover verified trading partners, analyze market trends, and access key contacts.

The platform is targeted at Pakistani agricultural importers, exporters, suppliers, buyers, and trade agents who need to:

- Find reliable suppliers or buyers for agricultural commodities (rice, wheat, cotton, sugar, dextrose, etc.)
- Understand price trends and volume patterns for specific products by country
- Verify who has actually traded what, with whom, and at what price
- Access direct contacts to initiate trade relationships

The name "Zarailink" combines the Urdu word **"Zarai"** (agricultural/farm-related) with **"link"** — connecting agricultural businesses through data.

---

## 2. Purpose & Problem Statement

### The Problem

Pakistan's agricultural trade suffers from severe **information asymmetry**:
- Small and mid-sized businesses have no reliable way to find verified suppliers or buyers
- Market prices are opaque — traders often overpay or undersell without reference benchmarks
- Import/export transaction records exist in government databases but are not easily accessible or searchable
- Identifying whether a company has actually traded a given product before requires manual research

### The Solution

Zarailink ingests raw government trade transaction data (IMPORT / EXPORT records at the shipment level) and:
1. Structures it into a searchable database of transactions, products, and companies
2. Applies NLP, semantic search, and machine learning to make it intelligently queryable in plain English
3. Surfaces a business directory of companies with verified trade history
4. Provides market intelligence alerts and analytics dashboards

Businesses can search in natural language — "Who buys dextrose from China at under $700/MT?" — and get a ranked list of real suppliers backed by actual transaction data.

---

## 3. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER — React SPA                         │
│  Pages: Dashboard, Search, Trade Directory, Trade Intelligence,        │
│         Trade Ledger, Trade Pulse, Trade Lens, Subscriptions          │
│  Auth Context (global session state) │ Axios API client (port 3000)   │
└──────────────────────────┬─────────────────────────────────────────────┘
                           │ HTTP/REST (CORS, Session cookies, CSRF)
┌──────────────────────────▼─────────────────────────────────────────────┐
│                   API LAYER — Django REST Framework                    │
│  Routed at http://localhost:8000                                       │
│  /accounts/api/*  │  /api/*  │  /api/market-intel/*  │  /admin/       │
└──────────────────────────┬─────────────────────────────────────────────┘
                           │
        ┌──────────────────┼───────────────────────────┐
        │                  │                           │
┌───────▼──────┐  ┌────────▼──────────┐  ┌────────────▼────────────────┐
│  accounts    │  │  companies +       │  │  SEARCH MODULE              │
│  auth/users  │  │  subscriptions +   │  │  4-Stage Pipeline:          │
│              │  │  trade_ledger +    │  │  1. QueryInterpreter        │
│  token       │  │  market_intel +    │  │  2. QueryMatcher (SBERT)    │
│  economy     │  │  trade_lens        │  │  3. SupplierAggregator      │
└──────────────┘  └────────────────────┘  │  4. RankingEnsemble (LTR)  │
                                          └─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────────────────┐
│                  DATA LAYER — PostgreSQL                               │
│  Transaction (core trade records) │ Product hierarchy │ Companies      │
│  Users │ Subscriptions │ Alerts │ Embeddings                          │
│  + Redis cache (optional, auto-detected on 127.0.0.1:6379)            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Technology Stack

| Layer | Technology | Version/Details |
|---|---|---|
| **Backend framework** | Django + DRF | 4.2 / DRF 3.x |
| **Database** | PostgreSQL | Local, user=postgres/postgres |
| **Cache** | Redis | Optional; falls back to LocMemCache |
| **Frontend framework** | React (CRA) | v19 |
| **Styling** | TailwindCSS | Utility-first |
| **Animations** | Framer Motion | Page transitions |
| **Charts** | Recharts | Trade analytics dashboards |
| **HTTP client** | Axios | Session credentials |
| **Auth** | Session-based | NOT JWT (simplejwt installed but unused for auth) |
| **Semantic search** | SentenceTransformers | `all-MiniLM-L6-v2` (384-dim) |
| **Learn-to-Rank** | LightGBM | LambdaRank objective |
| **Graph ML** | Node2Vec | Company similarity embeddings |
| **Clustering** | HDBSCAN | Company reputation segmentation |
| **AI fallback** | OpenAI | `gpt-4o-mini` + `text-embedding-3-small` (optional) |
| **Rich text** | CKEditor 5 | Market intelligence alerts |
| **Audit logging** | django-auditlog | Company profile change tracking |

---

## 5. Backend — Django Applications

### 5.1 `accounts` App

**Purpose:** User management, session authentication, email verification, and token balance tracking.

#### Models

**`User`** (custom `AbstractUser`):
- Identifies by **email** (not username)
- `token_balance` (IntegerField) — tracks contact-unlock tokens
- `email_verified` (bool) — must be True before login allowed
- `verification_token` (UUID) — 24-hour expiring email verification token
- `token_created_at` (datetime) — token expiry reference
- Instance methods: `has_tokens()`, `deduct_tokens(n)`, `add_tokens(n)`, `is_verification_token_valid()`

**`UserAlertPreference`**:
- Per-user alert subscription settings
- Fields: `subscribed_products`, `subscribed_countries`, `subscribed_categories` (all JSON/text)
- `notification_frequency`: realtime / daily / weekly / monthly
- `email_notifications`, `in_app_notifications` (bool toggles)

#### Views / API Endpoints

| Endpoint | Method | What it does |
|---|---|---|
| `/accounts/api/signup/` | POST | Creates user, sends HTML verification email |
| `/accounts/api/login/` | POST | Validates email+password, checks `email_verified`, creates session |
| `/accounts/api/logout/` | POST | Destroys Django session |
| `/accounts/api/check-auth/` | GET | Returns current user info + token balance |
| `/accounts/api/forgot-password/` | POST | Sends password reset link via email |
| `/accounts/api/verify-email/<token>/` | GET | Marks user verified, redirects to frontend |
| `/accounts/api/resend-verification/` | POST | Regenerates UUID token, resends email |
| `/accounts/api/reset-password/` | POST | Validates reset token, updates password |

---

### 5.2 `companies` App

**Purpose:** Business directory with company profiles, product listings, and token-gated contact info.

#### Models

**`Sector`** — Product category tag (Rice, Wheat, Cotton, Sugar, etc.)

**`CompanyRole`** — Business role (Supplier, Buyer, Trader, Agent, etc.)

**`CompanyType`** — Legal structure (Pvt Ltd, Partnership, Sole Proprietor, etc.)

**`Company`** — Core company profile:
- `name`, `legal_name`, `country`, `province`, `district`, `address`, `website`
- `contact_email`, `phone`, `established_year`
- `logo_image` (FK → Image)
- `sector` (FK → Sector), `company_role` (FK), `company_type` (FK)
- `verification_status`: unverified → pending → verified → premium
- `has_trade_data` (bool) — whether linked to real Transaction records
- `is_directory_profile` (bool) — whether it appears in company directory
- Audit log enabled (all field changes tracked)

**`CompanyProduct`** — Products a company trades:
- FK to Company, FK to ProductSubCategory
- `variety`, `value_added`, `hsn_code`

**`KeyContact`** — Private contact info (locked behind tokens by default):
- `company` (FK), `name`, `designation`
- `phone`, `email`, `whatsapp`
- `is_public` (bool) — if True, visible without token cost

**`KeyContactUnlock`** — Records token-based contact unlocks:
- `user` (FK), `key_contact` (FK)
- `unlocked_at`
- Unique together: (user, key_contact) — no double-charging

**`Image`** — Polymorphic image model for companies, products, users

**`CompanyMetricsCache`** — Computed metrics cached to avoid expensive repeated queries

**`IngestionLog`** — Tracks data import jobs (filename, records imported, status, timestamp)

**`AdminAnnouncement`** — System-wide platform announcements

#### Views / API Endpoints

- **`CompanyViewSet`** (ReadOnly, AllowAny):
  - `GET /api/companies/` — Paginated list of verified companies with filters
  - `GET /api/companies/<id>/` — Single company profile; logs UserInteraction
  - `GET /api/companies/regions/` — Available provinces/regions
  - `GET /api/companies/hsn_codes/` — Available HSN codes
  - Optional AI fallback: OpenAI GPT-4o-mini for unstructured company queries

- **`KeyContactViewSet`** (IsAuthenticated):
  - `POST /api/key-contacts/<id>/unlock/` — Deducts 1 token (or 0 for public), creates KeyContactUnlock record

- **`SectorListView`**, **`CompanyTypeListView`**, **`CompanyRoleListView`** — Reference data lists

---

### 5.3 `subscriptions` App

**Purpose:** Subscription plan management, token economy, and MVP redemption code system.

#### Models

**`SubscriptionPlan`**:
- `plan_name`, `price` (decimal, USD), `currency`
- `tokens_included` (int) — tokens granted on activation
- `features` (JSON) — list of plan features
- `plan_type`: basic / professional / enterprise

**`UserSubscription`**:
- FK to User, FK to SubscriptionPlan
- `status`: pending / active / cancelled / expired
- `billing_cycle`: monthly / yearly / lifetime
- `start_date`, `end_date`
- `payment_reference` (transaction ID from payment provider)

**`TokenPurchase`** — Standalone token purchases (add-ons outside subscription):
- `user`, `tokens_purchased`, `amount_paid`
- `payment_provider`: Stripe / PayPal / JazzCash / Other
- `payment_reference`, `purchase_date`, `status`

**`RedeemCode`** — Promotional/beta access codes:
- `code` (unique, 12-char alphanumeric; excludes 0, O, I, 1)
- `plan` (FK → SubscriptionPlan)
- `status`: active / redeemed / expired
- `redeemed_by` (FK → User), `redeemed_at`, `expires_at`
- `@staticmethod generate_code()` — Generates safe, readable codes
- `redeem(user)` method — Creates UserSubscription + adds tokens to user

#### Views / API Endpoints

| Endpoint | Method | What it does |
|---|---|---|
| `/api/subscriptions/plans/` | GET | Returns all SubscriptionPlan objects |
| `/api/subscriptions/redeem/` | POST | Validates & redeems a code; updates user token balance |
| `/api/subscriptions/generate-codes/` | POST | Staff-only: generates 10 codes for a given plan |

**MVP Note:** Payment processing (Stripe/JazzCash) is stubbed. The platform runs entirely on redemption codes for beta access. Payment integration is the #1 next milestone.

---

### 5.4 `trade_data` App

**Purpose:** Core data models for the product taxonomy and the raw transaction records from government data.

#### Product Hierarchy (4-Level)

```
Product
  └── ProductCategory
        └── ProductSubCategory   ← what search matches against
              └── ProductItem    ← specific variants (e.g., "Dextrose Monohydrate")
```

- **`Product`** — Top level (e.g., "Sugar", "Rice")
- **`ProductCategory`** — Mid level (e.g., "Refined Sugar", "Basmati Rice")
- **`ProductSubCategory`** — Leaf level matched by search (e.g., "Dextrose", "IRRI-6")
  - Has `hs_code`, `description`
  - SBERT embeddings precomputed for all entries → stored in `/backend/search_index.pkl`
- **`ProductItem`** — Specific variants under a SubCategory
  - Used to propagate specificity: if user searches "Dextrose Monohydrate" → matches ProductItem → mapped back to parent SubCategory for aggregation

**`HsToProductMap`** — Maps HS codes ↔ product names (for HS-code-based queries)

#### Transaction Model (Core Data)

```python
class Transaction:
    trade_type          = 'IMPORT' | 'EXPORT'
    reporting_date      = DateField (indexed)
    buyer               = CharField (company name, raw text)
    seller              = CharField (company name, raw text)
    shipping_agent      = CharField
    origin_country      = CharField (indexed)
    destination_country = CharField (indexed)
    product_item        = ForeignKey(ProductItem)
    hs_code             = CharField (indexed)
    qty_kg              = DecimalField
    qty_mt              = DecimalField
    usd_per_kg          = DecimalField
    usd_per_mt          = DecimalField
    pkr                 = DecimalField
    usd                 = DecimalField
    source_file         = CharField  # which government file
    tx_reference        = CharField  # government reference
```

**Key design decisions:**
- `buyer` and `seller` are raw text fields (not ForeignKey to Company) — this reflects real government data where company names are not normalized
- Multiple database indexes: reporting_date, buyer, seller, hs_code, trade_type, origin_country, destination_country
- Search aggregates by these raw name fields (GROUP BY buyer / GROUP BY seller)

#### ML Embedding Models

**`CompanyEmbedding`** — Stores Node2Vec GNN outputs:
- `company_name`, `embedding` (JSON array), `cluster_tag` (reputation segment from HDBSCAN)
- `pagerank`, `degree` (network centrality metrics from transaction graph)

**`ProductEmbedding`** — Precomputed SBERT embeddings for products (backup; primary index is pickle file)

---

### 5.5 `search` App — The Core

**Purpose:** The intelligent search engine. Accepts natural-language queries and returns ranked lists of suppliers or buyers backed by real transaction data.

The search app has **no Django models** of its own — it reads from `trade_data` models and orchestrates the 4-stage pipeline.

See [Section 6](#6-the-4-stage-search-pipeline) for full pipeline documentation.

#### Views / API Endpoints

| Endpoint | Method | What it does |
|---|---|---|
| `GET /api/search/query/?q=...&scope=...` | GET | Main search — runs full 4-stage pipeline |
| `GET /api/search/supplier-detail/?name=...&query=...` | GET | Deep-dive on single supplier/buyer |
| `GET /api/search/query/debug_nlp/?q=...` | GET | Returns raw QueryMatcher output (dev tool) |

---

### 5.6 `trade_ledger` App

**Purpose:** Company explorer and deep analytics — who traded what, with whom, and at what price.

#### Views / API Endpoints

| Endpoint | Method | What it does |
|---|---|---|
| `/api/trade-ledger/explorer/` | GET | Lists companies with filters (direction, date, country, product) |
| `/api/trade-ledger/company/<name>/overview/` | GET | Volume, partners, products, network influence metrics |
| `/api/trade-ledger/company/<name>/products/` | GET | Product performance, price trends, co-traded products |
| `/api/trade-ledger/company/<name>/partners/` | GET | Top trading partners, trend analysis |
| `/api/trade-ledger/company/<name>/trends/` | GET | Time-series trends |
| `/api/trade-ledger/compare/` | POST | Side-by-side comparison of multiple companies |

All endpoints perform ORM aggregations over the Transaction table — no precomputed data (live queries, cached via Redis where available).

---

### 5.7 `market_intel` App

**Purpose:** Market intelligence alerts and news — early warning system for supply disruptions, price surges, and market events.

#### Models

**`Alert`** — AI-generated market intelligence:
- `headline`, `summary` (CKEditor rich text)
- `category`: Price Surge / Supply Disruption / Regulatory Change / Trade Policy / Other
- `severity`: low / medium / high / critical
- `product` (FK → ProductSubCategory), `country`
- `detected_at`, `source`, `meta` (JSON for extra data)

**`NewsArticle`** — News articles linked to an Alert

**`SavedAnalysis`** — User bookmarks: user + alert + optional personal notes

**`UserInteraction`** — Tracks user actions (company views, searches) for recommendation engine

#### Views / API Endpoints

- `GET /api/market-intel/alerts/` — List alerts with filters (severity, category, product)
- `GET /api/market-intel/alerts/<id>/` — Alert detail
- `POST /api/market-intel/alerts/<id>/save/` — Save to personal analysis
- `GET /api/market-intel/saved/` — User's saved analyses

---

### 5.8 `trade_lens` App

**Purpose:** Isolated analytics module with its own product and transaction models — used for demo/test data in the Trade Lens dashboard without polluting the main transaction table.

#### Models

**`TradeLensProduct`** — Curated product list for Trade Lens views
**`TradeLensTransaction`** — Demo/prototype transaction records for visualizations

**Note:** The main Transaction table (trade_data) contains real data; TradeLens has its own isolated data store for the analytics dashboard while the team builds out the real analytics pipeline.

---

## 6. The 4-Stage Search Pipeline

This is the intellectual core of Zarailink. A natural-language query flows through four sequential stages:

```
User Query (string)
      │
      ▼
┌─────────────────────────────────────────┐
│  Stage 1: QueryInterpreter              │
│  query_parser.py                        │
│  → structured ParsedQuery object        │
│  → intent (BUY/SELL), family (1-9),     │
│    product, scope, country_filter,      │
│    volume_mt, price range, time range   │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Stage 2: QueryMatcher                  │
│  nlp.py                                 │
│  → keyword + semantic + fuzzy match     │
│  → list of ProductSubCategory IDs       │
│    with confidence scores               │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Stage 3: SupplierAggregator            │
│  aggregation.py                         │
│  → Django ORM GROUP BY + annotations    │
│  → raw list of suppliers/buyers         │
│    with volume, price, recency data     │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Stage 4: RankingEnsemble               │
│  ranking_ltr.py                         │
│  → 70% heuristic + 30% LightGBM LTR    │
│  → final ranked list                    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
        JSON Response to Frontend
```

---

### Stage 1: QueryInterpreter (`query_parser.py`)

Parses a free-form string into a `ParsedQuery` object with structured fields.

#### Intent Detection

Scoring system: counts BUY vs SELL keywords, applies heuristics for ambiguous phrases.
- BUY keywords: "buy", "purchase", "import", "who sells", "looking for", "find supplier", "source"
- SELL keywords: "sell", "export", "who buys", "find buyer", "market for"

#### Query Family Detection (9 Families)

| Family | Description | Example Query |
|---|---|---|
| F1 | Generic buyer/supplier discovery | "Find dextrose suppliers" |
| F2 | Country-filtered discovery | "Dextrose suppliers from China" |
| F3 | Volume-matched discovery | "Who can supply 500 MT of rice?" |
| F4 | Price-filtered discovery | "Wheat buyers at above $300/MT" |
| F5 | Recency-filtered discovery | "Who bought cotton in Q1 2025?" |
| F6 | Top/recommended suppliers | "Top 5 dextrose suppliers" |
| F7 | Country comparison | "Compare dextrose demand by country" |
| F8 | Transaction evidence for named company | "Has Company X bought dextrose before?" |
| F9 | Multi-intent hybrid | "Find suppliers; also compare by country" |

#### Multi-Intent Splitting (F9)

- Always splits on `;`
- Splits on `and`/`also`/`but` **only** if the right side is "complex":
  - Contains an intent keyword (buy/sell/find/compare), OR
  - Contains a product + country combination
- Context product is carried across splits to resolve anaphora (e.g., "there" refers to previous product)
- Each sub-intent runs independently through the full pipeline
- Results returned as stacked sections

#### Extraction Features

- **Country extraction**: fuzzy matching against known country names + alias table (US → USA, UAE → United Arab Emirates, etc.)
- **Volume extraction**: regex `(\d+(?:\.\d+)?)\s*(mt|metric ton|tonnes?)` with unit normalization
- **Price extraction**: floor/ceiling from phrases like "under $700" / "above $300" / "$500-$800"
- **Time range extraction**: "Q1 2025", "Last 6 months", "since January 2024", "2024"
- **Scope detection**: PAKISTAN (default, local market) vs WORLDWIDE (international)
- **F8 company name extraction**: pattern-matches after keywords like "has", "did", "does"

#### Output (ParsedQuery)

```python
{
    'intent':            'BUY' | 'SELL',
    'family':            1-9,
    'product':           'dextrose',
    'scope':             'PAKISTAN' | 'WORLDWIDE',
    'country_filter':    ['China', 'India'],   # [] if none
    'volume_mt':         100.0,                # None if not specified
    'price_floor':       500.0,                # None if not specified
    'price_ceiling':     700.0,                # None if not specified
    'time_range':        'Q1 2025',            # None if not specified
    'counterparty_name': 'Company ABC',        # F8 only
    'multi_intent':      True | False,
    'sub_intents':       [ParsedQuery, ...]    # F9 only
}
```

---

### Stage 2: QueryMatcher (`nlp.py`)

Matches the extracted product string to `ProductSubCategory` IDs using a 4-method hybrid approach.

#### Matching Methods (in priority order)

1. **Keyword Match** (`keyword_subcat`): `ProductSubCategory.objects.filter(name__icontains=product)` — exact/partial substring match; highest confidence (score = 1.0)

2. **ProductItem Match** (`keyword_item`): Same but on `ProductItem.name` → maps back to parent SubCategory — enables matching specific variants like "Dextrose Anhydrous" → Dextrose SubCategory

3. **Semantic Match** (`semantic`): SBERT embedding cosine similarity against precomputed index
   - Model: `all-MiniLM-L6-v2` loaded once at class level (singleton)
   - Index: `/backend/search_index.pkl` — precomputed 384-dim vectors for all SubCategories
   - Threshold: cosine similarity ≥ 0.4
   - Score = raw cosine similarity (< 1.0)

4. **Fuzzy Variant Match**: `difflib.SequenceMatcher` ratio ≥ 0.6 for typo tolerance

#### Search Index File

`/backend/search_index.pkl` — Python pickle:
```python
{
    'embeddings': np.ndarray,   # shape: (N, 384)
    'ids':        list[int],    # ProductSubCategory IDs
    'names':      list[str],    # ProductSubCategory names
    'hs_codes':   list[str],    # corresponding HS codes
}
```
Rebuilt via management command when product data changes.

#### Output

```python
[
    {
        'id':               45,
        'name':             'Dextrose',
        'hs_code':          '1702.30',
        'score':            1.0,
        'method':           'keyword_subcat',
        'matched_variants': [789, 790],    # ProductItem IDs
        'variant_name':     'Dextrose Monohydrate'
    }
]
```

---

### Stage 3: SupplierAggregator (`aggregation.py`)

Translates matched ProductSubCategory IDs and parsed filters into an ORM query that aggregates Transaction records into supplier/buyer profiles.

#### Scope × Intent → Trade Direction

| Intent | Scope | Trade Type Filter | Group By |
|---|---|---|---|
| BUY | PAKISTAN | EXPORT, origin_country='Pakistan' | seller (who exports to Pakistan buyers) |
| BUY | WORLDWIDE | IMPORT | seller (who imports into any country) |
| SELL | PAKISTAN | IMPORT, destination_country='Pakistan' | buyer (who imports into Pakistan) |
| SELL | WORLDWIDE | EXPORT | buyer (who buys from Pakistani exporters) |

#### ORM Aggregation

```python
Transaction.objects
    .filter(product_item__sub_category_id__in=subcategory_ids, ...)
    .values(target_field, country_field)
    .annotate(
        total_volume    = Sum('qty_mt'),
        avg_price       = Avg('usd_per_mt'),
        shipment_count  = Count('id'),
        last_shipment   = Max('reporting_date'),
        max_shipment_vol= Max('qty_mt'),
        avg_shipment_vol= Avg('qty_mt'),
    )
```

#### Volume Compatibility Scoring

When `volume_mt` is specified, each supplier gets a compatibility score:
```
score = 0.5 × (max_single_shipment / requested_volume)
      + 0.3 × (total_volume / requested_volume)
      + 0.2 × (avg_shipment / requested_volume)
```
Capped at 1.0. Labels: Strong (≥0.8), Good (≥0.5), Partial (≥0.3), Low (<0.3).

This is a **soft filter** — low-scoring suppliers still appear but are ranked lower, giving the user a complete picture.

#### Special Handlers

**`CountryComparator`** (F7):
- Groups transactions by origin/destination country
- Returns per-country: total volume, avg price, shipment count, trend
- Suitable for "compare dextrose demand by country" queries

**`EvidenceRetriever`** (F8):
- Filters by exact/fuzzy buyer/seller name match
- Returns full transaction history for named company + product
- Also returns "similar buyers" (others who bought the same product)

---

### Stage 4: RankingEnsemble (`ranking_ltr.py`)

Produces the final ranked list using a weighted ensemble of two signals.

#### Heuristic Ranker (70% weight)

Features computed for each candidate:
- **Recency score**: `exp(-days_since_last_trade / 180)` — recent activity valued higher
- **Volume consistency**: `log(total_volume)` normalized — higher and more consistent is better
- **Price proximity**: `1 - |avg_price - user_budget| / user_budget` — closer to stated budget
- **Relationship maturity**: `log(shipment_count)` — more shipments = more established

#### LightGBM LTR (30% weight)

- **Algorithm**: LambdaRank (pointwise → listwise gradient boosting)
- **Model file**: `/backend/search/models/lgbm_ltr.txt`
- **Feature vector** (per candidate):
  ```
  [log(total_volume), days_since_trade, price_fit, shipment_count, recency_weight]
  ```
- **Labels**: Pseudo-labels generated by heuristic ranker (no real user clicks yet)
- **Cold-start strategy**: Domain heuristics as training signal → model learns ranking patterns without needing real user data
- **Training script**: `/backend/search/services/train_ltr.py`

#### Ensemble Formula

```python
final_score = 0.7 × heuristic_score + 0.3 × ltr_score
```

#### ComparableFinder

Used by the `supplier_detail` endpoint to find "similar suppliers":
- Fetches CompanyEmbedding (Node2Vec vectors) for the target company
- Cosine similarity against all other company embeddings
- Returns top-K most similar suppliers with similarity scores

---

## 7. ML Pipeline In Depth

### SentenceTransformer Semantic Search

- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Embedding dimension**: 384
- **Size**: ~32 MB
- **Loaded**: Once per Django process (class-level singleton in `QueryMatcher`)
- **Index**: `/backend/search_index.pkl` — precomputed for all ProductSubCategory names
- **Inference**: ~5-20ms per query (CPU)
- **Rebuild**: Management command `python manage.py rebuild_search_index`

### LightGBM Learn-to-Rank

- **Objective**: `lambdarank` (NDCG optimization)
- **Model format**: Text-based tree dump (`lgbm_ltr.txt`)
- **Training**: `train_ltr.py` script — generates query groups from transaction history, pseudo-labels from heuristic ranker
- **Features**: 5 numeric features (see Stage 4 above)
- **Current state**: Trained on pseudo-labels; production upgrade path = real click log data

### Node2Vec Graph Embeddings

- **Purpose**: Company similarity for `supplier_detail` "similar suppliers" section
- **Method**: Node2Vec — random walks on transaction graph (edges = transactions between buyer/seller)
- **Output**: Per-company 128-dim embedding stored in `CompanyEmbedding.embedding` (JSON)
- **Metrics**: `pagerank` (importance in trade network), `degree` (number of unique partners)

### HDBSCAN Clustering

- **Purpose**: Reputation segmentation of companies
- **Input**: Node2Vec embeddings
- **Output**: `cluster_tag` on `CompanyEmbedding` — labels like "Major Exporter", "Niche Supplier", "New Entrant"
- **Use**: Filter/label companies in the Trade Directory

### OpenAI Fallback (Optional)

- **Models**: `gpt-4o-mini` (text), `text-embedding-3-small` (semantic)
- **Trigger**: Falls back to OpenAI when local SBERT returns zero high-confidence matches
- **Requires**: `OPENAI_KEY` env variable — disabled gracefully if not set

---

## 8. Frontend — React Application

### Application Shell (`App.js`)

- React Router v6 with lazy loading (all routes use `React.lazy`)
- `Suspense` with skeleton fallback
- **Route types**:
  - `ProtectedRoute`: redirects to `/login` if not authenticated
  - `PublicRoute`: redirects to `/dashboard` if already authenticated
- Global providers: `ThemeProvider`, `AuthProvider`, `ToastProvider`

### Global Auth State (`context/AuthContext.js`)

- Context provides: `user`, `loading`, `isAuthenticated`, `tokenBalance`
- Methods: `login(email, pass)`, `logout()`, `checkAuthStatus()`, `refreshUser()`
- Uses `fetch` with `credentials: 'include'` for session cookie handling
- On mount: hits `/accounts/api/check-auth/` to restore session

### API Client (`services/api.js`)

- Axios instance: `baseURL: 'http://localhost:8000/api'`
- `withCredentials: true` — sends session cookies automatically
- No auth header (session-based, not token-based)

### Pages & Components

#### Auth Module (`/components/Auth/`)

| Component | Route | Purpose |
|---|---|---|
| `Signup` | `/signup` | Registration form → email verification |
| `Login` | `/login` | Email + password login |
| `ForgotPassword` | `/forgot-password` | Email password reset request |
| `ResetPassword` | `/reset-password/:token` | Token-based password change |
| `EmailVerification` | `/verify-email` | Status/instructions page |
| `VerifyEmailSuccess` | `/verify-email-success` | Success landing page |

#### Dashboard (`/components/Dashboard/`)

| Component | Route | Purpose |
|---|---|---|
| `Dashboard` | `/dashboard` | User home — quick stats, recent activity |
| `MarketBrief` | embedded | Market summary cards, alerts preview |

#### Trade Directory (`/components/TradeDirectory/`)

| Component | Route | Purpose |
|---|---|---|
| `FindSuppliers` | `/find-suppliers` | Search + filter + paginated supplier list |
| `FindBuyers` | `/find-buyers` | Same interface, buyer intent |
| `CompanyProfile` | `/company/:id` | Full company profile page |

#### Search Module (`/components/Search/`)

| Component | Route | Purpose |
|---|---|---|
| `SearchHome` | `/search` | Natural language search entry point |
| `SearchResults` | `/search/results` | Results page with section rendering |
| `DealDetail` | `/search/supplier/:name` | Supplier deep-dive with comparables |

The `SearchResults` component handles F9 multi-intent results by rendering stacked sections, F7 as country comparison tables, and F8 as transaction evidence cards.

#### Trade Intelligence (`/components/TradeIntelligence/`)

| Component | Route | Purpose |
|---|---|---|
| `TradeLedger` | `/trade-ledger` | Company explorer with filters |
| `CompanyOverview` | `/trade-ledger/:name` | Company analytics overview |
| `CompanyProducts` | `/trade-ledger/:name/products` | Product breakdown for company |
| `CompanyPartners` | `/trade-ledger/:name/partners` | Top trading partners |
| `CompanyTrends` | `/trade-ledger/:name/trends` | Time-series trade trends |
| `CompareCompanies` | `/compare` | Side-by-side multi-company comparison |
| `TradePulse` | `/trade-pulse` | Market alerts feed |
| `TradeLens` | `/trade-lens` | Product analytics dashboard |
| `TradeLensOverview` | nested | Summary tiles |
| `TradeLensSummary` | nested | Metrics summary |
| `TradeLensComparison` | nested | Country vs country comparison |
| `TradeLensDetails` | nested | Transaction detail table |
| `TradeLensGlobal` | nested | World map visualization |
| `LinkPrediction` | `/link-prediction` | GNN-based partner recommendations |

#### Subscriptions (`/components/Subscriptions/`)

| Component | Route | Purpose |
|---|---|---|
| `Subscription` | `/subscription` | Plan cards, redemption code input |

#### Common Components

- `Modal` — Reusable modal wrapper with backdrop
- `Pagination` — Page navigation for lists
- `Breadcrumb` — Navigation breadcrumbs
- `ContactUnlockModal` — "Unlock contact" flow (shows token cost, confirms)
- `TokenPurchaseModal` — Opens subscription page if token-poor
- `ToastProvider` + `useToast` — Notification system (success/error/info)
- `VerificationBadge` — Verified / Premium company status badge
- `WatchlistButton` — Save company to watchlist (local state)
- `ExportButton` — Download results as CSV/PDF
- `SortSelector` — Column sort control for tables
- `ShareButton` — Share a company/search link
- `Skeleton` — Loading placeholder components

---

## 9. Authentication & Authorization System

### Session-Based Auth

- Django `SessionMiddleware` manages session cookies
- `django.contrib.auth.authenticate()` + `login()` / `logout()`
- Frontend sends `credentials: 'include'` — session cookie in every request
- CSRF: DRF handles automatically with session auth

### Email Verification Flow

```
1. User submits signup form
   → User created (email_verified=False, verification_token=UUID4, token_created_at=now)
   → HTML + plain text verification email sent

2. User clicks link in email
   → GET /accounts/api/verify-email/{token}/
   → Checks: token exists AND token_created_at + 24h > now
   → Sets email_verified=True, clears token
   → Redirects to {FRONTEND_URL}/verify-email-success

3. User attempts login
   → Checks email_verified=True; if False → 403 "Please verify your email"

4. Resend verification
   → Generates new UUID, resets token_created_at
   → Sends new email
```

### Permission Model

| Resource | Permission |
|---|---|
| Company list / profiles | AllowAny |
| Company search | AllowAny |
| Key contact unlock | IsAuthenticated |
| Trade ledger | IsAuthenticated |
| Market intelligence | IsAuthenticated |
| Subscriptions / redemption | IsAuthenticated |
| Code generation | IsAdminUser (is_staff=True) |

---

## 10. Token Economy

Tokens are the in-app currency that gates access to private contact information.

### How It Works

1. **Earning tokens**: Redeem a subscription plan code → `RedeemCode.redeem(user)` → `user.add_tokens(plan.tokens_included)`
2. **Spending tokens**: Unlock a KeyContact → `user.deduct_tokens(1)` → create `KeyContactUnlock` record
3. **Public contacts**: `KeyContact.is_public=True` → 0 tokens, free to view
4. **Replay protection**: `KeyContactUnlock` has unique_together(user, contact) — same contact never charged twice
5. **Atomic safety**: Token deduction wrapped in `transaction.atomic()` — no double-spend

### Token Sources (current)

- `RedeemCode` → `UserSubscription` + tokens batch
- `TokenPurchase` (model exists, payment integration pending)

### Token Economy Status

The token economy model is **fully built** at the data and logic layer. What remains is the payment integration to allow users to purchase tokens with real money (Stripe / JazzCash).

---

## 11. Database Schema Summary

### Core Tables

| Table | Rows | Purpose |
|---|---|---|
| `accounts_user` | User accounts | Email, password hash, token balance, verification |
| `companies_company` | Company directory | Profiles, verification status, sector |
| `companies_keycontact` | Contact info | Phone, email, WhatsApp (token-gated) |
| `companies_keycontactunlock` | Unlock records | (user, contact) unlock history |
| `trade_data_transaction` | **Core data** | Raw import/export records from government |
| `trade_data_product` | Product taxonomy | Top level products |
| `trade_data_productcategory` | Product taxonomy | Mid level |
| `trade_data_productsubcategory` | Product taxonomy | Leaf level (what search matches) |
| `trade_data_productitem` | Product variants | Specific items (e.g., Dextrose Monohydrate) |
| `trade_data_companyembedding` | GNN embeddings | Node2Vec vectors + pagerank + cluster |
| `subscriptions_subscriptionplan` | Plans | Price, tokens, features |
| `subscriptions_redeemcode` | Codes | Beta access / promo codes |
| `subscriptions_usersubscription` | Active subscriptions | Per-user subscription records |
| `market_intel_alert` | Alerts | AI market intelligence |
| `market_intel_userinteraction` | Behavior | User view/search events |
| `market_intel_savedanalysis` | Bookmarks | User-saved alerts |

### Key Indexes on Transaction Table

- `reporting_date` — for time range filtering
- `buyer` — GROUP BY buyer (SELL queries)
- `seller` — GROUP BY seller (BUY queries)
- `hs_code` — for HS-code-based lookup
- `trade_type` — IMPORT/EXPORT split
- `origin_country`, `destination_country` — country filtering

---

## 12. API Endpoints Reference

### Accounts (`/accounts/api/`)

```
POST   /signup/                    Create account + send verification email
POST   /login/                     Authenticate, create session
POST   /logout/                    Destroy session
GET    /check-auth/                 Returns current user info
POST   /forgot-password/            Send password reset email
GET    /verify-email/<token>/       Verify email, redirect to frontend
POST   /resend-verification/        Regenerate + resend verification token
POST   /reset-password/             Update password via token
```

### Companies (`/api/`)

```
GET    /companies/                  List verified companies (paginated, filterable)
GET    /companies/<id>/             Company detail (logs interaction)
GET    /companies/regions/          Available regions/provinces
GET    /companies/hsn_codes/        Available HSN codes
POST   /key-contacts/<id>/unlock/   Unlock contact (costs 1 token)
GET    /sectors/                    List sectors
GET    /company-types/              List company types
GET    /company-roles/              List company roles
```

### Search (`/api/search/`)

```
GET    /query/?q=...&scope=...      Main natural-language search
GET    /query/debug_nlp/?q=...      Debug NLP parsing output
GET    /supplier-detail/?name=...   Supplier deep-dive page
```

### Trade Ledger (`/api/trade-ledger/`)

```
GET    /explorer/                   Company list with filters
GET    /company/<name>/overview/    Company metrics summary
GET    /company/<name>/products/    Product breakdown
GET    /company/<name>/partners/    Trading partners
GET    /company/<name>/trends/      Time-series trends
POST   /compare/                    Compare multiple companies
```

### Subscriptions (`/api/subscriptions/`)

```
GET    /plans/                      List subscription plans
POST   /redeem/                     Redeem a code
POST   /generate-codes/             Generate codes (staff only)
```

### Market Intelligence (`/api/market-intel/`)

```
GET    /alerts/                     List alerts (filterable)
GET    /alerts/<id>/                Alert detail
POST   /alerts/<id>/save/           Save alert to personal list
GET    /saved/                      User's saved analyses
```

### Trade Lens (`/api/trade-lens/`)

```
GET    /overview/                   Trade Lens product overview
GET    /transactions/               Trade Lens transaction data
GET    /comparison/                 Country comparison
```

---

## 13. Data Flow Examples

### Example 1: Natural Language Search — F2 (Country-Filtered)

```
Query: "Find dextrose suppliers from China under $700/MT"

Stage 1 — QueryInterpreter:
  intent = BUY
  family = F2 (country-filtered)
  product = 'dextrose'
  country_filter = ['China']
  price_ceiling = 700.0
  scope = WORLDWIDE

Stage 2 — QueryMatcher:
  Keyword match: ProductSubCategory(id=45, name='Dextrose')
  Variant match: ProductItem 'Dextrose Monohydrate' → SubCat 45
  Returns: [{id: 45, score: 1.0, method: 'keyword_subcat'}]

Stage 3 — SupplierAggregator:
  trade_type = 'IMPORT'
  Filter: product_item__sub_category_id__in=[45], origin_country='China',
          usd_per_mt__lte=700
  GROUP BY: seller, origin_country
  Aggregates: total_volume, avg_price, shipment_count, last_shipment
  Returns: 8 suppliers

Stage 4 — RankingEnsemble:
  Heuristic scores calculated for each supplier
  LTR model inference on 5-feature vectors
  Ensemble: 0.7×heuristic + 0.3×ltr
  Final ranked list: [Supplier A, Supplier B, ...]

Response:
  {
    results: [{name, country, total_volume, avg_price, shipment_count, volume_fit, ...}],
    parsed_query: {...},
    matched_products: [...]
  }
```

### Example 2: Transaction Evidence — F8

```
Query: "Has Muller & Phipps Pakistan imported dextrose?"

Stage 1:
  family = F8
  intent = BUY
  product = 'dextrose'
  counterparty_name = 'Muller & Phipps Pakistan'

Stage 2:
  ProductSubCategory(id=45)

Stage 3 — EvidenceRetriever:
  Transaction.objects.filter(
    buyer__iexact='Muller & Phipps Pakistan',
    product_item__sub_category_id__in=[45]
  )
  Returns: 12 transactions, buyer summary, similar buyers list

Response:
  {
    type: 'evidence',
    company_name: 'Muller & Phipps Pakistan',
    transaction_count: 12,
    total_volume: 450.5,
    transactions: [...],
    similar_buyers: [...]
  }
```

### Example 3: Multi-Intent — F9

```
Query: "Find dextrose buyers in Pakistan; also show which countries buy most"

Stage 1 — Splits on ';':
  Sub-intent 1: family=F2, intent=SELL, product='dextrose', country=['Pakistan'], scope=PAKISTAN
  Sub-intent 2: family=F7, intent=SELL, product='dextrose' (carried from sub-intent 1)

Sub-intent 1 pipeline → buyer list for Pakistan dextrose
Sub-intent 2 pipeline → CountryComparator → per-country volume/price

Response:
  {
    type: 'multi_intent',
    sections: [
      { family: 'F2', title: 'Buyers in Pakistan', results: [...] },
      { family: 'F7', title: 'Demand by Country', countries: [...] }
    ]
  }
```

---

## 14. What Has Been Built & Accomplished

This section captures the complete implemented scope of the platform as of March 2026.

### Core Infrastructure

- [x] Django project with 8 apps, full migrations, PostgreSQL integration
- [x] Custom User model (email-based auth, token balance, email verification)
- [x] Session-based authentication (signup, login, logout, password reset)
- [x] 24-hour email verification with expiring UUID tokens
- [x] HTML + plain-text email templates
- [x] Redis cache integration with LocMemCache fallback (auto-detected)
- [x] CORS configured for React frontend on localhost:3000
- [x] django-auditlog integrated for company profile change tracking
- [x] CKEditor 5 integration for rich-text alert content
- [x] Django admin panel with all models registered

### Search Engine (The Core Product)

- [x] **4-stage search pipeline** fully implemented and production-ready
- [x] **Stage 1 — QueryInterpreter**: 9 query families with full intent, product, country, volume, price, time range, and scope extraction
- [x] **Stage 2 — QueryMatcher**: Hybrid keyword + SentenceTransformer SBERT + fuzzy matching with ProductItem specificity propagation
- [x] **Stage 3 — SupplierAggregator**: Django ORM aggregation with intent-driven scope/direction logic, volume compatibility scoring, soft-filter approach
- [x] **Stage 4 — RankingEnsemble**: 70/30 heuristic + LightGBM LambdaRank ensemble
- [x] **Search index** (`search_index.pkl`) with precomputed SBERT embeddings for all ProductSubCategories
- [x] **LTR model** (`lgbm_ltr.txt`) trained on pseudo-labels from heuristic ranker
- [x] **Multi-intent query support** (F9): splits on `;` and smart `and`, runs sub-intents independently, returns stacked sections
- [x] **Country comparison** (F7): CountryComparator aggregates by country
- [x] **Transaction evidence** (F8): EvidenceRetriever for named-company queries
- [x] **Supplier deep-dive** endpoint with comparable finder (Node2Vec embeddings)
- [x] **Debug NLP endpoint** for development inspection
- [x] **F7 downgrade guard**: preserves F7 when query contains country/countries keywords, downgrades to F2 when specific country extracted
- [x] **F9 SELL+WORLDWIDE** sub-intent handling — correctly returns results
- [x] **F9 multi-intent splitting** on F6/F7/F8 structural keywords after "and"
- [x] **SentenceTransformer meta-tensor crash fix** — deferred model load to avoid import-time crash
- [x] **F8 and/& normalization** — handles "&" in company names

### Data Models

- [x] 4-level product taxonomy (Product → Category → SubCategory → Item)
- [x] Transaction model with full trade record fields + all required indexes
- [x] HS code mapping table
- [x] Company model with verification status, logo, sector, role, type
- [x] KeyContact model with token-gating flag
- [x] KeyContactUnlock with unique-together replay protection
- [x] CompanyEmbedding with Node2Vec vectors + pagerank + cluster tags
- [x] IngestionLog for tracking data imports

### Token Economy

- [x] User.token_balance field with `has_tokens()`, `deduct_tokens()`, `add_tokens()` methods
- [x] KeyContact.is_public flag (0-token access for public contacts)
- [x] KeyContactUnlock record creation on unlock
- [x] Atomic token deduction (no double-spend)
- [x] SubscriptionPlan model with token bundles
- [x] RedeemCode model with safe code generation (excludes 0/O/I/1)
- [x] `RedeemCode.redeem()` method — creates UserSubscription + adds tokens
- [x] TokenPurchase model (payment integration pending)
- [x] Staff endpoint to generate 10 codes for a given plan

### Company Directory & Trade Ledger

- [x] Company CRUD via DRF ViewSet (ReadOnly, public)
- [x] Company profile page with UserInteraction logging
- [x] Region/HSN code reference endpoints
- [x] KeyContact unlock flow (token check → deduct → record)
- [x] Trade Ledger: company explorer with multi-filter support
- [x] Company overview analytics (volume, partners, products, network influence)
- [x] Company product breakdown (price trends, co-traded products)
- [x] Company partner analytics (top partners, trend)
- [x] Company time-series trends
- [x] Company comparison (side-by-side multi-company)

### Market Intelligence

- [x] Alert model (headline, summary, severity, category)
- [x] Alert list + detail views
- [x] SavedAnalysis (user bookmarks alerts with notes)
- [x] UserInteraction tracking (views, searches for recommendation engine)
- [x] NewsArticle linked to alerts

### ML Infrastructure

- [x] SentenceTransformer integration (all-MiniLM-L6-v2)
- [x] SBERT search index build + precomputed embedding pickle
- [x] LightGBM LambdaRank model trained + serialized
- [x] LTR training script with pseudo-label generation
- [x] Node2Vec GNN embeddings stored per company
- [x] HDBSCAN company clustering (cluster_tag)
- [x] ComparableFinder using embedding cosine similarity
- [x] OpenAI fallback (gpt-4o-mini + text-embedding-3-small) — optional, gracefully disabled

### Frontend

- [x] React SPA with React Router v6 and lazy loading
- [x] AuthContext with session management (login/logout/refresh/checkAuth)
- [x] Axios API client (session cookies, no token headers)
- [x] Complete Auth module: signup, login, logout, forgot password, reset password, email verification flows
- [x] Dashboard with market brief
- [x] Trade Directory: Find Suppliers, Find Buyers, Company Profile
- [x] Search module: SearchHome, SearchResults (handles all families), DealDetail (supplier deep-dive)
- [x] Trade Ledger: company explorer + full analytics sub-pages
- [x] Trade Pulse: market alerts feed
- [x] Trade Lens: product analytics dashboard with 5 sub-views (overview, summary, comparison, details, global map)
- [x] Link Prediction page (GNN partner recommendations)
- [x] Subscriptions page with plan cards + code redemption
- [x] Watchlist (save companies locally)
- [x] Common component library: Modal, Pagination, Breadcrumb, ContactUnlockModal, TokenPurchaseModal, ToastProvider, VerificationBadge, WatchlistButton, ExportButton, SortSelector, ShareButton, Skeleton loaders
- [x] TailwindCSS styling throughout
- [x] Framer Motion page transitions
- [x] Recharts for analytics visualizations

---

## 15. Configuration & Dev Setup

### Local Development

```bash
# Backend
cd backend
python manage.py migrate
python manage.py runserver
# Running at: http://localhost:8000

# Frontend
cd frontend
npm install
npm start
# Running at: http://localhost:3000
```

### Environment Variables (`backend/.env`)

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | Hardcoded (dev only) |
| `OPENAI_KEY` | OpenAI API key | None (AI fallback disabled) |
| `FRONTEND_URL` | Email redirect base URL | `http://localhost:3000` |
| `DATABASE_URL` | Override DB connection | Not used (hardcoded in settings) |

### Database Config (hardcoded in settings.py)

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'zarailink',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': 5432,
    }
}
```

### Cache Config

```python
# Auto-detects Redis; falls back to LocMemCache
# Redis: 127.0.0.1:6379
```

### Key Management Commands

```bash
python manage.py rebuild_search_index    # Rebuild SBERT embedding pickle
python manage.py train_ltr               # Retrain LightGBM LTR model
python manage.py generate_embeddings     # (Re)compute Node2Vec embeddings
python manage.py ingest_transactions     # Import transaction data from CSV
```

---

## 16. Known Gaps & Next Steps

### Production Blockers

1. **Hardcoded credentials** — `settings.py` has DB password and secret key hardcoded; must use env vars before deployment
2. **DEBUG=True** — Must be False in production; ALLOWED_HOSTS must be expanded
3. **Email SMTP** — Currently uses Django's console email backend or basic SMTP; production email service (SendGrid, SES) needed
4. **Payment integration** — `TokenPurchase` and `UserSubscription` models exist but Stripe/JazzCash is stubbed; subscription economy currently runs on redemption codes only
5. **Rate limiting** — No rate limiter on the search endpoint; susceptible to scraping or abuse

### ML Upgrades

6. **Click log pipeline** — LTR currently trained on pseudo-labels; real user clicks/interactions are tracked in `UserInteraction` but no pipeline yet feeds them back into LTR retraining
7. **Search index freshness** — When new products are added, `search_index.pkl` must be manually rebuilt; no automation yet
8. **LTR model refresh** — No scheduled retraining; manual `train_ltr.py` only

### Feature Gaps

9. **Real payment gateway** — The single biggest commercial gap; blocks the subscription economy from going live
10. **Admin data ingestion UI** — `IngestionLog` model exists but the admin UI for uploading new government transaction data is not built; currently manual management command
11. **API versioning** — No versioning strategy; breaking changes would impact all clients
12. **Test coverage** — Tests exist in `accounts/tests/` but coverage is minimal across other apps
13. **Monitoring & observability** — No APM tool (Sentry, Datadog) configured; minimal structured logging

### Architecture Opportunities

14. **Async search** — The 4-stage pipeline is synchronous; for long-running queries, a Celery task + polling pattern would improve UX
15. **Elasticsearch** — As transaction data grows, PostgreSQL ILIKE queries on text fields (buyer, seller) will become the bottleneck; Elasticsearch or pgvector could scale better
16. **Real-time alerts** — Market intelligence alerts are static; a pipeline to auto-generate alerts from fresh transaction data would be high value

---

*This document was generated from a complete read of the Zarailink codebase as of March 2026. It reflects the actual state of the code — not the intended or aspirational state.*
