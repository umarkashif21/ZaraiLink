import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import { SkeletonCard } from '../Common/Skeleton';
import EmptyState from '../Common/EmptyState';
import Pagination from '../Common/Pagination';
import SortSelector from '../Common/SortSelector';
import ExportButton from '../Common/ExportButton';
import Breadcrumb from '../Common/Breadcrumb';
import WatchlistButton from '../Common/WatchlistButton';
import useWatchlist from '../../hooks/useWatchlist';
import useDebounce from '../../hooks/useDebounce';
import './TradeIntelligence.css';

const TradeLedger = () => {
  const navigate = useNavigate();
  const [comps, setComps] = useState([]);
  const [cats, setCats] = useState([]);
  const [load, setLoad] = useState(true);
  const [stats, setStats] = useState(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;
  
  // Sorting state
  const [sortBy, setSortBy] = useState('name_asc');
  
  // Watchlist hook
  const { isInWatchlist, toggleWatchlist } = useWatchlist();
  
  const [filts, setFilts] = useState({
    country: '',
    product: '',
    type: '',
    dateFrom: '',
    dateTo: ''
  });
  
  // Debounce country filter
  const debouncedCountry = useDebounce(filts.country, 300);

  useEffect(() => {
    loadCats();
    loadComps();
  }, []);

  useEffect(() => {
    loadComps();
  }, [filts]);

  const loadCats = async () => {
    try {
      // Use product-clusters endpoint which exists in trade_ledger
      const res = await fetch('http://localhost:8000/api/product-clusters/', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        // Convert clusters to category-like format
        const categories = data.clusters ? data.clusters.map((name, idx) => ({ id: idx + 1, name })) : [];
        setCats(categories);
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const loadComps = async () => {
    setLoad(true);
    try {
      const p = new URLSearchParams();
      p.append('direction', 'import'); // Default to import
      if (filts.country) p.append('country', filts.country);
      if (filts.dateFrom) p.append('date_from', filts.dateFrom);
      if (filts.dateTo) p.append('date_to', filts.dateTo);
      p.append('limit', '50');

      // Use the explorer API which exists
      const res = await fetch(`http://localhost:8000/api/explorer/?${p}`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        // Transform explorer data to match expected format
        const transformedComps = (data.results || []).map((item, idx) => ({
          id: idx + 1,
          company: {
            name: item.company,
            province: '',
            country: ''
          },
          estimated_revenue: item.avg_price * item.total_volume,
          trade_volume: item.total_volume,
          is_exporter: false,
          is_importer: true,
          active_since: null,
          top_products: [],
          segment_tag: item.segment_tag || 'Other'
        }));
        setComps(transformedComps);
      }

      // Stats calculation from the loaded companies
      if (filts.product) {
        // For now, just set basic stats
        setStats({
          avg_price: 0,
          avg_yoy_growth: 0,
          total_volume: 0,
          total_companies: 0
        });
      } else {
        setStats(null);
      }
    } catch (err) {
      console.error('Failed to load companies:', err);
    } finally {
      setLoad(false);
    }
  };

  const onFiltChange = (f, v) => {
    setFilts(prev => ({ ...prev, [f]: v }));
  };

  const onCompClick = (companyName) => {
    // Use the company name for navigation, URL encoded for safety
    const encodedName = encodeURIComponent(companyName);
    navigate(`/trade-intelligence/company/${encodedName}/overview`);
  };

  const fmtCurr = (v) => {
    if (!v) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(v);
  };

  const fmtPct = (v) => {
    if (v === null || v === undefined) return 'N/A';
    return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
  };

  // Sorted data
  const sortedComps = useMemo(() => {
    const sorted = [...comps];
    const [field, direction] = sortBy.split('_');
    sorted.sort((a, b) => {
      let valA, valB;
      if (field === 'name') {
        valA = a.company.name.toLowerCase();
        valB = b.company.name.toLowerCase();
      } else if (field === 'revenue') {
        valA = a.estimated_revenue || 0;
        valB = b.estimated_revenue || 0;
      } else if (field === 'volume') {
        valA = a.trade_volume || 0;
        valB = b.trade_volume || 0;
      } else {
        valA = a.company.name.toLowerCase();
        valB = b.company.name.toLowerCase();
      }
      if (direction === 'asc') return valA > valB ? 1 : -1;
      return valA < valB ? 1 : -1;
    });
    return sorted;
  }, [comps, sortBy]);

  // Paginated data
  const totalPages = Math.ceil(sortedComps.length / itemsPerPage);
  const paginatedComps = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return sortedComps.slice(start, start + itemsPerPage);
  }, [sortedComps, currentPage, itemsPerPage]);

  // Export columns
  const exportColumns = [
    { key: 'company.name', label: 'Company Name' },
    { key: 'estimated_revenue', label: 'Est. Revenue' },
    { key: 'trade_volume', label: 'Trade Volume' },
    { key: 'segment_tag', label: 'Segment' },
  ];

  // Format data for export
  const exportData = comps.map(c => ({
    'company.name': c.company.name,
    estimated_revenue: fmtCurr(c.estimated_revenue),
    trade_volume: fmtCurr(c.trade_volume),
    segment_tag: c.segment_tag,
  }));
  return (
    <>
      <Navbar />
      <div className="trade-ledger-container">
        <Breadcrumb />
        
        <div className="trade-ledger-header">
          <div>
            <h1>📊 Trade Ledger</h1>
            <p>Comprehensive trade intelligence and company analytics</p>
          </div>
          <div className="header-actions" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <SortSelector value={sortBy} onChange={setSortBy} />
            <ExportButton 
              data={exportData} 
              columns={exportColumns} 
              filename="trade-ledger-companies"
              title="Trade Ledger Export"
            />
          </div>
        </div>

        <div className="filters-section">
          <div className="filters-grid">
            <div className="filter-group">
              <label>Country</label>
              <input
                type="text"
                placeholder="Search by country..."
                value={filts.country}
                onChange={(e) => onFiltChange('country', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>Product Category</label>
              <select
                value={filts.product}
                onChange={(e) => onFiltChange('product', e.target.value)}
              >
                <option value="">All Products</option>
                {cats.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Company Type</label>
              <select
                value={filts.type}
                onChange={(e) => onFiltChange('type', e.target.value)}
              >
                <option value="">All Types</option>
                <option value="exporter">Exporter</option>
                <option value="importer">Importer</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Date From</label>
              <input
                type="date"
                value={filts.dateFrom}
                onChange={(e) => onFiltChange('dateFrom', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>Date To</label>
              <input
                type="date"
                value={filts.dateTo}
                onChange={(e) => onFiltChange('dateTo', e.target.value)}
              />
            </div>
          </div>
        </div>

        {stats && filts.product && (
          <div className="metrics-row">
            <div className="metric-card">
              <h3>Average Price</h3>
              <div className="metric-value">{fmtCurr(stats.avg_price)}</div>
              <p className="metric-subtext">Across all companies</p>
            </div>
            <div className="metric-card">
              <h3>YoY Growth</h3>
              <div className="metric-value" style={{
                color: stats.avg_yoy_growth >= 0 ? '#22c55e' : '#ef4444'
              }}>
                {fmtPct(stats.avg_yoy_growth)}
              </div>
              <p className="metric-subtext">Year-over-year</p>
            </div>
            <div className="metric-card">
              <h3>Total Volume</h3>
              <div className="metric-value">
                {stats.total_volume 
                  ? new Intl.NumberFormat('en-US').format(stats.total_volume) 
                  : 'N/A'}
              </div>
              <p className="metric-subtext">Combined volume</p>
            </div>
            <div className="metric-card">
              <h3>Total Companies</h3>
              <div className="metric-value">{stats.total_companies || comps.length}</div>
              <p className="metric-subtext">In this category</p>
            </div>
          </div>
        )}

        {load ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading companies...</p>
          </div>
        ) : comps.length === 0 ? (
          <EmptyState
            title="No companies found"
            description="Try adjusting your filters or search criteria"
            actionLabel="Clear Filters"
            onAction={() => setFilts({ country: '', product: '', type: '', dateFrom: '', dateTo: '' })}
          />
        ) : (
          <>
            <div className="trade-ledger-table-container">
              <table className="trade-ledger-table">
                <thead>
                  <tr>
                    <th>Company Name</th>
                    <th>Country</th>
                    <th>Trade Volume</th>
                    <th>Company Type</th>
                    <th>Products</th>
                    <th>Active Since</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedComps.map(c => (
                    <tr 
                      key={c.id}
                      onClick={() => onCompClick(c.company.name)}
                      className="table-row-clickable"
                    >
                      <td>
                        <div className="company-name-cell">
                          <strong>{c.company.name}</strong>
                          {c.company.province && (
                            <span className="company-location-sub">
                              📍 {c.company.province}
                            </span>
                          )}
                        </div>
                      </td>
                      <td>{c.company.country || 'N/A'}</td>
                      <td><strong>{fmtCurr(c.trade_volume)}</strong></td>
                      <td>
                        {c.is_exporter && c.is_importer ? (
                          <span className="company-badge badge-both">Both</span>
                        ) : c.is_exporter ? (
                          <span className="company-badge badge-exporter">Exporter</span>
                        ) : (
                          <span className="company-badge badge-importer">Importer</span>
                        )}
                      </td>
                      <td>{c.top_products?.length || 0}</td>
                      <td>
                        {c.active_since 
                          ? new Date(c.active_since).getFullYear()
                          : 'N/A'}
                      </td>
                      <td onClick={(e) => e.stopPropagation()}>
                        <WatchlistButton
                          isWatched={isInWatchlist(c.company.name)}
                          onToggle={() => {
                            toggleWatchlist({ id: c.company.name, name: c.company.name });
                          }}
                          size="small"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Pagination */}
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
              totalItems={comps.length}
              itemsPerPage={itemsPerPage}
            />
          </>
        )}
      </div>
    </>
  );
};

export default TradeLedger;
