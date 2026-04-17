# ZaraiLink Search Engine: End-to-End Architecture Deep Dive

This document provides a comprehensive technical breakdown of the ZaraiLink Search Engine, detailing the multi-stage pipeline from raw natural language input to final ranked supplier/buyer intelligence.

---

## 1. High-Level Pipeline Overview

The search engine operates as a **6-stage pipeline**, moving from high-level intent to granular trade intelligence.

1.  **NLU Layer**: Query parsing, intent classification, and entity extraction.
2.  **Product Resolution**: Mapping natural language to hard HS codes and DB categories.
3.  **Perspective Filtering**: Mapping (Intent + UI Context) to trade directions (Import/Export).
4.  **Aggregation**: Rolling up millions of transaction rows into counterparty profiles.
5.  **Multi-Factor Ranking**: Intent-aware scoring using Volume, Count, Price, and Recency.
6.  **Intelligence Metrics**: Calculating behavioral labels (Momentum, Loyalty, Pricing Power).

---

## 2. Phase 1: NLU Engine (The Modern Stack)

The system uses a state-of-the-art **ModernNLUEngine** (found in `nlu_engine.py`) that combines four distinct ML models to avoid generic keyword matching.

### A. Intent Classification (SetFit)
- **Model**: Fine-tuned **SetFit** model (based on `BAAI/bge-small-en-v1.5`).
- **Function**: Classifies the user's role as a **BUYER** or **SELLER**.
- **Logic**: Handles complex phrasing like *"I'm looking to source rice"* (BUY) vs *"I have dextrose to offer"* (SELL).
- **Fallback**: Robust Regex-based intent detection if the ML model is unavailable.

### B. Entity Extraction (GLiNER)
- **Model**: **GLiNER** (Generalist Model for Information Extraction).
- **Function**: Zero-shot extraction of `product`, `country`, `quantity`, and `price`.
- **Logic**: Unlike traditional NER, it can find "Basmati Rice" or "China" without being explicitly trained on those specific words.

### C. Keyword Processing (KeyBERT + Stopword Stripping)
- **Model**: **KeyBERT**.
- **Function**: Extracts the "Semantic Core" of the product name.
- **Logic**: Strips trade noise (*"i want to buy"*, *"please find me suppliers of"*) to isolate the search term (*"dextrose anhydrous"*).

### D. Advanced Price Extraction (LLM + Regex)
- **Stack**: **OpenRouter (DeepSeek/Mistral)** for complex natural language, with a **Fast Regex Fallback**.
- **Function**: Converts phrases like *"under 500 usd"* into machine-readable filters: `{"range": {"usd_per_mt": {"lte": 500}}}`.
- **Signals**: Detects "ranking hints" (e.g., "cheap" → `price_asc`).

---

## 3. Phase 2: Product Resolution & Disambiguation

Once a product keyword (e.g., "Rice") is extracted, the `SearchService` maps it to the database hierarchy.

- **HS Code Extraction**: If the user typed an HS code (*"170230"*), the system maps it directly to the subcategory.
- **Fuzzy Matching (Trigram Similarity)**: Uses Postgres `pg_trgm` to handle typos (*"dextos"* → *"Dextrose"*).
- **Prefix Matching**: Fast path for partial matches (*"dex"* → *"Dextrose"*).
- **Disambiguation Flow**: 
    - If "Dextrose" matches both "Dextrose Monohydrate" and "Dextrose Anhydrous", the engine triggers a **Variant Picker** in the UI.
    - **Scope-Aware Availability**: It only shows variants that actually have data for the current intent (e.g., if no one exports "Dextrose Ball" from Pakistan, that variant is hidden).

---

## 4. Phase 3: Candidate Retrieval & Aggregation

The engine retrieves "Company Candidates" by performing a massive roll-up of transaction data.

### The Aggregator Logic (`SupplierAggregator`)
The system does **NOT** just search for company names. It aggregates real trade data:
- **Filters**: Applies row-level filters for `trade_type` (IMPORT vs EXPORT), `origin_country`, and `destination_country`.
- **Perspective Resolution**:
    - **BUY Worldwide** → Filters for `IMPORT` transactions (finding foreign sellers).
    - **SELL Pakistan** → Filters for `IMPORT` transactions where destination is Pakistan (finding local buyers).
- **Metric Roll-up**:
    - `total_volume`: Sum of `qty_mt`.
    - `shipment_count`: Count of unique references.
    - `avg_price`: Weighted average (Sum of Price * Volume / Total Volume).
    - `last_shipped`: Max of `reporting_date`.

---

## 5. Phase 4: Multi-Factor Ranking (Composite Score)

ZaraiLink does not simply sort by volume. It uses a **Normalized Composite Score** to find the "Best Fit."

### The Scoring Equation
The score is a weighted sum of normalized factors:
`Score = (w1 * Volume) + (w2 * Frequency) + (w3 * NormalizedPrice) + (w4 * Recency)`

### Intent-Aware Weighting
The weights shift dynamically based on the NLU "ranking hint":
- **Default (Balanced)**: Vol 0.4, Freq 0.3, Price 0.2, Recency 0.1.
- **"Cheap" Intent**: Price weight jumps to **0.5**, decreasing Volume weight.
- **"Bulk/Premium" Intent**: Volume weight jumps to **0.5**, prioritizing the biggest established players.

---

## 6. Phase 5: Intelligence & Behavior Metrics

The final search result includes "Intelligence Labels" computed on the fly by the `SupplierAggregator`.

| Metric | logic | Interpretation |
| :--- | :--- | :--- |
| **Repeat Ratio** | % of transactions with returning customers | **Loyalty**: >70% = "Strong" market trust. |
| **Concentration** | % of volume going to Top 3 buyers | **Risk**: >60% = "High" dependency on few clients. |
| **Momentum** | Growth over last 90 days vs previous 90 | **Trend**: "Growing" vs "Declining". |
| **Pricing Power** | Price change vs repeat behavior | **Position**: "Premium" if prices rise and customers stay. |

---

## 7. Phase 6: Learn to Rank (LTR) — The Supervised Layer

For advanced relevance, the system includes an **LTR Pipeline** (found in `ranking_ltr.py`).

- **Algorithm**: **LambdaMART** (via LightGBM).
- **Training**: Uses **Pseudo-Labeling**. Since it lacks user click data, it uses "Expert Rules" to create a silver-standard dataset to teach the model what a "Good" supplier looks like.
- **Inference**: Predicts a `relevance_score` (0-1) that acts as a tie-breaker or secondary ranker in the ensemble.

---

## 7. Search Infrastructure & Data Sync

To maintain performance, the search engine utilizes several specialized infrastructure components:

### A. Semantic Indexing (`build_search_index.py`)
- **Process**: A periodic management command that iterates over all `ProductSubCategory` and `ProductItem` entries.
- **Embeddings**: Uses `sentence-transformers` to generate **384-dimensional vectors** for each product.
- **Storage**: Currently stored as a high-performance `.pkl` index for fast local retrieval, or pushed to **OpenSearch** for distributed KNN search.

### B. OpenSearch Vector Store (`vector_store.py`)
- **Indexing**: Transactions and products are indexed into OpenSearch with a `combined_vector` field.
- **Search Method**: Supports **Hybrid Search** (BM25 Keyword + KNN Semantic). 
- **Resilience**: The `SearchService` includes a heartbeat check; if OpenSearch is unreachable, it silently falls back to the **Postgres/ORM Aggregator** to ensure zero downtime.

### C. The LTR Trainer (`train_ltr.py` / `ltr_dataset_builder.py`)
- **Dataset Builder**: Generates synthetic query-document pairs.
- **Pseudo-Labeling**: Assigns relevance grades (0-4) based on historical trade success.
- **Versioning**: Models are saved as `lgbm_ltr.txt` and loaded at runtime by the ranker.

---

## 8. Summary of Technologies Used

- **Backend**: Django (Python), Postgres (Trigram Search), OpenSearch (Vector/BM25).
- **ML Classifiers**: SetFit (Intent), GLiNER (NER), KeyBERT (Keywords), Sentence-Transformers (Embeddings).
- **Ranking**: LightGBM (LambdaMART), NumPy/Pandas (Composite scoring logic).
- **External Intelligence**: OpenRouter API (DeepSeek/Mistral for natural language price/query parsing).
- **Performance**: Django Cache (NLU result caching), pg_trgm (Postgres Fuzzy Search).
