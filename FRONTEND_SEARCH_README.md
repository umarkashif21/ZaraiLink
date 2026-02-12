# Frontend Search Module - Developer Guide

This module implements the UI for the Unified Search Dashboard.

## 1. Directory Structure

Location: `frontend/src/components/Search/`

*   **SearchHome.js**: Main landing page with hero search bar and intent pills.
*   **SearchResults.js**: Displays list of suppliers, filters, and market snapshot.
*   **DealDetail.js**: Detailed view of a supplier with sparklines, history table, and comparables.

## 2. API Service

Location: `frontend/src/services/searchService.js`

*   `search(query)`: Calls `GET /api/search/query/`
*   `getSupplierDetails(name, query)`: Calls `GET /api/search/supplier-detail/`

It uses `frontend/src/services/api.js` (Axios) for requests, which handles base URL and credentials.

## 3. Key Dependencies

*   `react-router-dom`: For navigation (`/search`, `/search/results`, `/search/supplier/:name`).
*   `lucide-react`: For icons (Search, Filter, BarChart2, etc.).
*   `recharts`: For the sparkline charts in `DealDetail.js`.
*   `tailwindcss`: For styling (standard throughout the app).

## 4. How to Test

1.  **Login** to the application (Routes are protected).
2.  Navigate to `/search` (or click "Unified Search" if added to nav).
3.  **Search**: Type "dextrose" or click "I want to buy".
4.  **Results**: You should see supplier cards. Click "View Deal".
5.  **Detail**: You should see the sparkline chart and transaction history.

## 5. Adding Filters

To implement the filters in `SearchResults.js`:
1.  Update the `search` API to accept filter params (e.g. `country=China`).
2.  Update `SearchResults.js` to manage filter state and pass it to `searchService.search`.
