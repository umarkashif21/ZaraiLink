import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const CompanyProducts = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const loc = useLocation();
  const [comp, setComp] = useState(null);
  const [prods, setProds] = useState([]);
  const [load, setLoad] = useState(true);

  const tab = loc.pathname.split('/').pop();

  useEffect(() => {
    loadData();
    loadProds();
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

  const loadProds = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/trade-ledger/companies/${id}/products/`);
      if (res.ok) {
        const data = await res.json();
        setProds(data);
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
      currency: v.currency || 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(v);
  };

  const fmtPct = (v) => {
    if (v === null || v === undefined) return 'N/A';
    return `${v >= 0 ? '+' : ''}${parseFloat(v).toFixed(2)}%`;
  };

  if (load) {
    return (
      <>
        <Navbar />
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading products...</p>
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
          <h2>Product Performance</h2>

          {prods.length === 0 ? (
            <div className="empty-state">
              <p>No products found</p>
            </div>
          ) : (
            <table className="products-table">
              <thead>
                <tr>
                  <th>Product Name</th>
                  <th>Category</th>
                  <th>Avg Price</th>
                  <th>Volume</th>
                  <th>YoY Growth</th>
                </tr>
              </thead>
              <tbody>
                {prods.map((p, idx) => (
                  <tr key={idx}>
                    <td>
                      <strong>{p.product_name}</strong>
                      {p.hs_code && (
                        <div style={{ fontSize: '0.85rem', color: '#718096' }}>
                          HS Code: {p.hs_code}
                        </div>
                      )}
                    </td>
                    <td>{p.category_name || 'N/A'}</td>
                    <td>
                      {new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: p.currency || 'USD'
                      }).format(p.avg_price)}
                    </td>
                    <td>
                      {new Intl.NumberFormat('en-US').format(p.volume)} {p.unit}
                    </td>
                    <td>
                      {p.yoy_growth !== null && p.yoy_growth !== undefined ? (
                        <span className={`growth-badge ${parseFloat(p.yoy_growth) >= 0 ? 'positive' : 'negative'}`}>
                          {fmtPct(p.yoy_growth)}
                        </span>
                      ) : (
                        'N/A'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {prods.length > 0 && (
            <div style={{ marginTop: '2rem' }}>
              <h3>Product Analysis Charts</h3>
              <p style={{ color: '#718096', marginTop: '1rem' }}>
                Interactive charts showing product volume distribution, price trends, 
                and performance metrics are being prepared with real-time data.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default CompanyProducts;
