# ZaraiLink: Comprehensive Search Engine Architecture

The ZaraiLink search engine is designed to be highly flexible, catering to both industry veterans who know exact HS codes, and new users who prefer searching with natural language. 

This document breaks down the entire lifecycle of a search, how the different query modes work, and how data is ultimately presented to the user.

---

## 1. The Four Ways to Query (Frontend Modes)

The frontend search bar dynamically detects what the user is typing and adapts its behavior in real-time. There are four distinct ways a user can query the system:

### A. HS Code Mode (Numeric Search)
*   **How it works:** If the user types only numbers and periods (e.g., `1702.3000`), the frontend detects this and displays a blue **"HS Code Mode"** badge.
*   **Action:** It hits a specialized backend endpoint (`/api/search/hs-code-tree/`) to fetch hierarchical HS code suggestions.
*   **Result:** Clicking a suggestion routes the user to the Data Dashboard filtered exactly to that global HS code.

### B. Product Name Search (Variant Search)
*   **How it works:** The user types a specific product like `"dextrose monohydrate"`. The frontend displays a green **"Product Search"** badge.
*   **Action:** The autocomplete engine fetches matching products from the database. 
*   **Result:** Clicking the suggestion routes the user to the dashboard, pinning that exact product name (`variant_name=...`) as an active filter.

### C. Category Search (Broad Search)
*   **How it works:** The user types a broad category like `"Cane Molasses"`. 
*   **Action:** The autocomplete suggests the category. 
*   **Result:** The backend is smart enough to know this is a category, not a specific transaction variant. It safely drops the exact variant filter and loads the dashboard for the entire HS code category to prevent frustrating "0 results" errors.

### D. AI Query Mode (Natural Language)
*   **How it works:** The user selects a trade scope (Imports/Exports) and types a full sentence like *"I want to buy dextrose from China under $500"*. A purple **"AI Query Mode"** badge appears.
*   **Action:** The user hits "Search" without clicking an autocomplete suggestion.
*   **Result:** The raw sentence is sent to the backend, where it enters the **NLU Pipeline** to extract intent, product, country, and price constraints.

---

## 2. The Backend Routing: Fast Path vs. NLU Path

When the Django backend receives a search request at the `/api/search/` endpoint, it makes a critical decision on how to process it to save time and compute power.

### The Fast Path (Exact DB Match)
If the user clicked an item from the frontend autocomplete dropdown, the request arrives with explicit parameters (e.g., `hs_code=1701.9910` or `variant_name=Refined Sugar`). 
*   The backend **bypasses the AI/NLU pipeline entirely**.
*   It immediately queries the PostgreSQL database using these exact parameters.
*   This results in blazing-fast load times (milliseconds) for standard product searches.

### The NLU Path (AI Processing)
If the user submits a raw sentence, the backend routes the text through the 4-stage AI pipeline:
1.  **SetFit:** Decides if the user wants to BUY or SELL.
2.  **KeyBERT:** Extracts the product name.
3.  **RapidFuzz:** Matches geographic names to ISO country codes.
4.  **DeepSeek LLM:** Conditionally triggers if it detects price/volume numbers, extracting structural constraints.

---

## 3. The Data Dashboard & Trade Perspectives

Once the backend has the data (either via Fast Path or NLU), the user lands on the **Data Dashboard**. The core philosophy of the dashboard is **Direction-Aware Discovery**.

Because all trade on ZaraiLink is cross-border, a single product (like "Rice") means very different things depending on which side of the border you are on. The dashboard presents **4 Trade Perspectives (Pills)**:

1.  **Foreign Suppliers** (Who outside Pakistan is selling this?)
2.  **Foreign Buyers** (Who outside Pakistan is buying this?)
3.  **Pakistani Buyers** (Who inside Pakistan is importing this?)
4.  **Pakistani Suppliers** (Who inside Pakistan is exporting this?)

Clicking these pills instantly toggles the underlying dataset without requiring a page reload.

---

## 4. The Smart Sidebar & Aggregation

To help users refine their search, a sidebar sits on the left side of the dashboard displaying all product variants under the searched HS code.

**Decoupled Aggregation Logic:**
A major feature of the ZaraiLink search engine is its decoupled sidebar. 
*   The sidebar counts are calculated independently from the main results grid. 
*   If a user is looking at *Foreign Suppliers* (Import Data), the sidebar dynamically shows how many **Import** shipments exist for each product.
*   If they click *Foreign Buyers* (Export Data), the sidebar instantly updates to show the **Export** shipment counts.
*   If a product is heavily imported but never exported, its count drops to `0` and it visually fades out when switching to the Export pill, immediately informing the user of the market reality.

---

## 5. Paywall Integration

The search engine is deeply integrated with the Token Wallet.
*   When the search engine returns companies, it checks the user's access state.
*   If the user has not unlocked that specific HS code category, the search engine forcefully scrubs the data, returning only the top 2 "Preview" profiles with blurred contact details.
*   The user must spend Tokens to unlock the category, at which point the search engine releases the full paginated dataset.
