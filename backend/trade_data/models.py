from django.db import models


class HsToProductMap(models.Model):
    """Map HS codes to internal product taxonomy"""
    hs_code = models.CharField(max_length=50)
    product = models.ForeignKey(
        'companies.Sector',
        on_delete=models.CASCADE,
        related_name='hs_mappings'
    )
    product_name = models.CharField(max_length=255)
    notes = models.TextField(blank=True, help_text="Additional mapping notes")
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


class Transaction(models.Model):
    """Raw import/export transaction records"""
    source_file = models.CharField(max_length=255)
    tx_reference = models.CharField(max_length=255, blank=True)
    reporting_date = models.DateField()
    reporting_country = models.CharField(max_length=100)
    hs_code = models.CharField(max_length=50)
    product = models.ForeignKey(
        'companies.Sector',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    product_name = models.CharField(max_length=255)
    shipper = models.CharField(max_length=255, blank=True)
    shipper_code = models.CharField(max_length=100, blank=True)
    consignee = models.CharField(max_length=255, blank=True)
    consignee_country = models.CharField(max_length=100, blank=True)
    port_of_origin = models.CharField(max_length=50, blank=True)
    port_of_entry = models.CharField(max_length=50, blank=True)
    std_quantity = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Standardized quantity"
    )
    std_unit = models.CharField(max_length=20, blank=True, help_text="e.g., MT, KG, LBS")
    unit_rate_usd = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Price per unit in USD"
    )
    fob_value_usd = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total FOB value in USD"
    )
    currency = models.CharField(max_length=10, blank=True)
    raw_record = models.JSONField(null=True, blank=True, help_text="Original data as JSON")
    created_at = models.DateTimeField(auto_now_add=True)
    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-reporting_date']
        indexes = [
            models.Index(fields=['reporting_date', 'product']),
            models.Index(fields=['shipper']),
            models.Index(fields=['consignee_country']),
            models.Index(fields=['hs_code']),
        ]

    def __str__(self):
        return f"{self.shipper} -> {self.consignee} ({self.reporting_date})"


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
