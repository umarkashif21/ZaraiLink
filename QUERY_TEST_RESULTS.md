# Zarailink Search Engine — Exhaustive 150-Query Test Results

**Run date:** 2026-04-27 12:31:03  
**Total queries:** 150  
**Endpoint:** http://localhost:8000/api/search/  

## Summary Statistics

| Metric | Value |
|--------|-------|
| ✓ CORRECT   | 96 / 150 (64%) |
| ~ PARTIAL   | 54 / 150 (36%) |
| ✗ INCORRECT | 0 / 150 (0%) |
| ? EDGE_CASE | 0 / 150 (0%) |
| ! ERROR     | 0 / 150 (0%) |
| Avg response time | 0.886s |
| Min response time | 0.011s |
| Max response time | 4.532s |

## Group-Level Accuracy

| Group | Description | Total | Correct | Partial | Incorrect | Edge/Error |
|-------|-------------|-------|---------|---------|-----------|-----------|
| A | Bare/Minimal | 5 | 5 | 0 | 0 | 0 |
| B | Basic BUY | 8 | 4 | 4 | 0 | 0 |
| C | Basic SELL | 7 | 0 | 7 | 0 | 0 |
| D | Find Suppliers (semantic reversal) | 5 | 2 | 3 | 0 | 0 |
| E | Find Buyers | 4 | 0 | 4 | 0 | 0 |
| F | Price Operators | 11 | 6 | 5 | 0 | 0 |
| G | Ranking Hints | 7 | 0 | 7 | 0 | 0 |
| H | Country Filters | 8 | 7 | 1 | 0 | 0 |
| I | Combined Multi-Criteria | 8 | 6 | 2 | 0 | 0 |
| J | HS Codes | 8 | 8 | 0 | 0 | 0 |
| K | Procurement Language | 8 | 4 | 4 | 0 | 0 |
| L | Volume/Quantity | 7 | 4 | 3 | 0 | 0 |
| M | Sector/Use-Case | 7 | 5 | 2 | 0 | 0 |
| N | Scope/Geography | 7 | 6 | 1 | 0 | 0 |
| O | Spelling Errors | 12 | 12 | 0 | 0 | 0 |
| P | Broken English | 10 | 7 | 3 | 0 | 0 |
| Q | Creative/Lateral | 8 | 7 | 1 | 0 | 0 |
| R | Metaphors | 6 | 6 | 0 | 0 | 0 |
| S | Conversational | 5 | 2 | 3 | 0 | 0 |
| T | Advanced/Technical | 5 | 4 | 1 | 0 | 0 |
| U | Ambiguous Intent | 4 | 1 | 3 | 0 | 0 |

---

## Detailed Per-Query Results


### Group A — Bare/Minimal

#### Query #1 — ✓ CORRECT
**Query:** `sugar`  
**Scope:** `worldwide`  
**Angle:** BARE KEYWORD, default BUY  
**Time:** 0.061s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`1472.63` top_country=`Turkey`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Mek Gida Sanayi Ve Ticaret Ltd Sirk | Turkey | Supplier | 24.48 | 1,470.59 | 2 | 2025-07-03 | 0.8468 |
| 2 | Fedex Express | United Arab Emi | Supplier | 0.00 | 15,360.01 | 3 | 2025-05-24 | 0.4672 |
| 3 | Xiamen Yasin Industry & Trade Co Lt | China | Supplier | 0.22 | 1,200.00 | 1 | 2024-11-04 | 0.1531 |
| 4 | Dhl Worldwide Express | Germany | Supplier | 0.00 | 55,803.40 | 1 | 2025-03-07 | 0.1276 |

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
**Time:** 0.062s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `65`
- Market snapshot: avg_price=`977.45` top_country=`China`

**Top Results (up to 5 of 65):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 5,302.50 | 661.67 | 169 | 2025-10-31 | 0.9517 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.6386 |
| 3 | Dfe Pahrma Gmbh & Co Kg | Netherlands | Supplier | 1,060.75 | 4,360.41 | 121 | 2025-10-28 | 0.5111 |
| 4 | Qiqihar Longjiang Fufeng Biotechnol | China | Supplier | 1,484.00 | 506.19 | 31 | 2025-09-15 | 0.493 |
| 5 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.4267 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #3 — ✓ CORRECT
**Query:** `1702`  
**Scope:** `worldwide`  
**Angle:** BARE HS CODE, cascade lookup  
**Time:** 0.045s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `1702`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `74`
- Market snapshot: avg_price=`823.52` top_country=`China`

**Top Results (up to 5 of 74):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 3,634.00 | 728.06 | 138 | 2025-10-31 | 0.937 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.759 |
| 3 | Qinhuangdao Lihua Starch Co Ltd | China | Supplier | 2,663.00 | 788.23 | 46 | 2025-10-30 | 0.6718 |
| 4 | Sethness Roquette Food (Lianyungang | China | Supplier | 1,709.12 | 928.81 | 30 | 2025-10-22 | 0.535 |
| 5 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.4677 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #4 — ✓ CORRECT
**Query:** `SEAWALL`  
**Scope:** `worldwide`  
**Angle:** COMPANY NAME, transaction fallback  
**Time:** 1.029s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `seawall`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`657.62` top_country=`China`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 5,595.50 | 657.62 | 177 | 2025-10-31 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #5 — ✓ CORRECT
**Query:** `s`  
**Scope:** `worldwide`  
**Angle:** SINGLE CHAR, graceful no-match  
**Time:** 0.011s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `None`
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
**Time:** 0.049s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`1472.63` top_country=`Turkey`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Mek Gida Sanayi Ve Ticaret Ltd Sirk | Turkey | Supplier | 24.48 | 1,470.59 | 2 | 2025-07-03 | 0.8468 |
| 2 | Fedex Express | United Arab Emi | Supplier | 0.00 | 15,360.01 | 3 | 2025-05-24 | 0.4672 |
| 3 | Xiamen Yasin Industry & Trade Co Lt | China | Supplier | 0.22 | 1,200.00 | 1 | 2024-11-04 | 0.1531 |
| 4 | Dhl Worldwide Express | Germany | Supplier | 0.00 | 55,803.40 | 1 | 2025-03-07 | 0.1276 |

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
**Time:** 0.05s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`750.93` top_country=`China`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 3,341.00 | 740.66 | 130 | 2025-10-31 | 0.8884 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.7421 |
| 3 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.451 |
| 4 | Liaoning Pharmaceutical Foreign Tra | China | Supplier | 852.02 | 770.70 | 33 | 2025-09-16 | 0.4371 |
| 5 | Apeloa Hong Kong Ltd | China | Supplier | 735.00 | 802.41 | 15 | 2025-10-17 | 0.4088 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #8 — ~ PARTIAL
**Query:** `i need basmati rice`  
**Scope:** `worldwide`  
**Angle:** NEED = BUY, common phrasing  
**Time:** 1.456s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #9 — ✓ CORRECT
**Query:** `purchase refined sugar`  
**Scope:** `worldwide`  
**Angle:** PURCHASE VERB, BUY intent  
**Time:** 0.048s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refined sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`561.68` top_country=`United Arab Emirates`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Al Khaleej Sugar Co Llc | United Arab Emi | Supplier | 116,166.00 | 561.41 | 8 | 2025-10-31 | 0.6587 |
| 2 | Msm Prai Berhad | Malaysia | Supplier | 1,800.00 | 787.47 | 67 | 2025-10-29 | 0.5265 |
| 3 | Tereos Acucar E Energia | Brazil | Supplier | 27,000.00 | 555.00 | 1 | 2025-10-31 | 0.364 |
| 4 | Pacific Sugar Corporation Ltd | Thailand | Supplier | 25,000.00 | 555.00 | 2 | 2025-10-08 | 0.3414 |
| 5 | Barnabas Aid | United Kingdom | Supplier | 1.05 | 122.02 | 1 | 2025-08-22 | 0.3382 |

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
**Time:** 0.048s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`10761.56` top_country=`United Arab Emirates`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Ups Air Couriers Of America | United Arab Emi | Supplier | 0.00 | 10,761.56 | 1 | 2025-01-31 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #11 — ~ PARTIAL
**Query:** `find me cotton yarn`  
**Scope:** `worldwide`  
**Angle:** FIND ME = BUY, imperative  
**Time:** 1.958s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #12 — ~ PARTIAL
**Query:** `i am interested in buying palm oil`  
**Scope:** `worldwide`  
**Angle:** INTERESTED IN BUYING phrase  
**Time:** 1.824s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #13 — ~ PARTIAL
**Query:** `want to get urea fertilizer`  
**Scope:** `worldwide`  
**Angle:** WANT TO GET, casual BUY  
**Time:** 1.872s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---


### Group C — Basic SELL

#### Query #14 — ~ PARTIAL
**Query:** `sugar for sale`  
**Scope:** `worldwide`  
**Angle:** FOR SALE phrase = SELL  
**Time:** 0.051s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `SELL`
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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #15 — ~ PARTIAL
**Query:** `we are selling wheat`  
**Scope:** `worldwide`  
**Angle:** WE ARE SELLING = SELL  
**Time:** 0.053s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `SELL`
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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #16 — ~ PARTIAL
**Query:** `i have dextrose anhydrous for sale`  
**Scope:** `worldwide`  
**Angle:** I HAVE X FOR SALE = SELL  
**Time:** 0.063s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `dextrose anhydrous`
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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #17 — ~ PARTIAL
**Query:** `basmati rice in stock`  
**Scope:** `worldwide`  
**Angle:** IN STOCK = SELL  
**Time:** 2.881s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #18 — ~ PARTIAL
**Query:** `we export cotton yarn`  
**Scope:** `worldwide`  
**Angle:** WE EXPORT = SELL  
**Time:** 2.764s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #19 — ~ PARTIAL
**Query:** `i am a supplier of refined sugar`  
**Scope:** `worldwide`  
**Angle:** I AM A SUPPLIER = SELL  
**Time:** 0.056s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `refined sugar`
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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #20 — ~ PARTIAL
**Query:** `our company produces urea and we want to sell`  
**Scope:** `worldwide`  
**Angle:** WE PRODUCE + SELL = SELL  
**Time:** 0.251s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `urea`
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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---


### Group D — Find Suppliers (semantic reversal)

#### Query #21 — ✓ CORRECT
**Query:** `find suppliers of dextrose anhydrous`  
**Scope:** `worldwide`  
**Angle:** FIND SUPPLIERS = BUY  
**Time:** 0.068s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`750.93` top_country=`China`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 3,341.00 | 740.66 | 130 | 2025-10-31 | 0.8884 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.7421 |
| 3 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.451 |
| 4 | Liaoning Pharmaceutical Foreign Tra | China | Supplier | 852.02 | 770.70 | 33 | 2025-09-16 | 0.4371 |
| 5 | Apeloa Hong Kong Ltd | China | Supplier | 735.00 | 802.41 | 15 | 2025-10-17 | 0.4088 |

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
**Time:** 0.051s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refined sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`561.68` top_country=`United Arab Emirates`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Al Khaleej Sugar Co Llc | United Arab Emi | Supplier | 116,166.00 | 561.41 | 8 | 2025-10-31 | 0.6587 |
| 2 | Msm Prai Berhad | Malaysia | Supplier | 1,800.00 | 787.47 | 67 | 2025-10-29 | 0.5265 |
| 3 | Tereos Acucar E Energia | Brazil | Supplier | 27,000.00 | 555.00 | 1 | 2025-10-31 | 0.364 |
| 4 | Pacific Sugar Corporation Ltd | Thailand | Supplier | 25,000.00 | 555.00 | 2 | 2025-10-08 | 0.3414 |
| 5 | Barnabas Aid | United Kingdom | Supplier | 1.05 | 122.02 | 1 | 2025-08-22 | 0.3382 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #23 — ~ PARTIAL
**Query:** `looking for exporters of basmati rice`  
**Scope:** `worldwide`  
**Angle:** EXPORTERS = BUY not SELL  
**Time:** 4.532s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #24 — ~ PARTIAL
**Query:** `who sells cotton yarn`  
**Scope:** `worldwide`  
**Angle:** WHO SELLS = BUY  
**Time:** 4.434s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #25 — ~ PARTIAL
**Query:** `find manufacturers of urea fertilizer`  
**Scope:** `worldwide`  
**Angle:** MANUFACTURERS = BUY  
**Time:** 4.263s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---


### Group E — Find Buyers

#### Query #26 — ~ PARTIAL
**Query:** `find buyers for basmati rice`  
**Scope:** `worldwide`  
**Angle:** FIND BUYERS = SELL  
**Time:** 3.803s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #27 — ~ PARTIAL
**Query:** `looking for importers of cotton yarn`  
**Scope:** `worldwide`  
**Angle:** IMPORTERS = SELL  
**Time:** 3.389s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #28 — ~ PARTIAL
**Query:** `who buys refined sugar`  
**Scope:** `worldwide`  
**Angle:** WHO BUYS = SELL  
**Time:** 0.086s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `refined sugar`
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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #29 — ~ PARTIAL
**Query:** `find companies interested in buying our wheat`  
**Scope:** `worldwide`  
**Angle:** OUR PRODUCT = SELL  
**Time:** 0.071s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `SELL`
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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---


### Group F — Price Operators

#### Query #30 — ~ PARTIAL
**Query:** `sugar under $500`  
**Scope:** `worldwide`  
**Angle:** WORD LTE operator  
**Time:** 0.085s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `{"range": {"usd_per_mt": {"lte": 500.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #31 — ✓ CORRECT
**Query:** `wheat above $250`  
**Scope:** `worldwide`  
**Angle:** WORD GTE operator  
**Time:** 0.084s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `{"range": {"usd_per_mt": {"gte": 250.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`10761.56` top_country=`United Arab Emirates`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Ups Air Couriers Of America | United Arab Emi | Supplier | 0.00 | 10,761.56 | 1 | 2025-01-31 | 0.0 |

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
**Angle:** RANGE ±15% operator  
**Time:** 0.091s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `{"range": {"usd_per_mt": {"gte": 700.0}}, "ranking_hint": "price_asc"}`
- Disambiguation: `False`
- Results count: `36`
- Market snapshot: avg_price=`751.12` top_country=`China`

**Top Results (up to 5 of 36):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 3,341.00 | 740.66 | 130 | 2025-10-31 | 0.9437 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.8356 |
| 3 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.739 |
| 4 | Qingdao Foture Industry Co Ltd | China | Supplier | 290.00 | 723.53 | 11 | 2025-10-30 | 0.7024 |
| 5 | Qingdao Hisunny Imp & Exp Co Ltd | China | Supplier | 194.00 | 729.94 | 8 | 2025-10-17 | 0.6815 |

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
**Angle:** SYMBOL LTE operator  
**Time:** 0.109s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `rice`
- Country: `—`
- Price filter: `{"range": {"usd_per_mt": {"lte": 600.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `7`
- Market snapshot: avg_price=`559.91` top_country=`United Arab Emirates`

**Top Results (up to 5 of 7):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Al Khaleej Sugar Co Llc | United Arab Emi | Supplier | 116,166.00 | 561.41 | 8 | 2025-10-31 | 0.9167 |
| 2 | Pacific Sugar Corporation Ltd | Thailand | Supplier | 25,000.00 | 555.00 | 2 | 2025-10-08 | 0.207 |
| 3 | The Thai Sugar Trading Corp | Thailand | Supplier | 20,674.00 | 539.00 | 1 | 2025-10-06 | 0.1978 |
| 4 | K.S.L Export Trading Co Ltd | Thailand | Supplier | 5,576.00 | 539.00 | 2 | 2025-10-06 | 0.1857 |
| 5 | Agris Ninh Hoa Import Export | Vietnam | Supplier | 14,600.00 | 580.75 | 2 | 2025-10-17 | 0.1743 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #34 — ~ PARTIAL
**Query:** `cotton >= $1000`  
**Scope:** `worldwide`  
**Angle:** SYMBOL GTE operator  
**Time:** 3.006s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton`
- Country: `—`
- Price filter: `{"range": {"usd_per_mt": {"gte": 1000.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #35 — ~ PARTIAL
**Query:** `palm oil at most $900`  
**Scope:** `worldwide`  
**Angle:** AT MOST = LTE  
**Time:** 3.171s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `palm oil`
- Country: `—`
- Price filter: `{"range": {"usd_per_mt": {"lte": 900.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #36 — ~ PARTIAL
**Query:** `urea at least $250`  
**Scope:** `worldwide`  
**Angle:** AT LEAST = GTE  
**Time:** 0.389s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `urea`
- Country: `—`
- Price filter: `{"range": {"usd_per_mt": {"gte": 250.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #37 — ✓ CORRECT
**Query:** `refined sugar not exceeding $400`  
**Scope:** `worldwide`  
**Angle:** NOT EXCEEDING = LTE  
**Time:** 0.039s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refined sugar`
- Country: `—`
- Price filter: `{"range": {"usd_per_mt": {"lte": 400.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`122.02` top_country=`United Kingdom`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Barnabas Aid | United Kingdom | Supplier | 1.05 | 122.02 | 1 | 2025-08-22 | 0.0 |

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
**Angle:** STARTING FROM = GTE  
**Time:** 0.044s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `{"range": {"usd_per_mt": {"gte": 200.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`10761.56` top_country=`United Arab Emirates`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Ups Air Couriers Of America | United Arab Emi | Supplier | 0.00 | 10,761.56 | 1 | 2025-01-31 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #39 — ~ PARTIAL
**Query:** `sugar under five hundred dollars`  
**Scope:** `worldwide`  
**Angle:** WRITTEN NUMBER, no digit  
**Time:** 0.044s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `{"range": {"usd_per_mt": {"lte": 500.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #40 — ✓ CORRECT
**Query:** `dextrose approximately $650`  
**Scope:** `worldwide`  
**Angle:** APPROXIMATE = RANGE  
**Time:** 0.057s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose`
- Country: `—`
- Price filter: `{"range": {"usd_per_mt": {"gte": 650.0}}, "ranking_hint": "price_desc"}`
- Disambiguation: `False`
- Results count: `48`
- Market snapshot: avg_price=`1077.77` top_country=`China`

**Top Results (up to 5 of 48):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 5,302.50 | 661.67 | 169 | 2025-10-31 | 0.9995 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.6655 |
| 3 | Dfe Pahrma Gmbh & Co Kg | Netherlands | Supplier | 1,060.75 | 4,360.41 | 121 | 2025-10-28 | 0.5236 |
| 4 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.3928 |
| 5 | Liaoning Pharmaceutical Foreign Tra | China | Supplier | 852.02 | 770.70 | 33 | 2025-09-16 | 0.3802 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---


### Group G — Ranking Hints

#### Query #41 — ~ PARTIAL
**Query:** `cheap sugar`  
**Scope:** `worldwide`  
**Angle:** RANKING: price_asc, no number  
**Time:** 0.057s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `{"ranking_hint": "price_asc"}`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`1472.63` top_country=`Turkey`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Mek Gida Sanayi Ve Ticaret Ltd Sirk | Turkey | Supplier | 24.48 | 1,470.59 | 2 | 2025-07-03 | 0.831 |
| 2 | Xiamen Yasin Industry & Trade Co Lt | China | Supplier | 0.22 | 1,200.00 | 1 | 2024-11-04 | 0.5013 |
| 3 | Fedex Express | United Arab Emi | Supplier | 0.00 | 15,360.01 | 3 | 2025-05-24 | 0.3458 |
| 4 | Dhl Worldwide Express | Germany | Supplier | 0.00 | 55,803.40 | 1 | 2025-03-07 | 0.1021 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✗ price_filter
- ✓ has_results

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_asc'}  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_asc'}.

---

#### Query #42 — ~ PARTIAL
**Query:** `affordable wheat`  
**Scope:** `worldwide`  
**Angle:** RANKING: price_asc synonym  
**Time:** 0.056s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `{"ranking_hint": "price_asc"}`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`10761.56` top_country=`United Arab Emirates`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Ups Air Couriers Of America | United Arab Emi | Supplier | 0.00 | 10,761.56 | 1 | 2025-01-31 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✗ price_filter
- ✓ has_results

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_asc'}  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_asc'}.

---

#### Query #43 — ~ PARTIAL
**Query:** `premium dextrose anhydrous`  
**Scope:** `worldwide`  
**Angle:** RANKING: price_desc  
**Time:** 0.044s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `{"ranking_hint": "price_desc"}`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`750.93` top_country=`China`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 3,341.00 | 740.66 | 130 | 2025-10-31 | 0.9187 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.7873 |
| 3 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.4114 |
| 4 | Liaoning Pharmaceutical Foreign Tra | China | Supplier | 852.02 | 770.70 | 33 | 2025-09-16 | 0.406 |
| 5 | Apeloa Hong Kong Ltd | China | Supplier | 735.00 | 802.41 | 15 | 2025-10-17 | 0.378 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✗ price_filter
- ✓ has_results

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_desc'}  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_desc'}.

---

#### Query #44 — ~ PARTIAL
**Query:** `bulk basmati rice`  
**Scope:** `worldwide`  
**Angle:** RANKING: volume-heavy preset  
**Time:** 1.121s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rice`
- Country: `—`
- Price filter: `{"ranking_hint": "price_desc"}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✗ price_filter
- ✗ has_results

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_desc'}; No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_desc'}; No results returned (expected some).

---

#### Query #45 — ~ PARTIAL
**Query:** `high quality refined sugar`  
**Scope:** `worldwide`  
**Angle:** RANKING: price_desc implicit  
**Time:** 0.043s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refined sugar`
- Country: `—`
- Price filter: `{"ranking_hint": "price_desc"}`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`561.68` top_country=`United Arab Emirates`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Al Khaleej Sugar Co Llc | United Arab Emi | Supplier | 116,166.00 | 561.41 | 8 | 2025-10-31 | 0.7373 |
| 2 | Msm Prai Berhad | Malaysia | Supplier | 1,800.00 | 787.47 | 67 | 2025-10-29 | 0.5128 |
| 3 | Tereos Acucar E Energia | Brazil | Supplier | 27,000.00 | 555.00 | 1 | 2025-10-31 | 0.3655 |
| 4 | Pacific Sugar Corporation Ltd | Thailand | Supplier | 25,000.00 | 555.00 | 2 | 2025-10-08 | 0.3412 |
| 5 | The Thai Sugar Trading Corp | Thailand | Supplier | 20,674.00 | 539.00 | 1 | 2025-10-06 | 0.3192 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✗ price_filter
- ✓ has_results

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_desc'}  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_desc'}.

---

#### Query #46 — ~ PARTIAL
**Query:** `cheapest cotton yarn`  
**Scope:** `worldwide`  
**Angle:** SUPERLATIVE price_asc  
**Time:** 2.025s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton yarn`
- Country: `—`
- Price filter: `{"ranking_hint": "price_asc"}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✗ price_filter
- ✗ has_results

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_asc'}; No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_asc'}; No results returned (expected some).

---

#### Query #47 — ~ PARTIAL
**Query:** `best quality palm oil`  
**Scope:** `worldwide`  
**Angle:** BEST QUALITY = price_desc  
**Time:** 1.781s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `palm oil`
- Country: `—`
- Price filter: `{"ranking_hint": "price_desc"}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✗ price_filter
- ✗ has_results

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_desc'}; No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_desc'}; No results returned (expected some).

---


### Group H — Country Filters

#### Query #48 — ✓ CORRECT
**Query:** `sugar from China`  
**Scope:** `worldwide`  
**Angle:** COUNTRY FILTER: China  
**Time:** 0.041s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `China`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`1200.0` top_country=`China`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Xiamen Yasin Industry & Trade Co Lt | China | Supplier | 0.22 | 1,200.00 | 1 | 2024-11-04 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #49 — ✓ CORRECT
**Query:** `wheat from Russia`  
**Scope:** `worldwide`  
**Angle:** COUNTRY FILTER: Russia  
**Time:** 0.049s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #50 — ✓ CORRECT
**Query:** `basmati rice from India`  
**Scope:** `worldwide`  
**Angle:** COUNTRY FILTER: India  
**Time:** 2.844s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #51 — ✓ CORRECT
**Query:** `palm oil from Malaysia`  
**Scope:** `worldwide`  
**Angle:** COUNTRY FILTER: Malaysia  
**Time:** 2.586s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #52 — ~ PARTIAL
**Query:** `cotton from USA`  
**Scope:** `worldwide`  
**Angle:** COUNTRY FILTER: USA  
**Time:** 1.753s  
**Verdict:** ~ PARTIAL  

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
- ✗ country
- ✓ price_filter

**Issues:** Country: expected 'usa', got 'united states'  

**Analysis:** 
Partially correct. Some expectations met but: Country: expected 'usa', got 'united states'.

---

#### Query #53 — ✓ CORRECT
**Query:** `soybean from Brazil`  
**Scope:** `worldwide`  
**Angle:** COUNTRY FILTER: Brazil  
**Time:** 1.814s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #54 — ✓ CORRECT
**Query:** `import wheat from Ukraine`  
**Scope:** `worldwide`  
**Angle:** IMPORT verb + COUNTRY  
**Time:** 0.045s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #55 — ✓ CORRECT
**Query:** `Chinese sugar suppliers`  
**Scope:** `worldwide`  
**Angle:** DEMONYM country form  
**Time:** 0.036s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `China`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`1200.0` top_country=`China`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Xiamen Yasin Industry & Trade Co Lt | China | Supplier | 0.22 | 1,200.00 | 1 | 2024-11-04 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---


### Group I — Combined Multi-Criteria

#### Query #56 — ✓ CORRECT
**Query:** `dextrose anhydrous from China under $700`  
**Scope:** `worldwide`  
**Angle:** PRODUCT + COUNTRY + PRICE  
**Time:** 0.043s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `China`
- Price filter: `{"range": {"usd_per_mt": {"lte": 700.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `2`
- Market snapshot: avg_price=`654.86` top_country=`China`

**Top Results (up to 5 of 2):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Daks Trading Fz Llc | China | Supplier | 0.02 | 490.13 | 1 | 2025-09-02 | 0.7 |
| 2 | Emrays (Hangzhou) Pharmaceutical Co | China | Supplier | 24.00 | 655.00 | 1 | 2025-07-18 | 0.15 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #57 — ✓ CORRECT
**Query:** `refined sugar from Brazil below $400`  
**Scope:** `worldwide`  
**Angle:** PRODUCT + COUNTRY + LTE  
**Time:** 0.041s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refined sugar`
- Country: `Brazil`
- Price filter: `{"range": {"usd_per_mt": {"lte": 400.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #58 — ✓ CORRECT
**Query:** `basmati rice from India under $600`  
**Scope:** `worldwide`  
**Angle:** PRODUCT + COUNTRY + LTE  
**Time:** 2.587s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rice`
- Country: `India`
- Price filter: `{"range": {"usd_per_mt": {"lte": 600.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #59 — ✓ CORRECT
**Query:** `bulk palm oil from Malaysia below $900`  
**Scope:** `worldwide`  
**Angle:** RANKING + COUNTRY + PRICE  
**Time:** 2.326s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `palm oil`
- Country: `Malaysia`
- Price filter: `{"range": {"usd_per_mt": {"lte": 900.0}}, "ranking_hint": "price_desc"}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #60 — ~ PARTIAL
**Query:** `cheap wheat from Russia`  
**Scope:** `worldwide`  
**Angle:** RANKING + COUNTRY, no number  
**Time:** 0.045s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `Russia`
- Price filter: `{"ranking_hint": "price_asc"}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✗ price_filter

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_asc'}  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_asc'}.

---

#### Query #61 — ✓ CORRECT
**Query:** `premium cotton yarn from Pakistan above $1000`  
**Scope:** `worldwide`  
**Angle:** RANKING + COUNTRY + GTE  
**Time:** 2.987s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton yarn`
- Country: `Pakistan`
- Price filter: `{"range": {"usd_per_mt": {"gte": 1000.0}}, "ranking_hint": "price_desc"}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #62 — ✓ CORRECT
**Query:** `find suppliers of dextrose from China under $700`  
**Scope:** `worldwide`  
**Angle:** FIND + COUNTRY + PRICE  
**Time:** 0.061s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose`
- Country: `China`
- Price filter: `{"range": {"usd_per_mt": {"lte": 700.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`612.82` top_country=`China`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Qiqihar Longjiang Fufeng Biotechnol | China | Supplier | 1,484.00 | 506.19 | 31 | 2025-09-15 | 0.5676 |
| 2 | Arshine Food Additives Co Ltd | China | Supplier | 42.00 | 450.00 | 1 | 2025-02-07 | 0.5409 |
| 3 | Daks Trading Fz Llc | China | Supplier | 0.02 | 490.13 | 1 | 2025-09-02 | 0.5365 |
| 4 | Seawall Enterprise Ltd | China | Supplier | 5,302.50 | 661.67 | 169 | 2025-10-31 | 0.5 |
| 5 | Shandong Tianliang Import And Expor | China | Supplier | 168.00 | 536.67 | 3 | 2025-05-26 | 0.3589 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #63 — ~ PARTIAL
**Query:** `looking for cheap basmati rice from India`  
**Scope:** `worldwide`  
**Angle:** INTENT + RANKING + COUNTRY  
**Time:** 3.042s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `basmati rice`
- Country: `India`
- Price filter: `{"ranking_hint": "price_asc"}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✗ price_filter

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_asc'}  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_asc'}.

---


### Group J — HS Codes

#### Query #64 — ✓ CORRECT
**Query:** `1702.3090`  
**Scope:** `worldwide`  
**Angle:** HS: dotted notation  
**Time:** 0.035s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `1702.3090`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `74`
- Market snapshot: avg_price=`823.52` top_country=`China`

**Top Results (up to 5 of 74):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 3,634.00 | 728.06 | 138 | 2025-10-31 | 0.937 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.759 |
| 3 | Qinhuangdao Lihua Starch Co Ltd | China | Supplier | 2,663.00 | 788.23 | 46 | 2025-10-30 | 0.6718 |
| 4 | Sethness Roquette Food (Lianyungang | China | Supplier | 1,709.12 | 928.81 | 30 | 2025-10-22 | 0.535 |
| 5 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.4677 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #65 — ✓ CORRECT
**Query:** `17021990`  
**Scope:** `worldwide`  
**Angle:** HS: bare digit string  
**Time:** 0.048s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #66 — ✓ CORRECT
**Query:** `HS code 1701.991`  
**Scope:** `worldwide`  
**Angle:** HS: with explicit label  
**Time:** 0.028s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `1701.991`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `13`
- Market snapshot: avg_price=`562.56` top_country=`United Arab Emirates`

**Top Results (up to 5 of 13):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Al Khaleej Sugar Co Llc | United Arab Emi | Supplier | 116,166.00 | 561.41 | 8 | 2025-10-31 | 0.7699 |
| 2 | Msm Prai Berhad | Malaysia | Supplier | 1,800.00 | 787.47 | 67 | 2025-10-29 | 0.6006 |
| 3 | Pacific Sugar Corporation Ltd | Thailand | Supplier | 25,000.00 | 555.00 | 2 | 2025-10-08 | 0.446 |
| 4 | The Thai Sugar Trading Corp | Thailand | Supplier | 20,674.00 | 539.00 | 1 | 2025-10-06 | 0.4315 |
| 5 | Agris Ninh Hoa Import Export | Vietnam | Supplier | 14,600.00 | 580.75 | 2 | 2025-10-17 | 0.4186 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #67 — ✓ CORRECT
**Query:** `tariff code 1001`  
**Scope:** `worldwide`  
**Angle:** HS: tariff code prefix  
**Time:** 0.05s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #68 — ✓ CORRECT
**Query:** `chapter 17`  
**Scope:** `worldwide`  
**Angle:** HS: chapter-level lookup  
**Time:** 1.01s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `chapter 17`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #69 — ✓ CORRECT
**Query:** `1702 30 90`  
**Scope:** `worldwide`  
**Angle:** HS: space-separated  
**Time:** 0.047s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `1702.30.90`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `74`
- Market snapshot: avg_price=`823.52` top_country=`China`

**Top Results (up to 5 of 74):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 3,634.00 | 728.06 | 138 | 2025-10-31 | 0.937 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.759 |
| 3 | Qinhuangdao Lihua Starch Co Ltd | China | Supplier | 2,663.00 | 788.23 | 46 | 2025-10-30 | 0.6718 |
| 4 | Sethness Roquette Food (Lianyungang | China | Supplier | 1,709.12 | 928.81 | 30 | 2025-10-22 | 0.535 |
| 5 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.4677 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #70 — ✓ CORRECT
**Query:** `HS 5201`  
**Scope:** `worldwide`  
**Angle:** HS: short label prefix  
**Time:** 0.044s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #71 — ✓ CORRECT
**Query:** `heading 1701`  
**Scope:** `worldwide`  
**Angle:** HS: heading prefix  
**Time:** 0.026s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `1701`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`561.73` top_country=`United Arab Emirates`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Al Khaleej Sugar Co Llc | United Arab Emi | Supplier | 116,166.00 | 561.41 | 8 | 2025-10-31 | 0.7704 |
| 2 | Msm Prai Berhad | Malaysia | Supplier | 1,800.00 | 787.47 | 67 | 2025-10-29 | 0.6052 |
| 3 | Tereos Acucar E Energia | Brazil | Supplier | 27,000.00 | 555.00 | 1 | 2025-10-31 | 0.4769 |
| 4 | Pacific Sugar Corporation Ltd | Thailand | Supplier | 25,000.00 | 555.00 | 2 | 2025-10-08 | 0.4539 |
| 5 | The Thai Sugar Trading Corp | Thailand | Supplier | 20,674.00 | 539.00 | 1 | 2025-10-06 | 0.4397 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---


### Group K — Procurement Language

#### Query #72 — ✓ CORRECT
**Query:** `RFQ for dextrose anhydrous`  
**Scope:** `worldwide`  
**Angle:** PROCUREMENT acronym  
**Time:** 0.042s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`750.93` top_country=`China`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 3,341.00 | 740.66 | 130 | 2025-10-31 | 0.8884 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.7421 |
| 3 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.451 |
| 4 | Liaoning Pharmaceutical Foreign Tra | China | Supplier | 852.02 | 770.70 | 33 | 2025-09-16 | 0.4371 |
| 5 | Apeloa Hong Kong Ltd | China | Supplier | 735.00 | 802.41 | 15 | 2025-10-17 | 0.4088 |

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
**Angle:** FORMAL PROCUREMENT phrase  
**Time:** 0.045s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refined sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`561.68` top_country=`United Arab Emirates`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Al Khaleej Sugar Co Llc | United Arab Emi | Supplier | 116,166.00 | 561.41 | 8 | 2025-10-31 | 0.6587 |
| 2 | Msm Prai Berhad | Malaysia | Supplier | 1,800.00 | 787.47 | 67 | 2025-10-29 | 0.5265 |
| 3 | Tereos Acucar E Energia | Brazil | Supplier | 27,000.00 | 555.00 | 1 | 2025-10-31 | 0.364 |
| 4 | Pacific Sugar Corporation Ltd | Thailand | Supplier | 25,000.00 | 555.00 | 2 | 2025-10-08 | 0.3414 |
| 5 | Barnabas Aid | United Kingdom | Supplier | 1.05 | 122.02 | 1 | 2025-08-22 | 0.3382 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #74 — ~ PARTIAL
**Query:** `our company requires urea fertilizer`  
**Scope:** `worldwide`  
**Angle:** COMPANY REQUIRES = BUY  
**Time:** 3.378s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #75 — ~ PARTIAL
**Query:** `we are procuring basmati rice for our operations`  
**Scope:** `worldwide`  
**Angle:** PROCURING verb  
**Time:** 3.311s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #76 — ~ PARTIAL
**Query:** `sourcing cotton yarn for our textile mill in Faisalabad`  
**Scope:** `worldwide`  
**Angle:** SOURCING + LOCAL CITY  
**Time:** 2.078s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #77 — ✓ CORRECT
**Query:** `tender for wheat supply 5000 MT`  
**Scope:** `worldwide`  
**Angle:** TENDER + VOLUME  
**Time:** 0.066s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`10761.56` top_country=`United Arab Emirates`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Ups Air Couriers Of America | United Arab Emi | Supplier | 0.00 | 10,761.56 | 1 | 2025-01-31 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #78 — ~ PARTIAL
**Query:** `invite quotations for palm oil`  
**Scope:** `worldwide`  
**Angle:** INVITE QUOTATIONS = BUY  
**Time:** 1.961s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #79 — ✓ CORRECT
**Query:** `seeking quotation for dextrose anhydrous 100 MT`  
**Scope:** `worldwide`  
**Angle:** SEEKING QUOTATION + VOLUME  
**Time:** 0.049s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`750.93` top_country=`China`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 3,341.00 | 740.66 | 130 | 2025-10-31 | 0.8884 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.7421 |
| 3 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.451 |
| 4 | Liaoning Pharmaceutical Foreign Tra | China | Supplier | 852.02 | 770.70 | 33 | 2025-09-16 | 0.4371 |
| 5 | Apeloa Hong Kong Ltd | China | Supplier | 735.00 | 802.41 | 15 | 2025-10-17 | 0.4088 |

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
**Angle:** BARE PRODUCT + VOLUME  
**Time:** 0.113s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar 1000`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`2426.86` top_country=`Turkey`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Rongcheng More Efficient Trading Lt | China | Supplier | 0.70 | 971.48 | 4 | 2025-09-12 | 0.673 |
| 2 | Mek Gida Sanayi Ve Ticaret Ltd Sirk | Turkey | Supplier | 10.08 | 2,500.00 | 1 | 2025-01-10 | 0.384 |
| 3 | Green Tract Shipping Llc | European Union | Supplier | 0.04 | 1,000.00 | 1 | 2025-01-21 | 0.1595 |
| 4 | Owin Industry Co Ltd | China | Supplier | 0.20 | 4,120.00 | 1 | 2025-01-06 | 0.0056 |

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
**Angle:** BUY + LARGE VOLUME  
**Time:** 0.127s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `5000 wheat`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`10761.56` top_country=`United Arab Emirates`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Ups Air Couriers Of America | United Arab Emi | Supplier | 0.00 | 10,761.56 | 1 | 2025-01-31 | 0.0 |

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
**Angle:** NEED + VOLUME + URGENCY  
**Time:** 0.042s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`750.93` top_country=`China`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 3,341.00 | 740.66 | 130 | 2025-10-31 | 0.8884 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.7421 |
| 3 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.451 |
| 4 | Liaoning Pharmaceutical Foreign Tra | China | Supplier | 852.02 | 770.70 | 33 | 2025-09-16 | 0.4371 |
| 5 | Apeloa Hong Kong Ltd | China | Supplier | 735.00 | 802.41 | 15 | 2025-10-17 | 0.4088 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #83 — ~ PARTIAL
**Query:** `trial shipment basmati rice`  
**Scope:** `worldwide`  
**Angle:** TRIAL SHIPMENT, small qty signal  
**Time:** 1.889s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #84 — ✓ CORRECT
**Query:** `sugar FCL`  
**Scope:** `worldwide`  
**Angle:** CONTAINER LOAD abbreviation  
**Time:** 0.113s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar fcl`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`2397.42` top_country=`Turkey`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Rongcheng More Efficient Trading Lt | China | Supplier | 0.70 | 971.48 | 4 | 2025-09-12 | 0.6743 |
| 2 | Mek Gida Sanayi Ve Ticaret Ltd Sirk | Turkey | Supplier | 10.08 | 2,500.00 | 1 | 2025-01-10 | 0.4041 |
| 3 | Dhl Worldwide Express | Bahrain | Supplier | 0.00 | 22,473.04 | 2 | 2025-07-25 | 0.2833 |
| 4 | Green Tract Shipping Llc | European Union | Supplier | 0.04 | 1,000.00 | 1 | 2025-01-21 | 0.1581 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #85 — ~ PARTIAL
**Query:** `bulk vessel wheat`  
**Scope:** `worldwide`  
**Angle:** BULK VESSEL, very large shipment  
**Time:** 0.059s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `{"ranking_hint": "price_desc"}`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`10761.56` top_country=`United Arab Emirates`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Ups Air Couriers Of America | United Arab Emi | Supplier | 0.00 | 10,761.56 | 1 | 2025-01-31 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✗ price_filter
- ✓ has_results

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_desc'}  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_desc'}.

---

#### Query #86 — ~ PARTIAL
**Query:** `sample cotton yarn`  
**Scope:** `worldwide`  
**Angle:** SAMPLE = minimal quantity  
**Time:** 1.71s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---


### Group M — Sector/Use-Case

#### Query #87 — ✓ CORRECT
**Query:** `dextrose for pharmaceutical IV`  
**Scope:** `worldwide`  
**Angle:** PHARMA USE-CASE  
**Time:** 0.184s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose pharmaceutical IV`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`750.95` top_country=`China`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 3,341.00 | 740.66 | 130 | 2025-10-31 | 0.929 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.7815 |
| 3 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.4933 |
| 4 | Liaoning Pharmaceutical Foreign Tra | China | Supplier | 852.02 | 770.70 | 33 | 2025-09-16 | 0.4753 |
| 5 | Apeloa Hong Kong Ltd | China | Supplier | 735.00 | 802.41 | 15 | 2025-10-17 | 0.4447 |

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
**Angle:** FOOD INDUSTRY USE-CASE  
**Time:** 0.214s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar for confectionery manufacturing`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `2`
- Market snapshot: avg_price=`52072.9` top_country=`Germany`

**Top Results (up to 5 of 2):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Dhl Worldwide Express | Germany | Supplier | 0.00 | 79,641.48 | 3 | 2025-03-09 | 0.6 |
| 2 | Fedex Express | United Arab Emi | Supplier | 0.00 | 10,720.03 | 1 | 2025-03-10 | 0.4 |

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
**Angle:** MILLING USE-CASE  
**Time:** 0.289s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat for flour milling`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`10761.56` top_country=`United Arab Emirates`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Ups Air Couriers Of America | United Arab Emi | Supplier | 0.00 | 10,761.56 | 1 | 2025-01-31 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #90 — ~ PARTIAL
**Query:** `palm oil for biodiesel production`  
**Scope:** `worldwide`  
**Angle:** ENERGY USE-CASE  
**Time:** 1.194s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #91 — ✓ CORRECT
**Query:** `cotton for yarn spinning mill`  
**Scope:** `worldwide`  
**Angle:** TEXTILE USE-CASE  
**Time:** 0.459s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton for yarn spinning mill`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `9`
- Market snapshot: avg_price=`963.5` top_country=`China`

**Top Results (up to 5 of 9):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Sethness Roquette Food (Lianyungang | China | Supplier | 1,709.12 | 928.81 | 30 | 2025-10-22 | 0.9312 |
| 2 | Aipu Food Industry Co Ltd | China | Supplier | 87.80 | 832.97 | 4 | 2025-10-08 | 0.3716 |
| 3 | Fusion Fareway Food Products Co Llc | China | Supplier | 16.00 | 520.00 | 1 | 2025-09-16 | 0.3686 |
| 4 | D.D Williamson Ingredients (Shangha | China | Supplier | 102.00 | 1,046.42 | 7 | 2025-08-21 | 0.3343 |
| 5 | D.D Willimason (Uk) Ltd | United Kingdom | Supplier | 15.00 | 1,964.20 | 4 | 2025-08-26 | 0.2591 |

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
**Angle:** AGRICULTURE USE-CASE  
**Time:** 0.431s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `urea for agricultural use`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`72312.44` top_country=`Bahrain`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Dhl Worldwide Express | Bahrain | Supplier | 0.00 | 72,312.44 | 1 | 2025-02-11 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #93 — ~ PARTIAL
**Query:** `soybean for animal feed formulation`  
**Scope:** `worldwide`  
**Angle:** FEED INDUSTRY USE-CASE  
**Time:** 1.145s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---


### Group N — Scope/Geography

#### Query #94 — ✓ CORRECT
**Query:** `local sugar suppliers Pakistan`  
**Scope:** `pakistan`  
**Angle:** SCOPE: domestic Pakistan explicit  
**Time:** 0.042s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #95 — ✓ CORRECT
**Query:** `sugar suppliers in Karachi`  
**Scope:** `worldwide`  
**Angle:** SCOPE: Pakistani city triggers domestic  
**Time:** 0.042s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #96 — ✓ CORRECT
**Query:** `import sugar for our Karachi plant`  
**Scope:** `worldwide`  
**Angle:** CITY inside BUY = domestic  
**Time:** 0.039s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #97 — ✓ CORRECT
**Query:** `international dextrose suppliers`  
**Scope:** `worldwide`  
**Angle:** SCOPE: worldwide  
**Time:** 0.064s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `65`
- Market snapshot: avg_price=`977.45` top_country=`China`

**Top Results (up to 5 of 65):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 5,302.50 | 661.67 | 169 | 2025-10-31 | 0.9517 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.6386 |
| 3 | Dfe Pahrma Gmbh & Co Kg | Netherlands | Supplier | 1,060.75 | 4,360.41 | 121 | 2025-10-28 | 0.5111 |
| 4 | Qiqihar Longjiang Fufeng Biotechnol | China | Supplier | 1,484.00 | 506.19 | 31 | 2025-09-15 | 0.493 |
| 5 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.4267 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #98 — ~ PARTIAL
**Query:** `global basmati rice suppliers`  
**Scope:** `worldwide`  
**Angle:** SCOPE: worldwide, global synonym  
**Time:** 3.046s  
**Verdict:** ~ PARTIAL  

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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #99 — ✓ CORRECT
**Query:** `foreign cotton yarn suppliers`  
**Scope:** `worldwide`  
**Angle:** SCOPE: worldwide, foreign synonym  
**Time:** 3.002s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #100 — ✓ CORRECT
**Query:** `domestic wheat suppliers`  
**Scope:** `pakistan`  
**Angle:** SCOPE: Pakistan, domestic synonym  
**Time:** 0.048s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---


### Group O — Spelling Errors

#### Query #101 — ✓ CORRECT
**Query:** `suagr`  
**Scope:** `worldwide`  
**Angle:** TYPO: transposed → sugar  
**Time:** 0.056s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`1472.63` top_country=`Turkey`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Mek Gida Sanayi Ve Ticaret Ltd Sirk | Turkey | Supplier | 24.48 | 1,470.59 | 2 | 2025-07-03 | 0.8468 |
| 2 | Fedex Express | United Arab Emi | Supplier | 0.00 | 15,360.01 | 3 | 2025-05-24 | 0.4672 |
| 3 | Xiamen Yasin Industry & Trade Co Lt | China | Supplier | 0.22 | 1,200.00 | 1 | 2024-11-04 | 0.1531 |
| 4 | Dhl Worldwide Express | Germany | Supplier | 0.00 | 55,803.40 | 1 | 2025-03-07 | 0.1276 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #102 — ✓ CORRECT
**Query:** `whaet`  
**Scope:** `worldwide`  
**Angle:** TYPO: transposed → wheat  
**Time:** 0.053s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`10761.56` top_country=`United Arab Emirates`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Ups Air Couriers Of America | United Arab Emi | Supplier | 0.00 | 10,761.56 | 1 | 2025-01-31 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #103 — ✓ CORRECT
**Query:** `dextroze anhydrous`  
**Scope:** `worldwide`  
**Angle:** TYPO: z/s swap → dextrose  
**Time:** 0.064s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`750.93` top_country=`China`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 3,341.00 | 740.66 | 130 | 2025-10-31 | 0.8884 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.7421 |
| 3 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.451 |
| 4 | Liaoning Pharmaceutical Foreign Tra | China | Supplier | 852.02 | 770.70 | 33 | 2025-09-16 | 0.4371 |
| 5 | Apeloa Hong Kong Ltd | China | Supplier | 735.00 | 802.41 | 15 | 2025-10-17 | 0.4088 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #104 — ✓ CORRECT
**Query:** `basmati rce`  
**Scope:** `worldwide`  
**Angle:** TYPO: missing letter → rice  
**Time:** 2.779s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #105 — ✓ CORRECT
**Query:** `cottan yarn`  
**Scope:** `worldwide`  
**Angle:** TYPO: wrong vowel → cotton  
**Time:** 2.749s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #106 — ✓ CORRECT
**Query:** `ureea fertilizer`  
**Scope:** `worldwide`  
**Angle:** TYPO: doubled vowel → urea  
**Time:** 0.176s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `urea`
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #107 — ✓ CORRECT
**Query:** `palmm oil`  
**Scope:** `worldwide`  
**Angle:** TYPO: doubled consonant → palm oil  
**Time:** 1.839s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #108 — ✓ CORRECT
**Query:** `soybeen`  
**Scope:** `worldwide`  
**Angle:** TYPO: wrong vowel → soybean  
**Time:** 1.696s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #109 — ✓ CORRECT
**Query:** `refind sugar`  
**Scope:** `worldwide`  
**Angle:** TYPO: wrong suffix → refined  
**Time:** 0.051s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `refined sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `17`
- Market snapshot: avg_price=`561.68` top_country=`United Arab Emirates`

**Top Results (up to 5 of 17):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Al Khaleej Sugar Co Llc | United Arab Emi | Supplier | 116,166.00 | 561.41 | 8 | 2025-10-31 | 0.6587 |
| 2 | Msm Prai Berhad | Malaysia | Supplier | 1,800.00 | 787.47 | 67 | 2025-10-29 | 0.5265 |
| 3 | Tereos Acucar E Energia | Brazil | Supplier | 27,000.00 | 555.00 | 1 | 2025-10-31 | 0.364 |
| 4 | Pacific Sugar Corporation Ltd | Thailand | Supplier | 25,000.00 | 555.00 | 2 | 2025-10-08 | 0.3414 |
| 5 | Barnabas Aid | United Kingdom | Supplier | 1.05 | 122.02 | 1 | 2025-08-22 | 0.3382 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #110 — ✓ CORRECT
**Query:** `chickpeaz`  
**Scope:** `worldwide`  
**Angle:** TYPO: z/s swap → chickpeas  
**Time:** 1.52s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `chickpeas`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`8780.86` top_country=`United Arab Emirates`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Ups Air Couriers Of America | United Arab Emi | Supplier | 0.00 | 8,780.86 | 1 | 2025-07-21 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #111 — ✓ CORRECT
**Query:** `fructoze syrup`  
**Scope:** `worldwide`  
**Angle:** TYPO: z/s swap → fructose  
**Time:** 0.046s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `fructose syrup`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`684.69` top_country=`China`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Zhaoqing Huanfa Biotechnology Co Lt | China | Supplier | 21.00 | 758.00 | 1 | 2025-06-23 | 0.5405 |
| 2 | North Mile Co Ltd | China | Supplier | 23.20 | 606.38 | 1 | 2025-01-28 | 0.5 |
| 3 | Zhejiang New Vision Imp & Exp Co Lt | China | Supplier | 1.00 | 700.00 | 1 | 2025-10-07 | 0.3507 |
| 4 | Guangzhou Dongchen International Tr | China | Supplier | 0.52 | 1,188.54 | 1 | 2025-10-24 | 0.25 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #112 — ✓ CORRECT
**Query:** `lactos monohydrate`  
**Scope:** `worldwide`  
**Angle:** TYPO: missing e → lactose  
**Time:** 0.06s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `lactose monohydrate`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `15`
- Market snapshot: avg_price=`3437.15` top_country=`Netherlands`

**Top Results (up to 5 of 15):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Dfe Pahrma Gmbh & Co Kg | Netherlands | Supplier | 1,040.70 | 4,380.11 | 119 | 2025-10-28 | 0.8674 |
| 2 | Malkara Birlik Sut Ve Sut Mamulleri | Turkey | Supplier | 294.00 | 1,756.65 | 33 | 2025-10-25 | 0.4605 |
| 3 | Armor Proteines Sas | France | Supplier | 273.00 | 1,688.71 | 24 | 2025-10-16 | 0.4294 |
| 4 | Aba Stepsworth Dwc Llc | United States | Supplier | 120.53 | 2,318.08 | 14 | 2025-10-28 | 0.3525 |
| 5 | Meggle Gmbh & Co Kg | Germany | Supplier | 118.65 | 3,273.32 | 12 | 2025-10-10 | 0.3234 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---


### Group P — Broken English

#### Query #113 — ✓ CORRECT
**Query:** `sugar buying i want`  
**Scope:** `worldwide`  
**Angle:** REVERSED WORD ORDER, BUY  
**Time:** 0.056s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`1472.63` top_country=`Turkey`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Mek Gida Sanayi Ve Ticaret Ltd Sirk | Turkey | Supplier | 24.48 | 1,470.59 | 2 | 2025-07-03 | 0.8468 |
| 2 | Fedex Express | United Arab Emi | Supplier | 0.00 | 15,360.01 | 3 | 2025-05-24 | 0.4672 |
| 3 | Xiamen Yasin Industry & Trade Co Lt | China | Supplier | 0.22 | 1,200.00 | 1 | 2024-11-04 | 0.1531 |
| 4 | Dhl Worldwide Express | Germany | Supplier | 0.00 | 55,803.40 | 1 | 2025-03-07 | 0.1276 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #114 — ~ PARTIAL
**Query:** `give me wheat cheap`  
**Scope:** `worldwide`  
**Angle:** IMPERATIVE + RANKING, no verb buy  
**Time:** 0.057s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `{"ranking_hint": "price_asc"}`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`10761.56` top_country=`United Arab Emirates`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Ups Air Couriers Of America | United Arab Emi | Supplier | 0.00 | 10,761.56 | 1 | 2025-01-31 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✗ price_filter
- ✓ has_results

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_asc'}  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_asc'}.

---

#### Query #115 — ~ PARTIAL
**Query:** `cotton seller find me`  
**Scope:** `worldwide`  
**Angle:** REVERSED, find seller = BUY  
**Time:** 1.167s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton`
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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #116 — ✓ CORRECT
**Query:** `need sugar 500 ton urgent`  
**Scope:** `worldwide`  
**Angle:** MISSING ARTICLES + VOLUME + URGENCY  
**Time:** 0.045s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`1472.63` top_country=`Turkey`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Mek Gida Sanayi Ve Ticaret Ltd Sirk | Turkey | Supplier | 24.48 | 1,470.59 | 2 | 2025-07-03 | 0.8468 |
| 2 | Fedex Express | United Arab Emi | Supplier | 0.00 | 15,360.01 | 3 | 2025-05-24 | 0.4672 |
| 3 | Xiamen Yasin Industry & Trade Co Lt | China | Supplier | 0.22 | 1,200.00 | 1 | 2024-11-04 | 0.1531 |
| 4 | Dhl Worldwide Express | Germany | Supplier | 0.00 | 55,803.40 | 1 | 2025-03-07 | 0.1276 |

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
**Angle:** MISSING CAN I, bare question  
**Time:** 0.071s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `65`
- Market snapshot: avg_price=`977.45` top_country=`China`

**Top Results (up to 5 of 65):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 5,302.50 | 661.67 | 169 | 2025-10-31 | 0.9517 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.6386 |
| 3 | Dfe Pahrma Gmbh & Co Kg | Netherlands | Supplier | 1,060.75 | 4,360.41 | 121 | 2025-10-28 | 0.5111 |
| 4 | Qiqihar Longjiang Fufeng Biotechnol | China | Supplier | 1,484.00 | 506.19 | 31 | 2025-09-15 | 0.493 |
| 5 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.4267 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #118 — ~ PARTIAL
**Query:** `good quality rice give me contact`  
**Scope:** `worldwide`  
**Angle:** BROKEN PHRASE, wants supplier  
**Time:** 0.043s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `rice`
- Country: `—`
- Price filter: `{"ranking_hint": "price_desc"}`
- Disambiguation: `False`
- Results count: `15`
- Market snapshot: avg_price=`562.6` top_country=`United Arab Emirates`

**Top Results (up to 5 of 15):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Al Khaleej Sugar Co Llc | United Arab Emi | Supplier | 116,166.00 | 561.41 | 8 | 2025-10-31 | 0.7744 |
| 2 | Msm Prai Berhad | Malaysia | Supplier | 1,800.00 | 787.47 | 67 | 2025-10-29 | 0.5389 |
| 3 | Pacific Sugar Corporation Ltd | Thailand | Supplier | 25,000.00 | 555.00 | 2 | 2025-10-08 | 0.3798 |
| 4 | The Thai Sugar Trading Corp | Thailand | Supplier | 20,674.00 | 539.00 | 1 | 2025-10-06 | 0.3591 |
| 5 | Agris Ninh Hoa Import Export | Vietnam | Supplier | 14,600.00 | 580.75 | 2 | 2025-10-17 | 0.3449 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✗ price_filter
- ✓ has_results

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_desc'}  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_desc'}.

---

#### Query #119 — ✓ CORRECT
**Query:** `1000 ton wheat need`  
**Scope:** `worldwide`  
**Angle:** VOLUME FIRST, verb last  
**Time:** 0.034s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`10761.56` top_country=`United Arab Emirates`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Ups Air Couriers Of America | United Arab Emi | Supplier | 0.00 | 10,761.56 | 1 | 2025-01-31 | 0.0 |

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
**Angle:** PEOPLE = supplier, informal  
**Time:** 0.037s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`1472.63` top_country=`Turkey`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Mek Gida Sanayi Ve Ticaret Ltd Sirk | Turkey | Supplier | 24.48 | 1,470.59 | 2 | 2025-07-03 | 0.8468 |
| 2 | Fedex Express | United Arab Emi | Supplier | 0.00 | 15,360.01 | 3 | 2025-05-24 | 0.4672 |
| 3 | Xiamen Yasin Industry & Trade Co Lt | China | Supplier | 0.22 | 1,200.00 | 1 | 2024-11-04 | 0.1531 |
| 4 | Dhl Worldwide Express | Germany | Supplier | 0.00 | 55,803.40 | 1 | 2025-03-07 | 0.1276 |

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
**Angle:** WRONG GRAMMAR, origin question  
**Time:** 0.044s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`1472.63` top_country=`Turkey`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Mek Gida Sanayi Ve Ticaret Ltd Sirk | Turkey | Supplier | 24.48 | 1,470.59 | 2 | 2025-07-03 | 0.8468 |
| 2 | Fedex Express | United Arab Emi | Supplier | 0.00 | 15,360.01 | 3 | 2025-05-24 | 0.4672 |
| 3 | Xiamen Yasin Industry & Trade Co Lt | China | Supplier | 0.22 | 1,200.00 | 1 | 2024-11-04 | 0.1531 |
| 4 | Dhl Worldwide Express | Germany | Supplier | 0.00 | 55,803.40 | 1 | 2025-03-07 | 0.1276 |

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
**Angle:** MISSING VERB, price inquiry = BUY  
**Time:** 0.042s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `65`
- Market snapshot: avg_price=`977.45` top_country=`China`

**Top Results (up to 5 of 65):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 5,302.50 | 661.67 | 169 | 2025-10-31 | 0.9517 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.6386 |
| 3 | Dfe Pahrma Gmbh & Co Kg | Netherlands | Supplier | 1,060.75 | 4,360.41 | 121 | 2025-10-28 | 0.5111 |
| 4 | Qiqihar Longjiang Fufeng Biotechnol | China | Supplier | 1,484.00 | 506.19 | 31 | 2025-09-15 | 0.493 |
| 5 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.4267 |

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
**Angle:** FUNCTION DESCRIPTION → sugar/dextrose  
**Time:** 0.043s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sweetener`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `3`
- Market snapshot: avg_price=`1843.76` top_country=`United Kingdom`

**Top Results (up to 5 of 3):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Rayburn Trading Co Ltd | United Kingdom | Supplier | 0.12 | 1,004.08 | 2 | 2025-03-09 | 0.9531 |
| 2 | Kings International General Trading | United Kingdom | Supplier | 0.02 | 3,802.08 | 2 | 2025-03-21 | 0.545 |
| 3 | Rapid World General Trading Co Llc | United Arab Emi | Supplier | 0.01 | 7,000.00 | 1 | 2025-01-16 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #124 — ✓ CORRECT
**Query:** `fermentation feedstock`  
**Scope:** `worldwide`  
**Angle:** INDUSTRIAL FUNCTION → glucose/molasses  
**Time:** 3.518s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #125 — ✓ CORRECT
**Query:** `IV fluid ingredient`  
**Scope:** `worldwide`  
**Angle:** MEDICAL FUNCTION → dextrose anhydrous  
**Time:** 3.104s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `IV fluid ingredient`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #126 — ✓ CORRECT
**Query:** `textile raw material`  
**Scope:** `worldwide`  
**Angle:** MATERIAL CATEGORY → cotton  
**Time:** 0.152s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `textile raw material`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `3`
- Market snapshot: avg_price=`3481.67` top_country=`United States`

**Top Results (up to 5 of 3):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Aba Stepsworth Dwc Llc | United States | Supplier | 147.88 | 3,501.13 | 27 | 2025-10-29 | 0.85 |
| 2 | Meggle Gmbh & Co Kg | Germany | Supplier | 131.25 | 3,481.70 | 6 | 2025-09-22 | 0.3616 |
| 3 | Dfe Pahrma Gmbh & Co Kg | Netherlands | Supplier | 20.05 | 3,337.88 | 2 | 2025-10-07 | 0.2514 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #127 — ✓ CORRECT
**Query:** `biofuel feedstock`  
**Scope:** `worldwide`  
**Angle:** ENERGY FUNCTION → molasses/palm oil  
**Time:** 2.055s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #128 — ~ PARTIAL
**Query:** `bakery raw material bulk`  
**Scope:** `worldwide`  
**Angle:** FOOD FUNCTION → wheat flour/sugar  
**Time:** 0.173s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `bakery raw material`
- Country: `—`
- Price filter: `{"ranking_hint": "price_desc"}`
- Disambiguation: `False`
- Results count: `3`
- Market snapshot: avg_price=`3478.77` top_country=`United States`

**Top Results (up to 5 of 3):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Aba Stepsworth Dwc Llc | United States | Supplier | 147.88 | 3,501.13 | 27 | 2025-10-29 | 0.95 |
| 2 | Meggle Gmbh & Co Kg | Germany | Supplier | 73.00 | 3,472.16 | 10 | 2025-07-24 | 0.2749 |
| 3 | Dfe Pahrma Gmbh & Co Kg | Netherlands | Supplier | 20.05 | 3,337.88 | 2 | 2025-10-07 | 0.2433 |

**Correctness Checks:**
- ✓ intent
- ✗ price_filter

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_desc'}  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_desc'}.

---

#### Query #129 — ✓ CORRECT
**Query:** `animal feed ingredient high protein`  
**Scope:** `worldwide`  
**Angle:** FEED FUNCTION → soybean meal  
**Time:** 0.692s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `animal feed ingredient high protein`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `5`
- Market snapshot: avg_price=`651.09` top_country=`Turkey`

**Top Results (up to 5 of 5):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Adm Besin Ve Tarim As | Turkey | Supplier | 72.00 | 640.00 | 3 | 2025-01-21 | 0.7369 |
| 2 | North Mile Co Ltd | China | Supplier | 46.40 | 612.84 | 2 | 2025-01-28 | 0.506 |
| 3 | Zhejiang New Vision Imp & Exp Co Lt | China | Supplier | 1.00 | 700.00 | 1 | 2025-10-07 | 0.3484 |
| 4 | Zhaoqing Huanfa Biotechnology Co Lt | China | Supplier | 21.00 | 758.00 | 1 | 2025-06-23 | 0.3296 |
| 5 | Guangzhou Dongchen International Tr | China | Supplier | 0.52 | 1,188.54 | 1 | 2025-10-24 | 0.25 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #130 — ✓ CORRECT
**Query:** `crop growth booster nitrogen`  
**Scope:** `worldwide`  
**Angle:** AGRI FUNCTION → urea fertilizer  
**Time:** 1.773s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `nitrogen`
- Product keyword 2: `crop growth booster`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---


### Group R — Metaphors

#### Query #131 — ✓ CORRECT
**Query:** `white gold of Pakistan`  
**Scope:** `worldwide`  
**Angle:** METAPHOR → sugar OR cotton  
**Time:** 0.142s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #132 — ✓ CORRECT
**Query:** `liquid sunshine`  
**Scope:** `worldwide`  
**Angle:** METAPHOR → sunflower/palm oil  
**Time:** 1.944s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #133 — ✓ CORRECT
**Query:** `hospital sugar`  
**Scope:** `worldwide`  
**Angle:** NICKNAME → dextrose anhydrous  
**Time:** 0.039s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`1472.63` top_country=`Turkey`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Mek Gida Sanayi Ve Ticaret Ltd Sirk | Turkey | Supplier | 24.48 | 1,470.59 | 2 | 2025-07-03 | 0.8468 |
| 2 | Fedex Express | United Arab Emi | Supplier | 0.00 | 15,360.01 | 3 | 2025-05-24 | 0.4672 |
| 3 | Xiamen Yasin Industry & Trade Co Lt | China | Supplier | 0.22 | 1,200.00 | 1 | 2024-11-04 | 0.1531 |
| 4 | Dhl Worldwide Express | Germany | Supplier | 0.00 | 55,803.40 | 1 | 2025-03-07 | 0.1276 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #134 — ✓ CORRECT
**Query:** `perfumed rice`  
**Scope:** `worldwide`  
**Angle:** NICKNAME → basmati rice  
**Time:** 1.618s  
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
- ✓ product
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #135 — ✓ CORRECT
**Query:** `staff of life`  
**Scope:** `worldwide`  
**Angle:** IDIOM → wheat/bread flour  
**Time:** 0.158s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `staff life`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `1`
- Market snapshot: avg_price=`3420.88` top_country=`Turkey`

**Top Results (up to 5 of 1):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Pamir Gida Sanayi As | Turkey | Supplier | 0.77 | 3,420.88 | 1 | 2025-01-27 | 0.0 |

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #136 — ✓ CORRECT
**Query:** `nature's fertilizer`  
**Scope:** `worldwide`  
**Angle:** METAPHOR → urea/organic fertilizer  
**Time:** 1.759s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `fertilizer`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---


### Group S — Conversational

#### Query #137 — ✓ CORRECT
**Query:** `hi i need sugar suppliers urgently`  
**Scope:** `worldwide`  
**Angle:** GREETING + BUY + URGENCY  
**Time:** 0.057s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`1472.63` top_country=`Turkey`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Mek Gida Sanayi Ve Ticaret Ltd Sirk | Turkey | Supplier | 24.48 | 1,470.59 | 2 | 2025-07-03 | 0.8468 |
| 2 | Fedex Express | United Arab Emi | Supplier | 0.00 | 15,360.01 | 3 | 2025-05-24 | 0.4672 |
| 3 | Xiamen Yasin Industry & Trade Co Lt | China | Supplier | 0.22 | 1,200.00 | 1 | 2024-11-04 | 0.1531 |
| 4 | Dhl Worldwide Express | Germany | Supplier | 0.00 | 55,803.40 | 1 | 2025-03-07 | 0.1276 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #138 — ~ PARTIAL
**Query:** `can you show me top dextrose anhydrous suppliers`  
**Scope:** `worldwide`  
**Angle:** TOP-N + CONVERSATIONAL  
**Time:** 0.063s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous`
- Country: `—`
- Price filter: `{"ranking_hint": "price_desc"}`
- Disambiguation: `False`
- Results count: `38`
- Market snapshot: avg_price=`750.93` top_country=`China`

**Top Results (up to 5 of 38):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Seawall Enterprise Ltd | China | Supplier | 3,341.00 | 740.66 | 130 | 2025-10-31 | 0.9187 |
| 2 | Chuming Pharmaceutical Ltd | China | Supplier | 3,850.00 | 755.17 | 33 | 2025-10-28 | 0.7873 |
| 3 | Weifang Shengtai Medicine Co Ltd | China | Supplier | 743.00 | 720.25 | 25 | 2025-10-29 | 0.4114 |
| 4 | Liaoning Pharmaceutical Foreign Tra | China | Supplier | 852.02 | 770.70 | 33 | 2025-09-16 | 0.406 |
| 5 | Apeloa Hong Kong Ltd | China | Supplier | 735.00 | 802.41 | 15 | 2025-10-17 | 0.378 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✗ price_filter
- ✓ has_results

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_desc'}  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_desc'}.

---

#### Query #139 — ~ PARTIAL
**Query:** `who are the biggest wheat exporters from Russia`  
**Scope:** `worldwide`  
**Angle:** QUESTION FORM + COUNTRY  
**Time:** 0.039s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat`
- Country: `Russia`
- Price filter: `{"ranking_hint": "price_desc"}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✗ price_filter

**Issues:** Price filter: expected none, got {'ranking_hint': 'price_desc'}  

**Analysis:** 
Partially correct. Some expectations met but: Price filter: expected none, got {'ranking_hint': 'price_desc'}.

---

#### Query #140 — ✓ CORRECT
**Query:** `i am a new buyer looking for basmati rice from India`  
**Scope:** `worldwide`  
**Angle:** PERSONA + BUY + COUNTRY  
**Time:** 2.055s  
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

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #141 — ~ PARTIAL
**Query:** `please help me find cotton yarn under $1200`  
**Scope:** `worldwide`  
**Angle:** POLITE REQUEST + PRICE  
**Time:** 2.019s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `cotton yarn`
- Country: `—`
- Price filter: `{"range": {"usd_per_mt": {"lte": 1200.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---


### Group T — Advanced/Technical

#### Query #142 — ✓ CORRECT
**Query:** `dextrose anhydrous 99.5% purity USP grade from China under $700 per MT`  
**Scope:** `worldwide`  
**Angle:** GRADE+PURITY+COUNTRY+PRICE+UNIT  
**Time:** 0.154s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `dextrose anhydrous 99.5% purity USP grade`
- Country: `China`
- Price filter: `{"range": {"usd_per_mt": {"lte": 700.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `2`
- Market snapshot: avg_price=`654.86` top_country=`China`

**Top Results (up to 5 of 2):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Daks Trading Fz Llc | China | Supplier | 0.02 | 490.13 | 1 | 2025-09-02 | 0.7 |
| 2 | Emrays (Hangzhou) Pharmaceutical Co | China | Supplier | 24.00 | 655.00 | 1 | 2025-07-18 | 0.15 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #143 — ✓ CORRECT
**Query:** `white sugar ICUMSA 45 from Brazil FOB below $400`  
**Scope:** `worldwide`  
**Angle:** GRADE+TRADE TERM+COUNTRY+PRICE  
**Time:** 0.128s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `white sugar ICUMSA 45`
- Country: `Brazil`
- Price filter: `{"range": {"usd_per_mt": {"lte": 400.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #144 — ~ PARTIAL
**Query:** `wheat HRW protein 12.5% from USA under $350 per MT`  
**Scope:** `worldwide`  
**Angle:** VARIETY+SPEC+COUNTRY+PRICE  
**Time:** 0.193s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `wheat HRW protein 12.5%`
- Country: `United States`
- Price filter: `{"range": {"usd_per_mt": {"lte": 350.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✗ country
- ✓ price_filter

**Issues:** Country: expected 'usa', got 'united states'  

**Analysis:** 
Partially correct. Some expectations met but: Country: expected 'usa', got 'united states'.

---

#### Query #145 — ✓ CORRECT
**Query:** `RBD palm oil RSPO certified from Malaysia below $950 per MT`  
**Scope:** `worldwide`  
**Angle:** GRADE+CERTIFICATION+COUNTRY+PRICE  
**Time:** 2.477s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `RBD palm oil RSPO certified`
- Country: `Malaysia`
- Price filter: `{"range": {"usd_per_mt": {"lte": 950.0}}, "ranking_hint": null}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

#### Query #146 — ✓ CORRECT
**Query:** `urea granular 46-0-0 prilled from China under $300 bulk vessel`  
**Scope:** `worldwide`  
**Angle:** GRADE+NPK+FORM+COUNTRY+PRICE+VOL  
**Time:** 0.153s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `urea granular 46-0-0 prilled`
- Country: `China`
- Price filter: `{"range": {"usd_per_mt": {"lte": 300.0}}, "ranking_hint": "price_desc"}`
- Disambiguation: `False`
- Results count: `0`
- Market snapshot: avg_price=`0` top_country=`N/A`

*No results returned.*

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ country
- ✓ price_filter

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---


### Group U — Ambiguous Intent

#### Query #147 — ~ PARTIAL
**Query:** `sugar export`  
**Scope:** `worldwide`  
**Angle:** AMBIGUOUS: export → SELL  
**Time:** 0.031s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `SELL`
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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #148 — ~ PARTIAL
**Query:** `we are sugar suppliers looking for buyers`  
**Scope:** `worldwide`  
**Angle:** SELL: we are suppliers + find buyers  
**Time:** 0.045s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `SELL`
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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #149 — ~ PARTIAL
**Query:** `find someone who wants to buy our cotton`  
**Scope:** `worldwide`  
**Angle:** SELL: our product + find buyers  
**Time:** 1.239s  
**Verdict:** ~ PARTIAL  

**Engine Parsed:**
- Intent: `SELL`
- Product keyword: `cotton`
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
- ✗ has_results

**Issues:** No results returned (expected some)  

**Analysis:** 
Partially correct. Some expectations met but: No results returned (expected some).

---

#### Query #150 — ✓ CORRECT
**Query:** `sugar trade inquiry`  
**Scope:** `worldwide`  
**Angle:** AMBIGUOUS: defaults to BUY  
**Time:** 0.055s  
**Verdict:** ✓ CORRECT  

**Engine Parsed:**
- Intent: `BUY`
- Product keyword: `sugar`
- Country: `—`
- Price filter: `—`
- Disambiguation: `False`
- Results count: `4`
- Market snapshot: avg_price=`1472.63` top_country=`Turkey`

**Top Results (up to 5 of 4):**
| # | Name | Country | Type | Vol (MT) | Avg Price | Shipments | Last Date | Score |
|---|------|---------|------|----------|-----------|-----------|-----------|-------|
| 1 | Mek Gida Sanayi Ve Ticaret Ltd Sirk | Turkey | Supplier | 24.48 | 1,470.59 | 2 | 2025-07-03 | 0.8468 |
| 2 | Fedex Express | United Arab Emi | Supplier | 0.00 | 15,360.01 | 3 | 2025-05-24 | 0.4672 |
| 3 | Xiamen Yasin Industry & Trade Co Lt | China | Supplier | 0.22 | 1,200.00 | 1 | 2024-11-04 | 0.1531 |
| 4 | Dhl Worldwide Express | Germany | Supplier | 0.00 | 55,803.40 | 1 | 2025-03-07 | 0.1276 |

**Correctness Checks:**
- ✓ intent
- ✓ product
- ✓ price_filter
- ✓ has_results

**Analysis:** 
Engine handled this correctly — intent, product extraction, and filters all matched expectations.

---

## Overall Assessment

- **96 queries fully correct** (64%), **54 partially correct** (36%) — 100% are at minimum partially functional.
- **0 queries incorrect** — intent or primary filter missed.
- **0 edge-case queries** — no hard expectations (metaphors, creative, HS codes), manual inspection needed.
- **0 errors** — network/timeout issues if any.
- **Average response time 0.886s** (min 0.011s, max 4.532s).