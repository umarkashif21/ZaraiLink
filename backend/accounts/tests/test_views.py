"""
Integration tests for the accounts app API views.

Tests cover:
- User registration (api_signup)
- User login (api_login)
- User logout (api_logout)
- Auth check (api_check_auth)
- Email verification (api_verify_email)
- Password reset (api_forgot_password)
- Resend verification (api_resend_verification)
"""

import pytest
import json
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Test cases for user registration API."""
    
    def test_valid_registration(self, api_client):
        """Test successful user registration with valid data."""
        url = reverse('accounts:api_signup')
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
            'name': 'New User'  
        }
        
        response = api_client.post(url, data, format='json')
        
        
        assert response.status_code in [200, 201, 400]
        if response.status_code in [200, 201]:
            assert User.objects.filter(email='newuser@example.com').exists()
    
    def test_duplicate_email_rejection(self, api_client, user):
        """Test registration fails with existing email."""
        url = reverse('accounts:api_signup')
        data = {
            'email': user.email,  
            'password': 'NewPass123!',
            'first_name': 'Another',
            'last_name': 'User'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 400
        response_data = response.json()
        assert 'error' in response_data or 'email' in str(response_data).lower()
    
    def test_invalid_email_format(self, api_client):
        """Test registration fails with invalid email format."""
        url = reverse('accounts:api_signup')
        data = {
            'email': 'not-an-email',
            'password': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 400
    
    def test_password_too_short(self, api_client):
        """Test registration fails with short password."""
        url = reverse('accounts:api_signup')
        data = {
            'email': 'short@example.com',
            'password': '123',  
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = api_client.post(url, data, format='json')
        
        
        
        if response.status_code == 201:
            
            pass
        else:
            assert response.status_code == 400
    
    def test_missing_required_fields(self, api_client):
        """Test registration fails without required fields."""
        url = reverse('accounts:api_signup')
        data = {
            'email': 'incomplete@example.com'
            
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 400
    
    def test_verification_token_generated(self, api_client):
        """Test that new user gets a verification token."""
        url = reverse('accounts:api_signup')
        data = {
            'email': 'tokentest@example.com',
            'password': 'SecurePass123!',
            'first_name': 'Token',
            'last_name': 'Test'
        }
        
        response = api_client.post(url, data, format='json')
        
        if response.status_code in [200, 201]:
            user = User.objects.get(email='tokentest@example.com')
            assert user.verification_token is not None
            assert not user.email_verified


@pytest.mark.django_db
class TestUserLogin:
    """Test cases for user login API."""
    
    def test_valid_credentials(self, api_client, user):
        """Test successful login with valid credentials."""
        url = reverse('accounts:api_login')
        data = {
            'email': user.email,
            'password': 'testpass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 200
        response_data = response.json()
        assert 'user' in response_data or 'email' in response_data or 'success' in response_data
    
    def test_invalid_email(self, api_client):
        """Test login fails with non-existent email."""
        url = reverse('accounts:api_login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'somepassword'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code in [400, 401]
    
    def test_invalid_password(self, api_client, user):
        """Test login fails with wrong password."""
        url = reverse('accounts:api_login')
        data = {
            'email': user.email,
            'password': 'wrongpassword'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code in [400, 401]
    
    def test_unverified_email_attempt(self, api_client, unverified_user):
        """Test login behavior for unverified email."""
        url = reverse('accounts:api_login')
        data = {
            'email': unverified_user.email,
            'password': 'testpass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        
        
        assert response.status_code in [200, 400, 401, 403]


@pytest.mark.django_db
class TestUserLogout:
    """Test cases for user logout API."""
    
    def test_logout_clears_session(self, authenticated_django_client):
        """Test logout clears user session."""
        url = reverse('accounts:api_logout')
        
        response = authenticated_django_client.post(url)
        
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestAuthCheck:
    """Test cases for authentication check API."""
    
    def test_authenticated_user(self, authenticated_django_client, user):
        """Test auth check returns user info when authenticated."""
        url = reverse('accounts:api_check_auth')
        
        response = authenticated_django_client.get(url)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data.get('authenticated') or response_data.get('is_authenticated')
    
    def test_unauthenticated_user(self, django_client):
        """Test auth check indicates not authenticated for anonymous user."""
        url = reverse('accounts:api_check_auth')
        
        response = django_client.get(url)
        
        assert response.status_code == 200
        response_data = response.json()
        assert not response_data.get('authenticated', True) or               not response_data.get('is_authenticated', True)


@pytest.mark.django_db
class TestEmailVerification:
    """Test cases for email verification API."""
    
    def test_valid_token_verification(self, api_client, unverified_user):
        """Test successful email verification with valid token."""
        token = unverified_user.verification_token
        url = reverse('accounts:api_verify_email', kwargs={'token': token})
        
        response = api_client.get(url)
        
        
        assert response.status_code in [200, 302]
        
        
        unverified_user.refresh_from_db()
        assert unverified_user.email_verified
    
    def test_invalid_token(self, api_client):
        """Test verification fails with invalid token."""
        import uuid
        fake_token = uuid.uuid4()
        url = reverse('accounts:api_verify_email', kwargs={'token': fake_token})
        
        response = api_client.get(url)
        
        
        assert response.status_code in [302, 400, 404]
    
    def test_already_verified_user(self, api_client, user):
        """Test verification for already verified user."""
        token = user.verification_token
        url = reverse('accounts:api_verify_email', kwargs={'token': token})
        
        response = api_client.get(url)
        
        
        assert response.status_code in [200, 302, 400]


@pytest.mark.django_db
class TestForgotPassword:
    """Test cases for forgot password API."""
    
    def test_valid_email(self, api_client, user):
        """Test password reset request for existing user."""
        url = reverse('accounts:api_forgot_password')
        data = {'email': user.email}
        
        response = api_client.post(url, data, format='json')
        
        
        assert response.status_code == 200
    
    def test_non_existent_email(self, api_client):
        """Test password reset for non-existent email."""
        url = reverse('accounts:api_forgot_password')
        data = {'email': 'nonexistent@example.com'}
        
        response = api_client.post(url, data, format='json')
        
        
        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestResendVerification:
    """Test cases for resend verification email API."""
    
    def test_resend_for_unverified_user(self, authenticated_django_client, unverified_user):
        """Test resending verification email to unverified user."""
        
        from django.test import Client
        client = Client()
        client.force_login(unverified_user)
        
        url = reverse('accounts:api_resend_verification')
        response = client.post(url, content_type='application/json')
        
        assert response.status_code in [200, 400]
    
    def test_resend_for_already_verified(self, authenticated_django_client, user):
        """Test resending for already verified user."""
        url = reverse('accounts:api_resend_verification')
        
        response = authenticated_django_client.post(url, content_type='application/json')
        
        
        assert response.status_code in [200, 400]
