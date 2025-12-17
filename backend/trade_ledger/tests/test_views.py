"""
Integration tests for the trade_ledger app API views.

Tests cover:
- Explorer API
- Company profile APIs (overview, products, partners, trends)
- Compare companies API
- GNN APIs (similar companies, potential partners, network influence)
- Link Prediction APIs
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestExplorerAPI:
    """Test cases for the explorer API."""
    
    def test_explorer_basic_request(self, api_client):
        """Test basic explorer API request."""
        url = '/api/explorer/'
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (dict, list))
    
    def test_explorer_with_direction_filter(self, api_client):
        """Test explorer with import/export direction filter."""
        url = '/api/explorer/?direction=import'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_explorer_with_country_filter(self, api_client):
        """Test explorer with country filter."""
        url = '/api/explorer/?country=Pakistan'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_explorer_with_date_range(self, api_client):
        """Test explorer with date range filter."""
        url = '/api/explorer/?start_date=2023-01-01&end_date=2023-12-31'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_explorer_invalid_date_format(self, api_client):
        """Test explorer handles invalid date format gracefully."""
        url = '/api/explorer/?start_date=invalid-date'
        response = api_client.get(url)
        
        
        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestCompanyOverviewAPI:
    """Test cases for company overview API."""
    
    def test_valid_company_overview(self, api_client, create_company):
        """Test getting overview for valid company."""
        company = create_company(name='Overview Test Co')
        
        url = f'/api/company/{company.name}/overview/'
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, dict)
    
    def test_nonexistent_company_overview(self, api_client):
        """Test overview for non-existent company."""
        url = '/api/company/NonExistentCompany12345/overview/'
        response = api_client.get(url)
        
        
        assert response.status_code in [200, 404]


@pytest.mark.django_db
class TestCompanyProductsAPI:
    """Test cases for company products API."""
    
    def test_company_with_products(self, api_client, create_company):
        """Test getting products for company with products."""
        from companies.models import CompanyProduct
        
        company = create_company(name='Products Test Co')
        
        
        
        url = f'/api/company/{company.name}/products/'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_company_without_products(self, api_client, create_company):
        """Test getting products for company with no products."""
        company = create_company(name='Empty Products Co')
        
        url = f'/api/company/{company.name}/products/'
        response = api_client.get(url)
        
        assert response.status_code == 200


@pytest.mark.django_db
class TestCompanyPartnersAPI:
    """Test cases for company partners API."""
    
    def test_company_partners(self, api_client, create_company):
        """Test getting partners for a company."""
        company = create_company(name='Partners Test Co')
        
        url = f'/api/company/{company.name}/partners/'
        response = api_client.get(url)
        
        assert response.status_code == 200


@pytest.mark.django_db
class TestCompanyTrendsAPI:
    """Test cases for company trends API."""
    
    def test_company_trends(self, api_client, create_company):
        """Test getting trends for a company."""
        company = create_company(name='Trends Test Co')
        
        url = f'/api/company/{company.name}/trends/'
        response = api_client.get(url)
        
        assert response.status_code == 200


@pytest.mark.django_db
class TestCompareCompaniesAPI:
    """Test cases for company comparison API."""
    
    def test_compare_two_companies(self, api_client, create_company):
        """Test comparing two companies."""
        company1 = create_company(name='Compare Co A')
        company2 = create_company(name='Compare Co B')
        
        url = '/api/compare/'
        response = api_client.post(url, {'companies': [company1.name, company2.name]}, format='json')
        
        assert response.status_code in [200, 400]  
    
    def test_compare_multiple_companies(self, api_client, create_company):
        """Test comparing multiple companies."""
        company1 = create_company(name='Multi Compare A')
        company2 = create_company(name='Multi Compare B')
        company3 = create_company(name='Multi Compare C')
        
        url = '/api/compare/'
        response = api_client.post(url, {'companies': [company1.name, company2.name, company3.name]}, format='json')
        
        assert response.status_code in [200, 400]  


@pytest.mark.django_db
class TestGNNAPIs:
    """Test cases for GNN-based APIs."""
    
    def test_similar_companies(self, api_client, create_company):
        """Test similar companies API."""
        company = create_company(name='GNN Similar Test')
        
        url = f'/api/company/{company.name}/similar/'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_potential_partners(self, api_client, create_company):
        """Test potential partners API."""
        company = create_company(name='GNN Partners Test')
        
        url = f'/api/company/{company.name}/potential-partners/'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_network_influence(self, api_client, create_company):
        """Test network influence API."""
        company = create_company(name='GNN Influence Test')
        
        url = f'/api/company/{company.name}/network-influence/'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_product_clusters(self, api_client):
        """Test product clusters API."""
        url = '/api/product-clusters/'
        response = api_client.get(url)
        
        assert response.status_code == 200


@pytest.mark.django_db
class TestLinkPredictionAPIs:
    """Test cases for link prediction APIs."""
    
    def test_predict_sellers_combined(self, api_client, create_company):
        """Test predict sellers with combined method."""
        buyer = create_company(name='Link Pred Buyer')
        
        url = f'/api/predict/sellers/{buyer.name}/?method=combined'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_predict_sellers_node2vec(self, api_client, create_company):
        """Test predict sellers with Node2Vec method."""
        buyer = create_company(name='N2V Buyer Test')
        
        url = f'/api/predict/sellers/{buyer.name}/?method=node2vec'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_predict_sellers_jaccard(self, api_client, create_company):
        """Test predict sellers with Jaccard method."""
        buyer = create_company(name='Jaccard Buyer Test')
        
        url = f'/api/predict/sellers/{buyer.name}/?method=jaccard'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_predict_buyers_combined(self, api_client, create_company):
        """Test predict buyers with combined method."""
        seller = create_company(name='Link Pred Seller')
        
        url = f'/api/predict/buyers/{seller.name}/?method=combined'
        response = api_client.get(url)
        
        assert response.status_code == 200
    
    def test_link_prediction_methods(self, api_client):
        """Test getting available link prediction methods."""
        url = '/api/predict/methods/'
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        
        
        methods = data.get('methods', data)
        assert isinstance(methods, (list, dict))
