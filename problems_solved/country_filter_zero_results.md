# Fix: Country Filter Returning 0 Results

**Date**: 2026-02-13  
**Files Changed**: `backend/search/views.py`, `backend/search/services/query_parser.py`

## Problem
Searching with a country filter (e.g., "import from China") returned 0 results even though 825+ matching records existed in the database.

## Root Causes Found

**Bug 1 — Scope vs country_filter conflict** (`views.py`): When `scope=PAKISTAN` + `intent=BUY`, the aggregation filters `origin_country='Pakistan'`. Then the country_filter adds `origin_country__in=['China']` — impossible to match both, hence 0 results.

**Bug 2 — Dirty product text** (`query_parser.py`): Words like `"from"` and `"import"` weren't in the STOPWORDS list, so `"buy dextrose from China"` produced product=`"dextrose from"` instead of `"dextrose"`, degrading NLP matching.

## Changes Made

### views.py
Added scope+country conflict detection — returns a clear error message when the user searches with `scope=PAKISTAN` but specifies a non-Pakistan country filter.

```python
# Scope + Country conflict detection
active_scope = active_params.get('scope', 'WORLDWIDE')
if active_scope == 'PAKISTAN' and country_filter:
    non_pakistan_countries = [c for c in country_filter if c.lower() != 'pakistan']
    if non_pakistan_countries:
        return Response({
            "query": query,
            "parsed_query": parsed_query,
            "error": "scope_country_conflict",
            "message": f"You are searching within Pakistan scope but specified {', '.join(non_pakistan_countries)} as a country filter. Please switch your scope to Worldwide to search for international suppliers.",
            "results": [],
            "count": 0
        })
```

### query_parser.py
Added `"from"`, `"to"`, `"between"`, `"import"`, `"export"`, `"importing"`, `"exporting"` to STOPWORDS so they are cleaned from the product text after extraction.

```python
STOPWORDS = [
    " in ", " with ", " for ", " of ", " from ", " to ", " between ",
    "please", "search", "find", "show", "me", "list",
    "details", "price", "prices", "active", "recent", "data", "who", "is", "are",
    "import", "export", "importing", "exporting"
]
```

## Verification Results

| Test | Result |
|---|---|
| `"import from China"` → product cleaned | ✅ product=`""`, country=`['China']` |
| `"buy dextrose from China"` → product cleaned | ✅ product=`"dextrose"` |
| `scope=PAKISTAN` + `country=China` → conflict error | ✅ Returns `scope_country_conflict` |
| `scope=WORLDWIDE` + `country=China` → results | ✅ Returns matched suppliers |
| `scope=PAKISTAN` + no country → normal results | ✅ Works as before |
