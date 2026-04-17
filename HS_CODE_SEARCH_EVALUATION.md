# Evaluation: Incremental HS Code Search

## 1. Concept Overview
The goal is to allow users to search the trade database using numerical HS (Harmonized System) Codes. Rather than jumping straight to supplier/buyer results, the system will offer a **"Drill-Down / Stepped"** interface.

**Target Flow (As Requested):**
- Search `17` → Popup shows `1701`, `1702`, `1703`, `1704`.
- Click `1702` → Popup updates to show `1702.1900 (Other)`, `1702.9090 (Other)`.
- Click `1702.9090 (Other)` → Final results screen opens showing exact products mapped to it (e.g., `Flavours`, `Syrup`) along with the trade intel.
- (Typing `170` instantly filters the first popup to `1702`, `1703`. Typing `1702.1` instantly filters to `1702.1900`).

---

## 2. Feasibility & Architecture
**Can it be done alongside the current system?**
Yes. Since the backend detects if you are typing an HS Code (numbers and dots), it bypasses the heavy AI models and queries the database using blazingly fast `startswith` filters. 

### Database Reality Check
Your example maps perfectly to how the `trade_data` models are set up:
- **`ProductCategory`:** `1702`
- **`ProductSubCategory`:** `1702.9090 (Name: Other)`
- **`ProductItem`:** `Flavours`, `Syrup` (Both are linked to `1702.9090`).

Because `ProductItem` falls under `ProductSubCategory`, once the user drills down to `1702.9090`, the backend knows exactly which `ProductItem`s (Flavours, Syrup) to query the `TradeLedger` for.

---

## 3. The "Ambiguous Intent" Problem & Solution
**The Problem:** When a user types natural language like *"buy sugar"*, the AI knows the intent is `BUY`. It uses this alongside the UI scope (`Worldwide` vs `Pakistan`) to filter for Suppliers vs Buyers. 
If a user just types a raw HS code like `1702.9090`, there are no words! The AI has zero clue if the user wants to buy it or sell it.

**The Solution:** We decouple **Product Discovery** from **Trade Intent**.

Here is how the HS Code flow actually works with Intent:
1. **The Universal Dictionary Phase (The Dropdown)**: When the user types `17` -> `1702.9090`, the dropdown does **NOT** filter by Import/Export or Scope yet. It explores the universal dictionary of all HS codes.
2. **The Intent Declaration (Phase 2 UI implementation)**: This is why implementing the explicit **Import/Export Buttons** is so crucial! When the user clicks `1702.9090` in the dropdown, the UI requires them to have selected a stance:
   - *Example A*: Pakistani User has the **"Import (Find Suppliers)"** button selected. They click `1702.9090`. The backend searches for `TradeType = IMPORT`.
   - *Example B*: Pakistani User has the **"Export (Find Buyers)"** button selected. They click `1702.9090`. The backend searches for `TradeType = IMPORT` where `Destination = Pakistan` (or whatever the reverse logic demands).
3. **The UX Fallback (Tabbed Navigation)**: If we don't force a button selection *before* they search, the Results Page itself will have two main tabs at the top: **[View Foreign Suppliers]** and **[View Foreign Buyers]**. The user clicks standard `1702.9090`, lands on the page, and toggles between who they want to see, which triggers the specific API filtering.

---

## 4. Frontend Perspective: Is it a nightmare?

**The short answer:** No, it is not a nightmare, but it requires a completely new UI component for the search bar. 

### Why it's not a nightmare:
You **DO NOT** need to build multiple new screens! 
Instead of navigating the user to `Screen A` then `Screen B` then `Screen C`, you handle this entirely within a **Dynamic Search Dropdown (Popup Menu)** attached to the search bar.

### How it would look in React:
1. **The Search Bar:** User types `17`.
2. **The Dropdown (Step 1):** A custom dropdown menu opens seamlessly under the search bar displaying `1700, 1702, 1703`.
3. **The Dropdown (Step 2):** User clicks `1702` *inside the dropdown*. The dropdown does not close; instead, its content *slides* or *replaces* to show the next tier: `1702.1900`, `1702.9090`. 
4. **The Trigger:** The user clicks `1702.9090`. The dropdown finally closes, and the app redirects to the standard "Matched Products" results screen.

### Frontend Technical Requirements:
*   **Cascading State:** React needs to track `currentHsDepth` (e.g., are we looking at 2-digit, 4-digit, or 6-digit codes?).
*   **Debounced API Fetching:** As the user types `17` -> `170` -> `1702...`, React must fire tiny API requests to fetch the next branch of numbers without lagging the UI.
*   **Back Button in Dropdown:** If a user clicks `1702` but realizes they meant `1703`, the dropdown needs a tiny `< Back` button so they don't have to delete their text and start over.

---

## 5. Difficulty Assessment

**Overall Difficulty: 🟡 MEDIUM**

*   **Backend (Difficulty: 🟢 LOW):** Just one new endpoint (`/api/search/hs-code-tree/`) that accepts a string (e.g., `"170"`) and returns the immediate child nodes based on the HS mapping table.
*   **Frontend (Difficulty: 🟡 MEDIUM-HIGH):** Building a slick, multi-level "Cascading Popup" attached to an input field is moderately tricky. It requires managing focus, managing click-outside-to-close events, and ensuring smooth transitions between the tiers. However, UI libraries (like Material-UI, AntDesign, or Radix UI) have "Cascading Menu" components that can significantly speed this up.

### Verdict
It is incredibly viable. It solves the exact problem of narrowing down a massive HS tree without forcing the user to load heavy analytics screens prematurely. It keeps the heavy lifting strictly inside an intelligent dropdown menu.
