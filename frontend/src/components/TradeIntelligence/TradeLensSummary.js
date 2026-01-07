import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Line, Bar } from 'react-chartjs-2';
import Navbar from '../Layout/Navbar';
import Breadcrumb from '../Common/Breadcrumb';
import './TradeIntelligence.css';

const TradeLensSummary = () => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    trade_type: '',
    start_date: '',
    end_date: '',
  });

  useEffect(() => {
    loadSummaryData();
  }, [productId, filters]);

  const loadSummaryData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.trade_type) params.append('trade_type', filters.trade_type);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);

      const response = await fetch(
        `http://localhost:8000/api/trade-lens/products/${productId}/summary/?${params}`,
        { credentials: 'include' }
      );
      if (!response.ok) throw new Error('Failed to load summary data');
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

  const monthlyChartData = data?.monthly_trend ? {
    labels: data.monthly_trend.map(m => m.month),
    datasets: [
      {
        label: 'Trade Value',
        data: data.monthly_trend.map(m => m.total_value),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  } : null;

  const getProductIcon = (category) => {
    const icons = {
      'Cereals': '🌾', 'Textiles': '🧵', 'Fruits': '🥭',
      'Medical Equipment': '🏥', 'Sports Equipment': '⚽', 'Leather Products': '👜',
    };
    return icons[category] || '📦';
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
              className={`trade-lens-tab ${tab.id === 'summary' ? 'active' : ''}`}
              onClick={() => handleTabClick(tab.path)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="trade-lens-content">
          <div className="filters-section" style={{ marginBottom: '2rem' }}>
            <div className="filters-grid">
              <div className="filter-group">
                <label>Trade Type</label>
                <select
                  value={filters.trade_type}
                  onChange={(e) => setFilters({...filters, trade_type: e.target.value})}
                >
                  <option value="">All Types</option>
                  <option value="EXPORT">Export</option>
                  <option value="IMPORT">Import</option>
                </select>
              </div>
              <div className="filter-group">
                <label>Start Date</label>
                <input
                  type="date"
                  value={filters.start_date}
                  onChange={(e) => setFilters({...filters, start_date: e.target.value})}
                />
              </div>
              <div className="filter-group">
                <label>End Date</label>
                <input
                  type="date"
                  value={filters.end_date}
                  onChange={(e) => setFilters({...filters, end_date: e.target.value})}
                />
              </div>
            </div>
          </div>

          {loading ? (
            <div className="loading-container">
              <div className="spinner"></div>
            </div>
          ) : (
            <>
              <div className="trade-lens-overview-grid" style={{ marginBottom: '2rem' }}>
                <div className="trade-lens-overview-card primary">
                  <div className="card-value">{formatNumber(data?.total_quantity)} MT</div>
                  <div className="card-label">Total Quantity</div>
                </div>
                <div className="trade-lens-overview-card">
                  <div className="card-value">{formatCurrency(data?.total_value)}</div>
                  <div className="card-label">Total Value</div>
                </div>
                <div className="trade-lens-overview-card">
                  <div className="card-value">{formatCurrency(data?.avg_price)}</div>
                  <div className="card-label">Avg Price/MT</div>
                </div>
              </div>

              <div className="trade-lens-chart-row">
                <div className="trade-lens-chart-card full-width">
                  <h3>Monthly Trade Trend</h3>
                  {monthlyChartData && (
                    <Line
                      data={monthlyChartData}
                      options={{
                        responsive: true,
                        plugins: { legend: { display: false } },
                        scales: {
                          y: { ticks: { callback: (v) => formatCurrency(v) } }
                        }
                      }}
                    />
                  )}
                </div>
              </div>

              <div className="trade-lens-chart-row">
                <div className="trade-lens-chart-card">
                  <h3>Top Buyers</h3>
                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    <table className="trade-lens-table">
                      <thead>
                        <tr>
                          <th>Buyer</th>
                          <th>Country</th>
                          <th>Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data?.top_buyers?.map((buyer, idx) => (
                          <tr key={idx}>
                            <td>{buyer.buyer_name}</td>
                            <td>{buyer.buyer_country}</td>
                            <td>{formatCurrency(buyer.total_value)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="trade-lens-chart-card">
                  <h3>Top Sellers</h3>
                  <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    <table className="trade-lens-table">
                      <thead>
                        <tr>
                          <th>Seller</th>
                          <th>Country</th>
                          <th>Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data?.top_sellers?.map((seller, idx) => (
                          <tr key={idx}>
                            <td>{seller.seller_name}</td>
                            <td>{seller.seller_country}</td>
                            <td>{formatCurrency(seller.total_value)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default TradeLensSummary;
