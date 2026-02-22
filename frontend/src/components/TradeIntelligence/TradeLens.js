import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, ArrowDownRight, Package, Box } from 'lucide-react';
import Navbar from '../Layout/Navbar';
import Breadcrumb from '../Common/Breadcrumb';
import { SkeletonCard } from '../Common/Skeleton';
import EmptyState from '../Common/EmptyState';
import './TradeIntelligence.css';

const fmtCurrency = (value) => {
  if (!value || value === 0) return '$0';
  if (value >= 1000000000) return `$${(value / 1000000000).toFixed(1)}B`;
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
  return `$${value.toFixed(0)}`;
};

const fmtN = (v) => {
  if (!v || v === 0) return '0';
  return new Intl.NumberFormat('en-US').format(v);
};

const TradeLens = () => {
  const navigate = useNavigate();
  const [data, setData] = useState({ summary: {}, products: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [appliedFilters, setAppliedFilters] = useState({
    search: '',
    category: '',
    date_from: '',
    date_to: '',
    trade_type: ''
  });

  const [pendingFilters, setPendingFilters] = useState({
    search: '',
    category: '',
    date_from: '',
    date_to: '',
    trade_type: ''
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const p = new URLSearchParams();
      if (appliedFilters.search) p.append('search', appliedFilters.search);
      if (appliedFilters.category) p.append('category', appliedFilters.category);
      if (appliedFilters.date_from) p.append('start_date', appliedFilters.date_from);
      if (appliedFilters.date_to) p.append('end_date', appliedFilters.date_to);
      if (appliedFilters.trade_type) p.append('trade_type', appliedFilters.trade_type);

      const response = await fetch(`http://localhost:8000/api/trade-lens/products/?${p.toString()}`, {
        credentials: 'include'
      });
      if (!response.ok) {
        throw new Error('Failed to load products');
      }
      const jsonData = await response.json();
      setData(jsonData || { summary: {}, products: [] });
    } catch (err) {
      console.error('Error loading trade lens data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [appliedFilters]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleApplyFilters = () => {
    setAppliedFilters(pendingFilters);
  };

  const clearFilters = () => {
    const empty = { search: '', category: '', date_from: '', date_to: '', trade_type: '' };
    setPendingFilters(empty);
    setAppliedFilters(empty);
  };

  const summary = data.summary || {};
  const products = data.products || [];

  return (
    <>
      <Navbar />
      <div style={{ background: '#f8fafc', minHeight: '100vh', paddingBottom: '4rem', fontFamily: '"Satoshi", "Inter", sans-serif' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 2rem' }}>

          <div style={{ padding: '2rem 0' }}>
            <Breadcrumb />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '1rem' }}>
              <div>
                <h1 style={{ margin: 0, fontSize: '2.25rem', fontWeight: 700, color: '#111827', letterSpacing: '-0.02em' }}>Trade Lens</h1>
                <p style={{ margin: '0.5rem 0 0', color: '#64748b', fontSize: '1rem' }}>Product-centric trade intelligence dashboard.</p>
              </div>
            </div>
          </div>

          {/* ── Filters Section ── */}
          <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.5rem', marginBottom: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
            <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>

              <div style={{ flex: '2 1 250px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#64748b', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Search</label>
                <input
                  type="text"
                  placeholder="Product name or HS Code..."
                  value={pendingFilters.search}
                  onChange={(e) => setPendingFilters({ ...pendingFilters, search: e.target.value })}
                  style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.9rem', outline: 'none', background: '#f8fafc', transition: 'border-color 0.2s' }}
                />
              </div>

              <div style={{ flex: '1 1 150px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#64748b', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Trade Direction</label>
                <select
                  value={pendingFilters.trade_type}
                  onChange={(e) => setPendingFilters({ ...pendingFilters, trade_type: e.target.value })}
                  style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.9rem', outline: 'none', background: '#f8fafc' }}
                >
                  <option value="">All Directions</option>
                  <option value="IMPORT">Import</option>
                  <option value="EXPORT">Export</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '1rem', flex: '0 0 auto' }}>
                <button
                  onClick={clearFilters}
                  style={{ padding: '0.75rem 1.25rem', background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.9rem', fontWeight: 500, color: '#475569', cursor: 'pointer', transition: 'all 0.2s' }}
                >
                  Clear
                </button>
                <button
                  onClick={handleApplyFilters}
                  style={{ padding: '0.75rem 1.5rem', background: '#111827', border: 'none', borderRadius: '8px', fontSize: '0.9rem', fontWeight: 500, color: 'white', cursor: 'pointer', transition: 'all 0.2s' }}
                >
                  Apply Filters
                </button>
              </div>
            </div>
          </div>

          {/* ── Summary Metrics Row ── */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>

            <div style={{ background: 'white', borderRadius: '12px', padding: '1.5rem', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.02)', display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
              <div style={{ background: '#f1f5f9', padding: '1rem', borderRadius: '12px', color: '#475569' }}>
                <Box size={24} />
              </div>
              <div>
                <p style={{ margin: '0 0 0.25rem', fontSize: '0.8rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em' }}>Products Tracked</p>
                <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827', fontFeatureSettings: '"tnum"' }}>
                  {fmtN(summary.total_products)}
                </div>
              </div>
            </div>

            <div style={{ background: 'white', borderRadius: '12px', padding: '1.5rem', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.02)', display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
              <div style={{ background: '#eff6ff', padding: '1rem', borderRadius: '12px', color: '#2563eb' }}>
                <ArrowDownRight size={24} />
              </div>
              <div>
                <p style={{ margin: '0 0 0.25rem', fontSize: '0.8rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em' }}>Total Import Value</p>
                <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827', fontFeatureSettings: '"tnum"' }}>
                  {fmtCurrency(summary.total_import_value)}
                </div>
              </div>
            </div>

            <div style={{ background: 'white', borderRadius: '12px', padding: '1.5rem', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.02)', display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
              <div style={{ background: '#f0fdf4', padding: '1rem', borderRadius: '12px', color: '#16a34a' }}>
                <ArrowUpRight size={24} />
              </div>
              <div>
                <p style={{ margin: '0 0 0.25rem', fontSize: '0.8rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em' }}>Total Export Value</p>
                <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827', fontFeatureSettings: '"tnum"' }}>
                  {fmtCurrency(summary.total_export_value)}
                </div>
              </div>
            </div>

            <div style={{ background: 'white', borderRadius: '12px', padding: '1.5rem', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.02)', display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
              <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '12px', color: '#475569' }}>
                <Package size={24} />
              </div>
              <div>
                <p style={{ margin: '0 0 0.25rem', fontSize: '0.8rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em' }}>Total Transactions</p>
                <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827', fontFeatureSettings: '"tnum"' }}>
                  {fmtN(summary.total_transactions)}
                </div>
              </div>
            </div>

          </div>

          {/* ── Products List Table ── */}
          {loading ? (
            <div style={{ padding: '4rem', textAlign: 'center', color: '#64748b' }}>Loading Trade Lens Product Analytics...</div>
          ) : error ? (
            <EmptyState title="Error fetching data" description={error} actionLabel="Retry" onAction={loadData} />
          ) : products.length === 0 ? (
            <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '4rem 2rem', textAlign: 'center' }}>
              <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.25rem', color: '#111827', fontWeight: 600 }}>No products found</h3>
              <p style={{ margin: '0 0 1.5rem', color: '#64748b' }}>Adjust your Search or Trade Direction criteria to discover products.</p>
              <button onClick={clearFilters} style={{ padding: '0.5rem 1rem', background: '#111827', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>Clear Filters</button>
            </div>
          ) : (
            <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.02)', overflow: 'hidden' }}>
              <div style={{ overflowX: 'auto', maxHeight: '600px', overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', whiteSpace: 'nowrap' }}>
                  <thead style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', position: 'sticky', top: 0, zIndex: 10 }}>
                    <tr style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.05em' }}>
                      <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Product Name / HS Code</th>
                      <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Import Volume</th>
                      <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Import Value</th>
                      <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Export Volume</th>
                      <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Export Value</th>
                      <th style={{ width: '100%' }}></th>
                    </tr>
                  </thead>
                  <tbody style={{ divideY: '1px solid #f1f5f9' }}>
                    {products.map((p) => (
                      <tr
                        key={p.id}
                        onClick={() => navigate(`/trade-intelligence/lens/${p.id}/overview`)}
                        style={{ borderBottom: '1px solid #f1f5f9', cursor: 'pointer', transition: 'background 0.2s' }}
                        onMouseEnter={e => e.currentTarget.style.background = '#f8fafc'}
                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                      >
                        <td style={{ padding: '1.25rem 1.5rem' }}>
                          <div style={{ color: '#111827', fontWeight: 600, fontSize: '0.95rem', marginBottom: '4px' }}>{p.name}</div>
                          <div style={{ color: '#64748b', fontSize: '0.8rem', display: 'flex', gap: '0.5rem' }}>
                            <span style={{ fontFeatureSettings: '"tnum"' }}>HS: {p.hs_code}</span>
                            <span>•</span>
                            <span>{p.category}</span>
                          </div>
                        </td>
                        <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 500, color: '#111827', fontSize: '0.9rem', fontFeatureSettings: '"tnum"' }}>
                          {fmtN(p.import_quantity)} <span style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 400 }}>MT</span>
                        </td>
                        <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 500, color: '#2563eb', fontSize: '0.9rem', fontFeatureSettings: '"tnum"' }}>
                          {fmtCurrency(p.import_value)}
                        </td>
                        <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 500, color: '#111827', fontSize: '0.9rem', fontFeatureSettings: '"tnum"' }}>
                          {fmtN(p.export_quantity)} <span style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 400 }}>MT</span>
                        </td>
                        <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 500, color: '#16a34a', fontSize: '0.9rem', fontFeatureSettings: '"tnum"' }}>
                          {fmtCurrency(p.export_value)}
                        </td>
                        <td style={{ width: '100%' }}></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>
      </div>
    </>
  );
};

export default TradeLens;

