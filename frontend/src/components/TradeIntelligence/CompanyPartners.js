import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const CompanyPartners = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const loc = useLocation();
  const [parts, setParts] = useState(null);
  const [load, setLoad] = useState(true);
  const [error, setError] = useState(null);

  // Decode the company name from URL
  const companyName = decodeURIComponent(id);
  const tab = loc.pathname.split('/').pop();

  useEffect(() => {
    loadParts();
  }, [id]);

  const loadParts = async () => {
    setLoad(true);
    setError(null);
    try {
      // Use correct API endpoint: /api/company/{company_name}/partners/
      const res = await fetch(`http://localhost:8000/api/company/${id}/partners/`, {
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        setParts(data);
      } else {
        setError('Could not load partners');
      }
    } catch (err) {
      console.error('Failed to load partners:', err);
      setError('Failed to load partners data');
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

  // Get top partners from API response
  const topPartners = parts?.top_partners || [];
  const tradeByCountry = parts?.trade_volume_by_country || [];

  if (load) {
    return (
      <>
        <Navbar />
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading partners...</p>
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
          <h2>Partner Network</h2>

          {error ? (
            <div className="empty-state">
              <p>{error}</p>
            </div>
          ) : (
            <>
              <div className="info-cards-grid">
                <div className="info-card">
                  <h4>Top Partners</h4>
                  <div className="info-card-value">{topPartners.length}</div>
                </div>
                <div className="info-card">
                  <h4>Countries</h4>
                  <div className="info-card-value">{tradeByCountry.length}</div>
                </div>
              </div>

              <div style={{ marginTop: '2rem' }}>
                <h3>Top Partners</h3>
                {topPartners.length > 0 ? (
                  <div className="partners-grid">
                    {topPartners.map((p, idx) => (
                      <div key={idx} className="partner-card">
                        <div className="partner-country">{p.partner}</div>
                        <div className="partner-volume">
                          {fmtCurr(p.total_volume)}
                        </div>
                        <div style={{ fontSize: '0.85rem', color: '#718096', marginTop: '0.5rem' }}>
                          {p.transaction_count} transactions
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: '#718096', marginTop: '1rem' }}>No partners found</p>
                )}
              </div>

              <div style={{ marginTop: '2rem' }}>
                <h3>Trade Volume by Country</h3>
                {tradeByCountry.length > 0 ? (
                  <div className="partners-grid">
                    {tradeByCountry.map((c, idx) => (
                      <div key={idx} className="partner-card">
                        <div className="partner-country">{c.country}</div>
                        <div className="partner-volume">
                          {fmtCurr(c.total_volume)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: '#718096', marginTop: '1rem' }}>No country data available</p>
                )}
              </div>

              {topPartners.length > 0 && (
                <div style={{ marginTop: '2rem' }}>
                  <h3>All Partners</h3>
                  <table className="products-table" style={{ marginTop: '1rem' }}>
                    <thead>
                      <tr>
                        <th>Partner</th>
                        <th>Trade Volume</th>
                        <th>Transactions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topPartners.map((p, idx) => (
                        <tr key={idx}>
                          <td><strong>{p.partner}</strong></td>
                          <td>{fmtCurr(p.total_volume)}</td>
                          <td>{p.transaction_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default CompanyPartners;

