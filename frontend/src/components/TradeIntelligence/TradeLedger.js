import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const TradeLedger = () => {
  const navigate = useNavigate();
  const [comps, setComps] = useState([]);
  const [cats, setCats] = useState([]);
  const [load, setLoad] = useState(true);
  const [stats, setStats] = useState(null);
  
  const [filts, setFilts] = useState({
    country: '',
    product: '',
    type: '',
    dateFrom: '',
    dateTo: ''
  });

  useEffect(() => {
    loadCats();
    loadComps();
  }, []);

  useEffect(() => {
    loadComps();
  }, [filts]);

  const loadCats = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/trade-ledger/product-categories/');
      if (res.ok) {
        const data = await res.json();
        setCats(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadComps = async () => {
    setLoad(true);
    try {
      const p = new URLSearchParams();
      if (filts.country) p.append('country', filts.country);
      if (filts.product) p.append('product', filts.product);
      if (filts.type) p.append('type', filts.type);
      if (filts.dateFrom) p.append('date_from', filts.dateFrom);
      if (filts.dateTo) p.append('date_to', filts.dateTo);

      const res = await fetch(`http://localhost:8000/api/trade-ledger/companies/?${p}`);
      if (res.ok) {
        const data = await res.json();
        setComps(data);
      }

      if (filts.product) {
        const sRes = await fetch(
          `http://localhost:8000/api/trade-ledger/companies/statistics/?product=${filts.product}&${p}`
        );
        if (sRes.ok) {
          const sData = await sRes.json();
          setStats(sData);
        }
      } else {
        setStats(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoad(false);
    }
  };

  const onFiltChange = (f, v) => {
    setFilts(prev => ({ ...prev, [f]: v }));
  };

  const onCompClick = (id) => {
    navigate(`/trade-intelligence/company/${id}/overview`);
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

  const fmtPct = (v) => {
    if (v === null || v === undefined) return 'N/A';
    return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
  };

  return (
    <>
      <Navbar />
      <div className="trade-ledger-container">
        <div className="trade-ledger-header">
          <h1>📊 Trade Ledger</h1>
          <p>Comprehensive trade intelligence and company analytics</p>
        </div>

        <div className="filters-section">
          <div className="filters-grid">
            <div className="filter-group">
              <label>Country</label>
              <input
                type="text"
                placeholder="Search by country..."
                value={filts.country}
                onChange={(e) => onFiltChange('country', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>Product Category</label>
              <select
                value={filts.product}
                onChange={(e) => onFiltChange('product', e.target.value)}
              >
                <option value="">All Products</option>
                {cats.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Company Type</label>
              <select
                value={filts.type}
                onChange={(e) => onFiltChange('type', e.target.value)}
              >
                <option value="">All Types</option>
                <option value="exporter">Exporter</option>
                <option value="importer">Importer</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Date From</label>
              <input
                type="date"
                value={filts.dateFrom}
                onChange={(e) => onFiltChange('dateFrom', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>Date To</label>
              <input
                type="date"
                value={filts.dateTo}
                onChange={(e) => onFiltChange('dateTo', e.target.value)}
              />
            </div>
          </div>
        </div>

        {stats && filts.product && (
          <div className="metrics-row">
            <div className="metric-card">
              <h3>Average Price</h3>
              <div className="metric-value">{fmtCurr(stats.avg_price)}</div>
              <p className="metric-subtext">Across all companies</p>
            </div>
            <div className="metric-card">
              <h3>YoY Growth</h3>
              <div className="metric-value" style={{
                color: stats.avg_yoy_growth >= 0 ? '#22c55e' : '#ef4444'
              }}>
                {fmtPct(stats.avg_yoy_growth)}
              </div>
              <p className="metric-subtext">Year-over-year</p>
            </div>
            <div className="metric-card">
              <h3>Total Volume</h3>
              <div className="metric-value">
                {stats.total_volume 
                  ? new Intl.NumberFormat('en-US').format(stats.total_volume) 
                  : 'N/A'}
              </div>
              <p className="metric-subtext">Combined volume</p>
            </div>
            <div className="metric-card">
              <h3>Total Companies</h3>
              <div className="metric-value">{stats.total_companies || comps.length}</div>
              <p className="metric-subtext">In this category</p>
            </div>
          </div>
        )}

        {load ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading companies...</p>
          </div>
        ) : comps.length === 0 ? (
          <div className="empty-state">
            <h2>No companies found</h2>
            <p>Try adjusting your filters</p>
          </div>
        ) : (
          <div className="companies-grid">
            {comps.map(c => (
              <div
                key={c.id}
                className="company-card"
                onClick={() => onCompClick(c.id)}
              >
                <div className="company-card-header">
                  <div>
                    <h3>{c.company.name}</h3>
                    <p className="company-location">
                      📍 {c.company.province}, {c.company.country}
                    </p>
                  </div>
                  {c.is_exporter && c.is_importer ? (
                    <span className="company-badge">Both</span>
                  ) : c.is_exporter ? (
                    <span className="company-badge">Exporter</span>
                  ) : (
                    <span className="company-badge">Importer</span>
                  )}
                </div>

                <div className="company-stats">
                  <div className="stat-item">
                    <span className="stat-label">Est. Revenue</span>
                    <span className="stat-value">
                      {fmtCurr(c.estimated_revenue)}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Trade Volume</span>
                    <span className="stat-value">
                      {fmtCurr(c.trade_volume)}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Products</span>
                    <span className="stat-value">{c.top_products?.length || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Active Since</span>
                    <span className="stat-value">
                      {c.active_since 
                        ? new Date(c.active_since).getFullYear()
                        : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
};

export default TradeLedger;
