from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import uuid
from datetime import timedelta
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name=_("Email"))
    username = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Username"))
    bio = models.CharField(max_length=500, default="", blank=True, verbose_name=_("Bio"))
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Country"))

    # Email verification fields
    email_verified = models.BooleanField(default=False, verbose_name=_("Email Verified"))
    verification_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_column='email_verification_token'  # Match database column name
    )
    token_created_at = models.DateTimeField(default=timezone.now)

    # New fields for enhanced schema
    phone_number = models.CharField(max_length=30, blank=True, null=True, verbose_name=_("Phone Number"))
    job_title = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Job Title"))
    
    # Token balance for contact unlocking
    token_balance = models.IntegerField(default=0, verbose_name=_("Token Balance"))

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def is_verification_token_valid(self):
        """Check if verification token is still valid (24 hours)"""
        if self.email_verified:
            return False
        expiration_time = self.token_created_at + timedelta(hours=24)
        return timezone.now() < expiration_time

    def regenerate_verification_token(self):
        """Generate a new verification token"""
        self.verification_token = uuid.uuid4()
        self.token_created_at = timezone.now()
        self.save(update_fields=['verification_token', 'token_created_at'])
    
    # Token management methods
    def has_tokens(self, amount=1):
        """Check if user has enough tokens"""
        return self.token_balance >= amount
    
    def deduct_tokens(self, amount=1):
        """Deduct tokens from balance"""
        if self.has_tokens(amount):
            self.token_balance -= amount
            self.save(update_fields=['token_balance'])
            return True
        return False
    
    def add_tokens(self, amount):
        """Add tokens to balance"""
        self.token_balance += amount
        self.save(update_fields=['token_balance'])


class UserAlertPreference(models.Model):
    """User's notification preferences for alerts"""
    FREQUENCY_CHOICES = [
        ('realtime', 'Realtime'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='alert_preferences'
    )
    followed_products = models.JSONField(
        default=list,
        help_text="JSON array of product IDs"
    )
    followed_countries = models.JSONField(
        default=list,
        help_text="JSON array of country names"
    )
    categories = models.JSONField(
        default=list,
        help_text="JSON array of alert categories"
    )
    notify_email = models.BooleanField(default=True)
    notify_in_app = models.BooleanField(default=True)
    frequency = models.CharField(
        max_length=50,
        choices=FREQUENCY_CHOICES,
        default='daily'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Alert Preference'
        verbose_name_plural = 'User Alert Preferences'

    def __str__(self):
        return f"{self.user.email} - Alert Preferences"
