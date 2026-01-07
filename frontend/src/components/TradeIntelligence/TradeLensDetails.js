import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import Breadcrumb from '../Common/Breadcrumb';
import Pagination from '../Common/Pagination';
import './TradeIntelligence.css';

const TradeLensDetails = () => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    trade_type: '',
    buyer: '',
    seller: '',
    country: '',
  });

  useEffect(() => {
    loadDetailsData();
  }, [productId, currentPage, filters]);

  const loadDetailsData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', currentPage);
      if (filters.trade_type) params.append('trade_type', filters.trade_type);
      if (filters.buyer) params.append('buyer', filters.buyer);
      if (filters.seller) params.append('seller', filters.seller);
      if (filters.country) params.append('country', filters.country);

      const response = await fetch(
        `http://localhost:8000/api/trade-lens/products/${productId}/details/?${params}`,
        { credentials: 'include' }
      );
      if (!response.ok) throw new Error('Failed to load details');
      const result = await response.json();
      setData(result);
      setTotalPages(Math.ceil(result.count / 25));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (!value) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
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

  return (
    <>
      <Navbar />
      <div className="trade-lens-subpage-container">
        <Breadcrumb />

        <div className="trade-lens-subpage-header">
          <div className="product-info">
            <div className="product-icon">📋</div>
            <div className="product-details">
              <h1>Transaction Details</h1>
              <p>View individual transaction records</p>
            </div>
          </div>
        </div>

        <div className="trade-lens-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`trade-lens-tab ${tab.id === 'details' ? 'active' : ''}`}
              onClick={() => handleTabClick(tab.path)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="trade-lens-content">
          <div className="filters-section" style={{ marginBottom: '1.5rem' }}>
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
                <label>Buyer</label>
                <input
                  type="text"
                  placeholder="Search buyer..."
                  value={filters.buyer}
                  onChange={(e) => setFilters({...filters, buyer: e.target.value})}
                />
              </div>
              <div className="filter-group">
                <label>Seller</label>
                <input
                  type="text"
                  placeholder="Search seller..."
                  value={filters.seller}
                  onChange={(e) => setFilters({...filters, seller: e.target.value})}
                />
              </div>
              <div className="filter-group">
                <label>Country</label>
                <input
                  type="text"
                  placeholder="Search country..."
                  value={filters.country}
                  onChange={(e) => setFilters({...filters, country: e.target.value})}
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
              <div style={{ overflowX: 'auto' }}>
                <table className="trade-lens-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Type</th>
                      <th>Buyer</th>
                      <th>Seller</th>
                      <th>Quantity (MT)</th>
                      <th>Price (USD)</th>
                      <th>Total Value</th>
                      <th>Port</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data?.results?.map((tx, idx) => (
                      <tr key={idx}>
                        <td>{formatDate(tx.trade_date)}</td>
                        <td>
                          <span className={`growth-badge ${tx.trade_type === 'EXPORT' ? 'positive' : 'negative'}`}>
                            {tx.trade_type}
                          </span>
                        </td>
                        <td>
                          <div>{tx.buyer_name}</div>
                          <small style={{ color: 'var(--text-tertiary)' }}>{tx.buyer_country}</small>
                        </td>
                        <td>
                          <div>{tx.seller_name}</div>
                          <small style={{ color: 'var(--text-tertiary)' }}>{tx.seller_country}</small>
                        </td>
                        <td>{parseFloat(tx.quantity_mt).toFixed(2)}</td>
                        <td>{formatCurrency(tx.price_usd)}</td>
                        <td><strong>{formatCurrency(tx.total_value_usd)}</strong></td>
                        <td>{tx.port}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ marginTop: '1.5rem' }}>
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={setCurrentPage}
                  totalItems={data?.count || 0}
                  itemsPerPage={25}
                />
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default TradeLensDetails;
