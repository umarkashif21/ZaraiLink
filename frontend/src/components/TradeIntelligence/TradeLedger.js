import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import EmptyState from '../Common/EmptyState';
import Pagination from '../Common/Pagination';
import ExportButton from '../Common/ExportButton';
import Breadcrumb from '../Common/Breadcrumb';
import WatchlistButton from '../Common/WatchlistButton';
import useWatchlist from '../../hooks/useWatchlist';
import useDebounce from '../../hooks/useDebounce';
import './TradeIntelligence.css';

// Company type badge colours
const TYPE_COLORS = {
  'Pakistani Buyer': { bg: '#dbeafe', color: '#1d4ed8', label: 'PK Buyer' },
  'Pakistani Seller': { bg: '#dcfce7', color: '#15803d', label: 'PK Seller' },
  'Pakistani Trader': { bg: '#fef9c3', color: '#854d0e', label: 'PK Trader' },
  'Foreign Buyer': { bg: '#fce7f3', color: '#9d174d', label: 'FOR Buyer' },
  'Foreign Seller': { bg: '#ede9fe', color: '#6d28d9', label: 'FOR Seller' },
};

const COMPANY_TYPES = [
  'Pakistani Buyer',
  'Pakistani Seller',
  'Pakistani Trader',
  'Foreign Buyer',
  'Foreign Seller',
];

const TradeLedger = () => {
  const navigate = useNavigate();
  const [comps, setComps] = useState([]);
  const [load, setLoad] = useState(true);
  const [stats, setStats] = useState(null);   // computed from ALL loaded companies

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;

  const { isInWatchlist, toggleWatchlist } = useWatchlist();

  // ── Filters (all client-side) ────────────────────────────
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const debouncedSearch = useDebounce(search, 250);

  // ── Sort ─────────────────────────────────────────────────
  const SORT_OPTIONS = [
    { value: 'volume_desc', label: 'Volume (High→Low)' },
    { value: 'volume_asc', label: 'Volume (Low→High)' },
    { value: 'value_desc', label: 'Value (High→Low)' },
    { value: 'value_asc', label: 'Value (Low→High)' },
    { value: 'name_asc', label: 'Name (A→Z)' },
    { value: 'name_desc', label: 'Name (Z→A)' },
    { value: 'date_asc', label: 'First Trade (Old)' },
    { value: 'date_desc', label: 'First Trade (New)' },
  ];
  const [sortBy, setSortBy] = useState('volume_desc');

  // ── Load data once on mount ───────────────────────────────
  useEffect(() => { loadComps(); }, []);

  const loadComps = async () => {
    setLoad(true);
    try {
      const res = await fetch(
        'http://localhost:8000/api/explorer/?direction=both&limit=2000',
        { credentials: 'include' }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const rows = (data.results || []).map((item, idx) => ({
        id: idx + 1,
        company: item.company || '',
        country: item.country || '',
        company_type: item.company_type || 'Unknown',
        trade_volume: parseFloat(item.total_volume) || 0,
        import_volume: parseFloat(item.import_volume) || 0,
        export_volume: parseFloat(item.export_volume) || 0,
        total_value: parseFloat(item.total_value) || 0,
        import_value: parseFloat(item.import_value) || 0,
        export_value: parseFloat(item.export_value) || 0,
        transaction_count: parseInt(item.transaction_count) || 0,
        first_trade: item.first_trade || null,
        last_trade: item.last_trade || null,
        segment_tag: item.segment_tag || '',
      }));

      setComps(rows);

      // Global metrics (ALL companies, ignoring filters)
      const impVol = rows.reduce((s, c) => s + c.import_volume, 0);
      const expVol = rows.reduce((s, c) => s + c.export_volume, 0);
      const impVal = rows.reduce((s, c) => s + c.import_value, 0);
      const expVal = rows.reduce((s, c) => s + c.export_value, 0);
      setStats({
        total_companies: rows.length,
        import_volume: impVol,
        export_volume: expVol,
        import_value: impVal,
        export_value: expVal,
      });
    } catch (err) {
      console.error('TradeLedger: failed to load companies:', err);
    } finally {
      setLoad(false);
    }
  };

  // ── Format helpers ────────────────────────────────────────
  const fmtNum = (v, decimals = 0) =>
    new Intl.NumberFormat('en-US', { maximumFractionDigits: decimals }).format(v);

  const fmtCurr = (v) => {
    if (!v) return '—';
    if (v >= 1_000_000) return `$${fmtNum(v / 1_000_000, 1)}M`;
    if (v >= 1_000) return `$${fmtNum(v / 1_000, 0)}K`;
    return `$${fmtNum(v)}`;
  };

  const fmtDate = (d) => {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short' }); }
    catch { return d; }
  };

  // ── Client-side filtering + sorting ──────────────────────
  const sortedComps = useMemo(() => {
    let rows = [...comps];

    // Search: company name OR country
    if (debouncedSearch) {
      const q = debouncedSearch.toLowerCase();
      rows = rows.filter(c =>
        c.company.toLowerCase().includes(q) ||
        c.country.toLowerCase().includes(q)
      );
    }

    // Company type filter
    if (typeFilter) {
      rows = rows.filter(c => c.company_type === typeFilter);
    }

    // Sort
    rows.sort((a, b) => {
      switch (sortBy) {
        case 'volume_desc': return b.trade_volume - a.trade_volume;
        case 'volume_asc': return a.trade_volume - b.trade_volume;
        case 'value_desc': return b.total_value - a.total_value;
        case 'value_asc': return a.total_value - b.total_value;
        case 'name_asc': return a.company.localeCompare(b.company);
        case 'name_desc': return b.company.localeCompare(a.company);
        case 'date_asc': return (a.first_trade || '') < (b.first_trade || '') ? -1 : 1;
        case 'date_desc': return (a.first_trade || '') > (b.first_trade || '') ? -1 : 1;
        default: return b.trade_volume - a.trade_volume;
      }
    });

    return rows;
  }, [comps, debouncedSearch, typeFilter, sortBy]);

  // ── Derived metrics (update live with filters) ────────────
  const filteredStats = useMemo(() => ({
    total: sortedComps.length,
    impVol: sortedComps.reduce((s, c) => s + c.import_volume, 0),
    expVol: sortedComps.reduce((s, c) => s + c.export_volume, 0),
    impVal: sortedComps.reduce((s, c) => s + c.import_value, 0),
    expVal: sortedComps.reduce((s, c) => s + c.export_value, 0),
  }), [sortedComps]);

  // ── Pagination ────────────────────────────────────────────
  const totalPages = Math.ceil(sortedComps.length / itemsPerPage);
  const paginatedComps = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return sortedComps.slice(start, start + itemsPerPage);
  }, [sortedComps, currentPage]);

  // ── Export ────────────────────────────────────────────────
  const exportColumns = [
    { key: 'company', label: 'Company Name' },
    { key: 'country', label: 'Country' },
    { key: 'company_type', label: 'Company Type' },
    { key: 'trade_volume_fmt', label: 'Trade Volume (MT)' },
    { key: 'import_volume_fmt', label: 'Import Volume (MT)' },
    { key: 'export_volume_fmt', label: 'Export Volume (MT)' },
    { key: 'total_value_fmt', label: 'Est. Value (USD)' },
    { key: 'first_trade', label: 'First Trade' },
  ];

  const exportData = sortedComps.map(c => ({
    company: c.company,
    country: c.country,
    company_type: c.company_type,
    trade_volume_fmt: c.trade_volume.toFixed(2),
    import_volume_fmt: c.import_volume.toFixed(2),
    export_volume_fmt: c.export_volume.toFixed(2),
    total_value_fmt: c.total_value.toFixed(2),
    first_trade: c.first_trade || '',
  }));

  // ── Render ────────────────────────────────────────────────
  const TypeBadge = ({ type }) => {
    const { bg = '#f3f4f6', color = '#374151', label = type } = TYPE_COLORS[type] || {};
    return (
      <span style={{
        display: 'inline-block',
        padding: '2px 10px',
        borderRadius: '999px',
        fontSize: '0.72rem',
        fontWeight: 600,
        letterSpacing: '0.02em',
        background: bg,
        color,
        whiteSpace: 'nowrap',
      }}>
        {label}
      </span>
    );
  };

  return (
    <>
      <Navbar />
      <div className="trade-ledger-container">
        <Breadcrumb />

        {/* Header */}
        <div className="trade-ledger-header">
          <div>
            <h1>Trade Ledger</h1>
            <p>Comprehensive trade intelligence and company analytics</p>
          </div>
        </div>

        {/* Filters */}
        <div className="filters-section">
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div className="filter-group" style={{ flex: '1 1 280px' }}>
              <label>Search</label>
              <input
                type="text"
                placeholder="Company name or country..."
                value={search}
                onChange={e => { setSearch(e.target.value); setCurrentPage(1); }}
              />
            </div>

            <div className="filter-group" style={{ flex: '0 1 210px' }}>
              <label>Company Type</label>
              <select
                value={typeFilter}
                onChange={e => { setTypeFilter(e.target.value); setCurrentPage(1); }}
              >
                <option value="">All Types</option>
                {COMPANY_TYPES.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>

            {(search || typeFilter) && (
              <div className="filter-group" style={{ flex: '0 0 auto', paddingTop: '1.5rem' }}>
                <button
                  onClick={() => { setSearch(''); setTypeFilter(''); setCurrentPage(1); }}
                  style={{
                    padding: '0.45rem 1rem',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.2)',
                    background: 'transparent',
                    color: 'inherit',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                  }}
                >
                  Clear
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Metrics row — updates live with filters */}
        {stats && (
          <div className="metrics-row">
            <div className="metric-card">
              <h3>Companies</h3>
              <div className="metric-value">{fmtNum(filteredStats.total)}</div>
              <p className="metric-subtext">
                {(search || typeFilter) ? 'Matching filter' : 'Total loaded'}
              </p>
            </div>

            {filteredStats.impVol > 0 && (
              <div className="metric-card">
                <h3>Import Volume</h3>
                <div className="metric-value">{fmtNum(filteredStats.impVol)} MT</div>
                <p className="metric-subtext">Goods into Pakistan</p>
              </div>
            )}

            {filteredStats.expVol > 0 && (
              <div className="metric-card">
                <h3>Export Volume</h3>
                <div className="metric-value">{fmtNum(filteredStats.expVol)} MT</div>
                <p className="metric-subtext">Goods out of Pakistan</p>
              </div>
            )}

            {filteredStats.impVal > 0 && (
              <div className="metric-card">
                <h3>Import Value</h3>
                <div className="metric-value">{fmtCurr(filteredStats.impVal)}</div>
                <p className="metric-subtext">USD</p>
              </div>
            )}

            {filteredStats.expVal > 0 && (
              <div className="metric-card">
                <h3>Export Value</h3>
                <div className="metric-value">{fmtCurr(filteredStats.expVal)}</div>
                <p className="metric-subtext">USD</p>
              </div>
            )}
          </div>
        )}

        {/* Table */}
        {load ? (
          <div className="loading-container">
            <div className="spinner" />
            <p>Loading companies...</p>
          </div>
        ) : sortedComps.length === 0 ? (
          <EmptyState
            title="No companies found"
            description="Try adjusting your search or filter"
            actionLabel="Clear"
            onAction={() => { setSearch(''); setTypeFilter(''); }}
          />
        ) : (
          <>
            <div className="trade-ledger-table-container" style={{ fontFamily: "'Satoshi', 'Inter', -apple-system, sans-serif", border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden', background: '#fafafa', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
              <table className="trade-ledger-table" style={{ borderCollapse: 'collapse', width: '100%', background: '#ffffff', textAlign: 'left' }}>
                <thead style={{ background: '#fafafa', borderBottom: '1px solid #e5e7eb' }}>
                  <tr>
                    <th style={{ padding: '1.25rem 1.5rem', color: '#6b7280', fontWeight: 500, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Company</th>
                    <th style={{ padding: '1.25rem 1.5rem', color: '#6b7280', fontWeight: 500, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Type</th>
                    <th style={{ padding: '1.25rem 1.5rem', color: '#6b7280', fontWeight: 500, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em', textAlign: 'right' }}>Trade Volume</th>
                    <th style={{ padding: '1.25rem 1.5rem', color: '#6b7280', fontWeight: 500, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em', textAlign: 'right' }}>Est. Value</th>
                    <th style={{ padding: '1.25rem 1.5rem', width: 40 }}></th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedComps.map((c, i) => (
                    <tr
                      key={c.id}
                      onClick={() => navigate(`/trade-intelligence/company/${encodeURIComponent(c.company)}/overview`)}
                      style={{
                        borderBottom: i === paginatedComps.length - 1 ? 'none' : '1px solid #f3f4f6',
                        transition: 'background-color 0.15s ease, box-shadow 0.15s ease',
                        cursor: 'pointer'
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#f9fafb'; e.currentTarget.style.boxShadow = 'inset 2px 0 0 #3b82f6'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.boxShadow = 'none'; }}
                    >
                      {/* Company & Country */}
                      <td style={{ padding: '1.25rem 1.5rem' }}>
                        <div style={{ color: '#111827', fontWeight: 600, fontSize: '0.95rem', letterSpacing: '-0.01em', marginBottom: '0.2rem' }}>
                          {c.company}
                        </div>
                        <div style={{ color: '#6b7280', fontSize: '0.8rem', fontWeight: 400 }}>
                          {c.country && c.country !== 'Unknown' ? c.country : 'Unknown Location'}
                        </div>
                      </td>

                      {/* Clean Text Type */}
                      <td style={{ padding: '1.25rem 1.5rem' }}>
                        <div style={{ color: '#374151', fontSize: '0.85rem', fontWeight: 500 }}>
                          {c.company_type || 'Unknown'}
                        </div>
                      </td>

                      {/* Trade Volume */}
                      <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right' }}>
                        {c.trade_volume > 0 ? (
                          <div>
                            <div style={{ color: '#111827', fontWeight: 600, fontSize: '0.95rem', fontFeatureSettings: '"tnum"' }}>
                              {fmtNum(c.trade_volume, 0)} <span style={{ color: '#6b7280', fontWeight: 400, fontSize: '0.8rem' }}>MT</span>
                            </div>
                            {(c.import_volume > 0 || c.export_volume > 0) && (
                              <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', fontSize: '0.75rem', fontWeight: 500, color: '#9ca3af', marginTop: '0.2rem' }}>
                                {c.import_volume > 0 && <span>IMP {fmtNum(c.import_volume, 0)}</span>}
                                {c.export_volume > 0 && <span>EXP {fmtNum(c.export_volume, 0)}</span>}
                              </div>
                            )}
                          </div>
                        ) : <span style={{ color: '#d1d5db' }}>—</span>}
                      </td>

                      {/* Est Value */}
                      <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right' }}>
                        {c.total_value > 0 ? (
                          <div style={{ color: '#111827', fontWeight: 600, fontSize: '0.95rem', fontFeatureSettings: '"tnum"' }}>
                            {fmtCurr(c.total_value)}
                          </div>
                        ) : <span style={{ color: '#d1d5db' }}>—</span>}
                      </td>

                      {/* Watchlist */}
                      <td style={{ padding: '1.25rem 1.5rem' }} onClick={e => e.stopPropagation()}>
                        <WatchlistButton
                          isWatched={isInWatchlist(c.company)}
                          onToggle={() => toggleWatchlist({ id: c.company, name: c.company })}
                          size="small"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
              totalItems={sortedComps.length}
              itemsPerPage={itemsPerPage}
            />
          </>
        )}
      </div>
    </>
  );
};

export default TradeLedger;
