# System Design Specification: Database Architecture

## 1. Indexes and Optimization

To ensure sub-second retrieval performance across high-volume agricultural trade data, the system implements a rigorous database optimization strategy relying on PostgreSQL's advanced indexing structures and Django ORM configurations.

### 1.1 Foreign Key Indexing Strategy
*   **Automatic B-Tree Indexing:** Every relational mapping (e.g., `company_id`, `product_id`, `sector_id`) generated via Django's `ForeignKey` and `OneToOneField` constructs is automatically backed by a B-Tree index. This optimizes spatial locality for `JOIN` operations across massive tables like `TradeProduct` and `TradeCompany`.
*   **Vector and Trigram Indices:** For full-text search fallbacks, `pg_trgm` indices are utilized on text fields (e.g., `Company.name`, `ProductCategory.name`) to accelerate `ILIKE` clauses and fuzzy matching operations prior to semantic vector resolution.

### 1.2 Composite Indexes
For complex querying involving multiple attributes, composite indices minimize the query planner's scan time. Key implementations and provisions include:
*   **Geospatial & Taxonomy Routing:** `models.Index(fields=['country', 'sector'])` is implemented on the `Company` entity, dramatically reducing query space when users filter the directory for specific regional suppliers within an agricultural niche.
*   **Trade Analytics Aggregation (Proposed/Active):** An index on `(company_id, metric_date)` within analytical caching tables optimizes time-series charting.
*   **Transactional Uniqueness:** The `TradeTrend` model enforces `unique_together = ['company', 'product', 'month', 'year']`, which inherently creates a highly discriminant composite index, significantly accelerating monthly aggregate fetching.

### 1.3 Data Types Optimization
*   **Financial & Volumetric Precision:** Floating-point approximations are strictly avoided. All monetary values (`avg_price`, `estimated_revenue`) and physical trade volumes (`volume`) utilize `DecimalField(max_digits=15, decimal_places=2)` to ensure absolute arithmetic integrity and prevent rounding degradation.
*   **Binary Identifiers:** Security-critical fields such as `verification_token` employ native `UUIDField` rather than variable character strings, minimizing index depth and storage footprint.
*   **Categorical Encoding:** Repeated bounded datasets (e.g., specific dates, transaction types) favor `IntegerField` or predefined `CharField` choices over arbitrary text allocations to optimize tuple size.

### 1.4 Default Timestamp Strategy
*   **Automated Temporal Tracking:** The system enforces programmatic timestamping via `@auto_now_add=True` (`created_at`) and `@auto_now=True` (`updated_at`) attributes. This relegates the computational burden of temporal tracking from the application layer down to the underlying database engine level, ensuring timestamp manipulation cannot occur maliciously or accidentally outside of database lifecycle hooks.

---

## 2. Data Integrity and Validation

Ensuring the absolute fidelity of trade records and intelligence metrics is critical. The design incorporates a defense-in-depth architecture applying strict constraints at the relational layer.

### 2.1 Relational Constraints
*   **Foreign Key Constraints:** Referential integrity is structurally enforced. A `TradePartner` row intrinsically cannot exist without an overarching `TradeCompany` reference.
*   **Unique Constraints:** System-wide uniqueness is defined at the schema level avoiding race conditions. `User.email` guarantees unique credentialing, `RedeemCode.code` prevents concurrent voucher exploitation, and composite constraints (e.g., `User` + `KeyContact`) prevent double-deduction of intelligence tokens.

### 2.2 Field-Level Rules and Nullability
*   **Required vs. Nullable Boundaries:** Mandatory operational fields (e.g., `Company.country`, `TradeProduct.volume`) are mandated `null=False`. Fields representing progressive profile refinement (e.g., `phone_number`, `website`) are flagged `blank=True, null=True`, strictly bifurcating core operational capability from aesthetic completeness.
*   **Backend Validation Rules:** Enforced logic prevents corrupt data instantiation. `DecimalFields` inherently reject un-parseable numerics, whereas custom application-layer validations throw `ValidationError` if token balances fall below required operation thresholds. Positive constraints ensure physical trade metrics (Volume, Price) remain logically sound.

### 2.3 Cascading and Deletion Policies
*   **Hard Cascades (`CASCADE`):** Strong-coupled dependencies employ strict logical cascades. If a user deletes their account, their `UserAlertPreference` and `KeyContactUnlock` logs are forcefully wiped from the PostgreSQL instance to maintain GDPR compliance and schema cleanliness.
*   **Nullification Shelters (`SET_NULL`):** Weakly-coupled categorizations (e.g., removing a `Sector` or a `SubscriptionPlan`) do not delete the parent `Company` or User payment history. Instead, the pointer is gracefully set to `NULL`, preserving the integrity of historical logs and enterprise analytical data.

---

## 3. Scalability Considerations

As ZaraiLink ingests international shipping records and generates link-prediction models (GNN architectures), the database is tuned to scale horizontally and structurally.

### 3.1 Normalization Architecture
*   **Third Normal Form (3NF):** The core schema separates `Company` (core entity) from `TradeCompany` (extended metrics) and `KeyContact` (privacy-gated entity). By compartmentalizing discrete data domains, atomic updates occur without enforcing locks across the entire organizational profile, drastically reducing deadlock conditions during intensive concurrent web traffic.

### 3.2 Indexing Strategy for Large Datasets
*   **Selective Indexing Policies:** As the ledger grows to account for millions of specific `TradeProduct` entries, index bloat is minimized. Indices are restricted solely to cardinality-rich WHERE clauses (`hs_code`, `buyer_country`). Over-indexing write-heavy transaction tables is strictly avoided to maintain ingestion velocity.

### 3.3 High-Volume Transaction Handling & Caching
*   **Redis Caching Protocol:** High-read, computationally expensive views (e.g., Top 10 Buyer Leaderboards, NLU Intent results) circumvent the PostgreSQL engine entirely. Configured via `django_redis.cache.RedisCache`, responses are serialized, hashed via MD5, and served directly from memory, shielding the primary DB from redundant API calls.
*   **Query Optimization Techniques:** Utilizing Django's `select_related()` and `prefetch_related()` functions guarantees that hierarchical datasets (e.g., pulling a Company alongside all of its TradeProducts) compile into optimized single-sweep SQL `JOIN`s, eradicating the severe latency of N+1 query loops.

### 3.4 Future-Proofing and Partitioning Strategies
As data velocity exceeds threshold capacity, the monolithic table architecture will securely pivot toward declarative table partitioning features inherent in PostgreSQL:
*   **Temporal Partitioning (By Date):** Because intelligent trade analysis prioritizes recent data (e.g., preceding 36 months), historic raw `TradeLedger` data can be horizontally partitioned by year via PostgreSQL list partitioning, allowing cold-storage archival of obsolete data without sacrificing real-time analytical performance.
*   **Geographic Partitioning (By Country):** If system utilization isolates regionally (e.g., Asian markets vs. EU markets), list-based partition mapping on the `country` key will prevent index depth degradation and permit localized data residency compliance.
