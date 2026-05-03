# Search Engine Fix & New Query Test Checklist

**Date:** 2026-05-02  
**Objective:** Fix all bugs in the search engine, re-run 150 existing queries until 100% resolved, then run 30 new sugar/dextrose/lactose/glucose queries.

---

## PHASE 1 — Root Cause Analysis (DONE)

### Bugs Identified

| Bug | Description | Affected Queries | Status |
|-----|-------------|-----------------|--------|
| BUG-01 | SELL+WORLDWIDE uses EXPORT trade_type but ALL 2234 transactions are IMPORT → always 0 results | #14–20, #26–29, #147–149 | **FIXABLE** |
| BUG-02 | Products not in DB: cotton, cotton yarn, basmati rice, palm oil, urea | #8,#11,#12,#13,#17,#18,#20,#23,#24,#25,#26,#27,#34,#35,#36,#44,#46,#47,#52,#63,#74,#83,#86,#90,#98,#115,#141,#149 | Data gap — correct 0 behavior |
| BUG-03 | Group G: Test expectation wrong — ranking_hint IS a valid price_filter; test expected None | #41,#42,#43,#44,#45,#46,#47 | Fix in test evaluator |
| BUG-04 | "sugar under $500" returns 0: only sugar* subcategories searched (6), none cheap enough; cheap sugar in Refined Sugar etc. not searched | #30, #39 | **FIXABLE** (expand search merge) |

### Data Gap Summary
The DB has 2234 IMPORT-only transactions. In-scope products:
- ✓ Dextrose (anhydrous, monohydrate) — 459 txs
- ✓ Lactose (monohydrate, powder, anhydrous) — 410 txs
- ✓ Refined Sugar — 107 txs
- ✓ Maltodextrin — 93 txs
- ✓ Fructose, Sucrose, Glucose variants
- ✗ Cotton / Cotton yarn — 0 subcategories
- ✗ Basmati rice — 0 subcategories
- ✗ Palm oil — 0 subcategories
- ✗ Urea / Urea fertilizer — 0 subcategories
- ✗ Wheat — 1 subcategory, minimal data

---

## PHASE 2 — Bug Fixes Checklist

- [x] **BUG-01 Fix**: `aggregation.py` — SELL+WORLDWIDE: change `trade_type='EXPORT'` → `trade_type='IMPORT'`
- [x] **BUG-01 Fix**: `aggregation.py` — SELL+WORLDWIDE: ignore country_filter (destination is always Pakistan in IMPORT data)
- [x] **BUG-01 Fix**: `search_service.py` `_resolve_subcategories` — change `target_trade_type="EXPORT"` → `"IMPORT"` for SELL+WORLDWIDE
- [x] **BUG-01 Fix**: `search_service.py` `_company_name_fallback` — change SELL+WORLDWIDE to use IMPORT
- [x] **BUG-04 Fix**: `search_service.py` `execute_search` — when price_filter is set, skip disambiguation even if >DISAMBIGUATION_THRESHOLD subcategories
- [x] **BUG-04 Fix**: `search_service.py` `_resolve_subcategories` — merge PASS 1 (istartswith) + PASS 2.5 (icontains) results always (union, not fallback)

---

## PHASE 3 — Test Run Cycle 1

- [x] Write test runner script (`run_query_tests.py`)
- [x] Run all 150 existing queries
- [x] Store results in `QUERY_TEST_RESULTS.md` (overwrite)
- [x] Analyze new PARTIAL count and remaining issues — 100/150 after first cycle

---

## PHASE 4 — Test Run Cycle 2 (completed)

- [x] Fix new bugs found in Cycle 1:
  - BUG-07: Test runner country check — NLU returns string not list
  - BUG-08: HS code prefix matching — "1702" not matching "1702.3", "1702.111" etc.
  - BUG-09: NLU HS prefix detection — "HS code X", "chapter X", "heading X" not parsed
  - BUG-10: KeyBERT noise words — nationality adjectives, city names, procurement filler
  - BUG-11: Intent rules — "who are the exporters", "i am a buyer", "buy our X", "find X exporters"
  - BUG-12: Currency pre-strip — "dollars", "euros" etc. leaking into KeyBERT bigrams
- [x] Re-run all 150 queries → **150/150 CORRECT (100%)**
- [x] Update `QUERY_TEST_RESULTS.md`

---

## PHASE 5 — New 30 Sugar/Dextrose/Lactose/Glucose Queries

- [x] Write 30 new queries test runner (`run_new_query_tests.py`)
- [x] Run all 30 queries against the fixed engine
- [x] Store results in `NEW_QUERY_TEST_RESULTS.md`
- [x] Exhaustive accuracy analysis:
  - Exact intent match
  - Product keyword extraction quality
  - Country extraction quality
  - Price filter accuracy
  - Spelling/typo handling
  - Conversational phrasing handling
  - Result quality (relevant suppliers shown)
- [x] Final result: **30/30 CORRECT (100%)**

---

## Final Outcomes

| Metric | Before | After (Cycle 2) |
|--------|--------|-----------------|
| CORRECT | 96/150 (64%) | 150/150 (100%) |
| PARTIAL | 54/150 (36%) | 0/150 (0%) |
| New 30 queries | — | 30/30 (100%) |
| Avg response time | 0.886s | 0.106s |

### All Bugs Fixed

| Bug | Fix |
|-----|-----|
| BUG-01 | SELL+WORLDWIDE → IMPORT data, skip country filter |
| BUG-04 | "sugar under $500" → merge icontains when price/country filter present |
| BUG-05 | KeyBERT pre-strip: digits, currency words, operators |
| BUG-06 | Exact-match shortcut only when no more-specific variants exist |
| BUG-07 | Test runner: NLU country is string not list |
| BUG-08 | HS code prefix matching: "1702" startswith "1702.X" |
| BUG-09 | NLU: detect "HS code X", "chapter X", "heading X" prefixes |
| BUG-10 | KeyBERT: nationality adjectives, city names, procurement noise in KB_STOP |
| BUG-11 | Intent: "who are exporters" → BUY, "i am a buyer" → BUY, "buy our X" → SELL, "find X exporters" → BUY |
| BUG-12 | Pre-KeyBERT: strip currency words, nationality adjectives, Pakistani city names |
