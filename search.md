# ZaraiLink Search Engine: Implementation Journey

This document details the exact steps and tasks completed to build the ZaraiLink Unified Search Engine, from raw query parsing to AI-driven ranking.

---

## Technical Workflows

### 1. Unified Search Pipeline (Phase-Based Analysis)
To fit Canva/Slide decks, the pipeline is split into three horizontal execution phases.

#### Phase A: Natural Language Understanding (NLU)
Processes raw strings into actionable structured objects.

```mermaid
graph LR
    subgraph "Entry & Scope"
        U[4 User Types] --> Scope{Geographic Scope}
        Scope -->|PK| PK[Pakistan]
        Scope -->|WW| WW[Worldwide]
    end

    PK & WW --> Input([Raw Query])
    
    subgraph "NLU Brain"
        Input --> Tok[Tokenization + NER]
        Tok --> Intent{Intent}
        Intent -->|BUY| Buy[Search: Suppliers]
        Intent -->|SELL| Sell[Search: Buyers]
        Intent -->|Amb| Def[Default: BUY]
        
        Tok --> Ext[Constraint Extractor]
    end

    Buy & Sell & Def & Ext --> Meta[(Metadata)]
```

**Terminology & Key Concepts:**
- **The 4 Users:** Pakistan-based or Foreign-based users who select their search "Scope" (Pakistan marketplace or Worldwide intelligence).
- **Tokenization & NER (Named Entity Recognition):** Breaking a query into words and identifying "entities" like products, countries, or units.
- **Intent Classifier:** A logic gate that determines if the user wants to **BUY** (look for suppliers) or **SELL** (look for buyers).
- **Constraint Extractor:** Identifying filters like "below $500" or "exactly 100MT".
- **Default Fallback:** If the intent is unclear, the system defaults to "BUY" to provide the most likely useful results.

#### Phase B: Candidate Retrieval (Retrieval Engine)
A hybrid multi-path retrieval system handling sparse and dense data.

```mermaid
graph LR
    Meta[(Metadata)] --> SBERT[Dense Retrieval: SBERT Embedder]
    SBERT --> Vector[Vector Match: Top-K Subcats]
    Meta --> SQL[Sparse Retrieval: Structured SQL]
    SQL --> Joins[Relational Joins: Country/Price]
    Vector --> Aggregator[Aggregator Engine]
    Joins --> Aggregator
    Aggregator --> Candidates[[Unranked Candidates]]
```

**Terminology & Key Concepts:**
- **Dense Retrieval (SBERT):** Uses AI (Sentence-BERT) to understand *meaning*. If you search for "Liquid Glucose", it finds "Dextrose Syrup" because they are semantically similar, even if the words don't match.
- **Sparse Retrieval (SQL):** Uses traditional database queries to find exact matches for filters like "Country = China".
- **Top-K Subcats:** Fetching the most relevant product categories (e.g., the top 5 matches).
- **Aggregator Engine:** Combines the semantic results (from SBERT) with the structural results (from SQL) to create a single list of candidate companies.

#### Phase C: Ranking & Intelligence (LTR Pipeline)
A hybrid pipeline that combines AI ranking with expert business heuristics.

```mermaid
graph LR
    subgraph "Intelligence Loop"
        Data[(Trade Data)] --> Rules[Expert Rules]
        Rules --> Model[LambdaMART AI]
    end

    Candidates[[Unranked]] --> Extractor[Feature Vectorizer]
    Extractor --> Model
    Model -->|30% Weight| Ensemble{Hybrid Scorer}
    Rules -->|70% Weight| Ensemble
    Ensemble --> Results([Ranked JSON])
```

**Terminology & Key Concepts:**
- **Expert Rules:** Professional trade heuristics (e.g., Higher trade volume equals higher rank).
- **LambdaMART AI:** Our Learn-to-Rank (LTR) model. It "learns" from the Expert Rules to find complex patterns.
- **Hybrid Scorer:** A "Safety Gate" that ensures AI predictions never contradict core business logic.
- **Bootstrapping:** The process of using existing trade data to train an AI model before real users arrive.

### 2. Query Archetype Logic (Split for Slides)

To fit this into your presentation, we've split the logic into two slides:

#### Slide 1: Intent Classification (The Branching)
This phase identifies *what* the user wants (Buy, Sell, or Hybrid).

```mermaid
graph LR
    Start([User Query]) --> Logic{Execution Branch}

    subgraph "Phase 1: Archetype Detection"
        Logic --> Buyer[Buyer: Simple/Geo/Vol/Price]
        Logic --> Seller[Seller: Demand/Target Price]
        Logic --> Hybrid[Hybrid: Multi-Intent/Complex]
    end
```

#### Slide 2: The Execution Pipeline (The Ranking)
This phase takes the detected archetype and produces the final ranked results.

```mermaid
graph LR
    Input([Detected Archetype]) --> Processor[Recursive Constraint Resolver]
    Processor --> Retrieval{Semantic Retrieval}
    Retrieval --> Model[LTR Ranking]
    Retrieval --> Static[Heuristic Sorting]
    Model & Static --> Output([Final UI Render])
```

---

### 2. Learn to Rank (LTR) Lifecycle
This diagram shows the "Teacher-Student" relationship between our business heuristics and the AI model.

```mermaid
graph LR
    subgraph "Offline: Teaching the AI"
        DB[(Transaction DB)] --> DatasetBuilder[DatasetBuilder]
        DatasetBuilder --> Scenarios[Simulation Scenarios]
        Scenarios --> PseudoLabeler[Teacher: PseudoLabelGenerator]
        PseudoLabeler --> TrainSet[Labeled Training Data]
        TrainSet --> LightGBM[LightGBM Trainer]
        LightGBM --> ModelFile[[lgbm_ltr.txt]]
    end

    ModelFile -.-> modelLookup

    subgraph "Online: Real-time Thinking"
        Inbound[Candidate Supplier] --> Extractor[FeatureExtractor]
        Extractor --> Vector[Numeric Feature Vector]
        Vector --> modelLookup["Model Lookup (lgbm_ltr.txt)"]
        modelLookup --> Score[Relevance Score]
    end
```

---


## Phase 1: Natural Language Query Interpretation (NLP)
The goal was to move beyond keyword search and understand *user intent* and *constraints*.

**Tasks Completed:**
- **Intent Detection**: Built a parser to distinguish between "BUY" (Importing) and "SELL" (Exporting) intents.
- **Entity Extraction**: Implemented logic to extract **Products** (e.g., "Refined Sugar"), **Countries** (e.g., "Pakistan", "China"), and **Quantities** (e.g., "100MT").
- **Constraint Parsing**: Developed regex and heuristic handlers for **Price** ranges ("below $500/MT"), **Time** ranges ("Q1 2025", "Last 6 months"), and **Rank** requests ("Top 5").
- **Intent Splitting**: Added support for **Multi-intent** queries (e.g., "I want to buy Sugar and also check Rice buyers") using a sub-intent architecture.
- **Scope Logic**: Implemented **Pakistan vs. Worldwide** scoping to automatically filter origin/destination countries based on user context.

---

## Phase 2: Semantic Candidate Retrieval
The goal was to map vague human queries to specific database subcategories.

**Tasks Completed:**
- **Vector Search Integration**: Integrated **SBERT (Sentence-BERT)** to compute semantic embeddings of product names.
- **Subcategory Mapping**: Built a `QueryMatcher` to find the closest matching `ProductSubCategory` in the database, even if the spelling differs.
- **HS Code Alignment**: Linked the semantic search results to official HS Codes for trade data accuracy.
- **Variant Handling**: Implemented **ProductItem** logic to distinguish between specific product variants (e.g., "Dextrose Anhydrous" vs "Dextrose Monohydrate").

---

## Phase 3: High-Performance Data Aggregation
The goal was to turn 9,427+ raw transactions into meaningful supplier/buyer profiles.

**Tasks Completed:**
- **Direct SQL Aggregation**: Optimized Django ORM/SQL queries to aggregate transaction data on-the-fly.
- **Metric Calculation**: For every candidate supplier, we calculate:
    - **Total Volume (MT)**
    - **Shipment Frequency** (Number of shipments)
    - **Recency** (Days since last trade)
    - **Average Price** (USD/MT)
- **Buyer vs. Seller Logic**: Built separate aggregation paths to show *Suppliers* for buyers and *Buyers* for sellers.

---

## Phase 4: Learn to Rank (LTR) Model
The goal was to replace static sorting with machine-learned intelligence.

**Tasks Completed:**
- **Feature Engineering**: Defined 8 core mathematical features for the model, including `log_volume`, `inv_recency`, `volume_fit`, and `country_match`.
- **Pseudo-Labeling**: Created a `PseudoLabelGenerator` to simulate "expert" rankings (0-4 scores) so the model can learn even without historical user click data.
- **Dataset Builder**: Automated the creation of training datasets by matching existing queries against aggregated trade data.
- **LightGBM Training**: Implemented the training pipeline using **LambdaRank (LambdaMART)** to optimize for NDCG (Normalized Discounted Cumulative Gain).
- **Ranking Ensemble**: Built a hybrid ranker that combines **Model Predictions (30%)** with **Heuristic Baselines (70%)** for safety and stability.

---

## Phase 5: End-to-End Integration
The goal was to unify everything into a single, robust API.

**Tasks Completed:**
- **Unified API ViewSet**: Created `SearchViewSet` to handle all search types thru one endpoint (`/api/search/query/`).
- **Conflict Management**: Implemented "helpful error" messages for scope/country mismatches (e.g., searching "Worldwide" while scope is set to "Pakistan").
- **Supplier Deep-Dive**: Built the `supplier-detail` endpoint which provides transaction sparklines, port distributions, and market context (Bullish/Bearish).
- **Comparable Search**: Added a `ComparableFinder` to identify direct competitors/alternatives based on trade volume and product type.

---

## Current Status: **Fully Operational**
The engine now correctly interprets complex queries like *"Suggest top 5 sugar suppliers from Brazil below $600/MT"* and delivers a ranked, AI-verified list of candidates.
