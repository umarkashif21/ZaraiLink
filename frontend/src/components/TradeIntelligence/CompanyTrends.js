import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const CompanyTrends = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const loc = useLocation();
  const [trds, setTrds] = useState(null);
  const [load, setLoad] = useState(true);
  const [error, setError] = useState(null);

  // Decode the company name from URL
  const companyName = decodeURIComponent(id);
  const tab = loc.pathname.split('/').pop();

  useEffect(() => {
    loadTrds();
  }, [id]);

  const loadTrds = async () => {
    setLoad(true);
    setError(null);
    try {
      // Use correct API endpoint: /api/company/{company_name}/trends/
      const res = await fetch(`http://localhost:8000/api/company/${id}/trends/`, {
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        setTrds(data);
      } else {
        setError('Could not load trends');
      }
    } catch (err) {
      console.error('Failed to load trends:', err);
      setError('Failed to load trends data');
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
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(v);
  };

  // Get data from API response
  const volumePriceTrend = trds?.volume_price_trend || [];
  const quarterlyVolume = trds?.quarterly_volume || [];

  if (load) {
    return (
      <>
        <Navbar />
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading trends...</p>
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
            Products
          </button>
          <button
            className={`tab-button ${tab === 'partners' ? 'active' : ''}`}
            onClick={() => navTab('partners')}
          >
            Partners
          </button>
          <button
            className={`tab-button ${tab === 'trends' ? 'active' : ''}`}
            onClick={() => navTab('trends')}
          >
            Trends
          </button>
        </div>

        <div className="tab-content">
          <h2>Trade Trends & Analytics</h2>

          {error ? (
            <div className="empty-state">
              <p>{error}</p>
            </div>
          ) : !volumePriceTrend || volumePriceTrend.length === 0 ? (
            <div className="empty-state">
              <p>No trend data available</p>
            </div>
          ) : (
            <>
              <div style={{ marginTop: '2rem' }}>
                <h3>Monthly Volume vs Avg Price (Recent Data)</h3>
                <table className="products-table" style={{ marginTop: '1rem' }}>
                  <thead>
                    <tr>
                      <th>Period</th>
                      <th>Product</th>
                      <th>Volume</th>
                      <th>Avg Price</th>
                      <th>YoY Volume Growth</th>
                      <th>YoY Price Growth</th>
                    </tr>
                  </thead>
                  <tbody>
                    {volumePriceTrend.map((t, idx) => (
                      <tr key={idx}>
                        <td>
                          <strong>{t.month_name} {t.year}</strong>
                        </td>
                        <td>{t.product_name || 'All Products'}</td>
                        <td>{new Intl.NumberFormat('en-US').format(t.volume)}</td>
                        <td>{fmtCurr(t.avg_price)}</td>
                        <td>
                          {t.yoy_volume_growth !== null ? (
                            <span className={`growth-badge ${parseFloat(t.yoy_volume_growth) >= 0 ? 'positive' : 'negative'}`}>
                              {parseFloat(t.yoy_volume_growth) >= 0 ? '+' : ''}
                              {parseFloat(t.yoy_volume_growth).toFixed(2)}%
                            </span>
                          ) : (
                            'N/A'
                          )}
                        </td>
                        <td>
                          {t.yoy_price_growth !== null ? (
                            <span className={`growth-badge ${parseFloat(t.yoy_price_growth) >= 0 ? 'positive' : 'negative'}`}>
                              {parseFloat(t.yoy_price_growth) >= 0 ? '+' : ''}
                              {parseFloat(t.yoy_price_growth).toFixed(2)}%
                            </span>
                          ) : (
                            'N/A'
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ marginTop: '2rem' }}>
                <h3>YoY Volume Growth By Quarter</h3>
                <div className="info-cards-grid" style={{ marginTop: '1rem' }}>
                  {quarterlyVolume.map((q, idx) => (
                    <div key={idx} className="info-card">
                      <h4>{q.year}-Q{q.quarter}</h4>
                      <div className="info-card-value" style={{
                        color: parseFloat(q.yoy_growth || 0) >= 0 ? '#22c55e' : '#ef4444'
                      }}>
                        {q.yoy_growth !== null && q.yoy_growth !== undefined
                          ? `${parseFloat(q.yoy_growth) >= 0 ? '+' : ''}${parseFloat(q.yoy_growth).toFixed(2)}%`
                          : 'N/A'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ marginTop: '2rem' }}>
                <h3>Interactive Charts & Visualizations</h3>
                <p style={{ color: '#718096', marginTop: '1rem' }}>
                  Advanced visualizations including dual-axis charts for Monthly Volume vs Avg Price,
                  stacked area charts for Product Mix Over Time, and seasonal pattern analysis
                  are available with the complete dataset.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default CompanyTrends;

