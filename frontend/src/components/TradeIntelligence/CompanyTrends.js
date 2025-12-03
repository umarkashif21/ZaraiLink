import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const CompanyTrends = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [company, setCompany] = useState(null);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);

  const currentTab = location.pathname.split('/').pop();

  useEffect(() => {
    loadCompanyData();
    loadTrends();
  }, [id]);

  const loadCompanyData = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/trade-ledger/companies/${id}/`);
      if (response.ok) {
        const data = await response.json();
        setCompany(data);
      }
    } catch (err) {
      console.error('Failed to load company:', err);
    }
  };

  const loadTrends = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/trade-ledger/companies/${id}/trends/`);
      if (response.ok) {
        const data = await response.json();
        setTrends(data);
      }
    } catch (err) {
      console.error('Failed to load trends:', err);
    } finally {
      setLoading(false);
    }
  };

  const navigateToTab = (tab) => {
    navigate(`/trade-intelligence/company/${id}/${tab}`);
  };

  const formatCurrency = (value) => {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const getRecentTrends = () => {
    return [...trends]
      .sort((a, b) => {
        if (b.year !== a.year) return b.year - a.year;
        return b.month - a.month;
      })
      .slice(0, 12);
  };

  const getQuarterlyGrowth = () => {
    // Group by quarter and calculate average YoY growth
    const quarters = {};
    trends.forEach(trend => {
      const quarter = Math.ceil(trend.month / 3);
      const key = `${trend.year}-Q${quarter}`;
      if (!quarters[key]) {
        quarters[key] = { count: 0, totalGrowth: 0, year: trend.year, quarter };
      }
      if (trend.yoy_volume_growth !== null) {
        quarters[key].count += 1;
        quarters[key].totalGrowth += parseFloat(trend.yoy_volume_growth);
      }
    });

    return Object.entries(quarters)
      .map(([key, data]) => ({
        label: key,
        growth: data.count > 0 ? (data.totalGrowth / data.count).toFixed(2) : 0
      }))
      .slice(-8); // Last 8 quarters
  };

  if (loading) {
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
        {/* Header */}
        {company && (
          <>
            <div className="company-detail-header">
              <h1>{company.company.name}</h1>
              <p>📍 {company.company.province}, {company.company.country}</p>
              <div className="company-tags">
                {company.is_exporter && <span className="company-tag">Exporter</span>}
                {company.is_importer && <span className="company-tag">Importer</span>}
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="tab-navigation">
              <button
                className={`tab-button ${currentTab === 'overview' ? 'active' : ''}`}
                onClick={() => navigateToTab('overview')}
              >
                Overview
              </button>
              <button
                className={`tab-button ${currentTab === 'products' ? 'active' : ''}`}
                onClick={() => navigateToTab('products')}
              >
                Products ({company.total_products || 0})
              </button>
              <button
                className={`tab-button ${currentTab === 'partners' ? 'active' : ''}`}
                onClick={() => navigateToTab('partners')}
              >
                Partners ({company.total_partners || 0})
              </button>
              <button
                className={`tab-button ${currentTab === 'trends' ? 'active' : ''}`}
                onClick={() => navigateToTab('trends')}
              >
                Trends
              </button>
            </div>
          </>
        )}

        {/* Tab Content - Trends */}
        <div className="tab-content">
          <h2>Trade Trends & Analytics</h2>

          {trends.length === 0 ? (
            <div className="empty-state">
              <p>No trend data available</p>
            </div>
          ) : (
            <>
              {/* Recent Monthly Trends */}
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
                    {getRecentTrends().map((trend, idx) => (
                      <tr key={idx}>
                        <td>
                          <strong>{trend.month_name} {trend.year}</strong>
                        </td>
                        <td>{trend.product_name || 'All Products'}</td>
                        <td>{new Intl.NumberFormat('en-US').format(trend.volume)}</td>
                        <td>{formatCurrency(trend.avg_price)}</td>
                        <td>
                          {trend.yoy_volume_growth !== null ? (
                            <span className={`growth-badge ${parseFloat(trend.yoy_volume_growth) >= 0 ? 'positive' : 'negative'}`}>
                              {parseFloat(trend.yoy_volume_growth) >= 0 ? '+' : ''}
                              {parseFloat(trend.yoy_volume_growth).toFixed(2)}%
                            </span>
                          ) : (
                            'N/A'
                          )}
                        </td>
                        <td>
                          {trend.yoy_price_growth !== null ? (
                            <span className={`growth-badge ${parseFloat(trend.yoy_price_growth) >= 0 ? 'positive' : 'negative'}`}>
                              {parseFloat(trend.yoy_price_growth) >= 0 ? '+' : ''}
                              {parseFloat(trend.yoy_price_growth).toFixed(2)}%
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

              {/* Quarterly Growth Summary */}
              <div style={{ marginTop: '2rem' }}>
                <h3>YoY Volume Growth By Quarter</h3>
                <div className="info-cards-grid" style={{ marginTop: '1rem' }}>
                  {getQuarterlyGrowth().map((quarter, idx) => (
                    <div key={idx} className="info-card">
                      <h4>{quarter.label}</h4>
                      <div className="info-card-value" style={{
                        color: parseFloat(quarter.growth) >= 0 ? '#22c55e' : '#ef4444'
                      }}>
                        {parseFloat(quarter.growth) >= 0 ? '+' : ''}{quarter.growth}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Charts Placeholder */}
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
