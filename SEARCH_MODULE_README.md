# Unified Search Module - Developer Guide

## 1. What Was Implemented

We created a new Django app `search` to handle natural language queries.

### Files Created:
*   `backend/search/` app structure.
*   `backend/search/services/nlp.py`: usage of `sentence-transformers` for semantic search.
*   `backend/search/services/aggregation.py`: Aggregates supplier stats from transactions.
*   `backend/search/services/ranking.py`: Rule-based ranking logic (Volume/Frequency/Recency).
*   `backend/search/management/commands/build_search_index.py`: Script to generate vector embeddings.
*   `backend/search/views.py`: API endpoints for query processing.

### Configuration Changes:
*   Registered `search` app in `settings.py`.
*   Added `search` URLs to `zarailink/urls.py`.
*   Installed ML libraries (`sentence-transformers`, `scikit-learn`, `torch`).

## 2. Installation

The search module requires ML libraries for generating text embeddings.

```bash
pip install -r requirements.txt
# This installs: sentence-transformers, scikit-learn, torch
```

## 2. Setup (One-Time)

Before the search can work intelligently, you must build the semantic index. This generates vector embeddings for all `ProductSubCategory` entries in your database.

```bash
python manage.py build_search_index
```
*   **Output**: Creates `backend/search_index.pkl` (~5-10MB).
*   **When to run**: Run this whenever you add new `ProductSubCategory` entries.

## 3. How It Works

### Hybrid Search Logic
When a user searches for "I want to buy dextrose":

1.  **Keyword Match (High Precision)**:
    *   The system strips stop words ("I want to buy") -> "dextrose".
    *   It looks for exact substring matches in the database.
    *   Matches: "Dextrose", "Dextrose Monohydrate", "Dextrose Anhydrous".
    *   **Score**: 1.0 (Highest priority).

2.  **Semantic Match (High Recall)**:
    *   The system converts "dextrose" into a 384-dimensional vector.
    *   It finds subcategories with similar meaning (even if they don't share words).
    *   Example: "Glucose", "Sugar substitute".
    *   **Score**: cosine similarity (0.0 - 1.0).

3.  **Result**:
    *   Results are combined and ranked by score.
    *   This ensures "Dextrose Monohydrate" appears at the top for "dextrose", while relevant synonyms appear below.

## 4. API Usage

### Endpoint
`GET /api/search/query/?q=YOUR_QUERY`

### Example
`GET http://localhost:8000/api/search/query/?q=Who sells fructose`

### Response Structure
```json
{
    "query": "Who sells fructose",
    "matched_subcategories": [
        {
            "id": 12,
            "name": "Fructose Crystalline",
            "score": 1.0,
            "method": "keyword"
        },
        {
            "id": 45,
            "name": "Fruit Sugar",
            "score": 0.85,
            "method": "semantic"
        }
    ],
    "results": [
        {
            "name": "Global Sweeteners Ltd",
            "country": "China",
            "total_volume": 5000.0,
            "shipment_count": 12,
            "score": 0.95
        }
        ...
    ]
}
```

## 5. Testing & Verification

1.  **Run the server**: `python manage.py runserver`
2.  **Build the index**: `python manage.py build_search_index` (if not done)
3.  **Test Queries**:
    *   **Exact**: "I want to buy dextrose" -> Should list "Dextrose", "Dextrose Monohydrate".
    *   **Synonym**: "Sweetener for drinks" -> Should list "Fructose", "Sucrose" (via semantic search).
    *   **Vague**: "dextrose" -> Should list all dextrose variants.
