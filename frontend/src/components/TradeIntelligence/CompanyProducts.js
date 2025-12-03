import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const CompanyProducts = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [company, setCompany] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  const currentTab = location.pathname.split('/').pop();

  useEffect(() => {
    loadCompanyData();
    loadProducts();
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

  const loadProducts = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/trade-ledger/companies/${id}/products/`);
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
      }
    } catch (err) {
      console.error('Failed to load products:', err);
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
      currency: value.currency || 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value) => {
    if (value === null || value === undefined) return 'N/A';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${parseFloat(value).toFixed(2)}%`;
  };

  if (loading) {
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

        {/* Tab Content - Products */}
        <div className="tab-content">
          <h2>Product Performance</h2>

          {products.length === 0 ? (
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
                {products.map((product, idx) => (
                  <tr key={idx}>
                    <td>
                      <strong>{product.product_name}</strong>
                      {product.hs_code && (
                        <div style={{ fontSize: '0.85rem', color: '#718096' }}>
                          HS Code: {product.hs_code}
                        </div>
                      )}
                    </td>
                    <td>{product.category_name || 'N/A'}</td>
                    <td>
                      {new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: product.currency || 'USD'
                      }).format(product.avg_price)}
                    </td>
                    <td>
                      {new Intl.NumberFormat('en-US').format(product.volume)} {product.unit}
                    </td>
                    <td>
                      {product.yoy_growth !== null && product.yoy_growth !== undefined ? (
                        <span className={`growth-badge ${parseFloat(product.yoy_growth) >= 0 ? 'positive' : 'negative'}`}>
                          {formatPercentage(product.yoy_growth)}
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

          {/* Product Charts Section */}
          {products.length > 0 && (
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
