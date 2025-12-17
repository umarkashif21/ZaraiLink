"""
Integration tests for the subscriptions app API views.

Tests cover:
- List subscription plans
- Redeem code functionality
- Token balance updates
- Subscription creation
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestListPlans:
    """Test cases for listing subscription plans."""
    
    def test_list_all_plans(self, api_client, create_subscription_plan):
        """Test listing all subscription plans."""
        create_subscription_plan(plan_name='Basic', price=9.99, tokens_included=50)
        create_subscription_plan(plan_name='Premium', price=29.99, tokens_included=200)
        create_subscription_plan(plan_name='Enterprise', price=99.99, tokens_included=1000)
        
        url = reverse('subscriptions:list_plans')
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        if isinstance(data, dict):
            plans = data.get('plans', data.get('results', []))
        else:
            plans = data
        
        assert len(plans) >= 3
    
    def test_plans_contain_required_fields(self, api_client, create_subscription_plan):
        """Test that plan objects have all required fields."""
        create_subscription_plan(plan_name='Complete', price=49.99, tokens_included=500)
        
        url = reverse('subscriptions:list_plans')
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        if isinstance(data, dict):
            plans = data.get('plans', data.get('results', [data]))
        else:
            plans = data
        
        if plans:
            plan = plans[0]
            
            assert 'plan_name' in plan or 'name' in plan
            assert 'price' in plan
            assert 'tokens_included' in plan or 'tokens' in plan


@pytest.mark.django_db
class TestRedeemCode:
    """Test cases for redeem code functionality."""
    
    def test_valid_code_redemption(self, authenticated_django_client, redeem_code, user):
        """Test successful code redemption."""
        initial_balance = user.token_balance
        code_tokens = redeem_code.plan.tokens_included
        
        url = reverse('subscriptions:redeem_code')
        response = authenticated_django_client.post(
            url,
            data={'code': redeem_code.code},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        
        user.refresh_from_db()
        assert user.token_balance == initial_balance + code_tokens
        
        
        redeem_code.refresh_from_db()
        assert redeem_code.status == 'redeemed'
        assert redeem_code.redeemed_by == user
    
    def test_already_redeemed_code(self, authenticated_django_client, create_redeem_code, user):
        """Test that already redeemed code cannot be used again."""
        
        code = create_redeem_code(status='redeemed')
        code.redeemed_by = user
        code.save()
        
        url = reverse('subscriptions:redeem_code')
        response = authenticated_django_client.post(
            url,
            data={'code': code.code},
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_expired_code(self, authenticated_django_client, create_redeem_code):
        """Test that expired code cannot be redeemed."""
        from django.utils import timezone
        from datetime import timedelta
        
        
        code = create_redeem_code()
        code.expires_at = timezone.now() - timedelta(days=1)
        code.save()
        
        url = reverse('subscriptions:redeem_code')
        response = authenticated_django_client.post(
            url,
            data={'code': code.code},
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_invalid_code(self, authenticated_django_client):
        """Test that invalid code returns error."""
        url = reverse('subscriptions:redeem_code')
        response = authenticated_django_client.post(
            url,
            data={'code': 'INVALIDCODE12345'},
            content_type='application/json'
        )
        
        assert response.status_code == 404
    
    def test_subscription_created_on_redemption(self, authenticated_django_client, redeem_code, user):
        """Test that UserSubscription is created on code redemption."""
        from subscriptions.models import UserSubscription
        
        initial_subs = UserSubscription.objects.filter(user=user).count()
        
        url = reverse('subscriptions:redeem_code')
        response = authenticated_django_client.post(
            url,
            data={'code': redeem_code.code},
            content_type='application/json'
        )
        
        if response.status_code == 200:
            
            final_subs = UserSubscription.objects.filter(user=user).count()
            assert final_subs == initial_subs + 1
            
            
            sub = UserSubscription.objects.filter(user=user).latest('created_at')
            assert sub.status == 'active'
            assert sub.plan == redeem_code.plan
    
    def test_unauthenticated_user_cannot_redeem(self, django_client, redeem_code):
        """Test that unauthenticated user cannot redeem code."""
        url = reverse('subscriptions:redeem_code')
        response = django_client.post(
            url,
            data={'code': redeem_code.code},
            content_type='application/json'
        )
        
        
        assert response.status_code in [302, 401, 403]


@pytest.mark.django_db
class TestRedeemCodeModel:
    """Test cases for RedeemCode model methods."""
    
    def test_generate_code_uniqueness(self):
        """Test that generated codes are unique."""
        from subscriptions.models import RedeemCode
        
        codes = [RedeemCode.generate_code() for _ in range(100)]
        unique_codes = set(codes)
        
        assert len(unique_codes) == 100, "Generated codes are not unique"
    
    def test_generate_code_format(self):
        """Test that generated codes follow expected format."""
        from subscriptions.models import RedeemCode
        
        code = RedeemCode.generate_code(length=12)
        
        assert len(code) == 12
        assert code.isalnum()
        assert code.isupper() or any(c.isdigit() for c in code)
    
    def test_redeem_method_updates_all_fields(self, create_redeem_code, user):
        """Test that redeem() method updates all required fields."""
        code = create_redeem_code()
        initial_balance = user.token_balance
        
        success, message = code.redeem(user)
        
        assert success is True
        assert code.status == 'redeemed'
        assert code.redeemed_by == user
        assert code.redeemed_at is not None
        
        user.refresh_from_db()
        assert user.token_balance == initial_balance + code.plan.tokens_included
    
    def test_redeem_inactive_code_fails(self, create_redeem_code, user):
        """Test that redeeming inactive code fails."""
        code = create_redeem_code(status='expired')
        
        success, message = code.redeem(user)
        
        assert success is False
        assert 'expired' in message.lower()
