from django.db import models


class TradeLensProduct(models.Model):
    """Products available in Trade Lens dashboard - Isolated for easy deletion"""
    name = models.CharField(max_length=255)
    hs_code = models.CharField(max_length=20)
    category = models.CharField(max_length=100)
    image_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Trade Lens Product'
        verbose_name_plural = 'Trade Lens Products'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.hs_code})"


class TradeLensTransaction(models.Model):
    """Isolated dummy transaction data for Trade Lens visualizations"""
    TRADE_TYPE_CHOICES = [
        ('IMPORT', 'Import'),
        ('EXPORT', 'Export'),
    ]

    product = models.ForeignKey(
        TradeLensProduct,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    trade_date = models.DateField()
    price_usd = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_mt = models.DecimalField(max_digits=12, decimal_places=2)
    total_value_usd = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    buyer_name = models.CharField(max_length=255)
    seller_name = models.CharField(max_length=255)
    buyer_country = models.CharField(max_length=100)
    seller_country = models.CharField(max_length=100)
    
    port = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    trade_type = models.CharField(max_length=10, choices=TRADE_TYPE_CHOICES)
    hs_code = models.CharField(max_length=20)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Trade Lens Transaction'
        verbose_name_plural = 'Trade Lens Transactions'
        ordering = ['-trade_date']
        indexes = [
            models.Index(fields=['product', 'trade_date']),
            models.Index(fields=['buyer_country']),
            models.Index(fields=['seller_country']),
            models.Index(fields=['port']),
            models.Index(fields=['province']),
            models.Index(fields=['trade_type']),
        ]

    def save(self, *args, **kwargs):
        self.total_value_usd = self.price_usd * self.quantity_mt
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} | {self.trade_date} | {self.trade_type}"
