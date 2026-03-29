import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import Navbar from '../Layout/Navbar';

const fmtN = (num) => new Intl.NumberFormat('en-US').format(Math.round(num || 0));
const fmtM = (num) => {
  if (!num) return '0';
  if (num >= 1000000) return `$${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `$${(num / 1000).toFixed(0)}K`;
  return `$${new Intl.NumberFormat('en-US').format(num)}`;
};

const CompanyProducts = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const loc = useLocation();
  const query = new URLSearchParams(loc.search);

  const [direction, setDirection] = useState(query.get('direction') || 'import');
  const [pendingProductName, setPendingProductName] = useState('');
  const [productName, setProductName] = useState('');

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const companyName = decodeURIComponent(id);
  const _tab = 'products'; // ensure tab highlight

  useEffect(() => {
    let cancel = false;
    const loadData = async () => {
      setLoading(true);
      try {
        let url = `${process.env.REACT_APP_API_BASE_URL}/api/company/${encodeURIComponent(companyName)}/products/?direction=${direction}`;
        if (productName) url += `&product_name=${encodeURIComponent(productName)}`;

        const res = await fetch(url, { credentials: 'include' });
        if (res.ok) {
          const json = await res.json();
          if (!cancel) setData(json);
        } else {
          if (!cancel) setError('Failed to fetch product insights');
        }
      } catch (e) {
        if (!cancel) setError('Network error loading product insights');
      } finally {
        if (!cancel) setLoading(false);
      }
    };
    loadData();
    return () => { cancel = true; };
  }, [companyName, direction, productName]);

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#0ea5e9', '#14b8a6', '#f43f5e', '#6366f1', '#84cc16'];

  const processedTrendData = React.useMemo(() => {
    const avg_price_trend = data?.avg_price_trend;
    if (!avg_price_trend) return [];
    const allMonths = new Set();
    Object.values(avg_price_trend).forEach(arr => arr.forEach(d => allMonths.add(d.month)));
    const sortedMonths = Array.from(allMonths).sort((a, b) => new Date(a) - new Date(b));
    return sortedMonths.map(m => {
      const row = { monthStr: new Date(m).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }) };
      Object.keys(avg_price_trend).forEach(p => {
        const match = avg_price_trend[p].find(d => d.month === m);
        if (match) row[p] = match.avg_price;
      });
      return row;
    });
  }, [data]);

  const partnerLabel = direction === 'import' ? 'Supplier' : 'Buyer';
  const partnerLabelPlural = direction === 'import' ? 'Suppliers' : 'Buyers';

  if (loading && !data) return <><Navbar /><div style={{ padding: '4rem', textAlign: 'center' }}>Loading products...</div></>;
  if (error) return <><Navbar /><div style={{ padding: '4rem', color: 'red' }}>{error}</div></>;
  if (!data) return null;

  const { summary, products, avg_price_trend, product_partner_matrix, top_partner_per_product } = data;

  const applyFilters = () => {
    setProductName(pendingProductName);
  };

  const clearFilters = () => {
    setPendingProductName('');
    setProductName('');
  };

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
              {t === 'products' ? `Products (${summary?.total_products || 0})` : t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {/* ── SECTION 1: Products Summary Header ────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
          <div style={{ background: 'white', borderRadius: '8px', padding: '1.25rem 1.5rem', border: '1px solid #e5e7eb', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
            <p style={{ margin: '0 0 0.5rem', fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>Total Products</p>
            <div style={{ fontSize: '2rem', fontWeight: 600, color: '#111827', fontFeatureSettings: '"tnum"', letterSpacing: '-0.01em', lineHeight: 1.1 }}>{summary?.total_products || 0}</div>
          </div>
          <div style={{ background: 'white', borderRadius: '8px', padding: '1.25rem 1.5rem', border: '1px solid #e5e7eb', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
            <p style={{ margin: '0 0 0.5rem', fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>Total Volume</p>
            <div style={{ fontSize: '2rem', fontWeight: 600, color: '#111827', fontFeatureSettings: '"tnum"', letterSpacing: '-0.01em', lineHeight: 1.1 }}>{fmtN(summary?.total_volume)} <span style={{ fontSize: '1rem', color: '#6b7280', fontWeight: 400 }}>MT</span></div>
          </div>
          <div style={{ background: 'white', borderRadius: '8px', padding: '1.25rem 1.5rem', border: '1px solid #e5e7eb', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
            <p style={{ margin: '0 0 0.5rem', fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>Total Est. Value</p>
            <div style={{ fontSize: '2rem', fontWeight: 600, color: '#111827', fontFeatureSettings: '"tnum"', letterSpacing: '-0.01em', lineHeight: 1.1 }}>{fmtM(summary?.total_value)}</div>
          </div>
        </div>

        {/* ── SECTION 7: Filters ────────────────────────── */}
        <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', marginBottom: '2rem', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
          <h3 style={{ margin: '0 0 1.25rem', fontSize: '1.15rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Filter Analysis</h3>
          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div style={{ flex: '1 1 200px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, color: '#6b7280', marginBottom: 6 }}>Trade Direction</label>
              <select value={direction} onChange={e => setDirection(e.target.value)}
                style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.9rem', color: '#111827', outline: 'none', appearance: 'none', background: '#f9fafb' }}>
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

        {/* ── SECTION 2/3: Products Table & Dist ────────── */}
        <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
          {/* Section 2: Products Table */}
          <div style={{ flex: '2 1 600px', background: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 2px 8px rgba(0,0,0,0.02)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '1.5rem', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: '0', fontSize: '1.15rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Product Portfolio</h3>
              <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#6b7280' }}>Key traded products sorted by overall volume</p>
            </div>
            <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '400px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', whiteSpace: 'nowrap' }}>
                <thead style={{ position: 'sticky', top: 0, zIndex: 1, background: '#f9fafb' }}>
                  <tr style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#6b7280', letterSpacing: '0.04em', boxShadow: '0 1px 0 #e5e7eb' }}>
                    <th style={{ padding: '1rem 1.5rem', fontWeight: 500 }}>Product Details</th>
                    <th style={{ padding: '1rem 1.5rem', fontWeight: 500, textAlign: 'right' }}>Total Volume (MT)</th>
                    <th style={{ padding: '1rem 1.5rem', fontWeight: 500, textAlign: 'right' }}>Est. Value</th>
                    <th style={{ padding: '1rem 1.5rem', fontWeight: 500, textAlign: 'right' }}>Avg Price</th>
                    <th style={{ padding: '1rem 1.5rem', fontWeight: 500, textAlign: 'right' }}>{partnerLabelPlural}</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((p, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', transition: 'background 0.2s', cursor: 'default' }}
                      onMouseEnter={e => { e.currentTarget.style.background = '#f9fafb'; }} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                      <td style={{ padding: '1.25rem 1.5rem' }}>
                        <div style={{ color: '#111827', fontWeight: 500, fontSize: '0.85rem', whiteSpace: 'normal', maxWidth: '300px', lineHeight: 1.4 }}>
                          {p.product_name}
                        </div>
                        <div style={{ color: '#6b7280', fontSize: '0.75rem', marginTop: 4 }}>{p.subcat || 'Unknown'}</div>
                      </td>
                      <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 500, color: '#111827', fontSize: '0.85rem', fontFeatureSettings: '"tnum"' }}>
                        {fmtN(p.total_volume)}
                      </td>
                      <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 500, color: '#4b5563', fontSize: '0.85rem', fontFeatureSettings: '"tnum"' }}>
                        ${fmtN(p.total_value)}
                      </td>
                      <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 500, color: '#4b5563', fontSize: '0.85rem', fontFeatureSettings: '"tnum"' }}>
                        {p.avg_price ? `$${Math.round(p.avg_price)}` : '-'}
                      </td>
                      <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 500, color: '#6b7280', fontSize: '0.85rem', fontFeatureSettings: '"tnum"' }}>
                        {p.unique_partners}
                      </td>
                    </tr>
                  ))}
                  {products.length === 0 && (
                    <tr><td colSpan="5" style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.9rem' }}>No products found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 3: Product Distribution */}
          <div style={{ flex: '1 1 300px', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
              <h3 style={{ margin: '0 0 1.25rem', fontSize: '1.15rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Volume Distribution</h3>
              <div style={{ height: 300 }}>
                {products.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                      <Pie
                        data={products.slice(0, 5).map(p => ({ name: p.subcat ? (p.subcat.length > 15 ? p.subcat.substring(0, 15) + '...' : p.subcat) : 'Other', value: parseFloat(p.total_volume) }))}
                        cx="50%" cy="50%" innerRadius={50} outerRadius={85} fill="#8884d8" dataKey="value" stroke="none"
                        nameKey="name"
                        labelLine={false}
                        label={({ cx, cy, midAngle, innerRadius, outerRadius, percent, name }) => {
                          if (percent < 0.05) return null;
                          const radius = outerRadius + 15;
                          const x = cx + radius * Math.cos(-midAngle * Math.PI / 180);
                          const y = cy + radius * Math.sin(-midAngle * Math.PI / 180);
                          return (
                            <text x={x} y={y} fill="#4b5563" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize={10} fontWeight={500}>
                              {name} ({(percent * 100).toFixed(0)}%)
                            </text>
                          );
                        }}
                      >
                        {products.slice(0, 5).map((e, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                      </Pie>
                      <Tooltip formatter={(v) => `${fmtN(v)} MT`} contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>No data</div>}
              </div>
            </div>
          </div>
        </div>

        {/* ── SECTION 4 & 5: Trend & Matrix ──────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '2rem', marginBottom: '2rem' }}>

          {/* Section 4: Avg Price Trend */}
          <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
            <h3 style={{ margin: '0', fontSize: '1.15rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Average Price Trends</h3>
            <p style={{ margin: '0.25rem 0 1.25rem 0', fontSize: '0.85rem', color: '#6b7280' }}>Monthly USD/MT trajectory for leading products</p>
            <div style={{ height: 280 }}>
              {processedTrendData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={processedTrendData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                    <XAxis dataKey="monthStr" tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}`} width={40} />
                    <Tooltip contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', fontSize: '0.85rem' }}
                      formatter={v => `$${Math.round(v)}`} />
                    {Object.keys(avg_price_trend).map((productName, idx) => (
                      <Line key={productName} dataKey={productName} connectNulls
                        name={productName.substring(0, 15) + '...'} type="monotone"
                        stroke={COLORS[idx % COLORS.length]} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              ) : <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af', fontSize: '0.85rem' }}>No trend data</div>}
            </div>
          </div>

          {/* Section 5: Matrix Table */}
          <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.02)', overflowY: 'auto', maxHeight: '370px' }}>
            <h3 style={{ margin: '0', fontSize: '1.15rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Top {partnerLabelPlural} by Product</h3>
            <p style={{ margin: '0.25rem 0 1.25rem 0', fontSize: '0.85rem', color: '#6b7280' }}>Revenue concentration amongst counterparties</p>
            {product_partner_matrix?.length > 0 ? (
              <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
                {product_partner_matrix.slice(0, 15).map((row, i) => (
                  <li key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', padding: '10px 0', borderBottom: '1px solid #f3f4f6' }}>
                    <div style={{ flex: 1, overflow: 'hidden', paddingRight: 10 }}>
                      <div style={{ color: '#111827', fontWeight: 500, textOverflow: 'ellipsis', whiteSpace: 'nowrap', overflow: 'hidden' }}>{row.partner}</div>
                      <div style={{ color: '#6b7280', fontSize: '0.75rem', textOverflow: 'ellipsis', whiteSpace: 'nowrap', overflow: 'hidden' }}>{row.product_item__name}</div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div style={{ color: '#111827', fontWeight: 600, fontFeatureSettings: '"tnum"' }}>${fmtM(row.revenue)}</div>
                      <div style={{ color: '#6b7280', fontSize: '0.75rem', fontFeatureSettings: '"tnum"' }}>{fmtN(row.volume)} MT</div>
                    </div>
                  </li>
                ))}
              </ul>
            ) : <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af', fontSize: '0.85rem', height: '100%' }}>No partner data</div>}
          </div>
        </div>

        {/* ── SECTION 6: Top Partner Per Product ────────── */}
        <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', marginBottom: '2rem', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
          <h3 style={{ margin: '0', fontSize: '1.15rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Primary {partnerLabel} per Product</h3>
          <p style={{ margin: '0.25rem 0 1.25rem 0', fontSize: '0.85rem', color: '#6b7280' }}>Identify the leading counterparties driving product volume</p>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', whiteSpace: 'nowrap' }}>
              <thead>
                <tr style={{ background: '#f9fafb', fontSize: '0.75rem', textTransform: 'uppercase', color: '#6b7280', letterSpacing: '0.04em' }}>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 500 }}>Product</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 500 }}>Primary {partnerLabel}</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 500, textAlign: 'right' }}>{partnerLabel} Volume</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 500, textAlign: 'right' }}>{partnerLabel} Revenue</th>
                </tr>
              </thead>
              <tbody>
                {top_partner_per_product?.map((row, i) => (
                  <tr key={i} style={{ borderTop: '1px solid #f3f4f6', transition: 'background 0.2s', cursor: 'default' }}
                    onMouseEnter={e => { e.currentTarget.style.background = '#f9fafb'; }} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                    <td style={{ padding: '1.25rem 1.5rem', color: '#111827', fontWeight: 500, fontSize: '0.85rem', whiteSpace: 'normal', maxWidth: '300px', lineHeight: 1.4 }}>
                      {row.product_item__name}
                    </td>
                    <td style={{ padding: '1.25rem 1.5rem', color: '#4b5563', fontSize: '0.85rem', fontWeight: 500 }}>
                      {row.partner}
                    </td>
                    <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 500, color: '#111827', fontSize: '0.85rem', fontFeatureSettings: '"tnum"' }}>
                      {fmtN(row.volume)} MT
                    </td>
                    <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 500, color: '#4b5563', fontSize: '0.85rem', fontFeatureSettings: '"tnum"' }}>
                      ${fmtN(row.revenue)}
                    </td>
                  </tr>
                ))}
                {(!top_partner_per_product || top_partner_per_product.length === 0) && (
                  <tr><td colSpan="4" style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', fontSize: '0.9rem' }}>No top partner data</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </>
  );
};

export default CompanyProducts;
