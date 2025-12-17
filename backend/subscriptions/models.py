from django.db import models
from django.conf import settings
import secrets
import string


class SubscriptionPlan(models.Model):
    """Subscription plan tiers with pricing and token allocations"""
    plan_name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    tokens_included = models.IntegerField(help_text="Number of tokens included per billing cycle")
    description = models.TextField(blank=True)
    features = models.JSONField(default=dict, help_text="JSON object containing feature flags and limits")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'
        ordering = ['price']

    def __str__(self):
        return f"{self.plan_name} - {self.currency} {self.price}"


class UserSubscription(models.Model):
    """User's active subscription"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateField()
    end_date = models.DateField()
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='monthly')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User Subscription'
        verbose_name_plural = 'User Subscriptions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.plan.plan_name} ({self.status})"


class TokenPurchase(models.Model):
    """Standalone token purchases (beyond subscription)"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='token_purchases'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='token_purchases',
        help_text="Optional link to plan for add-on purchases"
    )
    tokens_purchased = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    payment_provider = models.CharField(max_length=100, help_text="e.g., Stripe, PayPal, JazzCash")
    payment_reference = models.CharField(max_length=255, help_text="Transaction ID from payment provider")
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Token Purchase'
        verbose_name_plural = 'Token Purchases'
        ordering = ['-purchased_at']

    def __str__(self):
        return f"{self.user.email} - {self.tokens_purchased} tokens - {self.purchased_at}"


class RedeemCode(models.Model):
    """
    Redeemable codes for subscription plans
    Replaces payment processing for MVP/testing
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('redeemed', 'Redeemed'),
        ('expired', 'Expired'),
    ]
    
    code = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        help_text="Unique redemption code"
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name='redeem_codes'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    redeemed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='redeemed_codes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional expiration date")
    
    class Meta:
        verbose_name = 'Redeem Code'
        verbose_name_plural = 'Redeem Codes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code', 'status']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.plan.plan_name} ({self.status})"
    
    @staticmethod
    def generate_code(length=12):
        """Generate a random alphanumeric code"""
        
        chars = string.ascii_uppercase + string.digits
        chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def redeem(self, user):
        """Redeem this code for a user"""
        from django.utils import timezone
        
        if self.status != 'active':
            return False, f"Code is {self.status}"
        
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = 'expired'
            self.save()
            return False, "Code has expired"
        
        
        self.status = 'redeemed'
        self.redeemed_by = user
        self.redeemed_at = timezone.now()
        self.save()
        
        
        user.add_tokens(self.plan.tokens_included)
        
        
        from datetime import timedelta
        
        
        plan_name_lower = self.plan.plan_name.lower()
        if 'annual' in plan_name_lower or 'yearly' in plan_name_lower:
            billing_cycle = 'yearly'
            duration_days = 365
        else:
            billing_cycle = 'monthly'
            duration_days = 30
        
        end_date = timezone.now().date() + timedelta(days=duration_days)
        
        UserSubscription.objects.create(
            user=user,
            plan=self.plan,
            status='active',
            start_date=timezone.now().date(),
            end_date=end_date,
            billing_cycle=billing_cycle
        )
        
        return True, "Code redeemed successfully"
