import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Line, Bar } from 'react-chartjs-2';
import Navbar from '../Layout/Navbar';
import Breadcrumb from '../Common/Breadcrumb';
import './TradeIntelligence.css';

const TradeLensComparison = () => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadComparisonData();
  }, [productId]);

  const loadComparisonData = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/trade-lens/products/${productId}/comparison/`,
        { credentials: 'include' }
      );
      if (!response.ok) throw new Error('Failed to load comparison data');
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

  // Process price trends for export/import comparison
  const processPriceTrends = () => {
    if (!data?.price_trends) return null;
    
    const months = [...new Set(data.price_trends.map(p => p.month))];
    const exportData = months.map(m => {
      const entry = data.price_trends.find(p => p.month === m && p.trade_type === 'EXPORT');
      return entry?.avg_price || null;
    });
    const importData = months.map(m => {
      const entry = data.price_trends.find(p => p.month === m && p.trade_type === 'IMPORT');
      return entry?.avg_price || null;
    });

    return {
      labels: months,
      datasets: [
        {
          label: 'Export Price',
          data: exportData,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4,
        },
        {
          label: 'Import Price',
          data: importData,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
        },
      ],
    };
  };

  const countryExportChart = data?.country_exports ? {
    labels: data.country_exports.map(c => c.country),
    datasets: [{
      label: 'Export Value',
      data: data.country_exports.map(c => c.total_value),
      backgroundColor: '#10b981',
      borderRadius: 8,
    }],
  } : null;

  const countryImportChart = data?.country_imports ? {
    labels: data.country_imports.map(c => c.country),
    datasets: [{
      label: 'Import Value',
      data: data.country_imports.map(c => c.total_value),
      backgroundColor: '#3b82f6',
      borderRadius: 8,
    }],
  } : null;

  const priceTrendChart = processPriceTrends();

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
              className={`trade-lens-tab ${tab.id === 'comparison' ? 'active' : ''}`}
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
                  <div className="card-value">
                    {formatCurrency(data?.trade_type_breakdown?.exports?.total_value)}
                  </div>
                  <div className="card-label">Total Exports</div>
                </div>
                <div className="trade-lens-overview-card">
                  <div className="card-value">
                    {formatCurrency(data?.trade_type_breakdown?.imports?.total_value)}
                  </div>
                  <div className="card-label">Total Imports</div>
                </div>
              </div>

              <div className="trade-lens-chart-row">
                <div className="trade-lens-chart-card full-width">
                  <h3>Export vs Import Price Trends</h3>
                  {priceTrendChart && (
                    <Line
                      data={priceTrendChart}
                      options={{
                        responsive: true,
                        plugins: { legend: { position: 'top' } },
                        scales: {
                          y: { ticks: { callback: (v) => `$${v}` } }
                        }
                      }}
                    />
                  )}
                </div>
              </div>

              <div className="trade-lens-chart-row">
                <div className="trade-lens-chart-card">
                  <h3>Top Export Destinations</h3>
                  {countryExportChart && (
                    <Bar
                      data={countryExportChart}
                      options={{
                        responsive: true,
                        indexAxis: 'y',
                        plugins: { legend: { display: false } },
                        scales: {
                          x: { ticks: { callback: (v) => formatCurrency(v) } }
                        }
                      }}
                    />
                  )}
                </div>

                <div className="trade-lens-chart-card">
                  <h3>Top Import Sources</h3>
                  {countryImportChart && (
                    <Bar
                      data={countryImportChart}
                      options={{
                        responsive: true,
                        indexAxis: 'y',
                        plugins: { legend: { display: false } },
                        scales: {
                          x: { ticks: { callback: (v) => formatCurrency(v) } }
                        }
                      }}
                    />
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default TradeLensComparison;
