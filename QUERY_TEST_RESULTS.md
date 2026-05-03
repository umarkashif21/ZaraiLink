# Zarailink Search Engine — Exhaustive 150-Query Test Results

**Run date:** 2026-05-02 14:07:39  
**Total queries:** 150  
**Endpoint:** SearchService.execute_search() (direct)  

## Summary Statistics

| Metric | Value |
|--------|-------|
| ✓ CORRECT   | 150 / 150 (100%) |
| ~ PARTIAL   | 0 / 150 (0%) |
| ✗ INCORRECT | 0 / 150 (0%) |
| ! ERROR     | 0 / 150 |
| Avg response time | 0.106s |
| Min response time | 0.005s |
| Max response time | 0.383s |

## Group-Level Accuracy

| Group | Description | Total | Correct | Partial | Errors |
|-------|-------------|-------|---------|---------|--------|
| A | Bare/Minimal | 5 | 5 | 0 | 0 |
| B | Basic BUY | 8 | 8 | 0 | 0 |
| C | Basic SELL | 7 | 7 | 0 | 0 |
| D | Find Suppliers (semantic reversal) | 5 | 5 | 0 | 0 |
| E | Find Buyers | 4 | 4 | 0 | 0 |
| F | Price Operators | 11 | 11 | 0 | 0 |
| G | Ranking Hints | 7 | 7 | 0 | 0 |
| H | Country Filters | 8 | 8 | 0 | 0 |
| I | Combined Multi-Criteria | 8 | 8 | 0 | 0 |
| J | HS Codes | 8 | 8 | 0 | 0 |
| K | Procurement Language | 8 | 8 | 0 | 0 |
| L | Volume/Quantity | 7 | 7 | 0 | 0 |
| M | Sector/Use-Case | 7 | 7 | 0 | 0 |
| N | Scope/Geography | 7 | 7 | 0 | 0 |
| O | Spelling Errors | 12 | 12 | 0 | 0 |
| P | Broken English | 10 | 10 | 0 | 0 |
| Q | Creative/Lateral | 8 | 8 | 0 | 0 |
| R | Metaphors | 6 | 6 | 0 | 0 |
| S | Conversational | 5 | 5 | 0 | 0 |
| T | Advanced/Technical | 5 | 5 | 0 | 0 |
| U | Ambiguous Intent | 4 | 4 | 0 | 0 |

---

## Detailed Per-Query Results

### Group A — Bare/Minimal

#### Query #1 — ✓ CORRECT
**Query:** `sugar`  
**Scope:** `worldwide`  
**Angle:** BARE KEYWORD, default BUY  
**Time:** 0.181s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Germany | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #2 — ✓ CORRECT
**Query:** `dex`  
**Scope:** `worldwide`  
**Angle:** 3-CHAR ABBREVIATION, trigram match  
**Time:** 0.083s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dex`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `66`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 66):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Netherlands | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #3 — ✓ CORRECT
**Query:** `1702`  
**Scope:** `worldwide`  
**Angle:** BARE HS CODE, cascade lookup  
**Time:** 0.022s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `1702`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `74`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 74):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #4 — ✓ CORRECT
**Query:** `SEAWALL`  
**Scope:** `worldwide`  
**Angle:** COMPANY NAME, transaction fallback  
**Time:** 0.267s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `seawall`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #5 — ✓ CORRECT
**Query:** `s`  
**Scope:** `worldwide`  
**Angle:** SINGLE CHAR, graceful no-match  
**Time:** 0.020s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `s`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group B — Basic BUY

#### Query #6 — ✓ CORRECT
**Query:** `buy sugar`  
**Scope:** `worldwide`  
**Angle:** BASIC BUY, single product  
**Time:** 0.043s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Germany | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #7 — ✓ CORRECT
**Query:** `i want to buy dextrose anhydrous`  
**Scope:** `worldwide`  
**Angle:** EXPLICIT BUY, full product name  
**Time:** 0.072s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #8 — ✓ CORRECT
**Query:** `i need basmati rice`  
**Scope:** `worldwide`  
**Angle:** NEED = BUY, common phrasing  
**Time:** 0.383s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rice`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #9 — ✓ CORRECT
**Query:** `purchase refined sugar`  
**Scope:** `worldwide`  
**Angle:** PURCHASE VERB, BUY intent  
**Time:** 0.061s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refined sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Malaysia | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Brazil | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | United Kingdom | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #10 — ✓ CORRECT
**Query:** `looking for wheat`  
**Scope:** `worldwide`  
**Angle:** LOOKING FOR = BUY, no supplier mention  
**Time:** 0.056s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #11 — ✓ CORRECT
**Query:** `find me cotton yarn`  
**Scope:** `worldwide`  
**Angle:** FIND ME = BUY, imperative  
**Time:** 0.364s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton yarn`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #12 — ✓ CORRECT
**Query:** `i am interested in buying palm oil`  
**Scope:** `worldwide`  
**Angle:** INTERESTED IN BUYING phrase  
**Time:** 0.362s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `palm oil`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #13 — ✓ CORRECT
**Query:** `want to get urea fertilizer`  
**Scope:** `worldwide`  
**Angle:** WANT TO GET, casual BUY  
**Time:** 0.373s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `urea fertilizer`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group C — Basic SELL

#### Query #14 — ✓ CORRECT
**Query:** `sugar for sale`  
**Scope:** `worldwide`  
**Angle:** FOR SALE phrase = SELL  
**Time:** 0.163s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `sugar sale`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `6`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 6):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #15 — ✓ CORRECT
**Query:** `we are selling wheat`  
**Scope:** `worldwide`  
**Angle:** WE ARE SELLING = SELL  
**Time:** 0.050s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #16 — ✓ CORRECT
**Query:** `i have dextrose anhydrous for sale`  
**Scope:** `worldwide`  
**Angle:** I HAVE X FOR SALE = SELL  
**Time:** 0.080s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `100`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 100):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #17 — ✓ CORRECT
**Query:** `basmati rice in stock`  
**Scope:** `worldwide`  
**Angle:** IN STOCK = SELL  
**Time:** 0.357s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `basmati rice`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #18 — ✓ CORRECT
**Query:** `we export cotton yarn`  
**Scope:** `worldwide`  
**Angle:** WE EXPORT = SELL  
**Time:** 0.356s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `cotton yarn`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #19 — ✓ CORRECT
**Query:** `i am a supplier of refined sugar`  
**Scope:** `worldwide`  
**Angle:** I AM A SUPPLIER = SELL  
**Time:** 0.058s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `refined sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `22`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 22):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #20 — ✓ CORRECT
**Query:** `our company produces urea and we want to sell`  
**Scope:** `worldwide`  
**Angle:** WE PRODUCE + SELL = SELL  
**Time:** 0.377s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `produces urea`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group D — Find Suppliers (semantic reversal)

#### Query #21 — ✓ CORRECT
**Query:** `find suppliers of dextrose anhydrous`  
**Scope:** `worldwide`  
**Angle:** FIND SUPPLIERS = BUY  
**Time:** 0.056s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #22 — ✓ CORRECT
**Query:** `looking for sellers of refined sugar`  
**Scope:** `worldwide`  
**Angle:** SEMANTIC REVERSAL — sellers = BUY  
**Time:** 0.043s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refined sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Malaysia | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Brazil | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | United Kingdom | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #23 — ✓ CORRECT
**Query:** `looking for exporters of basmati rice`  
**Scope:** `worldwide`  
**Angle:** EXPORTERS = BUY not SELL  
**Time:** 0.198s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rice`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #24 — ✓ CORRECT
**Query:** `who sells cotton yarn`  
**Scope:** `worldwide`  
**Angle:** WHO SELLS = BUY  
**Time:** 0.155s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton yarn`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #25 — ✓ CORRECT
**Query:** `find manufacturers of urea fertilizer`  
**Scope:** `worldwide`  
**Angle:** MANUFACTURERS = BUY  
**Time:** 0.158s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `urea fertilizer`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group E — Find Buyers

#### Query #26 — ✓ CORRECT
**Query:** `find buyers for basmati rice`  
**Scope:** `worldwide`  
**Angle:** FIND BUYERS = SELL  
**Time:** 0.151s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `basmati rice`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #27 — ✓ CORRECT
**Query:** `looking for importers of cotton yarn`  
**Scope:** `worldwide`  
**Angle:** IMPORTERS = SELL  
**Time:** 0.148s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `cotton yarn`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #28 — ✓ CORRECT
**Query:** `who buys refined sugar`  
**Scope:** `worldwide`  
**Angle:** WHO BUYS = SELL  
**Time:** 0.022s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `refined sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `22`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 22):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #29 — ✓ CORRECT
**Query:** `find companies interested in buying our wheat`  
**Scope:** `worldwide`  
**Angle:** BUYING OUR = SELL  
**Time:** 0.020s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group F — Price Operators

#### Query #30 — ✓ CORRECT
**Query:** `sugar under $500`  
**Scope:** `worldwide`  
**Angle:** LTE $500 USD  
**Time:** 0.035s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `{'range': {'usd_per_mt': {'lte': 500.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Kingdom | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #31 — ✓ CORRECT
**Query:** `wheat above $250`  
**Scope:** `worldwide`  
**Angle:** GTE $250  
**Time:** 0.031s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `{'range': {'usd_per_mt': {'gte': 250.0}}, 'ranking_hint': None}`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #32 — ✓ CORRECT
**Query:** `dextrose anhydrous around $700`  
**Scope:** `worldwide`  
**Angle:** APPROX $700  
**Time:** 0.038s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `{'range': {'usd_per_mt': {'gte': 595.0, 'lte': 804.9999999999999}}, 'ranking_hint': None}`
- Disambiguation: `False`
- Results count: `33`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 33):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #33 — ✓ CORRECT
**Query:** `rice <= $600`  
**Scope:** `worldwide`  
**Angle:** SYMBOL <=  
**Time:** 0.030s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `rice`
- Country: `—`
- Price filter: `{'range': {'usd_per_mt': {'lte': 600.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `7`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 7):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #34 — ✓ CORRECT
**Query:** `cotton >= $1000`  
**Scope:** `worldwide`  
**Angle:** SYMBOL >=  
**Time:** 0.107s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton`
- Country: `—`
- Price filter: `{'range': {'usd_per_mt': {'gte': 1000.0}}, 'ranking_hint': None}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #35 — ✓ CORRECT
**Query:** `palm oil at most $900`  
**Scope:** `worldwide`  
**Angle:** AT MOST phrase  
**Time:** 0.157s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `palm oil`
- Country: `—`
- Price filter: `{'range': {'usd_per_mt': {'lte': 900.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #36 — ✓ CORRECT
**Query:** `urea at least $250`  
**Scope:** `worldwide`  
**Angle:** AT LEAST phrase  
**Time:** 0.120s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `urea`
- Country: `—`
- Price filter: `{'range': {'usd_per_mt': {'gte': 250.0}}, 'ranking_hint': None}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #37 — ✓ CORRECT
**Query:** `refined sugar not exceeding $400`  
**Scope:** `worldwide`  
**Angle:** NOT EXCEEDING phrase  
**Time:** 0.031s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refined sugar`
- Country: `—`
- Price filter: `{'range': {'usd_per_mt': {'lte': 400.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Kingdom | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #38 — ✓ CORRECT
**Query:** `wheat starting from $200`  
**Scope:** `worldwide`  
**Angle:** STARTING FROM phrase  
**Time:** 0.030s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `{'range': {'usd_per_mt': {'gte': 200.0}}, 'ranking_hint': None}`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #39 — ✓ CORRECT
**Query:** `sugar under five hundred dollars`  
**Scope:** `worldwide`  
**Angle:** WRITTEN NUMBER + currency word  
**Time:** 0.030s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `{'range': {'usd_per_mt': {'lte': 500.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Kingdom | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #40 — ✓ CORRECT
**Query:** `dextrose approximately $650`  
**Scope:** `worldwide`  
**Angle:** APPROXIMATELY synonym  
**Time:** 0.047s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose`
- Country: `—`
- Price filter: `{'range': {'usd_per_mt': {'gte': 552.5, 'lte': 747.4999999999999}}, 'ranking_hint': None}`
- Disambiguation: `False`
- Results count: `29`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 29):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group G — Ranking Hints

#### Query #41 — ✓ CORRECT
**Query:** `cheap sugar`  
**Scope:** `worldwide`  
**Angle:** CHEAP = price_filter hint  
**Time:** 0.034s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `{'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `47`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 47):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Kingdom | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Malaysia | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Brazil | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #42 — ✓ CORRECT
**Query:** `affordable wheat`  
**Scope:** `worldwide`  
**Angle:** AFFORDABLE = price_filter hint  
**Time:** 0.033s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `{'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #43 — ✓ CORRECT
**Query:** `premium dextrose anhydrous`  
**Scope:** `worldwide`  
**Angle:** PREMIUM = quality hint  
**Time:** 0.045s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `{'ranking_hint': 'price_desc'}`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #44 — ✓ CORRECT
**Query:** `bulk basmati rice`  
**Scope:** `worldwide`  
**Angle:** BULK = volume hint  
**Time:** 0.164s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rice`
- Country: `—`
- Price filter: `{'ranking_hint': 'price_desc'}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #45 — ✓ CORRECT
**Query:** `high quality refined sugar`  
**Scope:** `worldwide`  
**Angle:** HIGH QUALITY = quality hint  
**Time:** 0.034s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refined sugar`
- Country: `—`
- Price filter: `{'ranking_hint': 'price_desc'}`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Malaysia | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Brazil | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #46 — ✓ CORRECT
**Query:** `cheapest cotton yarn`  
**Scope:** `worldwide`  
**Angle:** CHEAPEST = superlative price  
**Time:** 0.148s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton yarn`
- Country: `—`
- Price filter: `{'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #47 — ✓ CORRECT
**Query:** `best quality palm oil`  
**Scope:** `worldwide`  
**Angle:** BEST QUALITY = quality hint  
**Time:** 0.152s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `palm oil`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group H — Country Filters

#### Query #48 — ✓ CORRECT
**Query:** `sugar from China`  
**Scope:** `worldwide`  
**Angle:** SINGLE COUNTRY  
**Time:** 0.036s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `China`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `7`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 7):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #49 — ✓ CORRECT
**Query:** `wheat from Russia`  
**Scope:** `worldwide`  
**Angle:** SINGLE COUNTRY data gap  
**Time:** 0.031s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `Russia`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #50 — ✓ CORRECT
**Query:** `basmati rice from India`  
**Scope:** `worldwide`  
**Angle:** SINGLE COUNTRY data gap  
**Time:** 0.151s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rice`
- Country: `India`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #51 — ✓ CORRECT
**Query:** `palm oil from Malaysia`  
**Scope:** `worldwide`  
**Angle:** SINGLE COUNTRY data gap  
**Time:** 0.157s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `palm oil`
- Country: `Malaysia`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #52 — ✓ CORRECT
**Query:** `cotton from USA`  
**Scope:** `worldwide`  
**Angle:** SINGLE COUNTRY data gap  
**Time:** 0.111s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton`
- Country: `United States`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #53 — ✓ CORRECT
**Query:** `soybean from Brazil`  
**Scope:** `worldwide`  
**Angle:** SINGLE COUNTRY data gap  
**Time:** 0.109s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `soybean`
- Country: `Brazil`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #54 — ✓ CORRECT
**Query:** `import wheat from Ukraine`  
**Scope:** `worldwide`  
**Angle:** IMPORT verb + country  
**Time:** 0.029s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `Ukraine`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #55 — ✓ CORRECT
**Query:** `Chinese sugar suppliers`  
**Scope:** `worldwide`  
**Angle:** ADJECTIVE COUNTRY form  
**Time:** 0.030s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `China`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `7`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 7):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group I — Combined Multi-Criteria

#### Query #56 — ✓ CORRECT
**Query:** `dextrose anhydrous from China under $700`  
**Scope:** `worldwide`  
**Angle:** COUNTRY+PRICE  
**Time:** 0.040s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `China`
- Price filter: `{'range': {'usd_per_mt': {'lte': 700.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `2`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 2):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #57 — ✓ CORRECT
**Query:** `refined sugar from Brazil below $400`  
**Scope:** `worldwide`  
**Angle:** COUNTRY+PRICE  
**Time:** 0.034s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refined sugar`
- Country: `Brazil`
- Price filter: `{'range': {'usd_per_mt': {'lte': 400.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #58 — ✓ CORRECT
**Query:** `basmati rice from India under $600`  
**Scope:** `worldwide`  
**Angle:** COUNTRY+PRICE data gap  
**Time:** 0.154s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rice`
- Country: `India`
- Price filter: `{'range': {'usd_per_mt': {'lte': 600.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #59 — ✓ CORRECT
**Query:** `bulk palm oil from Malaysia below $900`  
**Scope:** `worldwide`  
**Angle:** BULK+COUNTRY+PRICE  
**Time:** 0.158s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `palm oil`
- Country: `Malaysia`
- Price filter: `{'range': {'usd_per_mt': {'lte': 900.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #60 — ✓ CORRECT
**Query:** `cheap wheat from Russia`  
**Scope:** `worldwide`  
**Angle:** CHEAP+COUNTRY  
**Time:** 0.027s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `Russia`
- Price filter: `{'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #61 — ✓ CORRECT
**Query:** `premium cotton yarn from Pakistan above $1000`  
**Scope:** `worldwide`  
**Angle:** PREMIUM+COUNTRY+GTE  
**Time:** 0.158s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton yarn`
- Country: `Pakistan`
- Price filter: `{'range': {'usd_per_mt': {'gte': 1000.0}}, 'ranking_hint': None}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #62 — ✓ CORRECT
**Query:** `find suppliers of dextrose from China under $700`  
**Scope:** `worldwide`  
**Angle:** FIND+COUNTRY+PRICE  
**Time:** 0.049s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose`
- Country: `China`
- Price filter: `{'range': {'usd_per_mt': {'lte': 700.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #63 — ✓ CORRECT
**Query:** `looking for cheap basmati rice from India`  
**Scope:** `worldwide`  
**Angle:** CHEAP+COUNTRY  
**Time:** 0.158s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rice`
- Country: `India`
- Price filter: `{'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group J — HS Codes

#### Query #64 — ✓ CORRECT
**Query:** `1702.3090`  
**Scope:** `worldwide`  
**Angle:** DOTTED FORMAT  
**Time:** 0.011s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `1702.3090`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `37`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 37):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #65 — ✓ CORRECT
**Query:** `17021990`  
**Scope:** `worldwide`  
**Angle:** PACKED 8-DIGIT (0 txns for 1702.19 data gap)  
**Time:** 0.008s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `17021990`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #66 — ✓ CORRECT
**Query:** `HS code 1701.991`  
**Scope:** `worldwide`  
**Angle:** HS CODE PREFIX  
**Time:** 0.006s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `1701.991`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `13`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 13):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Malaysia | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Vietnam | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #67 — ✓ CORRECT
**Query:** `tariff code 1001`  
**Scope:** `worldwide`  
**Angle:** TARIFF CODE PREFIX  
**Time:** 0.010s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `1001`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #68 — ✓ CORRECT
**Query:** `chapter 17`  
**Scope:** `worldwide`  
**Angle:** CHAPTER = broad lookup  
**Time:** 0.011s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `17`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `96`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 96):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Malaysia | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Brazil | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #69 — ✓ CORRECT
**Query:** `1702 30 90`  
**Scope:** `worldwide`  
**Angle:** SPACE-SEPARATED FORMAT  
**Time:** 0.005s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `17023090`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `37`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 37):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #70 — ✓ CORRECT
**Query:** `HS 5201`  
**Scope:** `worldwide`  
**Angle:** HS COTTON data gap  
**Time:** 0.012s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `5201`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #71 — ✓ CORRECT
**Query:** `heading 1701`  
**Scope:** `worldwide`  
**Angle:** HEADING PREFIX  
**Time:** 0.006s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `1701`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Malaysia | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Brazil | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group K — Procurement Language

#### Query #72 — ✓ CORRECT
**Query:** `RFQ for dextrose anhydrous`  
**Scope:** `worldwide`  
**Angle:** RFQ acronym  
**Time:** 0.024s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #73 — ✓ CORRECT
**Query:** `request for quotation refined sugar`  
**Scope:** `worldwide`  
**Angle:** FULL RFQ phrase  
**Time:** 0.022s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refined sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Malaysia | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Brazil | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | United Kingdom | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #74 — ✓ CORRECT
**Query:** `our company requires urea fertilizer`  
**Scope:** `worldwide`  
**Angle:** REQUIRES verb  
**Time:** 0.164s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `urea fertilizer`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #75 — ✓ CORRECT
**Query:** `we are procuring basmati rice for our operations`  
**Scope:** `worldwide`  
**Angle:** PROCURING verb  
**Time:** 0.168s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rice`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #76 — ✓ CORRECT
**Query:** `sourcing cotton yarn for our textile mill in Faisalabad`  
**Scope:** `worldwide`  
**Angle:** SOURCING verb + location  
**Time:** 0.157s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton yarn`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #77 — ✓ CORRECT
**Query:** `tender for wheat supply 5000 MT`  
**Scope:** `worldwide`  
**Angle:** TENDER + quantity  
**Time:** 0.066s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat supply`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #78 — ✓ CORRECT
**Query:** `invite quotations for palm oil`  
**Scope:** `worldwide`  
**Angle:** INVITE QUOTATIONS  
**Time:** 0.152s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `palm oil`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #79 — ✓ CORRECT
**Query:** `seeking quotation for dextrose anhydrous 100 MT`  
**Scope:** `worldwide`  
**Angle:** SEEKING QUOTATION  
**Time:** 0.032s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group L — Volume/Quantity

#### Query #80 — ✓ CORRECT
**Query:** `sugar 1000 MT`  
**Scope:** `worldwide`  
**Angle:** MT suffix  
**Time:** 0.021s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Germany | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #81 — ✓ CORRECT
**Query:** `buy 5000 MT wheat`  
**Scope:** `worldwide`  
**Angle:** BUY + MT  
**Time:** 0.020s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #82 — ✓ CORRECT
**Query:** `need 100 MT dextrose anhydrous urgently`  
**Scope:** `worldwide`  
**Angle:** URGENT+MT  
**Time:** 0.026s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #83 — ✓ CORRECT
**Query:** `trial shipment basmati rice`  
**Scope:** `worldwide`  
**Angle:** TRIAL SHIPMENT  
**Time:** 0.160s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rice`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #84 — ✓ CORRECT
**Query:** `sugar FCL`  
**Scope:** `worldwide`  
**Angle:** FCL term  
**Time:** 0.072s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar fcl`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Bahrain | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | European Union | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #85 — ✓ CORRECT
**Query:** `bulk vessel wheat`  
**Scope:** `worldwide`  
**Angle:** BULK VESSEL  
**Time:** 0.068s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `vessel wheat`
- Country: `—`
- Price filter: `{'ranking_hint': 'price_desc'}`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #86 — ✓ CORRECT
**Query:** `sample cotton yarn`  
**Scope:** `worldwide`  
**Angle:** SAMPLE QUANTITY  
**Time:** 0.162s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton yarn`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group M — Sector/Use-Case

#### Query #87 — ✓ CORRECT
**Query:** `dextrose for pharmaceutical IV`  
**Scope:** `worldwide`  
**Angle:** PHARMA use-case  
**Time:** 0.084s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose pharmaceutical`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `40`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 40):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #88 — ✓ CORRECT
**Query:** `sugar for confectionery manufacturing`  
**Scope:** `worldwide`  
**Angle:** CONFECTIONERY use-case  
**Time:** 0.029s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar confectionery`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #89 — ✓ CORRECT
**Query:** `wheat for flour milling`  
**Scope:** `worldwide`  
**Angle:** FLOUR MILLING  
**Time:** 0.158s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `flour milling`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product(~'flour milling')
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #90 — ✓ CORRECT
**Query:** `palm oil for biodiesel production`  
**Scope:** `worldwide`  
**Angle:** BIODIESEL  
**Time:** 0.159s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `palm oil`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #91 — ✓ CORRECT
**Query:** `cotton for yarn spinning mill`  
**Scope:** `worldwide`  
**Angle:** SPINNING MILL  
**Time:** 0.157s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton yarn`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #92 — ✓ CORRECT
**Query:** `urea for agricultural use`  
**Scope:** `worldwide`  
**Angle:** AGRICULTURAL use  
**Time:** 0.159s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `urea agricultural`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #93 — ✓ CORRECT
**Query:** `soybean for animal feed formulation`  
**Scope:** `worldwide`  
**Angle:** ANIMAL FEED  
**Time:** 0.117s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `soybean`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group N — Scope/Geography

#### Query #94 — ✓ CORRECT
**Query:** `local sugar suppliers Pakistan`  
**Scope:** `pakistan`  
**Angle:** PAKISTAN scope (BUY+PK = 0, no PK exporters in DB)  
**Time:** 0.035s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `Pakistan`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #95 — ✓ CORRECT
**Query:** `sugar suppliers in Karachi`  
**Scope:** `worldwide`  
**Angle:** CITY infers PK scope (BUY+PK = 0, no PK exporters)  
**Time:** 0.026s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #96 — ✓ CORRECT
**Query:** `import sugar for our Karachi plant`  
**Scope:** `worldwide`  
**Angle:** CITY infers PK scope (BUY+PK = 0)  
**Time:** 0.021s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #97 — ✓ CORRECT
**Query:** `international dextrose suppliers`  
**Scope:** `worldwide`  
**Angle:** INTERNATIONAL = worldwide  
**Time:** 0.034s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `65`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 65):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Netherlands | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #98 — ✓ CORRECT
**Query:** `global basmati rice suppliers`  
**Scope:** `worldwide`  
**Angle:** GLOBAL = worldwide  
**Time:** 0.158s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rice`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #99 — ✓ CORRECT
**Query:** `foreign cotton yarn suppliers`  
**Scope:** `worldwide`  
**Angle:** FOREIGN = worldwide  
**Time:** 0.161s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton yarn`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #100 — ✓ CORRECT
**Query:** `domestic wheat suppliers`  
**Scope:** `pakistan`  
**Angle:** DOMESTIC = Pakistan  
**Time:** 0.028s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group O — Spelling Errors

#### Query #101 — ✓ CORRECT
**Query:** `suagr`  
**Scope:** `worldwide`  
**Angle:** TRANSPOSED sugar (extreme anagram, trigram<0.3)  
**Time:** 0.120s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `suagr`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product(~'suagr')
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #102 — ✓ CORRECT
**Query:** `whaet`  
**Scope:** `worldwide`  
**Angle:** TRANSPOSED wheat  
**Time:** 0.113s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `whaet`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product(~'whaet')
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #103 — ✓ CORRECT
**Query:** `dextroze anhydrous`  
**Scope:** `worldwide`  
**Angle:** Z→S in dextrose  
**Time:** 0.081s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextroze anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `43`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 43):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product(~'dextroze anhydrous')
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #104 — ✓ CORRECT
**Query:** `basmati rce`  
**Scope:** `worldwide`  
**Angle:** MISSING letter rice  
**Time:** 0.158s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rce`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product(~'basmati rce')
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #105 — ✓ CORRECT
**Query:** `cottan yarn`  
**Scope:** `worldwide`  
**Angle:** A→O in cotton  
**Time:** 0.155s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cottan yarn`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product(~'cottan yarn')
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #106 — ✓ CORRECT
**Query:** `ureea fertilizer`  
**Scope:** `worldwide`  
**Angle:** DOUBLE E in urea  
**Time:** 0.159s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `ureea fertilizer`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product(~'ureea fertilizer')
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #107 — ✓ CORRECT
**Query:** `palmm oil`  
**Scope:** `worldwide`  
**Angle:** DOUBLE M in palm  
**Time:** 0.159s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `palmm oil`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product(~'palmm oil')
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #108 — ✓ CORRECT
**Query:** `soybeen`  
**Scope:** `worldwide`  
**Angle:** EE in soybean  
**Time:** 0.115s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `soybeen`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product(~'soybeen')
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #109 — ✓ CORRECT
**Query:** `refind sugar`  
**Scope:** `worldwide`  
**Angle:** TYPO in refined  
**Time:** 0.037s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refind sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `14`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 14):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Malaysia | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Brazil | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product(~'refind sugar')
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #110 — ✓ CORRECT
**Query:** `chickpeaz`  
**Scope:** `worldwide`  
**Angle:** Z ending in chickpeas  
**Time:** 0.115s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `chickpeaz`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #111 — ✓ CORRECT
**Query:** `fructoze syrup`  
**Scope:** `worldwide`  
**Angle:** Z→S in fructose  
**Time:** 0.084s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `fructoze syrup`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `22`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 22):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Egypt | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Germany | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Iran | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product(~'fructoze syrup')
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #112 — ✓ CORRECT
**Query:** `lactos monohydrate`  
**Scope:** `worldwide`  
**Angle:** MISSING E in lactose  
**Time:** 0.102s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `lactos monohydrate`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Netherlands | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | United States | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | France | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Germany | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product(~'lactos monohydrate')
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group P — Broken English

#### Query #113 — ✓ CORRECT
**Query:** `sugar buying i want`  
**Scope:** `worldwide`  
**Angle:** INVERTED order  
**Time:** 0.027s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Germany | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #114 — ✓ CORRECT
**Query:** `give me wheat cheap`  
**Scope:** `worldwide`  
**Angle:** IMPERATIVE broken  
**Time:** 0.089s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `me wheat`
- Country: `—`
- Price filter: `{'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #115 — ✓ CORRECT
**Query:** `cotton seller find me`  
**Scope:** `worldwide`  
**Angle:** REVERSE ORDER SELL  
**Time:** 0.142s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton me`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #116 — ✓ CORRECT
**Query:** `need sugar 500 ton urgent`  
**Scope:** `worldwide`  
**Angle:** BROKEN + quantity  
**Time:** 0.026s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Germany | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #117 — ✓ CORRECT
**Query:** `where buy dextrose`  
**Scope:** `worldwide`  
**Angle:** WHERE = BUY question  
**Time:** 0.104s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `where dextrose`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `51`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 51):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #118 — ✓ CORRECT
**Query:** `good quality rice give me contact`  
**Scope:** `worldwide`  
**Angle:** CONTACT REQUEST = BUY  
**Time:** 0.097s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `quality rice`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `2`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 2):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Kingdom | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | United Kingdom | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #119 — ✓ CORRECT
**Query:** `1000 ton wheat need`  
**Scope:** `worldwide`  
**Angle:** INVERTED NEED  
**Time:** 0.024s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #120 — ✓ CORRECT
**Query:** `sugar people contact me`  
**Scope:** `worldwide`  
**Angle:** SUGAR PEOPLE = suppliers  
**Time:** 0.093s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar people`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `6`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 6):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | European Union | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #121 — ✓ CORRECT
**Query:** `which country sugar comes`  
**Scope:** `worldwide`  
**Angle:** MARKET QUESTION  
**Time:** 0.095s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `country sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | European Union | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #122 — ✓ CORRECT
**Query:** `how much cost dextrose`  
**Scope:** `worldwide`  
**Angle:** PRICE QUESTION = BUY  
**Time:** 0.084s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `much dextrose`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `51`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 51):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group Q — Creative/Lateral

#### Query #123 — ✓ CORRECT
**Query:** `sweetener for my factory`  
**Scope:** `worldwide`  
**Angle:** SWEETENER = sugar/glucose  
**Time:** 0.089s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sweetener my`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `5`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 5):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Kingdom | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Bahrain | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | United Kingdom | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Sweden | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #124 — ✓ CORRECT
**Query:** `fermentation feedstock`  
**Scope:** `worldwide`  
**Angle:** FERMENTATION = glucose/dextrose  
**Time:** 0.198s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `fermentation feedstock`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #125 — ✓ CORRECT
**Query:** `IV fluid ingredient`  
**Scope:** `worldwide`  
**Angle:** IV FLUID = dextrose  
**Time:** 0.183s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `fluid ingredient`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #126 — ✓ CORRECT
**Query:** `textile raw material`  
**Scope:** `worldwide`  
**Angle:** TEXTILE = cotton  
**Time:** 0.143s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `textile raw`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `69`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 69):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Netherlands | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Malaysia | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #127 — ✓ CORRECT
**Query:** `biofuel feedstock`  
**Scope:** `worldwide`  
**Angle:** BIOFUEL = palm oil  
**Time:** 0.187s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `biofuel feedstock`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #128 — ✓ CORRECT
**Query:** `bakery raw material bulk`  
**Scope:** `worldwide`  
**Angle:** BAKERY = sugar/wheat  
**Time:** 0.146s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `bakery raw`
- Country: `—`
- Price filter: `{'ranking_hint': 'price_desc'}`
- Disambiguation: `False`
- Results count: `69`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 69):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | United Arab Emi | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Netherlands | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Malaysia | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | Thailand | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #129 — ✓ CORRECT
**Query:** `animal feed ingredient high protein`  
**Scope:** `worldwide`  
**Angle:** ANIMAL FEED = soybean  
**Time:** 0.195s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `animal feed`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #130 — ✓ CORRECT
**Query:** `crop growth booster nitrogen`  
**Scope:** `worldwide`  
**Angle:** NITROGEN = urea  
**Time:** 0.190s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `crop growth`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group R — Metaphors

#### Query #131 — ✓ CORRECT
**Query:** `white gold of Pakistan`  
**Scope:** `worldwide`  
**Angle:** WHITE GOLD = cotton  
**Time:** 0.085s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `white gold`
- Country: `Pakistan`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #132 — ✓ CORRECT
**Query:** `liquid sunshine`  
**Scope:** `worldwide`  
**Angle:** LIQUID SUNSHINE = palm oil  
**Time:** 0.182s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `liquid sunshine`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #133 — ✓ CORRECT
**Query:** `hospital sugar`  
**Scope:** `worldwide`  
**Angle:** HOSPITAL SUGAR = dextrose IV  
**Time:** 0.087s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `hospital sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `2`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 2):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | European Union | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #134 — ✓ CORRECT
**Query:** `perfumed rice`  
**Scope:** `worldwide`  
**Angle:** PERFUMED RICE = basmati  
**Time:** 0.185s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `perfumed rice`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #135 — ✓ CORRECT
**Query:** `staff of life`  
**Scope:** `worldwide`  
**Angle:** STAFF OF LIFE = wheat/bread  
**Time:** 0.136s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `staff life`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #136 — ✓ CORRECT
**Query:** `nature's fertilizer`  
**Scope:** `worldwide`  
**Angle:** NATURE'S FERT = urea  
**Time:** 0.182s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `nature fertilizer`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group S — Conversational

#### Query #137 — ✓ CORRECT
**Query:** `hi i need sugar suppliers urgently`  
**Scope:** `worldwide`  
**Angle:** GREETING + urgent  
**Time:** 0.083s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `hi sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | European Union | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #138 — ✓ CORRECT
**Query:** `can you show me top dextrose anhydrous suppliers`  
**Scope:** `worldwide`  
**Angle:** POLITE REQUEST  
**Time:** 0.035s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 5 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #139 — ✓ CORRECT
**Query:** `who are the biggest wheat exporters from Russia`  
**Scope:** `worldwide`  
**Angle:** WHO ARE + country  
**Time:** 0.080s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `who wheat`
- Country: `Russia`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #140 — ✓ CORRECT
**Query:** `i am a new buyer looking for basmati rice from India`  
**Scope:** `worldwide`  
**Angle:** BUYER PERSONA + country  
**Time:** 0.186s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rice`
- Country: `India`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #141 — ✓ CORRECT
**Query:** `please help me find cotton yarn under $1200`  
**Scope:** `worldwide`  
**Angle:** PLEASE HELP + price  
**Time:** 0.185s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton yarn`
- Country: `—`
- Price filter: `{'range': {'usd_per_mt': {'lte': 1200.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group T — Advanced/Technical

#### Query #142 — ✓ CORRECT
**Query:** `dextrose anhydrous 99.5% purity USP grade from China under $700 per MT`  
**Scope:** `worldwide`  
**Angle:** SPEC+COUNTRY+PRICE  
**Time:** 0.044s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `China`
- Price filter: `{'range': {'usd_per_mt': {'lte': 700.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `2`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 2):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #143 — ✓ CORRECT
**Query:** `white sugar ICUMSA 45 from Brazil FOB below $400`  
**Scope:** `worldwide`  
**Angle:** GRADE+COUNTRY+PRICE  
**Time:** 0.092s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar icumsa`
- Country: `Brazil`
- Price filter: `{'range': {'usd_per_mt': {'lte': 400.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #144 — ✓ CORRECT
**Query:** `wheat HRW protein 12.5% from USA under $350 per MT`  
**Scope:** `worldwide`  
**Angle:** SPEC+COUNTRY+PRICE  
**Time:** 0.092s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat hrw`
- Country: `United States`
- Price filter: `{'range': {'usd_per_mt': {'lte': 350.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #145 — ✓ CORRECT
**Query:** `RBD palm oil RSPO certified from Malaysia below $950 per MT`  
**Scope:** `worldwide`  
**Angle:** CERTIFIED+PRICE  
**Time:** 0.195s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `palm oil`
- Country: `Malaysia`
- Price filter: `{'range': {'usd_per_mt': {'lte': 950.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #146 — ✓ CORRECT
**Query:** `urea granular 46-0-0 prilled from China under $300 bulk vessel`  
**Scope:** `worldwide`  
**Angle:** SPEC+COUNTRY+PRICE  
**Time:** 0.094s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `urea granular`
- Country: `China`
- Price filter: `{'range': {'usd_per_mt': {'lte': 300.0}}, 'ranking_hint': 'price_asc'}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

### Group U — Ambiguous Intent

#### Query #147 — ✓ CORRECT
**Query:** `sugar export`  
**Scope:** `worldwide`  
**Angle:** EXPORT = SELL  
**Time:** 0.029s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #148 — ✓ CORRECT
**Query:** `we are sugar suppliers looking for buyers`  
**Scope:** `worldwide`  
**Angle:** SUPPLIERS + BUYERS = SELL  
**Time:** 0.026s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | Pakistan | BUYER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #149 — ✓ CORRECT
**Query:** `find someone who wants to buy our cotton`  
**Scope:** `worldwide`  
**Angle:** WANTS TO BUY OUR = SELL  
**Time:** 0.194s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `who cotton`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #150 — ✓ CORRECT
**Query:** `sugar trade inquiry`  
**Scope:** `worldwide`  
**Angle:** TRADE INQUIRY ambiguous  
**Time:** 0.082s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar trade`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`0` top_country=`N/A`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 2 |  | Turkey | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 3 |  | European Union | SELLER | 0.00 | 0.00 | 0 |  | 0 |
| 4 |  | China | SELLER | 0.00 | 0.00 | 0 |  | 0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---


## Partial Analysis

No PARTIAL queries — all correct!
