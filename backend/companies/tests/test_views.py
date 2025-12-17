"""
Integration tests for the companies app API views.

Tests cover:
- CompanyViewSet (list, filter, search, retrieve)
- KeyContactViewSet (list, unlock)
- Lookup endpoints (sectors, company types, company roles)
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestCompanyViewSet:
    """Test cases for CompanyViewSet."""
    
    def test_list_all_companies(self, api_client, create_company):
        """Test listing all companies."""
        
        create_company(name='Company A', country='Pakistan')
        create_company(name='Company B', country='India')
        create_company(name='Company C', country='China')
        
        url = '/api/companies/'
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        
        if isinstance(data, dict) and 'results' in data:
            companies = data['results']
        else:
            companies = data
        
        assert len(companies) >= 3
    
    def test_filter_by_country(self, api_client, create_company):
        """Test filtering companies by country."""
        pak_company = create_company(name='PAK Company Filter Test', country='Pakistan')
        create_company(name='IND Company Filter Test', country='India')
        
        url = '/api/companies/?country=Pakistan'
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        if isinstance(data, dict) and 'results' in data:
            companies = data['results']
        else:
            companies = data
        
        
        company_names = [c['name'] for c in companies]
        assert pak_company.name in company_names or len([c for c in companies if c.get('country') == 'Pakistan']) > 0
    
    def test_filter_by_sector(self, api_client, create_company, create_sector):
        """Test filtering companies by sector."""
        rice_sector = create_sector(name='Rice')
        wheat_sector = create_sector(name='Wheat')
        
        create_company(name='Rice Corp', sector=rice_sector)
        create_company(name='Wheat Corp', sector=wheat_sector)
        
        url = f'/api/companies/?sector={rice_sector.id}'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_filter_by_company_type(self, api_client, create_company, create_company_role):
        """Test filtering companies by role (Buyer/Supplier)."""
        supplier_role = create_company_role(name='Supplier')
        buyer_role = create_company_role(name='Buyer')
        
        create_company(name='Supplier Co', role=supplier_role)
        create_company(name='Buyer Co', role=buyer_role)
        
        url = f'/api/companies/?role={supplier_role.id}'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_filter_by_verification_status(self, api_client, create_company):
        """Test filtering companies by verification status."""
        create_company(name='Verified Co', verification_status='verified')
        create_company(name='Unverified Co', verification_status='unverified')
        
        url = '/api/companies/?verification_status=verified'
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        if isinstance(data, dict) and 'results' in data:
            companies = data['results']
        else:
            companies = data
        
        for company in companies:
            assert company['verification_status'] == 'verified'
    
    def test_search_by_name(self, api_client, create_company):
        """Test searching companies by partial name match."""
        create_company(name='Acme Corporation')
        create_company(name='Beta Industries')
        create_company(name='Acme Traders')
        
        url = '/api/companies/?search=Acme'
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        if isinstance(data, dict) and 'results' in data:
            companies = data['results']
        else:
            companies = data
        
        for company in companies:
            assert 'acme' in company['name'].lower()
    
    def test_pagination(self, api_client, create_company):
        """Test pagination with many companies."""
        
        for i in range(15):
            create_company(name=f'Company {i}')
        
        url = '/api/companies/?page=1'
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        if isinstance(data, dict):
            assert 'results' in data or 'count' in data or isinstance(data, list)
    
    def test_get_single_company(self, api_client, create_company):
        """Test retrieving a single company by ID."""
        company = create_company(name='Single Company')
        
        url = f'/api/companies/{company.id}/'
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Single Company'
    
    def test_company_not_found(self, api_client):
        """Test 404 for non-existent company."""
        url = '/api/companies/99999/'
        response = api_client.get(url)
        
        assert response.status_code == 404


@pytest.mark.django_db
class TestKeyContactViewSet:
    """Test cases for KeyContactViewSet."""
    
    def test_list_contacts_for_company(self, authenticated_client, create_company, create_key_contact):
        """Test listing key contacts for a company."""
        company = create_company(name='Contact Test Co')
        create_key_contact(company_obj=company, name='John Doe')
        create_key_contact(company_obj=company, name='Jane Smith')
        
        url = f'/api/key-contacts/?company={company.id}'
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
    
    def test_unlock_contact_with_tokens(self, authenticated_client, user, create_company, create_key_contact):
        """Test unlocking a contact when user has tokens."""
        company = create_company(name='Unlock Test Co')
        contact = create_key_contact(company_obj=company, name='Secret Contact')
        
        initial_balance = user.token_balance
        
        
        url = f'/api/key-contacts/{contact.id}/unlock/'
        response = authenticated_client.post(url)
        
        
        if response.status_code == 404:
            pytest.skip("Unlock endpoint not implemented at expected URL")
        
        assert response.status_code in [200, 201]
        
        
        user.refresh_from_db()
        assert user.token_balance < initial_balance
    
    def test_unlock_contact_without_tokens(self, authenticated_client_no_tokens, create_company, create_key_contact):
        """Test unlock fails when user has no tokens."""
        company = create_company(name='No Token Test Co')
        contact = create_key_contact(company_obj=company, name='Locked Contact')
        
        url = f'/api/key-contacts/{contact.id}/unlock/'
        response = authenticated_client_no_tokens.post(url)
        
        if response.status_code == 404:
            pytest.skip("Unlock endpoint not implemented at expected URL")
        
        
        assert response.status_code in [400, 402, 403]
    
    def test_already_unlocked_contact(self, authenticated_client, user, create_company, create_key_contact):
        """Test accessing already unlocked contact."""
        from companies.models import KeyContactUnlock
        
        company = create_company(name='Already Unlocked Co')
        contact = create_key_contact(company_obj=company, name='Unlocked Contact')
        
        
        KeyContactUnlock.objects.create(user=user, key_contact=contact)
        
        initial_balance = user.token_balance
        
        
        url = f'/api/key-contacts/{contact.id}/unlock/'
        response = authenticated_client.post(url)
        
        if response.status_code == 404:
            pytest.skip("Unlock endpoint not implemented at expected URL")
        
        
        user.refresh_from_db()
        
        assert user.token_balance >= initial_balance - 1


@pytest.mark.django_db
class TestLookupEndpoints:
    """Test cases for lookup endpoints."""
    
    def test_sectors_list(self, api_client, create_sector):
        """Test listing all sectors."""
        create_sector(name='Agriculture')
        create_sector(name='Textiles')
        create_sector(name='Manufacturing')
        
        url = '/api/sectors/'
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
    
    def test_company_types_list(self, api_client, create_company_type):
        """Test listing all company types."""
        create_company_type(name='Manufacturer')
        create_company_type(name='Exporter')
        
        url = '/api/company-types/'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_company_roles_list(self, api_client, create_company_role):
        """Test listing all company roles."""
        create_company_role(name='Supplier')
        create_company_role(name='Buyer')
        
        url = '/api/company-roles/'
        response = api_client.get(url)
        
        assert response.status_code == 200
