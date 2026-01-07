import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import Breadcrumb from '../Common/Breadcrumb';
import { SkeletonCard } from '../Common/Skeleton';
import EmptyState from '../Common/EmptyState';
import './TradeIntelligence.css';

const TradeLens = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/trade-lens/products/', {
        credentials: 'include'
      });
      if (!response.ok) {
        throw new Error('Failed to load products');
      }
      const data = await response.json();
      setProducts(data.results || data || []);
    } catch (err) {
      console.error('Error loading products:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (!value || value === 0) return '$0';
    if (value >= 1000000000) {
      return `$${(value / 1000000000).toFixed(1)}B`;
    }
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

  const formatNumber = (value) => {
    if (!value || value === 0) return '0';
    return new Intl.NumberFormat('en-US').format(value);
  };

  const categories = [...new Set(products.map(p => p.category))].filter(Boolean);

  const filteredProducts = products.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         product.hs_code.includes(searchTerm);
    const matchesCategory = !selectedCategory || product.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleProductClick = (productId) => {
    navigate(`/trade-intelligence/lens/${productId}/overview`);
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

  const getProductGradient = (index) => {
    const gradients = [
      'linear-gradient(135deg, #10b981 0%, #059669 100%)',
      'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
      'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
      'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
      'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
      'linear-gradient(135deg, #ec4899 0%, #db2777 100%)',
      'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
      'linear-gradient(135deg, #84cc16 0%, #65a30d 100%)',
    ];
    return gradients[index % gradients.length];
  };

  return (
    <>
      <Navbar />
      <div className="trade-lens-container">
        <Breadcrumb />
        
        <div className="trade-lens-header">
          <div>
            <h1>Trade Lens</h1>
            <p>Product-centric trade intelligence dashboard - analyze trade patterns, pricing, and market trends by product</p>
          </div>
        </div>

        <div className="trade-lens-filters">
          <div className="search-box">
            <svg className="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z" clipRule="evenodd" />
            </svg>
            <input
              type="text"
              placeholder="Search products by name or HS code..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div className="category-filter">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="trade-lens-stats-row">
          <div className="trade-lens-stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <span className="stat-value">{products.length}</span>
              <span className="stat-label">Products Tracked</span>
            </div>
          </div>
          <div className="trade-lens-stat-card">
            <div className="stat-icon">💰</div>
            <div className="stat-content">
              <span className="stat-value">
                {formatCurrency(products.reduce((sum, p) => sum + (p.total_value || 0), 0))}
              </span>
              <span className="stat-label">Total Trade Value</span>
            </div>
          </div>
          <div className="trade-lens-stat-card">
            <div className="stat-icon">📈</div>
            <div className="stat-content">
              <span className="stat-value">
                {formatNumber(products.reduce((sum, p) => sum + (p.transaction_count || 0), 0))}
              </span>
              <span className="stat-label">Total Transactions</span>
            </div>
          </div>
          <div className="trade-lens-stat-card">
            <div className="stat-icon">🏷️</div>
            <div className="stat-content">
              <span className="stat-value">{categories.length}</span>
              <span className="stat-label">Categories</span>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="trade-lens-products-grid">
            {[...Array(8)].map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : error ? (
          <EmptyState
            title="Error loading products"
            description={error}
            actionLabel="Retry"
            onAction={loadProducts}
          />
        ) : filteredProducts.length === 0 ? (
          <EmptyState
            title="No products found"
            description="Try adjusting your search or filter criteria"
            actionLabel="Clear Filters"
            onAction={() => { setSearchTerm(''); setSelectedCategory(''); }}
          />
        ) : (
          <div className="trade-lens-products-grid">
            {filteredProducts.map((product, index) => (
              <div
                key={product.id}
                className="trade-lens-product-card"
                onClick={() => handleProductClick(product.id)}
              >
                <div 
                  className="product-card-header"
                  style={{ background: getProductGradient(index) }}
                >
                  <span className="product-icon">{getProductIcon(product.category)}</span>
                  <span className="product-category-badge">{product.category}</span>
                </div>
                
                <div className="product-card-body">
                  <h3 className="product-name">{product.name}</h3>
                  <p className="product-hs-code">HS Code: {product.hs_code}</p>
                  
                  {product.description && (
                    <p className="product-description">{product.description}</p>
                  )}
                  
                  <div className="product-stats">
                    <div className="product-stat">
                      <span className="product-stat-value">{formatCurrency(product.total_value)}</span>
                      <span className="product-stat-label">Trade Value</span>
                    </div>
                    <div className="product-stat">
                      <span className="product-stat-value">{formatNumber(product.transaction_count)}</span>
                      <span className="product-stat-label">Transactions</span>
                    </div>
                  </div>
                </div>
                
                <div className="product-card-footer">
                  <span className="view-details-link">
                    View Details
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clipRule="evenodd" />
                    </svg>
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
};

export default TradeLens;
