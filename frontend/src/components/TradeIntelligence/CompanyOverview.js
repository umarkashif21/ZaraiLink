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

  const tab = loc.pathname.split('/').pop();

  useEffect(() => {
    loadComp();
  }, [id]);

  const loadComp = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/trade-ledger/companies/${id}/`);
      if (res.ok) {
        const data = await res.json();
        setComp(data);
      }
    } catch (err) {
      console.error(err);
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

  if (!comp) {
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
        <div className="company-detail-header">
          <h1>{comp.company.name}</h1>
          <p>📍 {comp.company.province}, {comp.company.country}</p>
          <div className="company-tags">
            {comp.is_exporter && <span className="company-tag">Exporter</span>}
            {comp.is_importer && <span className="company-tag">Importer</span>}
            {comp.company.sector && <span className="company-tag">{comp.company.sector.name}</span>}
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
              <h4>Estimated Revenue</h4>
              <div className="info-card-value">{fmtCurr(comp.estimated_revenue)}</div>
            </div>
            <div className="info-card">
              <h4>Trade Volume</h4>
              <div className="info-card-value">{fmtCurr(comp.trade_volume)}</div>
            </div>
            <div className="info-card">
              <h4>Partner Diversity Score</h4>
              <div className="info-card-value">{comp.partner_diversity_score || 0}/100</div>
            </div>
            <div className="info-card">
              <h4>Active Since</h4>
              <div className="info-card-value">
                {comp.active_since ? new Date(comp.active_since).getFullYear() : 'N/A'}
              </div>
            </div>
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
