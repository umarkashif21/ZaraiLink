# backend/app/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

# ======================
# USERS
# ======================
class User(AbstractUser):
    tokens = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# ======================
# COMPANY STRUCTURE
# ======================
class CompanyRole(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Supplier / Buyer / Both

    def __str__(self):
        return self.name


class CompanyType(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Sugar Mill, Ethanol Producer, etc.

    def __str__(self):
        return self.name


class Sector(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Sugar, Ethanol, Pharma, etc.

    def __str__(self):
        return self.name

# ======================
# COMPANIES
# ======================
class Company(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    year_established = models.IntegerField(blank=True, null=True)
    number_of_employees = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    address = models.TextField()
    description = models.TextField(blank=True, null=True)
    landline_numbers = models.TextField(blank=True, null=True)


    sector = models.ForeignKey(Sector, on_delete=models.PROTECT, related_name='companies')
    company_role = models.ForeignKey(CompanyRole, on_delete=models.PROTECT, related_name='companies')
    company_type = models.ForeignKey(CompanyType, on_delete=models.PROTECT, related_name='companies')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# ======================
# PRODUCTS
# ======================
class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    value_added = models.CharField(max_length=255, blank=True, null=True)
    variety = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"

# ======================
# KEY CONTACTS
# ======================
class KeyContact(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='key_contacts')
    name = models.CharField(max_length=255)
    designation = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    whatsapp = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"

# ======================
# KEY CONTACT UNLOCKS
# ======================
class KeyContactUnlock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlocked_contacts')
    key_contact = models.ForeignKey(KeyContact, on_delete=models.CASCADE, related_name='unlock_history')
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'key_contact')

    def __str__(self):
        return f"{self.user.username} unlocked {self.key_contact.name}"

# ======================
# USER TOKENS (Optional)
# ======================
class UserToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tokens_history')
    tokens_available = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.tokens_available} tokens"