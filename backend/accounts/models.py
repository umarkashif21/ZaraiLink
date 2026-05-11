from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
import uuid
from datetime import timedelta
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, username=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name=_("Email"))
    username = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Username"))
    bio = models.CharField(max_length=500, default="", blank=True, verbose_name=_("Bio"))
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Country"))

    
    email_verified = models.BooleanField(default=False, verbose_name=_("Email Verified"))
    verification_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_column='email_verification_token'  
    )
    token_created_at = models.DateTimeField(default=timezone.now)

    
    phone_number = models.CharField(max_length=30, blank=True, null=True, verbose_name=_("Phone Number"))
    job_title = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Job Title"))
    
    
    token_balance = models.IntegerField(default=0, verbose_name=_("Token Balance"))

    
    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def is_verification_token_valid(self):
        if self.email_verified:
            return False
        expiration_time = self.token_created_at + timedelta(hours=24)
        return timezone.now() < expiration_time

    def regenerate_verification_token(self):
        self.verification_token = uuid.uuid4()
        self.token_created_at = timezone.now()
        self.save(update_fields=['verification_token', 'token_created_at'])
    
    
    def has_tokens(self, amount=1):
        return self.token_balance >= amount

    def deduct_tokens(self, amount=1):
        if self.has_tokens(amount):
            self.token_balance -= amount
            self.save(update_fields=['token_balance'])
            return True
        return False

    def add_tokens(self, amount):
        self.token_balance += amount
        self.save(update_fields=['token_balance'])


