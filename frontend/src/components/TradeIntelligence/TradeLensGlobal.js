import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import Breadcrumb from '../Common/Breadcrumb';
import './TradeIntelligence.css';

const TradeLensGlobal = () => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadGlobalData();
  }, [productId]);

  const loadGlobalData = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/trade-lens/products/${productId}/global_view/`,
        { credentials: 'include' }
      );
      if (!response.ok) throw new Error('Failed to load global data');
      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (!value) return '$0';
    if (value >= 1000000000) return `$${(value / 1000000000).toFixed(1)}B`;
    if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
    return `$${value.toFixed(0)}`;
  };

  const formatNumber = (value) => {
    if (!value) return '0';
    return new Intl.NumberFormat('en-US').format(Math.round(value));
  };

  const tabs = [
    { id: 'overview', label: 'Overview', path: 'overview' },
    { id: 'summary', label: 'Summary', path: 'summary' },
    { id: 'comparison', label: 'Comparison', path: 'comparison' },
    { id: 'details', label: 'Details', path: 'details' },
    { id: 'global', label: 'Global View', path: 'global' },
  ];

  const handleTabClick = (path) => {
    navigate(`/trade-intelligence/lens/${productId}/${path}`);
  };

  const getProductIcon = (category) => {
    const icons = {
      'Cereals': '🌾', 'Textiles': '🧵', 'Fruits': '🥭',
      'Medical Equipment': '🏥', 'Sports Equipment': '⚽', 'Leather Products': '👜',
    };
    return icons[category] || '📦';
  };

  const getCountryFlag = (country) => {
    const flags = {
      'United States': '🇺🇸', 'China': '🇨🇳', 'United Arab Emirates': '🇦🇪',
      'United Kingdom': '🇬🇧', 'Germany': '🇩🇪', 'Saudi Arabia': '🇸🇦',
      'Afghanistan': '🇦🇫', 'Netherlands': '🇳🇱', 'Italy': '🇮🇹',
      'Bangladesh': '🇧🇩', 'Turkey': '🇹🇷', 'Malaysia': '🇲🇾', 'Pakistan': '🇵🇰',
    };
    return flags[country] || '🌍';
  };

  return (
    <>
      <Navbar />
      <div className="trade-lens-subpage-container">
        <Breadcrumb />

        <div className="trade-lens-subpage-header">
          <div className="product-info">
            <div className="product-icon">
              {getProductIcon(data?.product?.category)}
            </div>
            <div className="product-details">
              <h1>{data?.product?.name || 'Loading...'}</h1>
              <p>HS Code: {data?.product?.hs_code} | {data?.product?.category}</p>
            </div>
          </div>
        </div>

        <div className="trade-lens-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`trade-lens-tab ${tab.id === 'global' ? 'active' : ''}`}
              onClick={() => handleTabClick(tab.path)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="trade-lens-content">
          {loading ? (
            <div className="loading-container">
              <div className="spinner"></div>
            </div>
          ) : (
            <>
              <div className="trade-lens-overview-grid" style={{ marginBottom: '2rem' }}>
                <div className="trade-lens-overview-card primary">
                  <div className="card-value">{formatCurrency(data?.total_trade_value)}</div>
                  <div className="card-label">Total Trade Value</div>
                </div>
                <div className="trade-lens-overview-card">
                  <div className="card-value">{formatCurrency(data?.total_export_value)}</div>
                  <div className="card-label">Export Value</div>
                </div>
                <div className="trade-lens-overview-card">
                  <div className="card-value">{formatCurrency(data?.total_import_value)}</div>
                  <div className="card-label">Import Value</div>
                </div>
                <div className="trade-lens-overview-card">
                  <div className="card-value">{data?.countries?.length || 0}</div>
                  <div className="card-label">Trading Partners</div>
                </div>
              </div>

              <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-primary)' }}>
                Global Trade Distribution
              </h3>

              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', 
                gap: '1rem' 
              }}>
                {data?.countries?.map((country, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'var(--bg-tertiary)',
                      borderRadius: '12px',
                      padding: '1.5rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      transition: 'all 0.2s',
                      cursor: 'pointer',
                    }}
                    className="country-card-hover"
                  >
                    <div style={{ fontSize: '2.5rem' }}>
                      {getCountryFlag(country.name)}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ 
                        fontWeight: 700, 
                        fontSize: '1.1rem', 
                        color: 'var(--text-primary)',
                        marginBottom: '0.5rem'
                      }}>
                        {country.name}
                      </div>
                      <div style={{ 
                        display: 'grid', 
                        gridTemplateColumns: '1fr 1fr', 
                        gap: '0.5rem',
                        fontSize: '0.85rem'
                      }}>
                        <div>
                          <span style={{ color: 'var(--text-tertiary)' }}>Exports: </span>
                          <span style={{ color: '#10b981', fontWeight: 600 }}>
                            {formatCurrency(country.export_value)}
                          </span>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-tertiary)' }}>Imports: </span>
                          <span style={{ color: '#3b82f6', fontWeight: 600 }}>
                            {formatCurrency(country.import_value)}
                          </span>
                        </div>
                      </div>
                      <div style={{ 
                        marginTop: '0.5rem', 
                        fontSize: '0.9rem',
                        fontWeight: 600,
                        color: 'var(--text-primary)'
                      }}>
                        Total: {formatCurrency(country.total_value)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {data?.countries?.length === 0 && (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '3rem',
                  color: 'var(--text-secondary)'
                }}>
                  No trading partner data available.
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default TradeLensGlobal;
