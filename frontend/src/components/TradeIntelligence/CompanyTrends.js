import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const CompanyTrends = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const loc = useLocation();
  const [comp, setComp] = useState(null);
  const [trds, setTrds] = useState([]);
  const [load, setLoad] = useState(true);

  const tab = loc.pathname.split('/').pop();

  useEffect(() => {
    loadData();
    loadTrds();
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

  const loadTrds = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/trade-ledger/companies/${id}/trends/`);
      if (res.ok) {
        const data = await res.json();
        setTrds(data);
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
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(v);
  };

  const recTrds = () => {
    return [...trds]
      .sort((a, b) => {
        if (b.year !== a.year) return b.year - a.year;
        return b.month - a.month;
      })
      .slice(0, 12);
  };

  const qGrowth = () => {
    const qs = {};
    trds.forEach(t => {
      const q = Math.ceil(t.month / 3);
      const k = `${t.year}-Q${q}`;
      if (!qs[k]) {
        qs[k] = { count: 0, total: 0, year: t.year, q };
      }
      if (t.yoy_volume_growth !== null) {
        qs[k].count += 1;
        qs[k].total += parseFloat(t.yoy_volume_growth);
      }
    });

    return Object.entries(qs)
      .map(([k, d]) => ({
        label: k,
        growth: d.count > 0 ? (d.total / d.count).toFixed(2) : 0
      }))
      .slice(-8);
  };

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
          <h2>Trade Trends & Analytics</h2>

          {trds.length === 0 ? (
            <div className="empty-state">
              <p>No trend data available</p>
            </div>
          ) : (
            <>
              <div style={{ marginTop: '2rem' }}>
                <h3>Monthly Volume vs Avg Price (Recent 12 Months)</h3>
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
                    {recTrds().map((t, idx) => (
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
                  {qGrowth().map((q, idx) => (
                    <div key={idx} className="info-card">
                      <h4>{q.label}</h4>
                      <div className="info-card-value" style={{
                        color: parseFloat(q.growth) >= 0 ? '#22c55e' : '#ef4444'
                      }}>
                        {parseFloat(q.growth) >= 0 ? '+' : ''}{q.growth}%
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
