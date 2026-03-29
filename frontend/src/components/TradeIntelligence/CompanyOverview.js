import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps';
import './TradeIntelligence.css';

// ─── Colour palette ────────────────────────────────────────
const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

const TYPE_STYLES = {
  'Pakistani Importer': { background: '#f8fafc', color: '#334155', border: '#e2e8f0' },
  'Pakistani Exporter': { background: '#f8fafc', color: '#334155', border: '#e2e8f0' },
  'Pakistani Trader': { background: '#f8fafc', color: '#334155', border: '#e2e8f0' },
  'Foreign Seller': { background: '#f8fafc', color: '#334155', border: '#e2e8f0' },
  'Foreign Buyer': { background: '#f8fafc', color: '#334155', border: '#e2e8f0' },
};

// [lon, lat] for react-simple-maps
const COORDS = {
  Malaysia: [101.9, 4.2], Indonesia: [113.9, -0.8], UAE: [53.8, 23.4],
  'United Arab Emirates': [53.8, 23.4], China: [104.2, 35.9],
  'Saudi Arabia': [45.0, 24.0], Brazil: [-51.9, -14.2], USA: [-95.7, 37.1],
  'United States': [-95.7, 37.1], India: [79.0, 20.6], Pakistan: [69.3, 30.4],
  Argentina: [-63.6, -38.4], Australia: [133.8, -25.3], Thailand: [101.0, 15.9],
  Germany: [10.5, 51.2], France: [2.2, 46.2], UK: [-3.4, 55.4],
  'United Kingdom': [-3.4, 55.4], Turkey: [35.2, 39.0], Singapore: [103.8, 1.4],
  Japan: [138.3, 36.2], 'South Korea': [128.0, 36.6], Bangladesh: [90.4, 23.7],
  'Sri Lanka': [80.8, 7.9], Iran: [53.7, 32.4], Iraq: [43.7, 33.2],
  Kuwait: [47.5, 29.3], Egypt: [30.8, 26.8], 'South Africa': [22.9, -30.6],
  Netherlands: [5.3, 52.1], Ukraine: [31.2, 48.4], Russia: [105.3, 61.5],
  Canada: [-106.4, 56.1], Vietnam: [108.3, 14.1], Philippines: [121.8, 12.9],
  Poland: [19.1, 51.9], Spain: [-3.7, 40.5], Italy: [12.6, 41.9],
  Morocco: [-7.1, 31.8], Nigeria: [8.7, 9.1], Chile: [-71.5, -35.7],
  Colombia: [-74.3, 4.6], Peru: [-75.0, -9.2], Sudan: [30.2, 12.9],
  Kenya: [37.9, -0.0], Ethiopia: [40.5, 9.1], Myanmar: [96.2, 16.9],
  Tanzania: [34.9, -6.4], Ghana: [-1.0, 7.9],
};

const GEO_URL = 'https://unpkg.com/world-atlas@2.0.2/countries-110m.json';

// ─── Formatters ───────────────────────────────────────────
const fmtN = (v, d = 0) =>
  new Intl.NumberFormat('en-US', { maximumFractionDigits: d }).format(v || 0);

const fmtM = (v) => {
  if (!v) return '—';
  if (v >= 1_000_000) return `$${fmtN(v / 1_000_000, 1)}M`;
  if (v >= 1_000) return `$${fmtN(v / 1_000, 0)}K`;
  return `$${fmtN(v)}`;
};

const fmtDate = (d) => {
  if (!d) return '';
  try { return new Date(d).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }); }
  catch { return d; }
};

const fmtMonth = (s) => {
  if (!s) return '';
  try { return new Date(s + '-01').toLocaleDateString('en-US', { month: 'short', year: '2-digit' }); }
  catch { return s; }
};

// ─── SVG Line Chart ───────────────────────────────────────
const LineChart = ({ data, width = 600, height = 180 }) => {
  if (!data || data.length < 2) return (
    <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#cbd5e0', fontSize: '0.85rem' }}>
      Not enough data for volume trend
    </div>
  );

  const PAD = { top: 15, right: 20, bottom: 35, left: 55 };
  const W = width - PAD.left - PAD.right;
  const H = height - PAD.top - PAD.bottom;

  const vols = data.map(d => d.volume);
  const maxV = Math.max(...vols) || 1;
  const minV = 0;

  const xs = data.map((_, i) => PAD.left + (i / (data.length - 1)) * W);
  const ys = data.map(d => PAD.top + H - ((d.volume - minV) / (maxV - minV)) * H);

  const linePath = xs.map((x, i) => `${i === 0 ? 'M' : 'L'} ${x} ${ys[i]}`).join(' ');
  const areaPath = `${linePath} L ${xs[xs.length - 1]} ${PAD.top + H} L ${xs[0]} ${PAD.top + H} Z`;

  const ticks = [0, 0.25, 0.5, 0.75, 1].map(f => ({
    y: PAD.top + H - f * H,
    label: fmtN(minV + f * (maxV - minV)),
  }));

  const step = Math.ceil(data.length / 6);

  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} style={{ overflow: 'visible' }}>
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.01" />
        </linearGradient>
      </defs>

      {/* Y grid + ticks */}
      {ticks.map((t, i) => (
        <g key={i}>
          <line x1={PAD.left} y1={t.y} x2={PAD.left + W} y2={t.y} stroke="#e2e8f0" strokeDasharray="4 4" />
          <text x={PAD.left - 8} y={t.y + 3} fontSize={10} fill="#718096" textAnchor="end">{t.label}</text>
        </g>
      ))}

      {/* Area + Line */}
      <path d={areaPath} fill="url(#areaGrad)" />
      <path d={linePath} fill="none" stroke="#8b5cf6" strokeWidth={3} strokeLinejoin="round" />

      {/* X labels */}
      {data.map((d, i) => i % step === 0 && (
        <text key={i} x={xs[i]} y={PAD.top + H + 20} fontSize={10} fill="#718096" textAnchor="middle">
          {fmtMonth(d.month)}
        </text>
      ))}

      {/* Point on last value */}
      <circle cx={xs[xs.length - 1]} cy={ys[ys.length - 1]} r={4} fill="#8b5cf6" />
    </svg>
  );
};

// ─── World Map with Pins ──────────────────────────────────
const GeoMap = ({ geoData }) => {
  const [tooltip, setTooltip] = useState(null);
  const maxVol = Math.max(...geoData.map(g => g.volume), 1);

  const pins = geoData.map(g => {
    const coords = COORDS[g.country] || [0, 0];
    const r = 4 + (g.volume / maxVol) * 8;
    return { ...g, coords, r };
  }).filter(p => p.coords[0] !== 0);

  return (
    <div style={{ position: 'relative', background: '#f8fafc', borderRadius: 8, overflow: 'hidden' }}>
      <ComposableMap projection="geoMercator" projectionConfig={{ scale: 110 }} style={{ width: '100%', height: 'auto', outline: 'none' }}>
        <Geographies geography={GEO_URL}>
          {({ geographies }) =>
            geographies.map((geo) => (
              <Geography key={geo.rsmKey} geography={geo} fill="#e2e8f0" stroke="#cbd5e0" strokeWidth={0.5} style={{ default: { outline: 'none' }, hover: { fill: '#cbd5e0', outline: 'none' }, pressed: { outline: 'none' } }} />
            ))
          }
        </Geographies>

        {pins.map((p, i) => (
          <Marker key={i} coordinates={p.coords}
            onMouseEnter={() => setTooltip(p)}
            onMouseLeave={() => setTooltip(null)}
            style={{ cursor: 'pointer' }}>
            <circle r={p.r} fill={p.trade_type === 'import' ? '#3b82f6' : '#10b981'} opacity={0.8} stroke="white" strokeWidth={1} />
          </Marker>
        ))}
      </ComposableMap>

      {/* Tooltip */}
      {tooltip && (
        <div style={{
          position: 'absolute', top: 10, right: 10, background: 'white', padding: '0.6rem 0.8rem',
          borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.1)', border: '1px solid #e2e8f0',
          pointerEvents: 'none', zIndex: 10
        }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#2d3748', marginBottom: 2 }}>{tooltip.country}</div>
          <div style={{ fontSize: '0.75rem', color: '#718096' }}>{fmtN(tooltip.volume)} MT · {tooltip.trade_type}</div>
        </div>
      )}

      {/* Legend */}
      <div style={{ padding: '0.5rem 1rem', background: 'rgba(255,255,255,0.7)', borderTop: '1px solid #e2e8f0', display: 'flex', gap: '1rem', fontSize: '0.75rem', color: '#4a5568' }}>
        <span><span style={{ color: '#3b82f6', fontWeight: 700 }}>●</span> Import partners</span>
        <span><span style={{ color: '#10b981', fontWeight: 700 }}>●</span> Export partners</span>
      </div>
    </div>
  );
};

// ─── Horizontal bar ───────────────────────────────────────
const HBar = ({ label, pct, note, color }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
    <span style={{ width: 130, fontSize: '0.85rem', color: '#2d3748', flexShrink: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 500 }} title={label}>
      {label}
    </span>
    <div style={{ flex: 1, height: 10, borderRadius: 5, background: '#edf2f7', overflow: 'hidden' }}>
      <div style={{ height: '100%', width: `${Math.min(pct, 100)}%`, background: color, borderRadius: 5, transition: 'width 0.5s ease' }} />
    </div>
    <span style={{ width: 45, textAlign: 'right', fontSize: '0.85rem', color: '#4a5568', fontWeight: 700, flexShrink: 0 }}>
      {note}
    </span>
  </div>
);

// ─── Section wrapper ───────────────────────────────────────
const Section = ({ title, children, accent = '#10b981', style = {} }) => (
  <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 12, padding: '1.5rem', marginBottom: '1.5rem', borderTop: `3px solid ${accent}`, boxShadow: '0 2px 8px rgba(0,0,0,0.03)', ...style }}>
    <h3 style={{ margin: '0 0 1.25rem', fontSize: '1.2rem', fontWeight: 800, color: '#1a202c' }}>{title}</h3>
    {children}
  </div>
);


const CompanyOverview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const loc = useLocation();
  const companyName = decodeURIComponent(id);
  const tab = loc.pathname.split('/').pop();

  const [data, setData] = useState(null);
  const [load, setLoad] = useState(true);
  const [error, setError] = useState(null);

  const [applied, setApplied] = useState({ dateFrom: '', dateTo: '', tradeType: '', productName: '' });
  const [pending, setPending] = useState({ dateFrom: '', dateTo: '', tradeType: '', productName: '' });

  const loadData = useCallback(async () => {
    setLoad(true); setError(null);
    try {
      const p = new URLSearchParams();
      if (applied.dateFrom) p.append('date_from', applied.dateFrom);
      if (applied.dateTo) p.append('date_to', applied.dateTo);
      if (applied.tradeType) p.append('direction', applied.tradeType);
      if (applied.productName) p.append('product_name', applied.productName);

      const res = await fetch(`${process.env.REACT_APP_API_BASE_URL}/api/company/${id}/overview/?${p}`, { credentials: 'include' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
    } catch (e) { setError('Failed to load company data'); }
    finally { setLoad(false); }
  }, [id, applied]);

  useEffect(() => { loadData(); }, [loadData]);

  if (load) return <><Navbar /><div className="loading-container"><div className="spinner" /><p>Loading…</p></div></>;
  if (error || !data) return (
    <><Navbar />
      <div className="empty-state">
        <h2>{error || 'Company not found'}</h2>
        <button className="btn-primary" style={{ marginTop: '1rem' }} onClick={() => navigate('/trade-intelligence/ledger')}>← Back</button>
      </div>
    </>
  );

  const km = data.key_metrics || {};
  const mix = data.product_mix || [];
  const geo = data.partner_geography || [];
  const trend = data.volume_trend || [];
  const ts = TYPE_STYLES[data.company_type] || { background: '#f1f5f9', color: '#374151', border: '#e2e8f0' };
  const maxGeo = Math.max(...geo.map(g => g.volume), 1);

  const dateLabel = [data.first_trade && fmtDate(data.first_trade), data.last_trade && fmtDate(data.last_trade)].filter(Boolean).join(' – ');

  const isBuyerOnly = data.company_type === 'Pakistani Importer' || data.company_type === 'Foreign Buyer';

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
            {data.company_type && (
              <span style={{ background: ts.background, color: ts.color, border: `1px solid ${ts.border}`, padding: '4px 12px', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 500 }}>
                {data.company_type}
              </span>
            )}
          </div>
          {(data.total_transactions || dateLabel) && (
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.9rem', color: '#6b7280', fontWeight: 400 }}>
              Based on {data.total_transactions || 0} verified transactions{dateLabel ? ` · ${dateLabel}` : ''}
            </p>
          )}
        </div>

        <div style={{ display: 'inline-flex', background: '#f1f5f9', padding: '4px', borderRadius: '10px', marginBottom: '2rem', gap: '4px', border: '1px solid #e2e8f0' }}>
          {['overview', 'products', 'partners'].map(t => (
            <button key={t}
              onClick={() => navigate(`/trade-intelligence/company/${id}/${t}`)}
              style={{
                background: tab === t ? 'white' : 'transparent',
                border: 'none',
                padding: '0.6rem 1.25rem',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: tab === t ? 600 : 500,
                color: tab === t ? '#111827' : '#64748b',
                borderRadius: '8px',
                boxShadow: tab === t ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                transition: 'all 0.2s ease-in-out',
                WebkitUserSelect: 'none'
              }}
            >
              {t === 'products' ? `Products (${data.total_products || 0})` :
                t === 'partners' ? `Partners (${data.total_partners || 0})` :
                  t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {/* ── SECTION 1: Metrics Row ────────────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>

          <div style={{ background: 'white', borderRadius: '8px', padding: '1.25rem 1.5rem', border: '1px solid #e5e7eb', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
            <p style={{ margin: '0 0 0.5rem', fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>Total Volume</p>
            <div style={{ fontSize: '2rem', fontWeight: 600, color: '#111827', fontFeatureSettings: '"tnum"', letterSpacing: '-0.01em', lineHeight: 1.1 }}>{fmtN(km.total_volume)} <span style={{ fontSize: '1rem', color: '#6b7280', fontWeight: 400 }}>MT</span></div>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', color: '#9ca3af' }}>{data.total_transactions || 0} transactions</p>
          </div>

          <div style={{ background: 'white', borderRadius: '8px', padding: '1.25rem 1.5rem', border: '1px solid #e5e7eb', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
            <p style={{ margin: '0 0 0.5rem', fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>{isBuyerOnly ? 'Estimated Purchases' : 'Estimated Revenue'}</p>
            <div style={{ fontSize: '2rem', fontWeight: 600, color: '#111827', fontFeatureSettings: '"tnum"', letterSpacing: '-0.01em', lineHeight: 1.1 }}>{fmtM(km.estimated_revenue)}</div>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', color: '#9ca3af' }}>USD</p>
          </div>

          <div style={{ background: 'white', borderRadius: '8px', padding: '1.25rem 1.5rem', border: '1px solid #e5e7eb', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
            <p style={{ margin: '0 0 0.8rem', fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>Top 5 Products by Volume</p>
            {km.top_products?.length > 0 ? (
              <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
                {km.top_products.map((p, i) => (
                  <li key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '6px 0', borderBottom: i < km.top_products.length - 1 ? '1px solid #f3f4f6' : 'none' }}>
                    <span style={{ color: '#374151', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, fontWeight: 500 }}>{p.product}</span>
                    <span style={{ color: '#6b7280', fontWeight: 500, marginLeft: 10, flexShrink: 0, fontFeatureSettings: '"tnum"' }}>{p.percent}%</span>
                  </li>
                ))}
              </ul>
            ) : <p style={{ color: '#9ca3af', fontSize: '0.85rem', margin: 0 }}>No data</p>}
          </div>

          <div style={{ background: 'white', borderRadius: '8px', padding: '1.25rem 1.5rem', border: '1px solid #e5e7eb', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
            <p style={{ margin: '0 0 0.8rem', fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>Top 5 Partners by Volume</p>
            {km.top_partners?.length > 0 ? (
              <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
                {km.top_partners.map((p, i) => (
                  <li key={i}
                    style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '6px 0', borderBottom: i < km.top_partners.length - 1 ? '1px solid #f3f4f6' : 'none', cursor: 'pointer' }}
                    onClick={() => navigate(`/trade-intelligence/company/${encodeURIComponent(p.partner)}/overview`)}>
                    <span style={{ color: '#374151', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, fontWeight: 500, transition: 'color 0.2s' }}
                      onMouseEnter={e => e.currentTarget.style.color = '#111827'} onMouseLeave={e => e.currentTarget.style.color = '#374151'}>
                      {p.partner}
                    </span>
                    <span style={{ color: '#6b7280', fontWeight: 500, marginLeft: 10, flexShrink: 0, fontFeatureSettings: '"tnum"' }}>{p.percent}%</span>
                  </li>
                ))}
              </ul>
            ) : <p style={{ color: '#9ca3af', fontSize: '0.85rem', margin: 0 }}>No data</p>}
          </div>
        </div>

        {/* ── SECTION 2 & 3: Geography and Trend ──────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem', alignItems: 'start' }}>

          {/* Partner Geography */}
          <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', height: '100%', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
            <h3 style={{ margin: '0 0 1.25rem', fontSize: '1.15rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Partner Geography</h3>
            {geo.length === 0 ? <p style={{ color: '#9ca3af', fontSize: '0.9rem' }}>No geographic data</p> : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <GeoMap geoData={geo} />
                <div>
                  {geo.slice(0, 5).map((g, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                      <span style={{ width: 130, fontSize: '0.85rem', color: '#374151', flexShrink: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 500 }} title={g.country}>
                        {g.country}
                      </span>
                      <div style={{ flex: 1, height: 6, borderRadius: 3, background: '#f3f4f6', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${Math.min((g.volume / maxGeo) * 100, 100)}%`, background: '#6b7280', borderRadius: 3, transition: 'width 0.5s ease' }} />
                      </div>
                      <span style={{ width: 60, textAlign: 'right', fontSize: '0.85rem', color: '#6b7280', fontWeight: 500, flexShrink: 0, fontFeatureSettings: '"tnum"' }}>
                        {fmtN(g.volume)} MT
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Volume Trend */}
          <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', height: '100%', display: 'flex', flexDirection: 'column', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
            <h3 style={{ margin: '0 0 1.25rem', fontSize: '1.15rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Volume Trend</h3>
            <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
              <LineChart data={trend} />
            </div>
          </div>
        </div>

        {/* ── SECTION 5: Filters (bottom) ─────────────────── */}
        <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
          <h3 style={{ margin: '0 0 1.25rem', fontSize: '1.15rem', fontWeight: 600, color: '#111827', letterSpacing: '-0.01em' }}>Filter Analysis</h3>
          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>

            <div className="filter-group" style={{ flex: '1 1 200px' }}>
              <label style={{ fontSize: '0.8rem', fontWeight: 500, color: '#6b7280', marginBottom: 6 }}>Product Name</label>
              <input type="text" placeholder="e.g. Sugar, Cotton" value={pending.productName}
                onChange={e => setPending(p => ({ ...p, productName: e.target.value }))}
                style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.9rem', color: '#111827', background: '#fafafa' }} />
            </div>

            <div className="filter-group" style={{ flex: '1 1 200px' }}>
              <label style={{ fontSize: '0.8rem', fontWeight: 500, color: '#6b7280', marginBottom: 6 }}>Date Range</label>
              <div style={{ display: 'flex', gap: 8 }}>
                <input type="date" value={pending.dateFrom}
                  onChange={e => setPending(p => ({ ...p, dateFrom: e.target.value }))} style={{ flex: 1, padding: '0.6rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.9rem', color: '#111827', background: '#fafafa' }} />
                <input type="date" value={pending.dateTo}
                  onChange={e => setPending(p => ({ ...p, dateTo: e.target.value }))} style={{ flex: 1, padding: '0.6rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.9rem', color: '#111827', background: '#fafafa' }} />
              </div>
            </div>

            <div className="filter-group" style={{ flex: '0 1 150px' }}>
              <label style={{ fontSize: '0.8rem', fontWeight: 500, color: '#6b7280', marginBottom: 6 }}>Trade Type</label>
              <select value={pending.tradeType}
                onChange={e => setPending(p => ({ ...p, tradeType: e.target.value }))}
                style={{ width: '100%', padding: '0.6rem 0.8rem', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '0.9rem', color: '#111827', background: '#fafafa' }}>
                <option value="">All Types</option>
                <option value="import">Import</option>
                <option value="export">Export</option>
              </select>
            </div>

            <div style={{ display: 'flex', gap: 10, alignSelf: 'flex-end' }}>
              <button onClick={() => setApplied({ ...pending })}
                style={{ padding: '0.6rem 1.4rem', borderRadius: '6px', border: '1px solid #111827', background: '#111827', color: 'white', fontWeight: 500, cursor: 'pointer', fontSize: '0.9rem', transition: 'background-color 0.2s' }}
                onMouseEnter={e => e.currentTarget.style.backgroundColor = '#1f2937'}
                onMouseLeave={e => e.currentTarget.style.backgroundColor = '#111827'}>
                Apply
              </button>
              {(applied.dateFrom || applied.dateTo || applied.tradeType || applied.productName) && (
                <button onClick={() => { setPending({ dateFrom: '', dateTo: '', tradeType: '', productName: '' }); setApplied({ dateFrom: '', dateTo: '', tradeType: '', productName: '' }); }}
                  style={{ padding: '0.6rem 1.2rem', borderRadius: '6px', border: '1px solid #d1d5db', background: 'white', color: '#374151', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 500, transition: 'background-color 0.2s' }}
                  onMouseEnter={e => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                  onMouseLeave={e => e.currentTarget.style.backgroundColor = 'white'}>
                  Clear
                </button>
              )}
            </div>

          </div>
        </div>

      </div>
    </>
  );
};

export default CompanyOverview;
