import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const TradeLedger = () => {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statistics, setStatistics] = useState(null);
  
  // Filter states
  const [filters, setFilters] = useState({
    country: '',
    product: '',
    type: '',
    dateFrom: '',
    dateTo: ''
  });

  useEffect(() => {
    loadCategories();
    loadCompanies();
  }, []);

  useEffect(() => {
    loadCompanies();
  }, [filters]);

  const loadCategories = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/trade-ledger/product-categories/');
      if (response.ok) {
        const data = await response.json();
        setCategories(data);
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const loadCompanies = async () => {
    setLoading(true);
    try {
      // Build query string
      const params = new URLSearchParams();
      if (filters.country) params.append('country', filters.country);
      if (filters.product) params.append('product', filters.product);
      if (filters.type) params.append('type', filters.type);
      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);

      const response = await fetch(`http://localhost:8000/api/trade-ledger/companies/?${params}`);
      if (response.ok) {
        const data = await response.json();
        setCompanies(data);
      }

      // Load statistics if product is selected
      if (filters.product) {
        const statsResponse = await fetch(
          `http://localhost:8000/api/trade-ledger/companies/statistics/?product=${filters.product}&${params}`
        );
        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          setStatistics(statsData);
        }
      } else {
        setStatistics(null);
      }
    } catch (err) {
      console.error('Failed to load companies:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCompanyClick = (companyId) => {
    navigate(`/trade-intelligence/company/${companyId}/overview`);
  };

  const formatCurrency = (value) => {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value) => {
    if (value === null || value === undefined) return 'N/A';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  return (
    <>
      <Navbar />
      <div className="trade-ledger-container">
        {/* Header */}
        <div className="trade-ledger-header">
          <h1>📊 Trade Ledger</h1>
          <p>Comprehensive trade intelligence and company analytics</p>
        </div>

        {/* Filters Section */}
        <div className="filters-section">
          <div className="filters-grid">
            <div className="filter-group">
              <label>Country</label>
              <input
                type="text"
                placeholder="Search by country..."
                value={filters.country}
                onChange={(e) => handleFilterChange('country', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>Product Category</label>
              <select
                value={filters.product}
                onChange={(e) => handleFilterChange('product', e.target.value)}
              >
                <option value="">All Products</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Company Type</label>
              <select
                value={filters.type}
                onChange={(e) => handleFilterChange('type', e.target.value)}
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
                value={filters.dateFrom}
                onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>Date To</label>
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) => handleFilterChange('dateTo', e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Metrics Row - Only show when product is selected */}
        {statistics && filters.product && (
          <div className="metrics-row">
            <div className="metric-card">
              <h3>Average Price</h3>
              <div className="metric-value">{formatCurrency(statistics.avg_price)}</div>
              <p className="metric-subtext">Across all companies</p>
            </div>
            <div className="metric-card">
              <h3>YoY Growth</h3>
              <div className="metric-value" style={{
                color: statistics.avg_yoy_growth >= 0 ? '#22c55e' : '#ef4444'
              }}>
                {formatPercentage(statistics.avg_yoy_growth)}
              </div>
              <p className="metric-subtext">Year-over-year</p>
            </div>
            <div className="metric-card">
              <h3>Total Volume</h3>
              <div className="metric-value">
                {statistics.total_volume 
                  ? new Intl.NumberFormat('en-US').format(statistics.total_volume) 
                  : 'N/A'}
              </div>
              <p className="metric-subtext">Combined volume</p>
            </div>
            <div className="metric-card">
              <h3>Total Companies</h3>
              <div className="metric-value">{statistics.total_companies || companies.length}</div>
              <p className="metric-subtext">In this category</p>
            </div>
          </div>
        )}

        {/* Companies Grid */}
        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading companies...</p>
          </div>
        ) : companies.length === 0 ? (
          <div className="empty-state">
            <h2>No companies found</h2>
            <p>Try adjusting your filters</p>
          </div>
        ) : (
          <div className="companies-grid">
            {companies.map(tradeCompany => (
              <div
                key={tradeCompany.id}
                className="company-card"
                onClick={() => handleCompanyClick(tradeCompany.id)}
              >
                <div className="company-card-header">
                  <div>
                    <h3>{tradeCompany.company.name}</h3>
                    <p className="company-location">
                      📍 {tradeCompany.company.province}, {tradeCompany.company.country}
                    </p>
                  </div>
                  {tradeCompany.is_exporter && tradeCompany.is_importer ? (
                    <span className="company-badge">Both</span>
                  ) : tradeCompany.is_exporter ? (
                    <span className="company-badge">Exporter</span>
                  ) : (
                    <span className="company-badge">Importer</span>
                  )}
                </div>

                <div className="company-stats">
                  <div className="stat-item">
                    <span className="stat-label">Est. Revenue</span>
                    <span className="stat-value">
                      {formatCurrency(tradeCompany.estimated_revenue)}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Trade Volume</span>
                    <span className="stat-value">
                      {formatCurrency(tradeCompany.trade_volume)}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Products</span>
                    <span className="stat-value">{tradeCompany.top_products?.length || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Active Since</span>
                    <span className="stat-value">
                      {tradeCompany.active_since 
                        ? new Date(tradeCompany.active_since).getFullYear()
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
