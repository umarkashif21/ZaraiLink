from django.db import models
from companies.models import Company


class ProductCategory(models.Model):
    name = models.CharField(max_length=200)
    hs_code = models.CharField(max_length=10, blank=True, help_text="Harmonized System Code")
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = 'Product Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TradeCompany(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='trade_data')
    estimated_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    trade_volume = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    active_since = models.DateField(null=True, blank=True)
    is_importer = models.BooleanField(default=False)
    is_exporter = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = 'Trade Companies'
        ordering = ['-trade_volume']
    
    def __str__(self):
        return f"{self.company.name} - Trade Data"


class TradeProduct(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilograms'), ('ton', 'Metric Ton'), ('lb', 'Pounds'),
        ('unit', 'Units'), ('box', 'Boxes'), ('container', 'Containers'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'), ('PKR', 'Pakistani Rupee'),
        ('EUR', 'Euro'), ('GBP', 'British Pound'),
    ]
    
    company = models.ForeignKey(TradeCompany, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, related_name='products')
    product_name = models.CharField(max_length=200)
    hs_code = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    
    avg_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    volume = models.DecimalField(max_digits=15, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    yoy_growth = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-volume']
    
    def __str__(self):
        return f"{self.product_name} - {self.company.company.name}"


class TradePartner(models.Model):
    company = models.ForeignKey(TradeCompany, on_delete=models.CASCADE, related_name='partners')
    country = models.CharField(max_length=100)
    port_name = models.CharField(max_length=200, blank=True)
    trade_volume = models.DecimalField(max_digits=15, decimal_places=2)
    percentage_share = models.DecimalField(max_digits=5, decimal_places=2)
    is_export = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-trade_volume']
    
    def __str__(self):
        return f"{self.company.company.name} - {self.country}"


class TradeTrend(models.Model):
    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'),
    ]
    
    company = models.ForeignKey(TradeCompany, on_delete=models.CASCADE, related_name='trends')
    product = models.ForeignKey(TradeProduct, on_delete=models.CASCADE, related_name='trends', null=True, blank=True)
    month = models.IntegerField(choices=MONTH_CHOICES)
    year = models.IntegerField()
    
    volume = models.DecimalField(max_digits=15, decimal_places=2)
    avg_price = models.DecimalField(max_digits=12, decimal_places=2)
    yoy_volume_growth = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    yoy_price_growth = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['company', 'product', 'month', 'year']
    
    def __str__(self):
        return f"{self.company.company.name} - {self.get_month_display()} {self.year}"
