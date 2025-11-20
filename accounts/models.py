from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name=_("Email"))
    username = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Username"))
    bio = models.CharField(max_length=500, default="", blank=True, verbose_name=_("Bio"))
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Country"))

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email