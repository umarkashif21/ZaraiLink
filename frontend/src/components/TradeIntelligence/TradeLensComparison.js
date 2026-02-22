import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Line, Bar } from 'react-chartjs-2';
import Navbar from '../Layout/Navbar';
import Breadcrumb from '../Common/Breadcrumb';
import { RotateCcw, X, Plus, Search } from 'lucide-react';

import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, Title, Tooltip, Legend, Filler
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, Filler);

// Premium distinct palette for multi-product comparison (up to 5 products)
const PRODUCT_COLORS = [
  { border: '#3b82f6', bg: 'rgba(59, 130, 246, 0.12)', label: '#3b82f6' },   // Blue   (primary)
  { border: '#10b981', bg: 'rgba(16, 185, 129, 0.12)', label: '#10b981' },   // Emerald
  { border: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.12)', label: '#8b5cf6' },   // Violet
  { border: '#f59e0b', bg: 'rgba(245, 158, 11, 0.12)', label: '#f59e0b' },   // Amber
  { border: '#ef4444', bg: 'rgba(239, 68, 68, 0.12)', label: '#ef4444' },   // Rose
];

const TradeLensComparison = () => {
  const { productId } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState({
    monthly_avg_price: [], avg_price_by_country: [], quantity_by_country: [],
    is_multi: false, compared_products: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // All available products for the picker
  const [allProducts, setAllProducts] = useState([]);
  const [productSearch, setProductSearch] = useState('');
  const [showProductDropdown, setShowProductDropdown] = useState(false);

  // Selected comparison products (array of {id, name})
  const [compareProducts, setCompareProducts] = useState([]);

  const [appliedFilters, setAppliedFilters] = useState({
    trade_type: '', buyer: '', seller: '', country: '', compare_with: [],
  });

  const [pendingFilters, setPendingFilters] = useState({
    trade_type: '', buyer: '', seller: '', country: '', compare_with: [],
  });

  // Fetch all products for the picker
  useEffect(() => {
    fetch('http://localhost:8000/api/trade-lens/products/', { credentials: 'include' })
      .then(r => r.json())
      .then(d => setAllProducts(d.products || []))
      .catch(console.error);
  }, []);

  const loadComparisonData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (appliedFilters.trade_type) params.append('trade_type', appliedFilters.trade_type);
      if (appliedFilters.buyer) params.append('buyer', appliedFilters.buyer);
      if (appliedFilters.seller) params.append('seller', appliedFilters.seller);
      if (appliedFilters.country) params.append('country', appliedFilters.country);
      if (appliedFilters.compare_with.length > 0) {
        params.append('compare_with', appliedFilters.compare_with.join(','));
      }

      const response = await fetch(
        `http://localhost:8000/api/trade-lens/products/${productId}/comparison/?${params.toString()}`,
        { credentials: 'include' }
      );
      if (!response.ok) throw new Error('Failed to load comparison data');
      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [productId, appliedFilters]);

  useEffect(() => {
    loadComparisonData();
  }, [loadComparisonData]);

  const handleApplyFilters = () => {
    setAppliedFilters({
      ...pendingFilters,
      compare_with: compareProducts.map(p => p.id),
    });
  };

  const clearFilters = () => {
    const empty = { trade_type: '', buyer: '', seller: '', country: '', compare_with: [] };
    setPendingFilters(empty);
    setAppliedFilters(empty);
    setCompareProducts([]);
  };

  const addProduct = (product) => {
    if (compareProducts.length >= 4) return; // max 4 extra = 5 total
    if (compareProducts.find(p => p.id === product.id)) return;
    if (String(product.id) === String(productId)) return;
    setCompareProducts(prev => [...prev, product]);
    setProductSearch('');
    setShowProductDropdown(false);
  };

  const removeProduct = (id) => {
    setCompareProducts(prev => prev.filter(p => p.id !== id));
  };

  const tabs = [
    { id: 'overview', label: 'Overview', path: 'overview' },
    { id: 'comparison', label: 'Comparison', path: 'comparison' },
    { id: 'details', label: 'Details', path: 'details' },
  ];

  /* ─────────── CHARTS BUILD ─────────── */

  const commonOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8, font: { family: "'DM Sans', sans-serif", size: 12, weight: '500' }, color: '#64748b' } },
      tooltip: {
        backgroundColor: '#0f172a', cornerRadius: 8, padding: 10,
        titleFont: { family: "'DM Sans', sans-serif", size: 13, weight: '600' },
        bodyFont: { family: "'DM Sans', sans-serif", size: 12 },
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#94a3b8', font: { family: "'DM Sans', sans-serif", size: 11, weight: '500' } }
      },
      y: {
        grid: { color: '#f1f5f9' },
        ticks: { color: '#94a3b8', font: { family: "'DM Sans', sans-serif", size: 11, weight: '500' } }
      }
    }
  };

  const horizontalBarOptions = {
    ...commonOptions, indexAxis: 'y',
    scales: {
      x: {
        grid: { color: '#f1f5f9' },
        ticks: { color: '#94a3b8', font: { family: "'DM Sans', sans-serif", size: 11, weight: '500' } }
      },
      y: {
        grid: { display: false },
        ticks: { color: '#64748b', font: { family: "'DM Sans', sans-serif", size: 11, weight: '500' } }
      }
    }
  };

  // ── SINGLE-PRODUCT MODE: Import vs Export ──
  const singlePriceTrendData = {
    labels: data.monthly_avg_price.map(d => d.month),
    datasets: [
      {
        label: 'Import Avg Price ($)',
        data: data.monthly_avg_price.map(d => d.import_avg),
        borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)', tension: 0.3,
        borderWidth: 2, pointRadius: 3, fill: true,
      },
      {
        label: 'Export Avg Price ($)',
        data: data.monthly_avg_price.map(d => d.export_avg),
        borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.1)', tension: 0.3,
        borderWidth: 2, pointRadius: 3, fill: true,
      }
    ]
  };

  const singlePriceByCountryData = {
    labels: data.avg_price_by_country.map(d => d.country),
    datasets: [
      { label: 'Import Avg Price', data: data.avg_price_by_country.map(d => d.import_avg), backgroundColor: '#3b82f6', borderRadius: 4 },
      { label: 'Export Avg Price', data: data.avg_price_by_country.map(d => d.export_avg), backgroundColor: '#10b981', borderRadius: 4 }
    ]
  };

  const singleQtyByCountryData = {
    labels: data.quantity_by_country.map(d => d.country),
    datasets: [
      { label: 'Import Vol (MT)', data: data.quantity_by_country.map(d => d.import_qty_mt), backgroundColor: '#3b82f6', borderRadius: 4 },
      { label: 'Export Vol (MT)', data: data.quantity_by_country.map(d => d.export_qty_mt), backgroundColor: '#10b981', borderRadius: 4 }
    ]
  };

  // ── MULTI-PRODUCT MODE: one dataset per product ──
  const multiProducts = data.compared_products || [];

  const multiPriceTrendData = {
    labels: data.monthly_avg_price.map(d => d.month),
    datasets: multiProducts.map((p, idx) => {
      const col = PRODUCT_COLORS[idx] || PRODUCT_COLORS[0];
      return {
        label: p.name,
        data: data.monthly_avg_price.map(d => d[p.id] ?? null),
        borderColor: col.border, backgroundColor: col.bg, tension: 0.3,
        borderWidth: 2.5, pointRadius: 3, fill: false,
      };
    })
  };

  const multiPriceByCountryData = {
    labels: data.avg_price_by_country.map(d => d.country),
    datasets: multiProducts.map((p, idx) => {
      const col = PRODUCT_COLORS[idx] || PRODUCT_COLORS[0];
      return {
        label: p.name,
        data: data.avg_price_by_country.map(d => d[p.id] ?? 0),
        backgroundColor: col.border, borderRadius: 4,
      };
    })
  };

  const multiQtyByCountryData = {
    labels: data.quantity_by_country.map(d => d.country),
    datasets: multiProducts.map((p, idx) => {
      const col = PRODUCT_COLORS[idx] || PRODUCT_COLORS[0];
      return {
        label: p.name,
        data: data.quantity_by_country.map(d => d[p.id] ?? 0),
        backgroundColor: col.border, borderRadius: 4,
      };
    })
  };

  const isMulti = data.is_multi;
  const priceTrendData = isMulti ? multiPriceTrendData : singlePriceTrendData;
  const priceByCountryData = isMulti ? multiPriceByCountryData : singlePriceByCountryData;
  const qtyByCountryData = isMulti ? multiQtyByCountryData : singleQtyByCountryData;

  // Filtered product list for dropdown
  const filteredProducts = allProducts.filter(p =>
    String(p.id) !== String(productId) &&
    !compareProducts.find(cp => cp.id === p.id) &&
    p.name.toLowerCase().includes(productSearch.toLowerCase())
  ).slice(0, 8);

  const cardStyle = {
    background: 'white', border: '1px solid rgba(226, 232, 240, 0.6)',
    borderRadius: '16px', boxShadow: '0 12px 32px -4px rgba(0,0,0,0.04), 0 4px 12px -2px rgba(0,0,0,0.02)'
  };

  return (
    <>
      <Navbar />
      <div style={{ background: '#ffffff', minHeight: '100vh', paddingBottom: '4rem', fontFamily: "'DM Sans', 'Inter', sans-serif" }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 2rem' }}>

          {/* Header & Tabs */}
          <div style={{ padding: '2rem 0', borderBottom: '1px solid #e2e8f0', marginBottom: '2rem' }}>
            <Breadcrumb />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '1rem' }}>
              <div>
                <h1 style={{ margin: 0, fontSize: '2.25rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.02em' }}>Trade Lens</h1>
                <p style={{ margin: '0.5rem 0 0', color: '#64748b', fontSize: '1rem' }}>
                  {isMulti
                    ? `Comparing ${multiProducts.length} products`
                    : `Comparison insights for ${data.product?.name || 'Loading...'}`}
                </p>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', background: '#f1f5f9', padding: '0.25rem', borderRadius: '8px' }}>
                <button style={{ padding: '0.5rem 1rem', background: '#0f172a', color: 'white', border: 'none', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer' }}>USD</button>
                <button style={{ padding: '0.5rem 1rem', background: 'transparent', color: '#64748b', border: 'none', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer' }}>PKR</button>
              </div>
            </div>

            <div style={{ display: 'inline-flex', background: '#f1f5f9', padding: '4px', borderRadius: '10px', marginTop: '2rem', gap: '4px', border: '1px solid #e2e8f0' }}>
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => navigate(`/trade-intelligence/lens/${productId}/${tab.path}`)}
                  style={{
                    background: tab.id === 'comparison' ? 'white' : 'transparent',
                    border: 'none', padding: '0.6rem 1.25rem', cursor: 'pointer',
                    fontSize: '0.9rem', fontWeight: tab.id === 'comparison' ? 600 : 500,
                    color: tab.id === 'comparison' ? '#0f172a' : '#64748b',
                    borderRadius: '8px', boxShadow: tab.id === 'comparison' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                    transition: 'all 0.2s ease-in-out', WebkitUserSelect: 'none'
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 320px) 1fr', gap: '2rem', alignItems: 'start' }}>

            {/* LEFT SIDEBAR */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

              {/* COMPARE PRODUCTS PICKER */}
              <div style={{ ...cardStyle, padding: '1.5rem' }}>
                <div style={{ marginBottom: '1.25rem' }}>
                  <h3 style={{ margin: '0 0 0.25rem', fontSize: '1.05rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.01em' }}>
                    Compare Products
                  </h3>
                  <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>
                    Select 1–4 products to overlay ({compareProducts.length}/4 selected)
                  </p>
                </div>

                {/* Selected chips */}
                {compareProducts.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
                    {compareProducts.map((p, idx) => {
                      const col = PRODUCT_COLORS[idx + 1] || PRODUCT_COLORS[idx];
                      return (
                        <div key={p.id} style={{
                          display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
                          background: col.bg, border: `1px solid ${col.border}40`,
                          borderRadius: '20px', padding: '0.3rem 0.7rem',
                          fontSize: '0.8rem', fontWeight: 600, color: col.border
                        }}>
                          <span style={{ width: 8, height: 8, borderRadius: '50%', background: col.border, display: 'inline-block', flexShrink: 0 }} />
                          {p.name.length > 20 ? p.name.slice(0, 20) + '…' : p.name}
                          <button
                            onClick={() => removeProduct(p.id)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: col.border, padding: 0, display: 'flex', alignItems: 'center' }}
                          >
                            <X size={12} />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Product search input */}
                {compareProducts.length < 4 && (
                  <div style={{ position: 'relative' }}>
                    <div style={{ position: 'relative' }}>
                      <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                      <input
                        type="text"
                        placeholder="Search product to add…"
                        value={productSearch}
                        onChange={e => { setProductSearch(e.target.value); setShowProductDropdown(true); }}
                        onFocus={() => setShowProductDropdown(true)}
                        style={{
                          width: '100%', padding: '0.6rem 1rem 0.6rem 2rem',
                          borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.875rem',
                          outline: 'none', background: '#f8fafc', boxSizing: 'border-box'
                        }}
                      />
                    </div>

                    {showProductDropdown && filteredProducts.length > 0 && (
                      <div style={{
                        position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
                        background: 'white', border: '1px solid #e2e8f0', borderRadius: '10px',
                        boxShadow: '0 16px 40px rgba(0,0,0,0.1)', overflow: 'hidden', marginTop: 4
                      }}>
                        {filteredProducts.map(p => (
                          <button
                            key={p.id}
                            onClick={() => addProduct(p)}
                            onMouseDown={e => e.preventDefault()}
                            style={{
                              width: '100%', display: 'flex', alignItems: 'center', gap: '0.6rem',
                              padding: '0.7rem 1rem', background: 'none', border: 'none',
                              textAlign: 'left', cursor: 'pointer', borderBottom: '1px solid #f1f5f9',
                              fontSize: '0.85rem', color: '#0f172a', fontWeight: 500,
                              transition: 'background 0.15s ease'
                            }}
                            onMouseOver={e => e.currentTarget.style.background = '#f8fafc'}
                            onMouseOut={e => e.currentTarget.style.background = 'none'}
                          >
                            <Plus size={13} style={{ color: '#64748b', flexShrink: 0 }} />
                            <span>{p.name}</span>
                            <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: '#94a3b8' }}>#{p.hs_code}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {compareProducts.length >= 4 && (
                  <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', color: '#f59e0b', fontWeight: 500 }}>
                    Maximum 4 products selected.
                  </p>
                )}
              </div>

              {/* FILTERS BOX */}
              <div style={{ ...cardStyle, padding: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                  <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.01em' }}>Filters</h3>
                  <button onClick={clearFilters} style={{ background: 'none', border: 'none', color: '#64748b', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.3rem', cursor: 'pointer', padding: 0 }}>
                    <RotateCcw size={14} /> Reset
                  </button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <select
                    value={pendingFilters.trade_type}
                    onChange={e => setPendingFilters({ ...pendingFilters, trade_type: e.target.value })}
                    style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.9rem', outline: 'none', background: '#f8fafc' }}
                  >
                    <option value="">All Trade Types</option>
                    <option value="IMPORT">Import</option>
                    <option value="EXPORT">Export</option>
                  </select>
                  <input type="text" placeholder="Search Buyer…" value={pendingFilters.buyer}
                    onChange={e => setPendingFilters({ ...pendingFilters, buyer: e.target.value })}
                    style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.9rem', outline: 'none', background: '#f8fafc', boxSizing: 'border-box' }} />
                  <input type="text" placeholder="Search Seller…" value={pendingFilters.seller}
                    onChange={e => setPendingFilters({ ...pendingFilters, seller: e.target.value })}
                    style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.9rem', outline: 'none', background: '#f8fafc', boxSizing: 'border-box' }} />
                  <input type="text" placeholder="Search Country…" value={pendingFilters.country}
                    onChange={e => setPendingFilters({ ...pendingFilters, country: e.target.value })}
                    style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.9rem', outline: 'none', background: '#f8fafc', boxSizing: 'border-box' }} />
                  <button
                    onClick={handleApplyFilters}
                    style={{ marginTop: '0.5rem', padding: '0.75rem', background: '#0f172a', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer' }}
                  >
                    Apply{compareProducts.length > 0 ? ` & Compare` : ' Filters'}
                  </button>
                </div>
              </div>

            </div>

            {/* MAIN DASHBOARD */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }} onClick={() => setShowProductDropdown(false)}>
              {loading ? (
                <div style={{ padding: '4rem 2rem', textAlign: 'center', color: '#64748b', ...cardStyle }}>Loading charts…</div>
              ) : error ? (
                <div style={{ padding: '4rem 2rem', textAlign: 'center', color: '#ef4444', ...cardStyle }}>{error}</div>
              ) : (
                <>
                  {/* Top row: 2 charts side by side */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: '2rem' }}>

                    {/* Avg Price by Date */}
                    <div style={{ ...cardStyle, padding: '1.5rem' }}>
                      <div style={{ marginBottom: '1.5rem' }}>
                        <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.02em' }}>Avg Price by Date (Monthly)</h2>
                        <p style={{ margin: '0.2rem 0 0', fontSize: '0.85rem', color: '#64748b' }}>
                          {isMulti ? `Weighted avg price per product` : `Import vs Export trend`}
                        </p>
                      </div>
                      <div style={{ height: '300px' }}>
                        <Line data={priceTrendData} options={commonOptions} />
                      </div>
                    </div>

                    {/* Avg Price by Country */}
                    <div style={{ ...cardStyle, padding: '1.5rem' }}>
                      <div style={{ marginBottom: '1.5rem' }}>
                        <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.02em' }}>Avg Price by Country</h2>
                        <p style={{ margin: '0.2rem 0 0', fontSize: '0.85rem', color: '#64748b' }}>
                          {isMulti ? `Price comparison across top countries` : `Import vs Export price per country`}
                        </p>
                      </div>
                      <div style={{ height: '300px' }}>
                        <Bar data={priceByCountryData} options={horizontalBarOptions} />
                      </div>
                    </div>
                  </div>

                  {/* Full-width Qty chart */}
                  <div style={{ ...cardStyle, padding: '1.5rem' }}>
                    <div style={{ marginBottom: '1.5rem' }}>
                      <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.02em' }}>Quantity by Country</h2>
                      <p style={{ margin: '0.2rem 0 0', fontSize: '0.85rem', color: '#64748b' }}>
                        {isMulti ? `Volume comparison across products per country` : `Import/Export volume per country`}
                      </p>
                    </div>
                    <div style={{ height: '400px' }}>
                      <Bar data={qtyByCountryData} options={horizontalBarOptions} />
                    </div>
                  </div>
                </>
              )}
            </div>

          </div>
        </div>
      </div>
    </>
  );
};

export default TradeLensComparison;
