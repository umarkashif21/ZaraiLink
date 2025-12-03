import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const CompanyOverview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);

  const currentTab = location.pathname.split('/').pop();

  useEffect(() => {
    loadCompanyDetails();
  }, [id]);

  const loadCompanyDetails = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/trade-ledger/companies/${id}/`);
      if (response.ok) {
        const data = await response.json();
        setCompany(data);
      }
    } catch (err) {
      console.error('Failed to load company:', err);
    } finally {
      setLoading(false);
    }
  };

  const navigateToTab = (tab) => {
    navigate(`/trade-intelligence/company/${id}/${tab}`);
  };

  const formatCurrency = (value) => {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading company details...</p>
        </div>
      </>
    );
  }

  if (!company) {
    return (
      <>
        <Navbar />
        <div className="empty-state">
          <h2>Company not found</h2>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="company-detail-container">
        {/* Header */}
        <div className="company-detail-header">
          <h1>{company.company.name}</h1>
          <p>📍 {company.company.province}, {company.company.country}</p>
          <div className="company-tags">
            {company.is_exporter && <span className="company-tag">Exporter</span>}
            {company.is_importer && <span className="company-tag">Importer</span>}
            {company.company.sector && <span className="company-tag">{company.company.sector.name}</span>}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="tab-navigation">
          <button
            className={`tab-button ${currentTab === 'overview' ? 'active' : ''}`}
            onClick={() => navigateToTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab-button ${currentTab === 'products' ? 'active' : ''}`}
            onClick={() => navigateToTab('products')}
          >
            Products ({company.total_products || 0})
          </button>
          <button
            className={`tab-button ${currentTab === 'partners' ? 'active' : ''}`}
            onClick={() => navigateToTab('partners')}
          >
            Partners ({company.total_partners || 0})
          </button>
          <button
            className={`tab-button ${currentTab === 'trends' ? 'active' : ''}`}
            onClick={() => navigateToTab('trends')}
          >
            Trends
          </button>
        </div>

        {/* Tab Content - Overview */}
        <div className="tab-content">
          <h2>Company Overview</h2>
          
          {/* Key Metrics */}
          <div className="info-cards-grid">
            <div className="info-card">
              <h4>Estimated Revenue</h4>
              <div className="info-card-value">{formatCurrency(company.estimated_revenue)}</div>
            </div>
            <div className="info-card">
              <h4>Trade Volume</h4>
              <div className="info-card-value">{formatCurrency(company.trade_volume)}</div>
            </div>
            <div className="info-card">
              <h4>Partner Diversity Score</h4>
              <div className="info-card-value">{company.partner_diversity_score || 0}/100</div>
            </div>
            <div className="info-card">
              <h4>Active Since</h4>
              <div className="info-card-value">
                {company.active_since ? new Date(company.active_since).getFullYear() : 'N/A'}
              </div>
            </div>
          </div>

          {/* Top 3 Products */}
          <div style={{ marginTop: '2rem' }}>
            <h3>Top Traded Products</h3>
            <div className="products-grid" style={{ marginTop: '1rem' }}>
              {company.products && company.products.slice(0, 3).map((product, idx) => (
                <div key={idx} className="info-card">
                  <h4>{product.product_name}</h4>
                  <div className="stat-item">
                    <span className="stat-label">Avg Price</span>
                    <span className="stat-value">{formatCurrency(product.avg_price)}</span>
                  </div>
                  <div className="stat-item" style={{ marginTop: '0.5rem' }}>
                    <span className="stat-label">Volume</span>
                    <span className="stat-value">
                      {new Intl.NumberFormat('en-US').format(product.volume)} {product.unit}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Similar Companies - Placeholder */}
          <div style={{ marginTop: '2rem' }}>
            <h3>Similar Companies</h3>
            <p style={{ color: '#718096', marginTop: '1rem' }}>
              Coming soon - AI-powered similar company recommendations
            </p>
          </div>
        </div>
      </div>
    </>
  );
};

export default CompanyOverview;
