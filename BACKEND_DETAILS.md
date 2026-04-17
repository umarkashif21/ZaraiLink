# ZaraiLink Backend Architecture: Deep Dive

## 1. Core Tech Stack
The ZaraiLink backend is a high-performance intelligence engine designed to process millions of trade records and provide sub-second semantic search.

*   **Framework**: Django 5.2 (Python)
*   **Primary Database**: PostgreSQL (Relational persistence)
*   **Search Engine**: OpenSearch (Vector store and Hybrid BM25 matching)
*   **Caching Layer**: Redis (For NLU results and session management)
*   **AI/ML Frameworks**: 
    - **Sentence-Transformers**: For 384-dimensional embeddings.
    - **SetFit**: For few-shot intent classification.
    - **GLiNER**: For zero-shot Named Entity Recognition (NER).
    - **LightGBM**: For the LambdaMART "Learn to Rank" (LTR) system.

---

## 2. The Intelligence Pipeline (NLU)
When a user types a query, it enters a 5-step semantic refinement process managed by the `ModernNLUEngine`:

1.  **Intent Detection (SetFit)**: Classifies the query as BUY (Import) or SELL (Export). It uses a fine-tuned `BAAI/bge-small-en-v1.5` backbone.
2.  **Entity Extraction (GLiNER)**: Identifies countries, product names, quantities, and price operators in one pass without custom training.
3.  **Keyword Isolation (KeyBERT)**: Strips "trade noise" (e.g., *"urgently looking for"*) and isolates the core commodity keyword.
4.  **Geographic Resolution (RapidFuzz)**: Normalizes country mentions to their standard DB keys.
5.  **Price Logic (LLM/Regex)**: Extracts numeric price ranges. It prioritizes a fast Regex path and only calls **OpenRouter (DeepSeek/Mistral)** for complex natural language logic.

---

## 3. Search & Aggregation Engine
Once the query is structured, the `SearchService` orchestrates the retrieval:

### A. Candidate Retrieval
- **OpenSearch Path**: Performs a hybrid search (Vector + Keyword) across the indexed product catalog.
- **ORM Fallback**: If OpenSearch is down, the system switches to a pure Postgres `pg_trgm` (Trigram similarity) search to ensure 100% uptime.

### B. The SupplierAggregator
This is the most compute-intensive part of the backend. It:
- **Perspective Filtering**: Real-time conversion of Buy/Sell intent into the relevant Trade Type (Import vs. Export).
- **Data Rollup**: Groups millions of transaction rows to compute weighted average prices, volume tonnage, and frequency for specific companies.
- **Intelligence Calc**: Computes real-time loyalty scores (Repeat Ratio) and risk metrics (Concentration) for every candidate.

---

## 4. Multi-Factor Ranking (The "Brain")
Candidates are sorted using a dual-layer approach:

1.  **Composite Scorer**: A heuristic model that normalizes Volume, Recency, Frequency, and Price into a 0-1 range using **Min-Max Scaling**.
2.  **Intent Weights**: The scorer dynamically shifts weights based on NLU signals (e.g., a "cheap" signal increases the weight of the Price factor by 500%).
3.  **LTR Reranker**: A **LightGBM** model performs final inference to tie-break results based on historical trade success patterns.

---

## 5. Data Infrastructure & Sync
- **Indexing Management**: `build_search_index.py` handles the mass transformation of Postgres rows into OpenSearch vectors.
- **Audit Logging**: Uses `auditlog` to track every change to the company directory and verified contact unlocks for security.
- **Vector Storage**: Products are embedded into **384-dimensional space**, allowing the system to know that *"Sugar"* and *"Saccharum"* are semantically identical.

---

## 6. Performance Optimizations
- **NLU Caching**: NLU results are hashed (MD5) and cached in Redis/LocMem for 24 hours to avoid redundant LLM calls.
- **Selective LLM Usage**: The system only hits external APIs (OpenRouter) if numeric extraction via local Regex fails.
- **Cold-Start LTR**: Uses "Pseudo-Labeling" to train the ranking model until enough real user click-data is collected for "Gold Standard" training.
