import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import Breadcrumb from '../Common/Breadcrumb';
import { ChevronLeft, ChevronRight, RotateCcw } from 'lucide-react';

const TradeLensDetails = () => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState({ summary: {}, top_buyers: [], top_sellers: [], results: [], count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 25;
  const [totalPages, setTotalPages] = useState(1);

  const [appliedFilters, setAppliedFilters] = useState({
    trade_type: '',
    buyer: '',
    seller: '',
    country: '',
  });

  const [pendingFilters, setPendingFilters] = useState({
    trade_type: '',
    buyer: '',
    seller: '',
    country: '',
  });

  const loadDetailsData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.append('page', currentPage);
      if (appliedFilters.trade_type) params.append('trade_type', appliedFilters.trade_type);
      if (appliedFilters.buyer) params.append('buyer', appliedFilters.buyer);
      if (appliedFilters.seller) params.append('seller', appliedFilters.seller);
      if (appliedFilters.country) params.append('country', appliedFilters.country);

      const response = await fetch(
        `http://localhost:8000/api/trade-lens/products/${productId}/details/?${params.toString()}`,
        { credentials: 'include' }
      );
      if (!response.ok) throw new Error('Failed to load transaction details.');
      const result = await response.json();
      setData(result);
      setTotalPages(Math.ceil((result.count || 0) / itemsPerPage));
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [productId, currentPage, appliedFilters]);

  useEffect(() => {
    loadDetailsData();
  }, [loadDetailsData]);

  const handleApplyFilters = () => {
    setCurrentPage(1);
    setAppliedFilters(pendingFilters);
  };

  const clearFilters = () => {
    const empty = { trade_type: '', buyer: '', seller: '', country: '' };
    setPendingFilters(empty);
    setAppliedFilters(empty);
    setCurrentPage(1);
  };

  const fmtCurrency = (value) => {
    if (value === undefined || value === null) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const fmtN = (value) => {
    if (value === undefined || value === null) return '-';
    return new Intl.NumberFormat('en-US').format(Math.round(value));
  };

  const tabs = [
    { id: 'overview', label: 'Overview', path: 'overview' },
    { id: 'comparison', label: 'Comparison', path: 'comparison' },
    { id: 'details', label: 'Details', path: 'details' },
  ];

  const transactions = data.results || [];
  const topBuyers = data.top_buyers || [];
  const topSellers = data.top_sellers || [];

  return (
    <>
      <Navbar />
      <div style={{ background: '#ffffff', minHeight: '100vh', paddingBottom: '4rem', fontFamily: "'DM Sans', 'Inter', sans-serif" }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 2rem' }}>

          {/* Header & Breadcrumb */}
          <div style={{ padding: '2rem 0', borderBottom: '1px solid #e2e8f0', marginBottom: '2rem' }}>
            <Breadcrumb />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '1rem' }}>
              <div>
                <h1 style={{ margin: 0, fontSize: '2.25rem', fontWeight: 700, color: '#111827', letterSpacing: '-0.02em' }}>Trade Lens</h1>
                <p style={{ margin: '0.5rem 0 0', color: '#64748b', fontSize: '1rem' }}>Transaction-level details.</p>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', background: '#f1f5f9', padding: '0.25rem', borderRadius: '8px' }}>
                <button style={{ padding: '0.5rem 1rem', background: '#111827', color: 'white', border: 'none', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer' }}>USD</button>
                <button style={{ padding: '0.5rem 1rem', background: 'transparent', color: '#64748b', border: 'none', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer' }}>PKR</button>
              </div>
            </div>

            {/* Tabs */}
            <div style={{ display: 'inline-flex', background: '#f1f5f9', padding: '4px', borderRadius: '10px', marginTop: '2rem', gap: '4px', border: '1px solid #e2e8f0' }}>
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => navigate(`/trade-intelligence/lens/${productId}/${tab.path}`)}
                  style={{
                    background: tab.id === 'details' ? 'white' : 'transparent',
                    border: 'none',
                    padding: '0.6rem 1.25rem',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    fontWeight: tab.id === 'details' ? 600 : 500,
                    color: tab.id === 'details' ? '#111827' : '#64748b',
                    borderRadius: '8px',
                    boxShadow: tab.id === 'details' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                    transition: 'all 0.2s ease-in-out',
                    WebkitUserSelect: 'none'
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 320px) 1fr', gap: '2rem', alignItems: 'start' }}>

            {/* LEFT SIDEBAR */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>

              {/* Filters Box */}
              <div style={{ background: 'white', borderRadius: '16px', padding: '1.5rem', border: '1px solid rgba(226, 232, 240, 0.6)', boxShadow: '0 12px 32px -4px rgba(0,0,0,0.04), 0 4px 12px -2px rgba(0,0,0,0.02)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                  <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.01em' }}>Filters</h3>
                  <button onClick={clearFilters} style={{ background: 'none', border: 'none', color: '#64748b', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.3rem', cursor: 'pointer', padding: 0 }}>
                    <RotateCcw size={14} /> Reset
                  </button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <select value={pendingFilters.trade_type} onChange={e => setPendingFilters({ ...pendingFilters, trade_type: e.target.value })} style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.9rem', outline: 'none', background: '#f8fafc' }}>
                      <option value="">All Trade Types</option>
                      <option value="IMPORT">Import</option>
                      <option value="EXPORT">Export</option>
                    </select>
                  </div>
                  <div>
                    <input type="text" placeholder="Search Buyer..." value={pendingFilters.buyer} onChange={e => setPendingFilters({ ...pendingFilters, buyer: e.target.value })} style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.9rem', outline: 'none', background: '#f8fafc', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <input type="text" placeholder="Search Seller..." value={pendingFilters.seller} onChange={e => setPendingFilters({ ...pendingFilters, seller: e.target.value })} style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.9rem', outline: 'none', background: '#f8fafc', boxSizing: 'border-box' }} />
                  </div>
                  <div>
                    <input type="text" placeholder="Search Country..." value={pendingFilters.country} onChange={e => setPendingFilters({ ...pendingFilters, country: e.target.value })} style={{ width: '100%', padding: '0.6rem 1rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.9rem', outline: 'none', background: '#f8fafc', boxSizing: 'border-box' }} />
                  </div>
                  <button onClick={handleApplyFilters} style={{ marginTop: '0.5rem', padding: '0.75rem', background: '#111827', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer' }}>
                    Apply Filters
                  </button>
                </div>
              </div>

              {/* Sidebar Mini Tables */}
              {topBuyers.length > 0 && (
                <div style={{ background: 'white', borderRadius: '16px', padding: '1.5rem', border: '1px solid rgba(226, 232, 240, 0.6)', boxShadow: '0 12px 32px -4px rgba(0,0,0,0.04), 0 4px 12px -2px rgba(0,0,0,0.02)' }}>
                  <h3 style={{ margin: '0 0 1rem 0', fontSize: '0.95rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.01em' }}>Top Buyers by Quantity</h3>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                      <thead>
                        <tr style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.05em', borderBottom: '1px solid #e2e8f0' }}>
                          <th style={{ padding: '0.5rem 0', fontWeight: 600 }}>Buyer</th>
                          <th style={{ padding: '0.5rem 0', fontWeight: 600, textAlign: 'right' }}>Qty (MT)</th>
                          <th style={{ padding: '0.5rem 0', fontWeight: 600, textAlign: 'right' }}>Avg Price</th>
                        </tr>
                      </thead>
                      <tbody>
                        {topBuyers.map((b, i) => (
                          <tr key={i} style={{ borderBottom: '1px solid #f1f5f9', fontSize: '0.8rem' }}>
                            <td style={{ padding: '0.75rem 0', color: '#334155', fontWeight: 500, maxWidth: '120px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{b.buyer}</td>
                            <td style={{ padding: '0.75rem 0', color: '#111827', textAlign: 'right', fontFeatureSettings: '"tnum"' }}>{fmtN(b.quantity_mt)}</td>
                            <td style={{ padding: '0.75rem 0', color: '#64748b', textAlign: 'right', fontFeatureSettings: '"tnum"' }}>${fmtN(b.avg_price)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {topSellers.length > 0 && (
                <div style={{ background: 'white', borderRadius: '16px', padding: '1.5rem', border: '1px solid rgba(226, 232, 240, 0.6)', boxShadow: '0 12px 32px -4px rgba(0,0,0,0.04), 0 4px 12px -2px rgba(0,0,0,0.02)' }}>
                  <h3 style={{ margin: '0 0 1rem 0', fontSize: '0.95rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.01em' }}>Top Sellers by Quantity</h3>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                      <thead>
                        <tr style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.05em', borderBottom: '1px solid #e2e8f0' }}>
                          <th style={{ padding: '0.5rem 0', fontWeight: 600 }}>Seller</th>
                          <th style={{ padding: '0.5rem 0', fontWeight: 600, textAlign: 'right' }}>Qty (MT)</th>
                          <th style={{ padding: '0.5rem 0', fontWeight: 600, textAlign: 'right' }}>Avg Price</th>
                        </tr>
                      </thead>
                      <tbody>
                        {topSellers.map((s, i) => (
                          <tr key={i} style={{ borderBottom: '1px solid #f1f5f9', fontSize: '0.8rem' }}>
                            <td style={{ padding: '0.75rem 0', color: '#334155', fontWeight: 500, maxWidth: '120px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.seller}</td>
                            <td style={{ padding: '0.75rem 0', color: '#111827', textAlign: 'right', fontFeatureSettings: '"tnum"' }}>{fmtN(s.quantity_mt)}</td>
                            <td style={{ padding: '0.75rem 0', color: '#64748b', textAlign: 'right', fontFeatureSettings: '"tnum"' }}>${fmtN(s.avg_price)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

            </div>

            {/* MAIN DASHBOARD (TABLE) */}
            <div style={{ background: 'white', border: '1px solid rgba(226, 232, 240, 0.6)', borderRadius: '16px', boxShadow: '0 12px 32px -4px rgba(0,0,0,0.04), 0 4px 12px -2px rgba(0,0,0,0.02)', display: 'flex', flexDirection: 'column' }}>
              <div style={{ padding: '1.5rem', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.02em' }}>Transaction Details</h2>
                  <p style={{ margin: '0.2rem 0 0', fontSize: '0.85rem', color: '#64748b' }}>Granular transaction data based on current filters.</p>
                </div>
                <button style={{ padding: '0.5rem 1rem', border: '1px solid #cbd5e1', background: 'white', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 500, color: '#475569', cursor: 'pointer' }}>Export CSV</button>
              </div>

              {loading ? (
                <div style={{ padding: '4rem 2rem', textAlign: 'center', color: '#64748b' }}>Loading transactions...</div>
              ) : error ? (
                <div style={{ padding: '4rem 2rem', textAlign: 'center', color: '#ef4444' }}>{error}</div>
              ) : transactions.length === 0 ? (
                <div style={{ padding: '4rem 2rem', textAlign: 'center', color: '#64748b' }}>No transactions found for these filters.</div>
              ) : (
                <div style={{ overflowX: 'auto', maxHeight: '700px', overflowY: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', whiteSpace: 'nowrap' }}>
                    <thead style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', position: 'sticky', top: 0, zIndex: 10 }}>
                      <tr style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.05em' }}>
                        <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Buyer</th>
                        <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Seller</th>
                        <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Country</th>
                        <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Quantity (MT)</th>
                        <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Avg Price (USD/MT)</th>
                        <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Date</th>
                        <th style={{ padding: '1rem 1.5rem', fontWeight: 600, textAlign: 'right' }}>Total Value (USD)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((tx, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9', transition: 'background-color 0.2s', cursor: 'pointer' }} onMouseOver={e => e.currentTarget.style.backgroundColor = '#f8fafc'} onMouseOut={e => e.currentTarget.style.backgroundColor = 'transparent'}>
                          <td style={{ padding: '1.25rem 1.5rem', fontSize: '0.9rem', color: '#111827', fontWeight: 500 }}>{tx.buyer || '-'}</td>
                          <td style={{ padding: '1.25rem 1.5rem', fontSize: '0.9rem', color: '#475569' }}>{tx.seller || '-'}</td>
                          <td style={{ padding: '1.25rem 1.5rem', fontSize: '0.9rem', color: '#64748b' }}>{tx.country || '-'}</td>
                          <td style={{ padding: '1.25rem 1.5rem', fontSize: '0.9rem', color: '#111827', textAlign: 'right', fontFeatureSettings: '"tnum"' }}>{fmtN(tx.quantity_mt)}</td>
                          <td style={{ padding: '1.25rem 1.5rem', fontSize: '0.9rem', color: '#64748b', textAlign: 'right', fontFeatureSettings: '"tnum"' }}>${fmtN(tx.avg_price_usd_mt)}</td>
                          <td style={{ padding: '1.25rem 1.5rem', fontSize: '0.9rem', color: '#64748b' }}>{tx.date}</td>
                          <td style={{ padding: '1.25rem 1.5rem', fontSize: '0.9rem', color: '#111827', fontWeight: 600, textAlign: 'right', fontFeatureSettings: '"tnum"' }}>{fmtCurrency(tx.total_value_usd)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Pagination */}
              {!loading && transactions.length > 0 && (
                <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc', borderBottomLeftRadius: '12px', borderBottomRightRadius: '12px' }}>
                  <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                    Showing page <span style={{ fontWeight: 600, color: '#111827' }}>{currentPage}</span> of <span style={{ fontWeight: 600, color: '#111827' }}>{totalPages || 1}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      disabled={currentPage === 1}
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      style={{ padding: '0.5rem', background: 'white', border: '1px solid #cbd5e1', borderRadius: '6px', cursor: currentPage === 1 ? 'not-allowed' : 'pointer', color: currentPage === 1 ? '#94a3b8' : '#475569', display: 'flex', alignItems: 'center' }}
                    >
                      <ChevronLeft size={16} /> <span style={{ marginLeft: '0.25rem', fontSize: '0.85rem', fontWeight: 500 }}>Previous</span>
                    </button>
                    <button
                      disabled={currentPage >= totalPages}
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      style={{ padding: '0.5rem', background: 'white', border: '1px solid #cbd5e1', borderRadius: '6px', cursor: currentPage >= totalPages ? 'not-allowed' : 'pointer', color: currentPage >= totalPages ? '#94a3b8' : '#475569', display: 'flex', alignItems: 'center' }}
                    >
                      <span style={{ marginRight: '0.25rem', fontSize: '0.85rem', fontWeight: 500 }}>Next</span> <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default TradeLensDetails;
