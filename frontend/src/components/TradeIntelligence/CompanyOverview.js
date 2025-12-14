import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const CompanyOverview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const loc = useLocation();
  const [comp, setComp] = useState(null);
  const [load, setLoad] = useState(true);
  const [error, setError] = useState(null);

  // Decode the company name from URL
  const companyName = decodeURIComponent(id);
  const tab = loc.pathname.split('/').pop();

  useEffect(() => {
    loadComp();
  }, [id]);

  const loadComp = async () => {
    setLoad(true);
    setError(null);
    try {
      // Use correct API endpoint: /api/company/{company_name}/overview/
      const res = await fetch(`http://localhost:8000/api/company/${id}/overview/`, {
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        setComp(data);
      } else {
        setError('Company not found');
      }
    } catch (err) {
      console.error('Failed to load company:', err);
      setError('Failed to load company data');
    } finally {
      setLoad(false);
    }
  };

  const navTab = (t) => {
    navigate(`/trade-intelligence/company/${id}/${t}`);
  };

  const fmtCurr = (v) => {
    if (!v) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(v);
  };

  if (load) {
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

  if (!comp || error) {
    return (
      <>
        <Navbar />
        <div className="empty-state">
          <h2>{error || 'Company not found'}</h2>
          <p>The company "{companyName}" could not be loaded.</p>
          <button 
            onClick={() => navigate('/trade-intelligence/ledger')}
            className="btn-primary"
            style={{ marginTop: '1rem' }}
          >
            Back to Trade Ledger
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="company-detail-container">
        <div className="company-detail-header">
          <h1>{companyName}</h1>
          <p>📍 Trade Intelligence Profile</p>
          <div className="company-tags">
            {comp.reputation_tags && comp.reputation_tags.map((tag, idx) => (
              <span key={idx} className="company-tag">{tag}</span>
            ))}
          </div>
        </div>

        <div className="tab-navigation">
          <button
            className={`tab-button ${tab === 'overview' ? 'active' : ''}`}
            onClick={() => navTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab-button ${tab === 'products' ? 'active' : ''}`}
            onClick={() => navTab('products')}
          >
            Products ({comp.total_products || 0})
          </button>
          <button
            className={`tab-button ${tab === 'partners' ? 'active' : ''}`}
            onClick={() => navTab('partners')}
          >
            Partners ({comp.total_partners || 0})
          </button>
          <button
            className={`tab-button ${tab === 'trends' ? 'active' : ''}`}
            onClick={() => navTab('trends')}
          >
            Trends
          </button>
        </div>

        <div className="tab-content">
          <h2>Company Overview</h2>
          
          <div className="info-cards-grid">
            <div className="info-card">
              <h4>Trade Volume</h4>
              <div className="info-card-value">{fmtCurr(comp.total_volume)}</div>
            </div>
            <div className="info-card">
              <h4>Average Price</h4>
              <div className="info-card-value">{fmtCurr(comp.avg_price)}</div>
            </div>
            <div className="info-card">
              <h4>Total Transactions</h4>
              <div className="info-card-value">{comp.total_transactions || 0}</div>
            </div>
            <div className="info-card">
              <h4>YoY Growth</h4>
              <div className="info-card-value" style={{
                color: (comp.yoy_growth || 0) >= 0 ? '#22c55e' : '#ef4444'
              }}>
                {comp.yoy_growth !== null && comp.yoy_growth !== undefined 
                  ? `${comp.yoy_growth >= 0 ? '+' : ''}${comp.yoy_growth.toFixed(1)}%`
                  : 'N/A'}
              </div>
            </div>
            {comp.network_influence && (
              <>
                <div className="info-card">
                  <h4>Network Influence</h4>
                  <div className="info-card-value">
                    {(comp.network_influence.pagerank * 100).toFixed(2)}%
                  </div>
                  <p style={{ fontSize: '0.8rem', color: '#718096' }}>PageRank Score</p>
                </div>
                <div className="info-card">
                  <h4>Network Connections</h4>
                  <div className="info-card-value">{comp.network_influence.degree}</div>
                  <p style={{ fontSize: '0.8rem', color: '#718096' }}>Trade Partners</p>
                </div>
              </>
            )}
          </div>

          <div style={{ marginTop: '2rem' }}>
            <h3>Top Traded Products</h3>
            <div className="products-grid" style={{ marginTop: '1rem' }}>
              {comp.products && comp.products.slice(0, 3).map((p, idx) => (
                <div key={idx} className="info-card">
                  <h4>{p.product_name}</h4>
                  <div className="stat-item">
                    <span className="stat-label">Avg Price</span>
                    <span className="stat-value">{fmtCurr(p.avg_price)}</span>
                  </div>
                  <div className="stat-item" style={{ marginTop: '0.5rem' }}>
                    <span className="stat-label">Volume</span>
                    <span className="stat-value">
                      {new Intl.NumberFormat('en-US').format(p.volume)} {p.unit}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

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
