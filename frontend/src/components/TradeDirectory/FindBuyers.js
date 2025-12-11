
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import { SkeletonCard } from '../Common/Skeleton';
import EmptyState from '../Common/EmptyState';
import Pagination from '../Common/Pagination';
import SortSelector from '../Common/SortSelector';
import ExportButton from '../Common/ExportButton';
import Breadcrumb from '../Common/Breadcrumb';
import WatchlistButton from '../Common/WatchlistButton';
import VerificationBadge from '../Common/VerificationBadge';
import useWatchlist from '../../hooks/useWatchlist';
import './FindBuyers.css';

const FindBuyers = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    search: '',
    region: '',
    sector: ''
  });

  // Pagination and sorting state
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;
  const [sortBy, setSortBy] = useState('name_asc');
  
  // Watchlist hook
  const { isInWatchlist, toggleWatchlist } = useWatchlist();

  // Filter options state
  const [regions, setRegions] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [buyerRoleId, setBuyerRoleId] = useState(null);

  const searchCompanies = useCallback(async () => {
    if (!buyerRoleId) return;
    
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.region) params.append('region', filters.region);
      if (filters.sector) params.append('sector', filters.sector);
      params.append('role', buyerRoleId);

      const response = await fetch(`http://localhost:8000/api/companies/?${params.toString()}`, { credentials: 'include' });

      if (response.ok) {
        const data = await response.json();
        const companies = data.results || data;
        setCompanies(companies);
      } else {
        throw new Error('Failed to load buyers');
      }
    } catch (err) {
      setError('Failed to load buyers. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [buyerRoleId, filters]);

  useEffect(() => {
    loadFilterOptions();
  }, []);

  useEffect(() => {
    if (buyerRoleId) {
      searchCompanies();
    }
  }, [buyerRoleId, searchCompanies]);

  const loadFilterOptions = async () => {
    try {
      const [regionsRes, sectorsRes, rolesRes] = await Promise.all([
        fetch('http://localhost:8000/api/companies/regions/'),
        fetch('http://localhost:8000/api/sectors/'),
        fetch('http://localhost:8000/api/company-roles/')
      ]);

      if (regionsRes.ok) {
        const regionsData = await regionsRes.json();
        setRegions(regionsData.filter(r => r && r.trim() !== ''));
      }
      if (sectorsRes.ok) setSectors(await sectorsRes.json());
      
      if (rolesRes.ok) {
        const roles = await rolesRes.json();
        const buyerRole = roles.find(r => r.name.toLowerCase() === 'buyers') ||
                          roles.find(r => r.name.toLowerCase() === 'buyer');
        if (buyerRole) {
          setBuyerRoleId(buyerRole.id);
        } else {
          setError('System configuration error: Buyer role missing');
        }
      }
    } catch (err) {
      console.error('Failed to load filter options', err);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setCurrentPage(1);
    searchCompanies();
  };

  const handleReset = () => {
    setFilters({ search: '', region: '', sector: '' });
    setCurrentPage(1);
    setTimeout(() => { if (buyerRoleId) searchCompanies(); }, 100);
  };

  // Sorted companies
  const sortedCompanies = useMemo(() => {
    const sorted = [...companies];
    const [field, direction] = sortBy.split('_');
    sorted.sort((a, b) => {
      const valA = (a.name || '').toLowerCase();
      const valB = (b.name || '').toLowerCase();
      if (direction === 'asc') return valA > valB ? 1 : -1;
      return valA < valB ? 1 : -1;
    });
    return sorted;
  }, [companies, sortBy]);

  // Paginated companies
  const totalPages = Math.ceil(sortedCompanies.length / itemsPerPage);
  const paginatedCompanies = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return sortedCompanies.slice(start, start + itemsPerPage);
  }, [sortedCompanies, currentPage, itemsPerPage]);

  // Export columns
  const exportColumns = [
    { key: 'name', label: 'Company Name' },
    { key: 'province', label: 'Province' },
    { key: 'sector_name', label: 'Sector' },
    { key: 'verification_status', label: 'Status' },
  ];

  return (
    <>
      <Navbar />
      <div className="find-buyers-container">
        <Breadcrumb />
        
        <div className="header">
          <div>
            <h1>Find Buyers</h1>
            <p className="subtitle">Connect with verified agricultural buyers and distributors</p>
          </div>
          <div className="header-actions" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <SortSelector value={sortBy} onChange={setSortBy} />
            <ExportButton 
              data={companies} 
              columns={exportColumns} 
              filename="buyers-list"
              title="Buyers Export"
            />
          </div>
        </div>

        <div className="filters-section">
          <form onSubmit={handleSearch} className="search-bar">
            <input
              type="text"
              name="search"
              placeholder="Search buyers by name, product, or keywords..."
              value={filters.search}
              onChange={handleFilterChange}
            />
            <button type="submit" className="btn-search">Search</button>
          </form>

          <div className="filter-options">
            <select name="region" value={filters.region} 
              onChange={(e) => { handleFilterChange(e); setTimeout(() => { if (buyerRoleId) searchCompanies(); }, 100); }}>
              <option value="">All Regions</option>
              {regions.map(region => (<option key={region} value={region}>{region}</option>))}
            </select>

            <select name="sector" value={filters.sector} 
              onChange={(e) => { handleFilterChange(e); setTimeout(() => { if (buyerRoleId) searchCompanies(); }, 100); }}>
              <option value="">All Sectors</option>
              {sectors.map(s => (<option key={s.id} value={s.id}>{s.name}</option>))}
            </select>

            <button type="button" onClick={handleReset} className="btn-reset">Reset Filters</button>
          </div>
        </div>

        {error && (<div className="error-message">{error}</div>)}

        {/* Loading State with Skeletons */}
        {loading && (
          <div className="companies-grid">
            {[1,2,3,4,5,6,7,8].map(i => <SkeletonCard key={i} />)}
          </div>
        )}

        {/* Companies Grid */}
        {!loading && !error && (
          <>
            <div className="results-header" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <span>{companies.length} buyers found</span>
            </div>

            {companies.length === 0 ? (
              <EmptyState
                title="No buyers found"
                description="Try adjusting your search or filters to find what you're looking for."
                actionLabel="Clear Filters"
                onAction={handleReset}
              />
            ) : (
              <>
                <div className="companies-grid">
                  {paginatedCompanies.map(company => (
                    <div key={company.id} className="company-card">
                      <div className="card-header">
                        <h3>{(company.name || '').toUpperCase()}</h3>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <WatchlistButton
                            isWatched={isInWatchlist(company.id)}
                            onToggle={() => toggleWatchlist({ id: company.id, name: company.name })}
                            size="small"
                          />
                          <VerificationBadge status={company.verification_status} />
                        </div>
                      </div>
                      
                      <div className="card-body">
                        <div className="info-row">
                          <span className="label">Location:</span>
                          <span className="value">{company.district || 'N/A'}, {company.province}</span>
                        </div>
                        <div className="info-row">
                          <span className="label">Sector:</span>
                          <span className="value">{company.sector_name}</span>
                        </div>
                        <div className="info-row">
                          <span className="label">Type:</span>
                          <span className="value">{company.type_name || 'N/A'}</span>
                        </div>
                      </div>

                      <div className="card-footer">
                        <Link to={`/trade-directory/company/${company.id}`} className="btn-view-profile">
                          View Profile
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Pagination */}
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={setCurrentPage}
                  totalItems={companies.length}
                  itemsPerPage={itemsPerPage}
                />
              </>
            )}
          </>
        )}
      </div>
    </>
  );
};

export default FindBuyers;

