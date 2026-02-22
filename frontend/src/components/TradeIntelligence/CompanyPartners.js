import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const fmtN = (v) => {
  if (!v) return '0';
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(v);
};

const fmtM = (v) => {
  if (!v) return '$0';
  if (v >= 1e6) return '$' + (v / 1e6).toFixed(1) + 'M';
  if (v >= 1e3) return '$' + (v / 1e3).toFixed(0) + 'K';
  return '$' + new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(v);
};

const CompanyPartners = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const loc = useLocation();
  const companyName = decodeURIComponent(id);
  const _tab = 'partners';

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [direction, setDirection] = useState('import');
  const [productName, setProductName] = useState('');
  const [pendingProductName, setPendingProductName] = useState('');

  // Sorting state for Top Partners Table
  const [sortConfig, setSortConfig] = useState({ key: 'total_volume', direction: 'desc' });

  useEffect(() => {
    let cancel = false;
    const loadParts = async () => {
      setLoading(true);
      setError(null);
      try {
        let url = `http://localhost:8000/api/company/${encodeURIComponent(companyName)}/partners/?direction=${direction}`;
        if (productName) url += `&product_name=${encodeURIComponent(productName)}`;

        const res = await fetch(url, { credentials: 'include' });
        if (res.ok) {
          const json = await res.json();
          if (!cancel) setData(json);
        } else {
          if (!cancel) setError('Failed to load partner insights');
        }
      } catch (err) {
        if (!cancel) setError('Network error loading partner insights');
      } finally {
        if (!cancel) setLoading(false);
      }
    };
    loadParts();
    return () => { cancel = true; };
  }, [companyName, direction, productName]);

  const applyFilters = () => setProductName(pendingProductName);
  const clearFilters = () => { setPendingProductName(''); setProductName(''); };

  const COLORS = ['#2563eb', '#3b82f6', '#60a5fa', '#f59e0b', '#10b981', '#6366f1'];

  // Data processing
  const top_partners = data?.top_partners || [];
  const volume_by_country = data?.volume_by_country || [];
  const monthly_partner_trends = data?.monthly_partner_trends || [];
  const product_mix_per_partner = data?.product_mix_per_partner || [];
  const summary = data?.summary || { total_volume: 0 };

  const totalVolumeOverall = summary.total_volume || 1;

  // Process Trends for Line Chart
  const processedTrendData = React.useMemo(() => {
    if (!monthly_partner_trends.length) return [];
    const allMonths = new Set();
    monthly_partner_trends.forEach(d => allMonths.add(d.month));
    const sortedMonths = Array.from(allMonths).sort((a, b) => new Date(a) - new Date(b));

    return sortedMonths.map(m => {
      const row = { monthStr: new Date(m).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }) };
      const records = monthly_partner_trends.filter(d => d.month === m);
      records.forEach(r => {
        row[r.partner] = r.volume;
      });
      return row;
    });
  }, [monthly_partner_trends]);

  // Sorting Logic for Top Partners Table
  const sortedPartners = React.useMemo(() => {
    let sortableItems = [...top_partners];
    if (sortConfig.key) {
      sortableItems.sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];

        if (aValue === null || aValue === undefined) return 1;
        if (bValue === null || bValue === undefined) return -1;

        if (typeof aValue === 'string') {
          return sortConfig.direction === 'asc'
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
        } else {
          return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
        }
      });
    }
    return sortableItems;
  }, [top_partners, sortConfig]);

  const requestSort = (key) => {
    let newDirection = 'desc';
    if (sortConfig.key === key && sortConfig.direction === 'desc') {
      newDirection = 'asc';
    }
    setSortConfig({ key, direction: newDirection });
  };

  const trendLines = Array.from(new Set(monthly_partner_trends.map(d => d.partner)));

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) return <span style={{ opacity: 0.3, marginLeft: 4 }}>↕</span>;
    return <span style={{ marginLeft: 4 }}>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>;
  };

  const partnerLabel = direction === 'import' ? 'Supplier' : 'Buyer';

  return (
    <><Navbar />
      <div style={{ padding: '2rem', background: '#fafafa', minHeight: '100vh', fontFamily: "'Satoshi', 'Inter', -apple-system, sans-serif" }}>

        {/* ── Header ─────────────────────────────────────── */}
        <div style={{ marginBottom: '2rem' }}>
          <button onClick={() => navigate('/trade-intelligence/ledger')}
            style={{ background: 'none', border: 'none', color: '#6b7280', cursor: 'pointer', fontSize: '0.85rem', padding: 0, marginBottom: '0.75rem', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            ← Back to Trade Ledger
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <h1 style={{ margin: 0, fontSize: '2.25rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.02em', lineHeight: 1.1 }}>{companyName}</h1>
          </div>
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', color: '#6b7280' }}>
            Partner Network & Trade Concentration
          </p>
        </div>

        <div style={{ display: 'inline-flex', background: '#f1f5f9', padding: '4px', borderRadius: '10px', marginBottom: '2rem', gap: '4px', border: '1px solid #e2e8f0' }}>
          {['overview', 'products', 'partners'].map(t => (
            <button key={t}
              onClick={() => navigate(`/trade-intelligence/company/${encodeURIComponent(companyName)}/${t}?direction=${direction}`)}
              style={{
                background: t === _tab ? 'white' : 'transparent',
                border: 'none',
                padding: '0.6rem 1.25rem',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: t === _tab ? 600 : 500,
                color: t === _tab ? '#111827' : '#64748b',
                borderRadius: '8px',
                boxShadow: t === _tab ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                transition: 'all 0.2s ease-in-out',
                WebkitUserSelect: 'none'
              }}
            >
              {t === 'partners' && summary ? `Partners (${summary.total_partners || 0})` : t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {/* ── SECTION 5: Filters ────────────────────────── */}
        <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', marginBottom: '2rem', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
          <h3 style={{ margin: '0 0 1.25rem', fontSize: '1.15rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Data Scope & Filters</h3>
          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div style={{ flex: '1 1 200px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, color: '#6b7280', marginBottom: 6 }}>Trade Direction</label>
              <select value={direction} onChange={e => setDirection(e.target.value)}
                style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.9rem', color: '#111827', outline: 'none', background: '#f9fafb' }}>
                <option value="import">Import Activity</option>
                <option value="export">Export Activity</option>
                <option value="both">Both Directions</option>
              </select>
            </div>
            <div style={{ flex: '1 1 200px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, color: '#6b7280', marginBottom: 6 }}>Product Search</label>
              <input type="text" placeholder="e.g. Sugar, Iron" value={pendingProductName}
                onChange={e => setPendingProductName(e.target.value)}
                style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box' }} />
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', flex: '0 0 auto' }}>
              <button onClick={clearFilters}
                style={{ padding: '0.6rem 1rem', background: '#f3f4f6', border: 'none', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 500, color: '#374151', cursor: 'pointer', transition: 'background 0.2s' }}
                onMouseEnter={e => e.currentTarget.style.background = '#e5e7eb'} onMouseLeave={e => e.currentTarget.style.background = '#f3f4f6'}>
                Clear
              </button>
              <button onClick={applyFilters}
                style={{ padding: '0.6rem 1.25rem', background: '#111827', border: 'none', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 500, color: 'white', cursor: 'pointer', transition: 'background 0.2s' }}
                onMouseEnter={e => e.currentTarget.style.background = '#374151'} onMouseLeave={e => e.currentTarget.style.background = '#111827'}>
                Apply Filters
              </button>
            </div>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '4rem', textAlign: 'center', color: '#6b7280' }}>Loading partner insights...</div>
        ) : error ? (
          <div style={{ padding: '4rem', textAlign: 'center', color: '#ef4444' }}>{error}</div>
        ) : !data ? null : (
          <>
            {/* ── SECTION 1: Top Trading Partners Table ──────── */}
            <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', marginBottom: '2rem', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
              <h3 style={{ margin: '0 0 1.25rem', fontSize: '1.25rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Top Trading Partners</h3>
              <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '450px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', whiteSpace: 'nowrap' }}>
                  <thead style={{ position: 'sticky', top: 0, zIndex: 1, background: '#f9fafb' }}>
                    <tr style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#6b7280', letterSpacing: '0.04em', boxShadow: '0 1px 0 #e5e7eb', cursor: 'pointer' }}>
                      <th onClick={() => requestSort('partner')} style={{ padding: '1rem 1.5rem', fontWeight: 500 }}>
                        Partner Company <SortIcon columnKey="partner" />
                      </th>
                      <th onClick={() => requestSort('partner_country')} style={{ padding: '1rem 1.5rem', fontWeight: 500 }}>
                        Country <SortIcon columnKey="partner_country" />
                      </th>
                      <th onClick={() => requestSort('total_volume')} style={{ padding: '1rem 1.5rem', fontWeight: 500, textAlign: 'right' }}>
                        Total Volume (MT) <SortIcon columnKey="total_volume" />
                      </th>
                      <th onClick={() => requestSort('avg_price')} style={{ padding: '1rem 1.5rem', fontWeight: 500, textAlign: 'right' }}>
                        Avg Price (USD/MT) <SortIcon columnKey="avg_price" />
                      </th>
                      <th onClick={() => requestSort('yoy_growth')} style={{ padding: '1rem 1.5rem', fontWeight: 500, textAlign: 'right' }}>
                        YoY Volume Change <SortIcon columnKey="yoy_growth" />
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedPartners.map((p, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', transition: 'background 0.2s' }}
                        onMouseEnter={e => { e.currentTarget.style.background = '#f9fafb'; }} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                        <td style={{ padding: '1.25rem 1.5rem', color: '#111827', fontWeight: 600, fontSize: '0.85rem' }}>
                          {p.partner}
                        </td>
                        <td style={{ padding: '1.25rem 1.5rem', color: '#6b7280', fontSize: '0.85rem' }}>
                          {p.partner_country || '-'}
                        </td>
                        <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 500, color: '#111827', fontSize: '0.85rem', fontFeatureSettings: '"tnum"' }}>
                          {fmtN(p.total_volume)}
                        </td>
                        <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 500, color: '#4b5563', fontSize: '0.85rem', fontFeatureSettings: '"tnum"' }}>
                          {p.avg_price ? `$${Math.round(p.avg_price)}` : '-'}
                        </td>
                        <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 500, fontSize: '0.85rem', fontFeatureSettings: '"tnum"', color: p.yoy_growth > 0 ? '#111827' : '#6b7280' }}>
                          {p.yoy_growth !== null ? `${p.yoy_growth > 0 ? '+' : ''}${p.yoy_growth}%` : '-'}
                        </td>
                      </tr>
                    ))}
                    {sortedPartners.length === 0 && (
                      <tr><td colSpan="5" style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.9rem' }}>No partners found</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* ── SECTION 2 / 3: Grid Wrapper ────────────────── */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', marginBottom: '2rem' }}>

              {/* SECTION 2: Trade Volume by Partner Country */}
              <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
                <h3 style={{ margin: '0 0 1.25rem', fontSize: '1.15rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Trade Volume by Partner Country</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {volume_by_country.map((c, i) => {
                    const pct = (c.total_volume / totalVolumeOverall) * 100;
                    return (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', fontSize: '0.85rem' }}>
                        <div style={{ width: '120px', color: '#4b5563', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: '1rem' }}>
                          {c.country || 'Unknown'}
                        </div>
                        <div style={{ flex: 1, height: '24px', background: '#f3f4f6', borderRadius: '4px', position: 'relative', overflow: 'hidden' }}>
                          <div style={{ position: 'absolute', top: 0, left: 0, bottom: 0, width: `${Math.min(pct, 100)}%`, background: '#cbd5e1' }} />
                        </div>
                        <div style={{ width: '100px', textAlign: 'right', color: '#111827', fontWeight: 600, fontFeatureSettings: '"tnum"', paddingLeft: '1rem' }}>
                          {fmtN(c.total_volume)} MT
                        </div>
                        <div style={{ width: '60px', textAlign: 'right', color: '#6b7280', fontFeatureSettings: '"tnum"' }}>
                          {pct.toFixed(1)}%
                        </div>
                      </div>
                    );
                  })}
                  {volume_by_country.length > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', fontSize: '0.85rem', paddingTop: '1rem', borderTop: '1px solid #e5e7eb', marginTop: '0.5rem' }}>
                      <div style={{ flex: 1, color: '#111827', fontWeight: 500 }}>Total Volume</div>
                      <div style={{ textAlign: 'right', color: '#111827', fontWeight: 600, fontFeatureSettings: '"tnum"' }}>
                        {fmtN(totalVolumeOverall)} MT
                      </div>
                    </div>
                  )}
                  {volume_by_country.length === 0 && (
                    <div style={{ textAlign: 'center', color: '#9ca3af', fontSize: '0.85rem', padding: '1rem' }}>No data</div>
                  )}
                </div>
              </div>

              {/* SECTION 3: Monthly Trade Activity */}
              <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
                <h3 style={{ margin: '0 0 1.25rem', fontSize: '1.15rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Monthly Trade Activity with Top Partners</h3>
                <div style={{ height: 320, background: '#f8fafc', padding: '1rem', borderRadius: '4px' }}>
                  {processedTrendData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={processedTrendData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                        <XAxis dataKey="monthStr" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} dy={10} />
                        <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} width={50} tickFormatter={v => fmtN(v)} />
                        <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.05)', fontSize: '0.85rem' }} />
                        <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '20px' }} iconType="plainline" />
                        {trendLines.map((partnerName, idx) => (
                          <Line key={partnerName} dataKey={partnerName} name={partnerName} connectNulls type="monotone"
                            stroke={COLORS[idx % COLORS.length]} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  ) : <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>No trend data</div>}
                </div>
              </div>

            </div>

            {/* ── SECTION 4: Product Mix per Partner ────────── */}
            <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', marginBottom: '2rem', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
              <h3 style={{ margin: '0 0 1.25rem', fontSize: '1.15rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Key Products Traded with Partners</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
                {product_mix_per_partner.map((group, idx) => {
                  const partnerTotal = group.top_products.reduce((acc, p) => acc + parseFloat(p.volume || 0), 0);
                  return (
                    <div key={idx} style={{ padding: '0 1rem' }}>
                      <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.9rem', fontWeight: 700, color: '#2563eb' }}>{group.partner}</h4>
                      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                        {group.top_products.map((prod, pIdx) => {
                          const pct = partnerTotal ? (parseFloat(prod.volume || 0) / partnerTotal) * 100 : 0;

                          let cleanName = prod.product_name || 'Unknown';
                          cleanName = cleanName.split('(NOTE:')[0].split('""')[0].split('(')[0].trim();
                          if (cleanName.length > 55) cleanName = cleanName.substring(0, 52) + '...';

                          return (
                            <li key={pIdx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#4b5563', padding: '6px 0', borderBottom: '1px solid #f8fafc' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, paddingRight: '1rem' }}>
                                <span style={{ color: '#3b82f6', fontSize: '1.2em' }}>•</span>
                                <span style={{ fontWeight: 500 }}>{cleanName}</span>
                              </div>
                              <div style={{ fontWeight: 600, color: '#111827', fontFeatureSettings: '"tnum"', whiteSpace: 'nowrap' }}>
                                {fmtN(prod.volume)} MT <span style={{ color: '#6b7280', fontWeight: 400, marginLeft: '4px' }}>({pct.toFixed(0)}%)</span>
                              </div>
                            </li>
                          )
                        })}
                      </ul>
                    </div>
                  );
                })}
              </div>
            </div>

          </>
        )}
      </div>
    </>
  );
};

export default CompanyPartners;

