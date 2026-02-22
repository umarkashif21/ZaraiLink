# Search Engine & Learn to Rank (LTR) Documentation

This document outlines the architecture and pipelines of the ZaraiLink search ecosystem.

## a) Search Engine Architecture (Horizontal Phases)

```mermaid
graph LR
    subgraph "NLU (Interpreter)"
        API[Search API] --> Parser[Tokenization]
        Parser --> Intent{Intent Classification}
    end

    subgraph "Retrieval Engine"
        API --> Dense[Dense: SBERT Matcher]
        API --> Sparse[Sparse: SQL Aggregator]
    end

    subgraph "Ranking Engine"
        Dense & Sparse --> Ranker[Ranking Ensemble]
        Ranker --> LTR[LTR: LambdaMART]
    end
    
    subgraph "Persistence"
        Sparse --> DB[("Postgres DB")]
        LTR --> ModelFile[[lgbm_ltr.txt]]
    end

    Ranker --> UI[JSON Response]
```

---

## b) Pipeline Sequence Execution

```mermaid
sequenceDiagram
    participant Q as Interpreter (NLU)
    participant R as Retrieval (Dense/Sparse)
    participant L as Ranking (LTR)
    
    Note over Q, L: Query Execution Lifecycle
    Q->>R: Structured Metadata + HS Codes
    R->>R: Parallel Vector Search & SQL Joins
    R->>L: Unranked Candidates
    L->>L: Feature Vectorization & LambdaMART Inference
    L-->>Q: Precision-Ranked JSON
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
