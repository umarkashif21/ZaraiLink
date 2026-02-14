from django.db import models
from auditlog.registry import auditlog


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


# -------------------------
# PRODUCT HIERARCHY
# -------------------------

class Product(models.Model):
    name = models.CharField(max_length=1000)
    hs_code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name} ({self.hs_code})"


class ProductCategory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=1000)
    hs_code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name} ({self.hs_code})"


class ProductSubCategory(models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name="sub_categories")
    name = models.CharField(max_length=1000)
    hs_code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.name} ({self.hs_code})"


class ProductItem(models.Model):
    sub_category = models.ForeignKey(ProductSubCategory, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=1000)

    def __str__(self):
        return self.name


# -------------------------
# TRANSACTION MODEL (UPDATED)
# -------------------------

class Transaction(models.Model):
    """Unified Import/Export Transaction Records"""

    TRADE_TYPE_CHOICES = (
        ("IMPORT", "Import"),
        ("EXPORT", "Export"),
    )

    id = models.BigAutoField(primary_key=True)

    source_file = models.CharField(max_length=500)
    tx_reference = models.CharField(max_length=500)

    reporting_date = models.DateField()

    # Direction of trade
    trade_type = models.CharField(
        max_length=10,
        choices=TRADE_TYPE_CHOICES,
        db_index=True,
        default="IMPORT"
    )

    # Product info
    hs_code = models.CharField(max_length=50)
    product_item = models.ForeignKey(
        ProductItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Companies
    buyer = models.CharField(max_length=500)
    seller = models.CharField(max_length=500)
    shipping_agent = models.CharField(max_length=500)

    # Directional geography (VERY IMPORTANT)
    origin_country = models.CharField(max_length=100, db_index=True, default="Unknown")
    destination_country = models.CharField(max_length=100, db_index=True, default="Unknown")

    # Quantities
    qty_kg = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    qty_mt = models.DecimalField(max_digits=20, decimal_places=6, default=0)

    # Pricing
    usd_per_kg = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    usd_per_mt = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    pkr = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True)
    usd = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True)

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
            models.Index(fields=['trade_type']),
            models.Index(fields=['origin_country']),
            models.Index(fields=['destination_country']),
        ]

    def __str__(self):
        item_name = self.product_item.name if self.product_item else "Unknown Item"
        return (
            f"{self.trade_type} | "
            f"{self.origin_country} → {self.destination_country} | "
            f"{self.buyer} -> {self.seller} "
            f"({item_name} | {self.reporting_date})"
        )


# -------------------------
# EMBEDDINGS
# -------------------------

class CompanyEmbedding(models.Model):
    company_name = models.CharField(max_length=500, unique=True)
    embedding = models.JSONField()
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
    embedding = models.JSONField()
    cluster_tag = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product Embedding'
        verbose_name_plural = 'Product Embeddings'
        unique_together = ['product_item']

    def __str__(self):
        return f"{self.product_item.name} → {self.cluster_tag}"


# -------------------------
# AUDIT LOG
# -------------------------

auditlog.register(Product)
auditlog.register(ProductCategory)
auditlog.register(ProductSubCategory)
auditlog.register(ProductItem)
