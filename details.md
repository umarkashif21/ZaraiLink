# Search Engine & Learn to Rank (LTR) Documentation

This document outlines the architecture and pipelines of the ZaraiLink search ecosystem.

## a) Search Engine Architecture

The ZaraiLink search engine follows a decoupled, service-oriented architecture designed for scalability and precision.

```mermaid
graph LR
    UI["Frontend (React SearchHome.js)"] --> API["Django SearchViewSet"]
    
    subgraph "Service Layer"
        API --> Parser["QueryInterpreter (NLP Parser)"]
        API --> Retrieval["QueryMatcher (SBERT Retrieval)"]
        API --> Aggregator["SupplierAggregator (Metric Aggregation)"]
        API --> Ranker["RankingEnsemble (LTR + Heuristics)"]
    end
    
    subgraph "Processing Logic"
        Parser --> Intent["Intent/Scope/Filter Extraction"]
        Retrieval --> VectorMatch["Subcategory & Item Mapping"]
        Aggregator --> DBQuery["PostgreSQL (Trade Data Transactions)"]
        Ranker --> LTR["LightGBM Ranker"]
    end
    
    subgraph "Data Layer"
        DBQuery --> PGDB[("PostgreSQL")]
        LTR --> ModelFile["lgbm_ltr.txt (Model Binary)"]
    end

    Response["JSON Response"] --> UI
    Ranker --> Response
```

---

## b) Search Engine Pipeline

The pipeline processes a natural language query through several stages to produce ranked results.

```mermaid
sequenceDiagram
    participant U as User
    participant Q as QueryInterpreter
    participant N as QueryMatcher
    participant A as SupplierAggregator
    participant R as RankingEnsemble
    
    U->>Q: "Import dextrose from China"
    Q-->>U: Intent: BUY, Product: Dextrose, Country: [China]
    U->>N: Search: "Dextrose"
    N-->>U: Subcategory IDs: [716, 12221]
    U->>A: Aggregate IDs for [716, 12221] + Country: China
    A-->>U: Candidate Candidates (Metric JSONs)
    U->>R: Rank Candidates + Query Context
    R->>R: Feature Extraction -> LTR Inference -> Weighted Ensemble
    R-->>U: Sorted Results (Ranked by Score)
```

---

## c) Learn to Rank (LTR) Architecture

The LTR component uses a Gradient Boosted Decision Tree (LightGBM) optimized for ranking.

```mermaid
graph LR
    subgraph "Input Features (X)"
        F1["Log Volume"]
        F2["Log Price"]
        F3["Shipment Frequency"]
        F4["Inverse Recency"]
        F5["Volume Fit Score"]
        F6["Scope Match (0/1)"]
        F7["Country Match (0/1)"]
        F8["Price Fit (0/1)"]
    end

    F1 & F2 & F3 & F4 & F5 & F6 & F7 & F8 --> Model["LightGBM LambdaMART"]
    
    Model --> LTRScore["LTR Raw Score"]
    
    Heuristic["Heuristic Baseline Score"] --> Ensemble{Weighting}
    LTRScore --> Ensemble
    
    Ensemble --> Final["Final Ranking Score"]
    
    style Ensemble fill:#f9f,stroke:#333,stroke-width:2px
```

---

## d) LTR Data Pipeline

The data pipeline manages the lifecycle from raw signals to model deployment.

```mermaid
flowchart TD
    Raw[("Raw Transaction Data")] --> Agg["Supplier/Buyer Aggregation"]
    Agg --> Samples["Dataset Samples (Supplier-Product Pairs)"]
    
    Heuristics["Heuristic Score (Volume/Recency/Price)"] --> Labeler["Pseudo-Label Generator"]
    Samples --> Labeler
    
    Labeler --> Labeled["Training Data (X, y_labels)"]
    
    Labeled --> Train["LTRTrainer (Group-Aware Split)"]
    Train --> Eval["LTR Evaluation (NDCG@5)"]
    
    Eval --> Save["Save Model (lgbm_ltr.txt)"]
    Save --> Infer["Online Inference (Ensemble)"]
```
