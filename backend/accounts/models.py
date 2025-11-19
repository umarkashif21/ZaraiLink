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
