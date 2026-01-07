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
import { isNA, formatCurrency, formatPercent } from '../../utils/formatUtils';
import './TradeIntelligence.css';

const TradeLedger = () => {
  const navigate = useNavigate();
  const [comps, setComps] = useState([]);
  const [cats, setCats] = useState([]);
  const [load, setLoad] = useState(true);
  const [stats, setStats] = useState(null);
  
  
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;
  
  
  const [sortBy, setSortBy] = useState('name_asc');
  
  
  const { isInWatchlist, toggleWatchlist } = useWatchlist();
  
  
  const [hideNA, setHideNA] = useState(false);
  
  const [filts, setFilts] = useState({
    country: '',
    product: '',
    type: '',
    dateFrom: '',
    dateTo: ''
  });
  
  
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
      
      const res = await fetch('http://localhost:8000/api/product-clusters/', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        
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
      p.append('direction', 'both'); 
      if (filts.country) p.append('country', filts.country);
      if (filts.dateFrom) p.append('date_from', filts.dateFrom);
      if (filts.dateTo) p.append('date_to', filts.dateTo);
      p.append('limit', '1000'); 

      
      const res = await fetch(`http://localhost:8000/api/explorer/?${p}`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        
        const transformedComps = (data.results || []).map((item, idx) => {
          const volume = parseFloat(item.total_volume) || 0;
          const avgPrice = parseFloat(item.avg_price) || 0;
          const totalValue = parseFloat(item.total_value) || (avgPrice * volume);
          const yoyGrowth = item.yoy_growth !== null && item.yoy_growth !== undefined 
            ? parseFloat(item.yoy_growth) 
            : null;
          
          return {
            id: idx + 1,
            company: {
              name: item.company,
              province: '',
              country: item.country || ''
            },
            estimated_revenue: totalValue,
            trade_volume: volume,
            is_exporter: false,
            is_importer: true,
            active_since: item.first_trade,
            top_products: item.top_products || [],
            segment_tag: item.segment_tag || 'Other',
            yoy_growth: !isNaN(yoyGrowth) ? yoyGrowth : null,
            transaction_count: parseInt(item.transaction_count) || 0,
            avg_price: avgPrice,
          };
        });
        setComps(transformedComps);
        
        
        const totalVolume = transformedComps.reduce((sum, c) => sum + c.trade_volume, 0);
        const totalRevenue = transformedComps.reduce((sum, c) => sum + c.estimated_revenue, 0);
        const avgPrice = transformedComps.length > 0 
          ? transformedComps.reduce((sum, c) => sum + c.avg_price, 0) / transformedComps.length 
          : 0;
        const validGrowth = transformedComps.filter(c => c.yoy_growth !== null && !isNaN(c.yoy_growth));
        const avgYoyGrowth = validGrowth.length > 0
          ? validGrowth.reduce((sum, c) => sum + c.yoy_growth, 0) / validGrowth.length
          : null;
        
        setStats({
          avg_price: avgPrice,
          avg_yoy_growth: avgYoyGrowth,
          total_volume: totalVolume,
          total_companies: transformedComps.length,
          total_value: totalRevenue,
        });
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
    
    const encodedName = encodeURIComponent(companyName);
    navigate(`/trade-intelligence/company/${encodedName}/overview`);
  };

  const fmtCurr = (v) => {
    if (!v) return '';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(v);
  };

  const fmtPct = (v) => {
    if (v === null || v === undefined) return '';
    const num = typeof v === 'number' ? v : parseFloat(v);
    if (isNaN(num)) return '';
    return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`;
  };

  
  const sortedComps = useMemo(() => {
    let sorted = [...comps];
    
    
    if (hideNA) {
      sorted = sorted.filter(c => {
        
        return c.trade_volume > 0 && 
               c.company.country !== 'N/A' && 
               c.company.country !== '';
      });
    }
    
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
  }, [comps, sortBy, hideNA]);

  
  const totalPages = Math.ceil(sortedComps.length / itemsPerPage);
  const paginatedComps = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return sortedComps.slice(start, start + itemsPerPage);
  }, [sortedComps, currentPage, itemsPerPage]);

  
  const exportColumns = [
    { key: 'company.name', label: 'Company Name' },
    { key: 'company.country', label: 'Country' },
    { key: 'trade_volume', label: 'Trade Volume (MT)' },
    { key: 'estimated_revenue', label: 'Total Value (USD)' },
    { key: 'yoy_growth', label: 'YoY Growth %' },
    { key: 'top_products_str', label: 'Top Products' },
    { key: 'segment_tag', label: 'Segment' },
  ];

  
  const exportData = comps.map(c => ({
    'company.name': c.company.name,
    'company.country': c.company.country || '',
    trade_volume: typeof c.trade_volume === 'number' ? c.trade_volume.toFixed(2) : '',
    estimated_revenue: fmtCurr(c.estimated_revenue),
    yoy_growth: c.yoy_growth !== null && c.yoy_growth !== undefined && !isNaN(c.yoy_growth) ? fmtPct(c.yoy_growth) : '',
    top_products_str: c.top_products?.join(', ') || '',
    segment_tag: c.segment_tag || '',
  }));
  return (
    <>
      <Navbar />
      <div className="trade-ledger-container">
        <Breadcrumb />
        
        <div className="trade-ledger-header">
          <div>
            <h1>Trade Ledger</h1>
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
            
            <div className="filter-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1.5rem' }}>
              <input
                type="checkbox"
                id="hideNA"
                checked={hideNA}
                onChange={(e) => setHideNA(e.target.checked)}
                style={{ width: '18px', height: '18px', cursor: 'pointer' }}
              />
              <label htmlFor="hideNA" style={{ cursor: 'pointer', fontWeight: 'normal' }}>
                Hide entries with missing data
              </label>
            </div>
          </div>
        </div>

        {stats && (
          <div className="metrics-row">
            <div className="metric-card">
              <h3>Total Companies</h3>
              <div className="metric-value">{stats.total_companies || comps.length}</div>
              <p className="metric-subtext">In current view</p>
            </div>
            {stats.total_volume > 0 && (
              <div className="metric-card">
                <h3>Total Volume</h3>
                <div className="metric-value">
                  {new Intl.NumberFormat('en-US', {maximumFractionDigits: 0}).format(stats.total_volume)} MT
                </div>
                <p className="metric-subtext">Combined volume</p>
              </div>
            )}
            {stats.total_value > 0 && (
              <div className="metric-card">
                <h3>Total Value</h3>
                <div className="metric-value">{fmtCurr(stats.total_value)}</div>
                <p className="metric-subtext">Trade value (USD)</p>
              </div>
            )}
            {stats.avg_yoy_growth !== null && stats.avg_yoy_growth !== undefined && !isNaN(stats.avg_yoy_growth) && (
              <div className="metric-card">
                <h3>Avg YoY Growth</h3>
                <div className="metric-value" style={{
                  color: stats.avg_yoy_growth >= 0 ? '#22c55e' : '#ef4444'
                }}>
                  {fmtPct(stats.avg_yoy_growth)}
                </div>
                <p className="metric-subtext">Year-over-year</p>
              </div>
            )}
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
                    <th>YoY Growth</th>
                    <th>Top Products</th>
                    <th>Segment</th>
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
                              {c.company.province}
                            </span>
                          )}
                        </div>
                      </td>
                      <td>{c.company.country && c.company.country !== 'N/A' ? c.company.country : ''}</td>
                      <td><strong>{c.trade_volume > 0 ? fmtCurr(c.trade_volume) : ''}</strong></td>
                      <td>
                        {c.yoy_growth !== null && c.yoy_growth !== undefined && !isNaN(c.yoy_growth) ? (
                          <span className={`growth-badge ${c.yoy_growth >= 0 ? 'positive' : 'negative'}`}>
                            {fmtPct(c.yoy_growth)}
                          </span>
                        ) : null}
                      </td>
                      <td>
                        {c.top_products && c.top_products.length > 0 ? (
                          <div className="products-cell">
                            {c.top_products.slice(0, 2).map((prod, idx) => (
                              <span key={idx} className="product-pill">{prod}</span>
                            ))}
                            {c.top_products.length > 2 && (
                              <span className="more-products">+{c.top_products.length - 2}</span>
                            )}
                          </div>
                        ) : null}
                      </td>
                      <td>
                        {c.segment_tag && c.segment_tag !== 'Other' ? (
                          <span className="segment-badge">{c.segment_tag}</span>
                        ) : null}
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
            
            {}
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
