"""
Unit tests for the accounts app models.

Tests cover:
- User model creation and validation
- Token management methods
- Email verification token handling
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test cases for the User model."""
    
    def test_create_user_with_email(self, create_user):
        """Test creating a user with email as primary identifier."""
        user = create_user(email='test@example.com', password='testpass123')
        
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser
    
    def test_user_str_with_full_name(self, create_user):
        """Test User __str__ returns full name when available."""
        user = create_user(
            email='john@example.com',
            first_name='John',
            last_name='Doe'
        )
        assert str(user) == 'John Doe'
    
    def test_user_str_with_email_only(self, create_user):
        """Test User __str__ returns email when name is empty."""
        user = create_user(
            email='noname@example.com',
            first_name='',
            last_name=''
        )
        assert str(user) == 'noname@example.com'
    
    def test_email_uniqueness(self, create_user):
        """Test that duplicate emails are rejected."""
        create_user(email='unique@example.com')
        
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            create_user(email='unique@example.com')
    
    def test_verification_token_generated_on_create(self, create_user):
        """Test that verification token is auto-generated."""
        user = create_user()
        
        assert user.verification_token is not None
        assert len(str(user.verification_token)) == 36  
    
    def test_is_verification_token_valid_for_new_user(self, create_user):
        """Test token is valid for newly created unverified user."""
        user = create_user(email_verified=False)
        
        assert user.is_verification_token_valid()
    
    def test_is_verification_token_invalid_for_verified_user(self, user):
        """Test token is invalid for already verified user."""
        assert not user.is_verification_token_valid()
    
    def test_is_verification_token_expired_after_24_hours(self, create_user):
        """Test token expires after 24 hours."""
        user = create_user(email_verified=False)
        
        
        user.token_created_at = timezone.now() - timedelta(hours=25)
        user.save()
        
        assert not user.is_verification_token_valid()
    
    def test_regenerate_verification_token(self, create_user):
        """Test regeneration creates new token and updates timestamp."""
        user = create_user(email_verified=False)
        old_token = user.verification_token
        old_timestamp = user.token_created_at
        
        user.regenerate_verification_token()
        
        assert user.verification_token != old_token
        assert user.token_created_at > old_timestamp


@pytest.mark.django_db
class TestUserTokenManagement:
    """Test cases for user token balance management."""
    
    def test_initial_token_balance(self, create_user):
        """Test default token balance is set correctly."""
        user = create_user(token_balance=10)
        assert user.token_balance == 10
    
    def test_has_tokens_returns_true_when_sufficient(self, create_user):
        """Test has_tokens returns True when balance >= amount."""
        user = create_user(token_balance=5)
        
        assert user.has_tokens(1)
        assert user.has_tokens(5)
    
    def test_has_tokens_returns_false_when_insufficient(self, create_user):
        """Test has_tokens returns False when balance < amount."""
        user = create_user(token_balance=3)
        
        assert not user.has_tokens(5)
        assert not user.has_tokens(4)
    
    def test_deduct_tokens_successful(self, create_user):
        """Test successful token deduction."""
        user = create_user(token_balance=10)
        
        result = user.deduct_tokens(3)
        
        assert result is True
        assert user.token_balance == 7
    
    def test_deduct_tokens_fails_with_insufficient_balance(self, create_user):
        """Test token deduction fails when balance insufficient."""
        user = create_user(token_balance=2)
        
        result = user.deduct_tokens(5)
        
        assert result is False
        assert user.token_balance == 2  
    
    def test_add_tokens(self, create_user):
        """Test adding tokens to balance."""
        user = create_user(token_balance=5)
        
        user.add_tokens(10)
        
        assert user.token_balance == 15
    
    def test_add_tokens_from_zero(self, user_no_tokens):
        """Test adding tokens to zero balance."""
        user_no_tokens.add_tokens(50)
        
        assert user_no_tokens.token_balance == 50


@pytest.mark.django_db
class TestUserAlertPreference:
    """Test cases for UserAlertPreference model."""
    
    def test_create_alert_preference(self, user):
        """Test creating alert preferences for a user."""
        from accounts.models import UserAlertPreference
        
        pref = UserAlertPreference.objects.create(
            user=user,
            followed_products=[1, 2, 3],
            followed_countries=['Pakistan', 'India'],
            notify_email=True,
            notify_in_app=True,
            frequency='daily'
        )
        
        assert pref.user == user
        assert pref.followed_products == [1, 2, 3]
        assert pref.frequency == 'daily'
    
    def test_alert_preference_one_to_one(self, user):
        """Test that each user can only have one preference object."""
        from accounts.models import UserAlertPreference
        from django.db import IntegrityError
        
        UserAlertPreference.objects.create(user=user)
        
        with pytest.raises(IntegrityError):
            UserAlertPreference.objects.create(user=user)
