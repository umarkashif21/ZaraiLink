import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const CompanyPartners = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const loc = useLocation();
  const [comp, setComp] = useState(null);
  const [parts, setParts] = useState([]);
  const [load, setLoad] = useState(true);

  const tab = loc.pathname.split('/').pop();

  useEffect(() => {
    loadData();
    loadParts();
  }, [id]);

  const loadData = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/trade-ledger/companies/${id}/`);
      if (res.ok) {
        const data = await res.json();
        setComp(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadParts = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/trade-ledger/companies/${id}/partners/`);
      if (res.ok) {
        const data = await res.json();
        setParts(data);
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

  const topExps = () => {
    return parts
      .filter(p => p.is_export)
      .sort((a, b) => parseFloat(b.trade_volume) - parseFloat(a.trade_volume))
      .slice(0, 5);
  };

  const topPorts = () => {
    return parts
      .filter(p => p.port_name)
      .sort((a, b) => parseFloat(b.trade_volume) - parseFloat(a.trade_volume))
      .slice(0, 5);
  };

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
        {comp && (
          <>
            <div className="company-detail-header">
              <h1>{comp.company.name}</h1>
              <p>📍 {comp.company.province}, {comp.company.country}</p>
              <div className="company-tags">
                {comp.is_exporter && <span className="company-tag">Exporter</span>}
                {comp.is_importer && <span className="company-tag">Importer</span>}
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
          </>
        )}

        <div className="tab-content">
          <h2>Partner Network</h2>

          {comp && (
            <div className="info-cards-grid">
              <div className="info-card">
                <h4>Partner Diversity Score</h4>
                <div className="info-card-value">{comp.partner_diversity_score || 0}/100</div>
              </div>
              <div className="info-card">
                <h4>Total Partner Countries</h4>
                <div className="info-card-value">{comp.total_partners || 0}</div>
              </div>
              <div className="info-card">
                <h4>Export Partners</h4>
                <div className="info-card-value">
                  {parts.filter(p => p.is_export).length}
                </div>
              </div>
              <div className="info-card">
                <h4>Import Partners</h4>
                <div className="info-card-value">
                  {parts.filter(p => !p.is_export).length}
                </div>
              </div>
            </div>
          )}

          <div style={{ marginTop: '2rem' }}>
            <h3>Top Exporting Countries</h3>
            {topExps().length > 0 ? (
              <div className="partners-grid">
                {topExps().map((p, idx) => (
                  <div key={idx} className="partner-card">
                    <div className="partner-country">{p.country}</div>
                    <div className="partner-volume">
                      {fmtCurr(p.trade_volume)}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#718096', marginTop: '0.5rem' }}>
                      {parseFloat(p.percentage_share).toFixed(1)}% of total
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#718096', marginTop: '1rem' }}>No export partners found</p>
            )}
          </div>

          <div style={{ marginTop: '2rem' }}>
            <h3>Top Ports of Entry</h3>
            {topPorts().length > 0 ? (
              <div className="partners-grid">
                {topPorts().map((p, idx) => (
                  <div key={idx} className="partner-card">
                    <div className="partner-country">{p.port_name}</div>
                    <div style={{ fontSize: '0.9rem', color: '#718096', marginTop: '0.3rem' }}>
                      {p.country}
                    </div>
                    <div className="partner-volume" style={{ marginTop: '0.5rem' }}>
                      {fmtCurr(p.trade_volume)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#718096', marginTop: '1rem' }}>No port information available</p>
            )}
          </div>

          {parts.length > 0 && (
            <div style={{ marginTop: '2rem' }}>
              <h3>All Partners</h3>
              <table className="products-table" style={{ marginTop: '1rem' }}>
                <thead>
                  <tr>
                    <th>Country</th>
                    <th>Port</th>
                    <th>Type</th>
                    <th>Trade Volume</th>
                    <th>Share</th>
                  </tr>
                </thead>
                <tbody>
                  {parts.map((p, idx) => (
                    <tr key={idx}>
                      <td><strong>{p.country}</strong></td>
                      <td>{p.port_name || 'N/A'}</td>
                      <td>
                        <span className={`growth-badge ${p.is_export ? 'positive' : 'negative'}`}>
                          {p.is_export ? 'Export' : 'Import'}
                        </span>
                      </td>
                      <td>{fmtCurr(p.trade_volume)}</td>
                      <td>{parseFloat(p.percentage_share).toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default CompanyPartners;
