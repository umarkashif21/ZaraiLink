# ZaraiLink Project - Complete SRS Analysis

## 🎯 **Project Overview**

**ZaraiLink** is an AI-driven agricultural trade intelligence platform designed to strengthen data-driven decision-making within Pakistan's agri-business ecosystem.

### **Core Purpose:**
Bridge information gaps by integrating verified customs and trade data from Pakistan Agriculture Research (PAR), enabling users to access actionable insights on exports, imports, and domestic market trends across the agricultural supply chain.

---

## 📦 **System Modules**

### **1. TradeLens – Market Intelligence**
- Export and import market insights for commodities
- Interactive visualizations: export volumes, top destinations, price trends
- Customized analytical reports based on PAR dashboards
- Data export in PDF and Excel formats
- KPIs: trade volume, average price, top buyers/sellers, country-wise shares
- Dynamic filters for year, month, country, commodity selection

### **2. TradeLedger – Company Analytics**
- Verified company transaction data
- Partner companies and export/import relationships visualization
- Trade volumes, frequency, trading partners analysis
- Company comparison features (side-by-side analysis)
- Partner diversity scoring
- Performance benchmarking across companies

### **3. TradePulse – Alerts & Market Events**
- Real-time intelligence feed
- Continuous monitoring of trade and pricing data
- Graph Neural Networks (GNNs) for anomaly detection
- Notifications for:
  - Sudden price spikes or drops
  - Policy changes or export restrictions
  - Market disruptions affecting supply/demand
- Categorized alerts (high, medium, low severity)
- News scraping from verified agricultural and trade sources

### **4. Trade Directory**
- Verified agricultural business directory sourced from PAR
- Search by product, HS code, or region
- Verified company profiles with trade data and contact information
- **Token-based access system** for unlocking key contacts
- Bookmark preferred companies or markets
- Advanced filtering and search capabilities

### **5. AI Chatbot Assistant (ZaraiBot)**
- Conversational AI interface for natural language queries
- Query handling for trade analytics, company lookup, partner recommendations
- Dynamic fetching from TradeLens, Ledger, and Directory databases
- Responses with text summaries, visual previews, and dashboard links
- Examples:
  - "Show sugar export trends in 2024"
  - "Which companies are importing wheat in Karachi?"

---

## 🎨 **UI/UX Design Specifications**

### **Design Philosophy:**
Modern, clean, data-focused interface prioritizing **clarity, usability, and performance**

### **Color Scheme (from wireframes):**

**Primary Colors:**
- **Green accents** - Agricultural theme, growth indicators (▲ symbols)
- **White/Light backgrounds** - #FFFFFF for main content areas
- **Dark text** - #000000 or #1A1A1A for primary text
- **Blue for links/actions** - Standard hyperlink blue

**Status Colors:**
- **Green** - Positive metrics, growth indicators (▲ +18%)
- **Red** - Negative metrics, declines (▼ -5%)
- **Neutral gray** - Borders, dividers, secondary information

**Semantic Colors:**
- Alerts use severity levels (high/medium/low)
- Price trends shown with green (up) and red (down)

### **Typography:**

**Font Family:**
- Clean, modern sans-serif font (likely Inter, Roboto, or similar)
- Professional, highly readable across all screen sizes

**Text Hierarchy:**
- **Large headers** - Company names, module titles
- **Medium subheaders** - Section titles, metrics labels
- **Small body text** - Data values, descriptions
- **Monospace** - Numbers, data values, prices (e.g., "$6.27M", "1.2M MT")

**Font Weights:**
- **Bold** - Headlines, key metrics, CTAs
- **Regular** - Body content, data labels
- **Light** - Secondary information, metadata

### **Layout Principles:**

**Navigation:**
- **Top navbar:** Sticky header with
  - ZaraiLink logo (left)
  - Main nav menu: Home | Trade Network ▼ | Trade Intelligence | Subscription
  - User profile badge (right) with initials (e.g., "FN")
  
**Content Structure:**
- **Card-based layouts** - Individual data cards with white backgrounds
- **Data tables** - Striped rows, clear column headers
- **Sidebar filters** - Left-aligned filter panels
- **Dashboard grids** - Multi-column metric cards

**Components:**
- **Dropdown menus** with ▼ indicators
- **Action buttons:** "View Analysis", "Unlock Contact", "Compare"
- **Badges:** "Popular", "New", verification status
- **Icons:** Social icons, arrow indicators (▲▼), close buttons (✕)

### **Spacing & Alignment:**
- Generous white space around content blocks
- Consistent padding in cards and tables
- Grid-based layouts for data presentation
- Clear visual separation between sections

---

## 📊 **Key UI Screens (from wireframes)**

### **1. Dashboard**
- Personalized view with access to all modules
- Saved searches, bookmarked companies, recent analytics
- Activity feed with market alerts
- Quick access cards to each module

### **2. Trade Directory**
- Search bar with filters (product, region, HS code)
- Company listing grid/table with:
  - Company name
  - Total volume, avg price, active partners
  - YoY growth % with colored indicators
- "View Profile" CTAs

### **3. Company Profile (Multi-tab)**
**Tabs:** Overview | Products | Partners | Trends

**Overview Tab:**
- Key metrics in card format:
  - Est. Revenue (USD/PKR toggle)
  - Total Volume (MT)
  - Active Partners
  - YoY Volume Growth
- Top 3 Traded Products (percentage breakdown)
- Top Importing/Exporting Countries (percentage)
- Recent Activity summary

**Products Tab:**
- Table of products with:
  - Product name
  - Total volume
  - Avg price
  - YoY change % (with ▲▼ indicators)
- Price trend charts
- Volume distribution pie chart

**Partners Tab:**
- Partner diversity score (0-1 scale)
- Top exporting countries with volume share
- Volume share by country visualization
- Top ports of entry

**Trends Tab:**
- Monthly volume vs avg price line chart
- YoY volume growth by quarter bar chart
- Key trend summary bullets

### **4. TradePulse Feed**
- Article/alert cards with:
  - Headline
  - Source and date
  - Tags (product, price, country, policy)
  - Summary section
  - "Why it matters" section
  - Market impact analysis
  - Related dashboard links
- Action buttons: Save | Subscribe | Download | Share

### **5. Subscription Page**
- Pricing tiers in cards: Starter | Standard (Popular) | Ultimate
- Credits per month displayed prominently
- PKR pricing with /mo suffix
- Feature checkmarks
- "Redeem" CTAs
- Monthly/Yearly toggle

---

## 🔧 **Technical Stack**

### **Frontend:**
- React.js
- Charting libraries (Plotly, likely Chart.js or D3.js)
- Responsive design (mobile + web)
- Urdu and English language support

### **Backend:**
- Python + FastAPI
- RESTful APIs
- PostgreSQL (relational data)
- Neo4j (graph-based GNN storage)

### **AI/ML:**
- Graph Neural Networks (GNNs) for:
  - Anomaly detection
  - Partner recommendations
  - Trade pattern discovery
- Hugging Face Transformers, PyTorch, NLTK (chatbot)

### **Data Processing:**
- Pandas, NumPy (data cleaning)
- BeautifulSoup, Requests (web scraping)
- Power BI integration for dashboards

### **Deployment:**
- Docker containerization
- AWS cloud hosting
- 99.9% uptime target
- Daily backups

---

## 🎯 **Design Consistency Rules**

1. **Data Presentation:**
   - All numbers formatted with commas (1,200,000)
   - Prices show currency (USD/PKR with toggle)
   - Percentages show +/- with ▲▼ indicators
   - Units clearly labeled (MT for metric tons, USD/MT for price per unit)

2. **Interactive Elements:**
   - Hover states for cards and buttons
   - Active states for selected filters
   - Loading states for async data
   - Clear CTAs with action verbs

3. **Accessibility:**
   - High contrast for readability
   - Clear focus states
   - Simplified navigation
   - Bilingual support (Urdu/English)

4. **Performance:**
   - Dashboard loads within 2-3 seconds
   - GNN recommendations within 5 seconds
   - Supports 15,000+ concurrent users

---

## 📝 **Key Business Features**

1. **Token-Based Monetization** ⭐
   - Contact unlocking uses credit/token system
   - Subscription tiers with monthly credit allocations
   - Starter: 600 credits/month (PKR 9)
   - Standard: 12k credits/month (PKR 32)
   - Ultimate: 60k credits/month (PKR 99)

2. **Verified Data Sources**
   - PAR (Pakistan Agriculture Research) partnership
   - Customs import-export data (Jan 2022 – Sep 2025)
   - Verified company directory
   - All revenue estimates based on customs declarations

3. **Personalization**
   - User dashboards adapt to behavior (importer/exporter patterns)
   - Saved analyses and followed topics
   - Notification preferences
   - Bookmarked companies

4. **GNN-Powered Intelligence**
   - Hidden trade relationship discovery
   - Buyer-supplier recommendations
   - Anomaly detection in trade flows
   - Market opportunity identification

---

## 🎨 **Visual Identity Summary**

**Brand Feel:** Professional, data-driven, agricultural, trustworthy

**UI Style:** Clean, modern, card-based, metric-focused

**Colors:** Green (agriculture/growth) + White (clean) + Dark text (professional)

**Typography:** Sans-serif, clear hierarchy, monospace for numbers

**Interactions:** Smooth, responsive, data-rich tooltips

**Tone:** Authoritative yet accessible, informative without overwhelming

---

## ✅ **Implementation Takeaways**

This matches EXACTLY what we've been building:
- ✅ Token-based contact unlocking (Trade Directory)
- ✅ Company profiles with analytics
- ✅ Django backend + React frontend
- ✅ PostgreSQL database
- ✅ Subscription/credit system
- ✅ User authentication and personalization

The SRS confirms our current implementation direction is perfectly aligned with the project vision!
