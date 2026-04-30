# ZaraiLink: Data & NLU Pipeline Specifications

## 1. Executive Summary
ZaraiLink utilizes a hybrid search architecture that marries a robust relational trade database with a state-of-the-art Natural Language Understanding (NLU) pipeline. This document outlines the technical specifications of both the underlying data layer and the sequential AI pipeline used to process plain-English trade queries.

## 2. Data Layer Overview
The foundation of ZaraiLink's intelligence is its structured PostgreSQL database, which houses comprehensive cross-border trade data.

*   **Total Trade Records:** **9,500+ individual transaction records** detailing real-world shipments, volumes, pricing, and dates.
*   **Company Directory:** Verified profiles of Pakistani and international trading entities (suppliers, buyers, mills, distributors).
*   **Taxonomy:** A hierarchical classification of products and Harmonized System (HS) codes mapped against the transaction data.

## 3. The NLU Pipeline Architecture
When a user enters a natural language query (e.g., *"I want to buy dextrose from China under $700"*), it bypasses standard keyword matching and enters a custom 4-stage NLU pipeline. This pipeline deconstructs the sentence into actionable database filters.

### Stage 1: Intent Classification (SetFit)
*   **Technology:** Sentence Transformer Fine-tuning (SetFit) framework.
*   **Purpose:** Determines the user's trade direction—whether they are looking to `BUY` (searching for suppliers) or `SELL` (searching for buyers).
*   **Training Data:** Fine-tuned on **354 labeled trade queries** specifically curated for ZaraiLink's domain.
*   **Performance:** Achieves **89.4% accuracy** in determining explicit and implicit trade intents.

### Stage 2: Product Keyword Extraction (KeyBERT)
*   **Technology:** KeyBERT (Keyword Extraction using BERT).
*   **Purpose:** Isolates the core product or commodity being searched for from the surrounding conversational filler.
*   **Output:** In the query *"buy dextrose from China"*, KeyBERT extracts `"dextrose"` to map against the HS Code and Variant database.

### Stage 3: Geographic Resolution (RapidFuzz)
*   **Technology:** RapidFuzz (C++ optimized string matching).
*   **Purpose:** Extracts and normalizes country or region names mentioned in the query.
*   **Resiliency:** Utilizes fuzzy matching (Levenshtein distance) to gracefully handle typos (e.g., extracting "India" from "Indai") and maps the resolved text to standard ISO country codes for accurate database filtering.

### Stage 4: Constraint Extraction (DeepSeek LLM) — *Conditional*
*   **Technology:** DeepSeek LLM (accessed via OpenRouter API).
*   **Purpose:** Extracts complex numerical constraints, such as maximum/minimum price parameters or target volumes (e.g., `price < $700`).
*   **Performance Optimization (The Bypass):** LLM API calls introduce network latency. To mitigate this, Stage 4 is strictly **conditional**. The pipeline runs a lightweight RegEx signal detector first. If no price or quantity signals (like `$`, digits, "MT", "tons", "under") are found in the raw query, this step is entirely bypassed, drastically reducing overall search latency.

## 4. The Composite Search Engine
Once the NLU pipeline completes its extraction, the structured parameters (Intent, Product, Country, Price Constraints) are handed back to the Django REST API. 

Django's Search Service translates these parameters into optimized PostgreSQL ORM queries. It aggregates the 9,500+ trade records to calculate:
*   Global Average Price per Metric Ton (MT)
*   Total Trade Volume
*   Shipment Counts
*   Ranked lists of counterparty companies.

These results are then scoped by the user's selected Trade Direction (Import/Export) and returned to the React frontend in under 3 seconds.

## 5. Key Metrics Summary
*   **Database Size:** 9,500+ Trade Transactions
*   **NLP Components:** 4 distinct models (SetFit, KeyBERT, RapidFuzz, DeepSeek)
*   **Intent Accuracy:** 89.4% (SetFit)
*   **Training Corpus:** 354 annotated queries
*   **Average Search Latency:** < 3 seconds
