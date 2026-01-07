import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import ExportButton from '../Common/ExportButton';
import './TradeIntelligence.css';

const CompanyOverview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const loc = useLocation();
  const [comp, setComp] = useState(null);
  const [load, setLoad] = useState(true);
  const [error, setError] = useState(null);

  
  const companyName = decodeURIComponent(id);
  const tab = loc.pathname.split('/').pop();

  useEffect(() => {
    loadComp();
  }, [id]);

  const loadComp = async () => {
    setLoad(true);
    setError(null);
    try {
      
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
    if (!v) return '';
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h1>{companyName}</h1>
              <p>Trade Intelligence Profile</p>
              <div className="company-tags">
                {comp.reputation_tags && comp.reputation_tags.map((tag, idx) => (
                  <span key={idx} className="company-tag">{tag}</span>
                ))}
              </div>
            </div>
            <ExportButton
              data={[{
                company_name: companyName,
                trade_volume: comp.total_volume,
                avg_price: comp.avg_price,
                total_transactions: comp.total_transactions,
                yoy_growth: comp.yoy_growth,
                total_products: comp.total_products,
                total_partners: comp.total_partners,
                pagerank: comp.network_influence?.pagerank,
                network_degree: comp.network_influence?.degree,
              }]}
              columns={[
                { key: 'company_name', label: 'Company' },
                { key: 'trade_volume', label: 'Trade Volume' },
                { key: 'avg_price', label: 'Avg Price' },
                { key: 'total_transactions', label: 'Transactions' },
                { key: 'yoy_growth', label: 'YoY Growth %' },
                { key: 'total_products', label: 'Products' },
                { key: 'total_partners', label: 'Partners' },
              ]}
              filename={`company-overview-${companyName}`}
              title={`${companyName} - Company Overview`}
            />
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
            {comp.total_volume > 0 && (
              <div className="info-card">
                <h4>Trade Volume</h4>
                <div className="info-card-value">
                  {new Intl.NumberFormat('en-US').format(comp.total_volume)} MT
                </div>
              </div>
            )}
            {comp.avg_price > 0 && (
              <div className="info-card">
                <h4>Average Price</h4>
                <div className="info-card-value">{fmtCurr(comp.avg_price)}</div>
              </div>
            )}
            {comp.total_transactions > 0 && (
              <div className="info-card">
                <h4>Total Transactions</h4>
                <div className="info-card-value">{comp.total_transactions}</div>
              </div>
            )}
            {comp.yoy_growth !== null && comp.yoy_growth !== undefined && !isNaN(comp.yoy_growth) && (
              <div className="info-card">
                <h4>YoY Growth</h4>
                <div className="info-card-value" style={{
                  color: comp.yoy_growth >= 0 ? '#22c55e' : '#ef4444'
                }}>
                  {`${comp.yoy_growth >= 0 ? '+' : ''}${comp.yoy_growth.toFixed(1)}%`}
                </div>
              </div>
            )}
            {comp.network_influence && comp.network_influence.pagerank > 0 && (
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
            {comp.products && comp.products.length > 0 && (
              <div className="products-grid" style={{ marginTop: '1rem' }}>
                {comp.products.slice(0, 3).map((p, idx) => (
                  <div key={idx} className="info-card">
                    <h4>{p.product_name || p.name}</h4>
                    <div className="stat-item">
                      <span className="stat-label">Avg Price</span>
                      <span className="stat-value">{fmtCurr(p.avg_price)}</span>
                    </div>
                    <div className="stat-item" style={{ marginTop: '0.5rem' }}>
                      <span className="stat-label">Volume</span>
                      <span className="stat-value">
                        {new Intl.NumberFormat('en-US').format(p.volume || p.vol)} {p.unit || 'MT'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {}
          {comp.country_distribution && comp.country_distribution.length > 0 && (
            <div style={{ marginTop: '2rem' }}>
              <h3>Trade by Country</h3>
              <div className="partners-grid" style={{ marginTop: '1rem' }}>
                {comp.country_distribution.slice(0, 5).map((c, idx) => (
                  <div key={idx} className="partner-card">
                    <div className="partner-country">{c.name}</div>
                    <div className="partner-volume">{fmtCurr(c.value)}</div>
                    <div style={{ fontSize: '0.8rem', color: '#718096', marginTop: '0.25rem' }}>
                      {new Intl.NumberFormat('en-US', {maximumFractionDigits: 0}).format(c.volume)} MT
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {}
          <div style={{ marginTop: '2rem' }}>
            <h3>Similar Companies (AI Recommended)</h3>
            {comp.similar_companies && comp.similar_companies.length > 0 ? (
              <div className="partners-grid" style={{ marginTop: '1rem' }}>
                {comp.similar_companies.map((sc, idx) => (
                  <div 
                    key={idx} 
                    className="partner-card" 
                    style={{ cursor: 'pointer', transition: 'transform 0.2s' }}
                    onClick={() => navigate(`/trade-intelligence/company/${encodeURIComponent(sc.company_name)}/overview`)}
                    onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                    onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                  >
                    <div className="partner-country">{sc.company_name}</div>
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      gap: '0.5rem',
                      marginTop: '0.5rem'
                    }}>
                      <span className="segment-badge" style={{ 
                        background: `hsl(${Math.floor((sc.similarity || sc.similarity_score || 0) * 120)}, 70%, 45%)`,
                        color: 'white'
                      }}>
                        {((sc.similarity || sc.similarity_score || 0) * 100).toFixed(0)}% Match
                      </span>
                    </div>
                    {sc.cluster_tag && (
                      <div style={{ fontSize: '0.8rem', color: '#718096', marginTop: '0.5rem' }}>
                        {sc.cluster_tag}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#718096', marginTop: '1rem' }}>
                No similar companies found based on trade patterns.
              </p>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default CompanyOverview;

