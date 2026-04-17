# ZaraiLink Performance & Feature Roadmap

This document evaluates the proposed architectural and functional updates for the ZaraiLink platform, providing a technical breakdown of difficulty, impact, and the recommended implementation sequence.

---

## 1. Feature Evaluation

### A. Token-Based Access (The Monetization Engine)
*   **Goal**: Implement a "Freemium" model where core directories are visible, but granular trade data (Price, Volume, Analytics) is locked behind a token paywall.
*   **Difficulty**: 🟡 **MEDIUM-HIGH**
*   **Backend Requirement**: 
    - Create an `UnlockedInsight` tracking table to map `(User, ProductItem)` pairs.
    - Implement a decorator or middleware for analytics endpoints to check for an "Unlocked" state.
*   **Frontend Requirement**: 
    - UI "Blur" overlays for sensitive data table rows and charts.
    - "Unlock with [X] Tokens" CTA button.
*   **Impact**: 🚀 **CRITICAL**. This is the core revenue driver for the platform and dictates how all other data is served.

### A. HS Code Drill-Down & Advanced Search
*   **Goal**: Implement a "numerical fast-path" that allows users to drill down from broad categories (17) to specific HS codes (1702.9090) via a cascading dropdown.
*   **Difficulty**: 🟡 **MEDIUM**
*   **Impact**: 🚀 **CRITICAL**. This is the highest-utility feature for industry power users. It simplifies the discovery process and ensures 100% precision before the user ever hits an analytics page.

### B. Trade Direction UI Refactor (Import/Export Buttons)
### D. Module & Page Consolidation (The "Unified Insight" Page)
*   **Goal**: Remove standalone "Trade Lens" and "Trade Ledger" modules. Consolidate their metrics into a 4-tabbed "Company/Product Details" page.
*   **Difficulty**: 🔴 **HIGH**
*   **Complexity**: Massive structural refactor. Moving complex Chart.js and transaction table components from independent routes into sub-tabs of a single view.
*   **Impact**: 🚀 **HIGH**. Dramatically cleans up the sidebar navigation and improves user retention by keeping intelligence in one place.

---

## 2. Recommended Implementation Order

To ensure technical stability and business value, the updates should be executed in this sequence:

| Phase | Feature | Rationale |
| :--- | :--- | :--- |
| **Phase 1** | **HS Code Drill-Down** | **The Discovery Win.** By fixing search first, we ensure the user can actually find the specific data they want to pay for. This provides immediate "Aha!" value. |
| **Phase 2** | **Trade Direction UI** | **The Perspective Fix.** This clarifies exactly who the "Buyers" and "Suppliers" are based on the user's location, ensuring the logic is 100% correct before we lock anything down. |
| **Phase 3** | **Token-Based Access** | **The Monetization Layer.** Now that users can find exactly what they want (Phase 1) and understand the direction of trade (Phase 2), we apply the paywall to the high-value insights. |
| **Phase 4** | **Module Consolidation** | **The Final UX Polish.** Once discovery, logic, and payment are working, we merge the modules into a single, unified "Intelligence Snapshot" page. |

---

## 3. Technical Precautions
*   **Data Integrity**: When implementing the paywall, ensure that "Top-Level" data (Company Name, Country) remains indexed by search engines to maintain SEO, while only "Computed Data" (Weighted Price) is obscured.
*   **Token Deductions**: Implement transaction atomicity in the backend `deduct_tokens` method to prevent double-charging or negative balances during concurrent requests.
