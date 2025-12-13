from django.db import models
from django.conf import settings


class Alert(models.Model):
    """AI-generated market intelligence alerts"""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    headline = models.CharField(max_length=512)
    summary = models.TextField()
    category = models.CharField(max_length=100, help_text="e.g., Price Surge, Supply Disruption")
    product = models.ForeignKey(
        'companies.Sector',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts'
    )
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    severity = models.CharField(max_length=50, choices=SEVERITY_CHOICES, default='medium')
    detected_at = models.DateTimeField()
    source = models.CharField(max_length=255, blank=True)
    meta = models.JSONField(null=True, blank=True, help_text="Additional data")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['product', 'severity']),
            models.Index(fields=['detected_at']),
        ]

    def __str__(self):
        return self.headline


class NewsArticle(models.Model):
    """News articles related to alerts"""
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='news_articles'
    )
    source = models.CharField(max_length=255, help_text="e.g., Dawn, Reuters")
    url = models.URLField(max_length=1024)
    title = models.CharField(max_length=512)
    full_text = models.TextField(blank=True)
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'News Article'
        verbose_name_plural = 'News Articles'
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class SavedAnalysis(models.Model):
    """User's bookmarked alerts with personal notes"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_analyses'
    )
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='saved_by_users'
    )
    title = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Saved Analysis'
        verbose_name_plural = 'Saved Analyses'
        ordering = ['-created_at']
        unique_together = ['user', 'alert']

    def __str__(self):
        return f"{self.user.email} - {self.alert.headline}"


class UserInteraction(models.Model):
    """Track user interactions for recommendations"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='interactions'
    )
    company = models.ForeignKey(
        'companies.Company', 
        on_delete=models.CASCADE,
        related_name='user_interactions'
    )
    action = models.CharField(max_length=50, default='view')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Interaction'
        verbose_name_plural = 'User Interactions'

