# ZaraiLink Database Design

### User
**App Context**: `accounts`
User(id, password, last_login, is_superuser, first_name, last_name, is_staff, is_active, date_joined, email, username, bio, country, email_verified, verification_token, token_created_at, phone_number, job_title, token_balance)

**Attributes:**
- `id` (BigAutoField) — Primary key
- `password` (CharField)
- `last_login` (DateTimeField) — Nullable
- `is_superuser` (BooleanField)
- `first_name` (CharField)
- `last_name` (CharField)
- `is_staff` (BooleanField)
- `is_active` (BooleanField)
- `date_joined` (DateTimeField)
- `email` (EmailField) — Unique
- `username` (CharField) — Nullable
- `bio` (CharField)
- `country` (CharField) — Nullable
- `email_verified` (BooleanField)
- `verification_token` (UUIDField) — Unique
- `token_created_at` (DateTimeField)
- `phone_number` (CharField) — Nullable
- `job_title` (CharField) — Nullable
- `token_balance` (IntegerField)
- `groups` (ManyToManyField) — Foreign key to Group
- `user_permissions` (ManyToManyField) — Foreign key to Permission

**Relationships:**
- One-to-Many with LogEntry
- One-to-Many with UserSubscription
- One-to-Many with TokenPurchase
- One-to-Many with RedeemCode
- One-to-Many with KeyContactUnlock
- Many-to-Many with Group
- Many-to-Many with Permission

---

### SubscriptionPlan
**App Context**: `subscriptions`
Subscription plan tiers with pricing and token allocations

**Attributes:**
- `id` (BigAutoField) — Primary key
- `plan_name` (CharField)
- `price` (DecimalField)
- `currency` (CharField)
- `tokens_included` (IntegerField)
- `description` (TextField)
- `features` (JSONField)
- `created_at` (DateTimeField)
- `updated_at` (DateTimeField)

**Relationships:**
- One-to-Many with UserSubscription
- One-to-Many with TokenPurchase
- One-to-Many with RedeemCode

---

### UserSubscription
**App Context**: `subscriptions`
User's active subscription

**Attributes:**
- `id` (BigAutoField) — Primary key
- `user` (ForeignKey) — Foreign key to User
- `plan` (ForeignKey) — Foreign key to SubscriptionPlan
- `status` (CharField)
- `start_date` (DateField)
- `end_date` (DateField)
- `billing_cycle` (CharField)
- `created_at` (DateTimeField)

**Relationships:**
- Many-to-One with User
- Many-to-One with SubscriptionPlan

---

### TokenPurchase
**App Context**: `subscriptions`
Standalone token purchases (beyond subscription)

**Attributes:**
- `id` (BigAutoField) — Primary key
- `user` (ForeignKey) — Foreign key to User
- `plan` (ForeignKey) — Nullable, Foreign key to SubscriptionPlan
- `tokens_purchased` (IntegerField)
- `price` (DecimalField)
- `currency` (CharField)
- `payment_provider` (CharField)
- `payment_reference` (CharField)
- `purchased_at` (DateTimeField)

**Relationships:**
- Many-to-One with User
- Many-to-One with SubscriptionPlan

---

### RedeemCode
**App Context**: `subscriptions`
Redeemable codes for subscription plans
Replaces payment processing for MVP/testing

**Attributes:**
- `id` (BigAutoField) — Primary key
- `code` (CharField) — Unique
- `plan` (ForeignKey) — Foreign key to SubscriptionPlan
- `status` (CharField)
- `redeemed_by` (ForeignKey) — Nullable, Foreign key to User
- `created_at` (DateTimeField)
- `redeemed_at` (DateTimeField) — Nullable
- `expires_at` (DateTimeField) — Nullable

**Relationships:**
- Many-to-One with SubscriptionPlan
- Many-to-One with User

---

### Sector
**App Context**: `companies`
Product categories/sectors (e.g., Rice, Wheat, Cotton)

**Attributes:**
- `id` (BigAutoField) — Primary key
- `name` (CharField)
- `description` (TextField)

**Relationships:**
- One-to-Many with Company

---

### CompanyRole
**App Context**: `companies`
Company's role in trade (Supplier, Buyer, etc.)

**Attributes:**
- `id` (BigAutoField) — Primary key
- `name` (CharField)
- `description` (TextField)

**Relationships:**
- One-to-Many with Company

---

### CompanyType
**App Context**: `companies`
Legal/structural company classification

**Attributes:**
- `id` (BigAutoField) — Primary key
- `name` (CharField)
- `description` (TextField)

**Relationships:**
- One-to-Many with Company

---

### Company
**App Context**: `companies`
Core company profile in trade directory

**Attributes:**
- `id` (BigAutoField) — Primary key
- `name` (CharField)
- `legal_name` (CharField)
- `description` (TextField)
- `country` (CharField)
- `province` (CharField)
- `district` (CharField)
- `address` (TextField)
- `market_sentiment` (CharField)
- `website` (URLField)
- `contact_email` (EmailField)
- `phone` (CharField)
- `year_established` (IntegerField) — Nullable
- `number_of_employees` (CharField)
- `horeca_retail_info` (CharField)
- `verification_status` (CharField)
- `ntn_number` (CharField)
- `trade_license_number` (CharField)
- `sector` (ForeignKey) — Nullable, Foreign key to Sector
- `company_role` (ForeignKey) — Nullable, Foreign key to CompanyRole
- `company_type` (ForeignKey) — Nullable, Foreign key to CompanyType
- `has_trade_data` (BooleanField)
- `is_directory_profile` (BooleanField)
- `created_at` (DateTimeField)
- `updated_at` (DateTimeField)

**Relationships:**
- One-to-Many with CompanyProduct
- One-to-Many with KeyContact
- Many-to-One with Sector
- Many-to-One with CompanyRole
- Many-to-One with CompanyType

---

### CompanyProduct
**App Context**: `companies`
Products/commodities offered by companies

**Attributes:**
- `id` (BigAutoField) — Primary key
- `company` (ForeignKey) — Foreign key to Company
- `name` (CharField)
- `description` (TextField)
- `variety` (CharField)
- `value_added` (CharField)
- `hsn_code` (CharField)
- `created_at` (DateTimeField)
- `updated_at` (DateTimeField)

**Relationships:**
- Many-to-One with Company

---

### KeyContact
**App Context**: `companies`
Private contact information for companies

**Attributes:**
- `id` (BigAutoField) — Primary key
- `company` (ForeignKey) — Foreign key to Company
- `name` (CharField)
- `designation` (CharField)
- `phone` (CharField)
- `whatsapp` (CharField)
- `email` (EmailField)
- `is_public` (BooleanField)
- `created_at` (DateTimeField)
- `updated_at` (DateTimeField)

**Relationships:**
- One-to-Many with KeyContactUnlock
- Many-to-One with Company

---

### KeyContactUnlock
**App Context**: `companies`
Track which users unlocked which contacts

**Attributes:**
- `id` (BigAutoField) — Primary key
- `user` (ForeignKey) — Foreign key to User
- `key_contact` (ForeignKey) — Foreign key to KeyContact
- `unlocked_at` (DateTimeField)

**Relationships:**
- Many-to-One with User
- Many-to-One with KeyContact

---

### HsToProductMap
**App Context**: `trade_data`
HsToProductMap(id, hs_code, product_name, notes, updated_at)

**Attributes:**
- `id` (BigAutoField) — Primary key
- `hs_code` (CharField)
- `product_name` (CharField)
- `notes` (TextField)
- `updated_at` (DateTimeField)

---

### Product
**App Context**: `trade_data`
Product(id, name, hs_code)

**Attributes:**
- `id` (BigAutoField) — Primary key
- `name` (CharField)
- `hs_code` (CharField) — Unique

**Relationships:**
- One-to-Many with ProductCategory

---

### ProductCategory
**App Context**: `trade_data`
ProductCategory(id, product, name, hs_code)

**Attributes:**
- `id` (BigAutoField) — Primary key
- `product` (ForeignKey) — Foreign key to Product
- `name` (CharField)
- `hs_code` (CharField) — Unique

**Relationships:**
- One-to-Many with ProductSubCategory
- Many-to-One with Product

---

### ProductSubCategory
**App Context**: `trade_data`
ProductSubCategory(id, category, name, hs_code)

**Attributes:**
- `id` (BigAutoField) — Primary key
- `category` (ForeignKey) — Foreign key to ProductCategory
- `name` (CharField)
- `hs_code` (CharField)

**Relationships:**
- One-to-Many with ProductItem
- Many-to-One with ProductCategory

---

### ProductItem
**App Context**: `trade_data`
ProductItem(id, sub_category, name)

**Attributes:**
- `id` (BigAutoField) — Primary key
- `sub_category` (ForeignKey) — Foreign key to ProductSubCategory
- `name` (CharField)

**Relationships:**
- One-to-Many with Transaction
- One-to-Many with ProductEmbedding
- Many-to-One with ProductSubCategory

---

### Transaction
**App Context**: `trade_data`
Unified Import/Export Transaction Records

**Attributes:**
- `id` (BigAutoField) — Primary key
- `source_file` (CharField)
- `tx_reference` (CharField)
- `reporting_date` (DateField)
- `trade_type` (CharField)
- `hs_code` (CharField)
- `product_item` (ForeignKey) — Nullable, Foreign key to ProductItem
- `buyer` (CharField)
- `seller` (CharField)
- `shipping_agent` (CharField)
- `origin_country` (CharField)
- `destination_country` (CharField)
- `qty_kg` (DecimalField)
- `qty_mt` (DecimalField)
- `usd_per_kg` (DecimalField) — Nullable
- `usd_per_mt` (DecimalField) — Nullable
- `pkr` (DecimalField) — Nullable
- `usd` (DecimalField) — Nullable
- `std_unit` (CharField)
- `created_at` (DateTimeField)
- `ingested_at` (DateTimeField)

**Relationships:**
- Many-to-One with ProductItem

---

### CompanyEmbedding
**App Context**: `trade_data`
CompanyEmbedding(id, company_name, embedding, cluster_tag, pagerank, degree, created_at)

**Attributes:**
- `id` (BigAutoField) — Primary key
- `company_name` (CharField) — Unique
- `embedding` (JSONField)
- `cluster_tag` (CharField)
- `pagerank` (FloatField)
- `degree` (IntegerField)
- `created_at` (DateTimeField)

---

### ProductEmbedding
**App Context**: `trade_data`
ProductEmbedding(id, product_item, embedding, cluster_tag, created_at)

**Attributes:**
- `id` (BigAutoField) — Primary key
- `product_item` (ForeignKey) — Foreign key to ProductItem
- `embedding` (JSONField)
- `cluster_tag` (CharField)
- `created_at` (DateTimeField)

**Relationships:**
- Many-to-One with ProductItem

---

### TradeLensProduct
**App Context**: `trade_lens`
Products available in Trade Lens dashboard - Isolated for easy deletion

**Attributes:**
- `id` (BigAutoField) — Primary key
- `name` (CharField)
- `hs_code` (CharField)
- `category` (CharField)
- `image_url` (URLField) — Nullable
- `description` (TextField)
- `created_at` (DateTimeField)

**Relationships:**
- One-to-Many with TradeLensTransaction

---

### TradeLensTransaction
**App Context**: `trade_lens`
Isolated dummy transaction data for Trade Lens visualizations

**Attributes:**
- `id` (BigAutoField) — Primary key
- `product` (ForeignKey) — Foreign key to TradeLensProduct
- `trade_date` (DateField)
- `price_usd` (DecimalField)
- `quantity_mt` (DecimalField)
- `total_value_usd` (DecimalField)
- `buyer_name` (CharField)
- `seller_name` (CharField)
- `buyer_country` (CharField)
- `seller_country` (CharField)
- `port` (CharField)
- `province` (CharField)
- `trade_type` (CharField)
- `hs_code` (CharField)
- `created_at` (DateTimeField)

**Relationships:**
- Many-to-One with TradeLensProduct

---
