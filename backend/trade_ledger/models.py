from django.db import models
from companies.models import Company


class ProductCategory(models.Model):
    """Product categories for trade classification"""
    name = models.CharField(max_length=200)
    hs_code = models.CharField(max_length=10, blank=True, help_text="Harmonized System Code")
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TradeCompany(models.Model):
    """Extended company data for trade intelligence"""
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='trade_data'
    )
    estimated_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated annual revenue in USD"
    )
    trade_volume = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual trade volume in USD"
    )
    active_since = models.DateField(null=True, blank=True)
    is_importer = models.BooleanField(default=False)
    is_exporter = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Trade Company'
        verbose_name_plural = 'Trade Companies'
        ordering = ['-trade_volume']
    
    def __str__(self):
        return f"{self.company.name} - Trade Data"


class TradeProduct(models.Model):
    """Trade product data with performance metrics"""
    UNIT_CHOICES = [
        ('kg', 'Kilograms'),
        ('ton', 'Metric Ton'),
        ('lb', 'Pounds'),
        ('unit', 'Units'),
        ('box', 'Boxes'),
        ('container', 'Containers'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('PKR', 'Pakistani Rupee'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    ]
    
    company = models.ForeignKey(
        TradeCompany,
        on_delete=models.CASCADE,
        related_name='products'
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    product_name = models.CharField(max_length=200)
    hs_code = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    
    # Performance metrics
    avg_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    volume = models.DecimalField(max_digits=15, decimal_places=2, help_text="Annual volume")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    yoy_growth = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Year-over-year growth percentage"
    )
    
    class Meta:
        verbose_name = 'Trade Product'
        verbose_name_plural = 'Trade Products'
        ordering = ['-volume']
    
    def __str__(self):
        return f"{self.product_name} - {self.company.company.name}"


class TradePartner(models.Model):
    """Partner countries and ports for trade companies"""
    company = models.ForeignKey(
        TradeCompany,
        on_delete=models.CASCADE,
        related_name='partners'
    )
    country = models.CharField(max_length=100)
    port_name = models.CharField(max_length=200, blank=True)
    trade_volume = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Trade volume with this partner in USD"
    )
    percentage_share = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage of total company trade"
    )
    is_export = models.BooleanField(default=True, help_text="Export if True, Import if False")
    
    class Meta:
        verbose_name = 'Trade Partner'
        verbose_name_plural = 'Trade Partners'
        ordering = ['-trade_volume']
    
    def __str__(self):
        return f"{self.company.company.name} - {self.country}"


class TradeTrend(models.Model):
    """Time-series trade data for trend analysis"""
    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'),
    ]
    
    company = models.ForeignKey(
        TradeCompany,
        on_delete=models.CASCADE,
        related_name='trends'
    )
    product = models.ForeignKey(
        TradeProduct,
        on_delete=models.CASCADE,
        related_name='trends',
        null=True,
        blank=True
    )
    month = models.IntegerField(choices=MONTH_CHOICES)
    year = models.IntegerField()
    
    volume = models.DecimalField(max_digits=15, decimal_places=2)
    avg_price = models.DecimalField(max_digits=12, decimal_places=2)
    yoy_volume_growth = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    yoy_price_growth = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Trade Trend'
        verbose_name_plural = 'Trade Trends'
        ordering = ['-year', '-month']
        unique_together = ['company', 'product', 'month', 'year']
    
    def __str__(self):
        return f"{self.company.company.name} - {self.get_month_display()} {self.year}"
