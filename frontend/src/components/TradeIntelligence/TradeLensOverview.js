import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import Navbar from '../Layout/Navbar';
import Breadcrumb from '../Common/Breadcrumb';
import './TradeIntelligence.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const TradeLensOverview = () => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadOverviewData();
  }, [productId]);

  const loadOverviewData = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/trade-lens/products/${productId}/overview/`,
        { credentials: 'include' }
      );
      if (!response.ok) throw new Error('Failed to load overview data');
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
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
      'Cereals': '🌾',
      'Textiles': '🧵',
      'Fruits': '🥭',
      'Medical Equipment': '🏥',
      'Sports Equipment': '⚽',
      'Leather Products': '👜',
    };
    return icons[category] || '📦';
  };

  const priceChartData = data?.price_trend ? {
    labels: data.price_trend.map(p => p.month),
    datasets: [
      {
        label: 'Avg Price (USD)',
        data: data.price_trend.map(p => p.avg_price),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  } : null;

  const provinceChartData = data?.provinces ? {
    labels: data.provinces.slice(0, 6).map(p => p.province),
    datasets: [
      {
        data: data.provinces.slice(0, 6).map(p => p.total_value),
        backgroundColor: [
          '#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'
        ],
      },
    ],
  } : null;

  const portChartData = data?.ports ? {
    labels: data.ports.map(p => p.port),
    datasets: [
      {
        label: 'Trade Value',
        data: data.ports.map(p => p.total_value),
        backgroundColor: '#10b981',
        borderRadius: 8,
      },
    ],
  } : null;

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="trade-lens-subpage-container">
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading overview data...</p>
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Navbar />
        <div className="trade-lens-subpage-container">
          <div className="empty-state">
            <h2>Error loading data</h2>
            <p>{error}</p>
            <button onClick={loadOverviewData}>Retry</button>
          </div>
        </div>
      </>
    );
  }

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
              <h1>{data?.product?.name}</h1>
              <p>HS Code: {data?.product?.hs_code} | {data?.product?.category}</p>
            </div>
          </div>
          <button
            className="btn-back"
            onClick={() => navigate('/trade-intelligence/lens')}
            style={{
              padding: '0.5rem 1rem',
              background: 'var(--bg-tertiary)',
              border: '1px solid var(--border-primary)',
              borderRadius: '8px',
              cursor: 'pointer',
              color: 'var(--text-primary)'
            }}
          >
            ← Back to Products
          </button>
        </div>

        <div className="trade-lens-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`trade-lens-tab ${tab.id === 'overview' ? 'active' : ''}`}
              onClick={() => handleTabClick(tab.path)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="trade-lens-overview-grid">
          <div className="trade-lens-overview-card primary">
            <div className="card-value">{formatCurrency(data?.avg_price)}</div>
            <div className="card-label">Average Price (USD/MT)</div>
          </div>
          <div className="trade-lens-overview-card">
            <div className="card-value">{formatNumber(data?.total_quantity)} MT</div>
            <div className="card-label">Total Quantity</div>
          </div>
          <div className="trade-lens-overview-card">
            <div className="card-value">{formatCurrency(data?.total_value)}</div>
            <div className="card-label">Total Trade Value</div>
          </div>
          <div className="trade-lens-overview-card">
            <div className="card-value">{formatNumber(data?.transaction_count)}</div>
            <div className="card-label">Transactions</div>
          </div>
        </div>

        <div className="trade-lens-chart-row">
          <div className="trade-lens-chart-card">
            <h3>Price Trend (24 Months)</h3>
            {priceChartData && (
              <Line
                data={priceChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: true,
                  plugins: {
                    legend: { display: false },
                  },
                  scales: {
                    y: {
                      beginAtZero: false,
                      ticks: { callback: (v) => `$${v}` }
                    }
                  }
                }}
              />
            )}
          </div>

          <div className="trade-lens-chart-card">
            <h3>Trade by Province</h3>
            {provinceChartData && (
              <Doughnut
                data={provinceChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: true,
                  plugins: {
                    legend: { position: 'right' },
                  },
                }}
              />
            )}
          </div>
        </div>

        <div className="trade-lens-chart-row">
          <div className="trade-lens-chart-card full-width">
            <h3>Trade by Port</h3>
            {portChartData && (
              <Bar
                data={portChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: true,
                  plugins: {
                    legend: { display: false },
                  },
                  scales: {
                    y: {
                      beginAtZero: true,
                      ticks: { callback: (v) => formatCurrency(v) }
                    }
                  }
                }}
              />
            )}
          </div>
        </div>

        <div className="trade-lens-chart-row">
          <div className="trade-lens-chart-card">
            <h3>Export vs Import</h3>
            <div style={{ display: 'flex', gap: '2rem', padding: '1rem 0' }}>
              <div style={{ textAlign: 'center', flex: 1 }}>
                <div style={{ fontSize: '2rem', fontWeight: 700, color: '#10b981' }}>
                  {formatNumber(data?.export_count)}
                </div>
                <div style={{ color: 'var(--text-secondary)' }}>Exports</div>
              </div>
              <div style={{ textAlign: 'center', flex: 1 }}>
                <div style={{ fontSize: '2rem', fontWeight: 700, color: '#3b82f6' }}>
                  {formatNumber(data?.import_count)}
                </div>
                <div style={{ color: 'var(--text-secondary)' }}>Imports</div>
              </div>
            </div>
          </div>

          <div className="trade-lens-chart-card">
            <h3>Supply Chain Flow</h3>
            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
              {data?.supply_chain_flow?.slice(0, 8).map((flow, idx) => (
                <div key={idx} style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0.5rem 0',
                  borderBottom: '1px solid var(--border-primary)'
                }}>
                  <span style={{ flex: 1 }}>{flow.source}</span>
                  <span style={{ margin: '0 0.5rem', color: 'var(--text-tertiary)' }}>→</span>
                  <span style={{ flex: 1 }}>{flow.target}</span>
                  <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
                    {formatCurrency(flow.value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default TradeLensOverview;
