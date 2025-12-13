from django.db import models
from django.conf import settings


class Sector(models.Model):
    """Product categories/sectors (e.g., Rice, Wheat, Cotton)"""
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Sector'
        verbose_name_plural = 'Sectors'
        ordering = ['name']

    def __str__(self):
        return self.name


class CompanyRole(models.Model):
    """Company's role in trade (Supplier, Buyer, etc.)"""
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Company Role'
        verbose_name_plural = 'Company Roles'
        ordering = ['name']

    def __str__(self):
        return self.name


class CompanyType(models.Model):
    """Legal/structural company classification"""
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Company Type'
        verbose_name_plural = 'Company Types'
        ordering = ['name']

    def __str__(self):
        return self.name


class Image(models.Model):
    """Generic image storage with polymorphic associations"""
    ENTITY_TYPE_CHOICES = [
        ('company', 'Company'),
        ('product', 'Product'),
        ('user', 'User'),
    ]
    
    url = models.URLField(max_length=1024)
    alt_text = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_images'
    )
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPE_CHOICES)
    entity_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Image'
        verbose_name_plural = 'Images'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
        ]

    def __str__(self):
        return f"{self.entity_type} Image ({self.entity_id})"


class Company(models.Model):
    """Core company profile in trade directory"""
    VERIFICATION_STATUS_CHOICES = [
        ('unverified', 'Unverified'),
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('premium', 'Premium'),
    ]
    
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    country = models.CharField(max_length=100)
    province = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    market_sentiment = models.CharField(max_length=20, default='Neutral', blank=True)
    website = models.URLField(max_length=255, blank=True)
    contact_email = models.EmailField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    logo_image = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='company_logos'
    )
    year_established = models.IntegerField(null=True, blank=True)
    number_of_employees = models.CharField(max_length=50, blank=True, help_text="e.g., 50-100, 100-500")
    horeca_retail_info = models.CharField(max_length=255, blank=True, help_text="HORECA/retail details")
    verification_status = models.CharField(
        max_length=50,
        choices=VERIFICATION_STATUS_CHOICES,
        default='unverified'
    )
    ntn_number = models.CharField(max_length=100, blank=True, help_text="National Tax Number")
    trade_license_number = models.CharField(max_length=100, blank=True)
    sector = models.ForeignKey(
        Sector,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies'
    )
    company_role = models.ForeignKey(
        CompanyRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies'
    )
    company_type = models.ForeignKey(
        CompanyType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies'
    )
    has_trade_data = models.BooleanField(default=False, help_text="Company appears in trade records")
    is_directory_profile = models.BooleanField(default=True, help_text="Manually created vs auto-generated")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['name']
        indexes = [
            models.Index(fields=['country', 'sector']),
            models.Index(fields=['verification_status']),
        ]

    def __str__(self):
        return self.name


class CompanyProduct(models.Model):
    """Products/commodities offered by companies"""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='products'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    variety = models.CharField(max_length=100, blank=True, help_text="e.g., Basmati, Super Kernel")
    value_added = models.CharField(max_length=255, blank=True, help_text="e.g., Organic certified, Pre-washed")
    hsn_code = models.CharField(max_length=20, blank=True, help_text="Harmonized System Nomenclature code")
    image = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_images'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Company Product'
        verbose_name_plural = 'Company Products'
        ordering = ['company', 'name']

    def __str__(self):
        return f"{self.company.name} - {self.name}"


class KeyContact(models.Model):
    """Private contact information for companies"""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='key_contacts'
    )
    name = models.CharField(max_length=255)
    designation = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    whatsapp = models.CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    is_public = models.BooleanField(default=False, help_text="Visible without tokens")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Key Contact'
        verbose_name_plural = 'Key Contacts'
        ordering = ['company', 'name']

    def __str__(self):
        return f"{self.name} - {self.company.name}"


class KeyContactUnlock(models.Model):
    """Track which users unlocked which contacts"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='unlocked_contacts'
    )
    key_contact = models.ForeignKey(
        KeyContact,
        on_delete=models.CASCADE,
        related_name='unlocks'
    )
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Key Contact Unlock'
        verbose_name_plural = 'Key Contact Unlocks'
        ordering = ['-unlocked_at']
        unique_together = ['user', 'key_contact']
        indexes = [
            models.Index(fields=['user', 'key_contact']),
        ]

    def __str__(self):
        return f"{self.user.email} unlocked {self.key_contact.name}"


class CompanyMetricsCache(models.Model):
    """Cached computed metrics for company profiles"""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='cached_metrics'
    )
    metric_date = models.DateField()
    metric_key = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=20, decimal_places=6)
    meta = models.JSONField(null=True, blank=True, help_text="Additional context")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Company Metrics Cache'
        verbose_name_plural = 'Company Metrics Cache'
        ordering = ['-metric_date']
        indexes = [
            models.Index(fields=['company', 'metric_key', 'metric_date']),
        ]

    def __str__(self):
        return f"{self.company.name} - {self.metric_key} ({self.metric_date})"


class IngestionLog(models.Model):
    """Track data import jobs"""
    source_file = models.CharField(max_length=255)
    rows_processed = models.IntegerField(default=0)
    rows_inserted = models.IntegerField(default=0)
    errors = models.IntegerField(default=0)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Error details or notes")

    class Meta:
        verbose_name = 'Ingestion Log'
        verbose_name_plural = 'Ingestion Logs'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.source_file} - {self.started_at.date()}"


class AdminAnnouncement(models.Model):
    """System-wide announcements to users"""
    title = models.CharField(max_length=255)
    content = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Admin Announcement'
        verbose_name_plural = 'Admin Announcements'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


from auditlog.registry import auditlog
auditlog.register(Company)
auditlog.register(CompanyProduct)
auditlog.register(KeyContact)

