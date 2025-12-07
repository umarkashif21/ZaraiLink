from django.db import models


class HsToProductMap(models.Model):
    hs_code = models.CharField(max_length=50)
    product_name = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'HS to Product Map'
        verbose_name_plural = 'HS to Product Maps'
        ordering = ['hs_code']
        indexes = [
            models.Index(fields=['hs_code']),
        ]

    def __str__(self):
        return f"{self.hs_code} -> {self.product_name}"



# -------------------
# Product hierarchy
# -------------------
class Product(models.Model):
    name = models.CharField(max_length=1000)         # e.g., "Sugar"
    hs_code = models.CharField(max_length=10, unique=True)  # e.g., "17"

    def __str__(self):
        return f"{self.name} ({self.hs_code})"


class ProductCategory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=1000)         # e.g., "Other sugars"
    hs_code = models.CharField(max_length=10, unique=True)  # e.g., "17.02"

    def __str__(self):
        return f"{self.name} ({self.hs_code})"


class ProductSubCategory(models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name="sub_categories")
    name = models.CharField(max_length=1000)         # e.g., "Glucose and glucose syrup"
    hs_code = models.CharField(max_length=50, unique=True)  # e.g., "1702.3000"

    def __str__(self):
        return f"{self.name} ({self.hs_code})"


class ProductItem(models.Model):
    sub_category = models.ForeignKey(ProductSubCategory, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=1000)         # e.g., "Dextrose Anhydrous"

    def __str__(self):
        return self.name


# -------------------
# Transaction model
# -------------------
class Transaction(models.Model):
    """Raw import/export transaction records"""
    id = models.BigAutoField(primary_key=True)
    source_file = models.CharField(max_length=500)
    tx_reference = models.CharField(max_length=500)
    reporting_date = models.DateField()  
    hs_code = models.CharField(max_length=50)  # keep raw HS code for reference
    product_item = models.ForeignKey(ProductItem, on_delete=models.SET_NULL, null=True, blank=True)
    buyer = models.CharField(max_length=500)
    seller = models.CharField(max_length=500)
    shipping_agent = models.CharField(max_length=500)
    country = models.CharField(max_length=100)
    qty_kg = models.DecimalField(max_digits=20, decimal_places=6)
    qty_mt = models.DecimalField(max_digits=20, decimal_places=6)
    usd_per_kg = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    usd_per_mt = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    pkr = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True)
    usd = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True)
    trade_type = models.CharField(max_length=10)
    std_unit = models.CharField(max_length=20, default="MT")
    created_at = models.DateTimeField(auto_now_add=True)
    ingested_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-reporting_date']
        indexes = [
            models.Index(fields=['reporting_date']),
            models.Index(fields=['buyer']),
            models.Index(fields=['seller']),
            models.Index(fields=['hs_code']),
        ]

    def __str__(self):
        item_name = self.product_item.name if self.product_item else "Unknown Item"
        return f"{self.buyer} -> {self.seller} ({item_name} | {self.reporting_date})"


class AggProductMonthCountry(models.Model):
    """Pre-computed product trade statistics by month and country"""
    product = models.ForeignKey(
        'companies.Sector',
        on_delete=models.CASCADE,
        related_name='monthly_country_aggregations'
    )
    year = models.IntegerField()
    month = models.IntegerField()
    country = models.CharField(max_length=100)
    total_quantity = models.DecimalField(
        max_digits=30,
        decimal_places=6,
        default=0
    )
    avg_price_usd = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True
    )
    total_value_usd = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Agg Product Month Country'
        verbose_name_plural = 'Agg Product Month Country'
        ordering = ['-year', '-month']
        indexes = [
            models.Index(fields=['product', 'year', 'month', 'country']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.year}/{self.month:02d} - {self.country}"


class AggCompanyMonthProduct(models.Model):
    """Pre-computed company trade statistics by month and product"""
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='monthly_product_aggregations'
    )
    product = models.ForeignKey(
        'companies.Sector',
        on_delete=models.CASCADE,
        related_name='company_monthly_aggregations'
    )
    year = models.IntegerField()
    month = models.IntegerField()
    total_quantity = models.DecimalField(
        max_digits=30,
        decimal_places=6,
        default=0
    )
    avg_price_usd = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True
    )
    total_value_usd = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Agg Company Month Product'
        verbose_name_plural = 'Agg Company Month Product'
        ordering = ['-year', '-month']
        indexes = [
            models.Index(fields=['company', 'product', 'year', 'month']),
        ]

    def __str__(self):
        return f"{self.company.name} - {self.product.name} - {self.year}/{self.month:02d}"
    
    


#GNN EMBEDDINGS


class CompanyEmbedding(models.Model):
    company_name = models.CharField(max_length=500, unique=True)
    embedding = models.JSONField()  # ✅ Built-in JSONField (works with PostgreSQL)
    cluster_tag = models.CharField(max_length=100, blank=True)
    pagerank = models.FloatField(default=0.0)
    degree = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Company Embedding'
        verbose_name_plural = 'Company Embeddings'

    def __str__(self):
        return f"{self.company_name} → {self.cluster_tag}"


class ProductEmbedding(models.Model):
    product_item = models.ForeignKey(ProductItem, on_delete=models.CASCADE)
    embedding = models.JSONField()  # ✅ Built-in JSONField
    cluster_tag = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product Embedding'
        verbose_name_plural = 'Product Embeddings'
        unique_together = ['product_item']

    def __str__(self):
        return f"{self.product_item.name} → {self.cluster_tag}"