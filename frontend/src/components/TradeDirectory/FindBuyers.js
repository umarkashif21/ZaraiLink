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
import useDebounce from '../../hooks/useDebounce';
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
  
  
  const [useAI, setUseAI] = useState(false);
  const [aiFallback, setAiFallback] = useState(false);
  
  
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;
  const [sortBy, setSortBy] = useState('name_asc');
  
  
  const { isInWatchlist, toggleWatchlist } = useWatchlist();
  
  
  const debouncedSearch = useDebounce(filters.search, 300);
  
  
  const [filterOptions, setFilterOptions] = useState({
    regions: [],
    sectors: []
  });
  
  
  const [buyerRoleId, setBuyerRoleId] = useState(null);

  const searchCompanies = useCallback(async (roleIdToUse) => {
    const roleId = roleIdToUse || buyerRoleId;
    console.log('🔍 searchCompanies called with roleId:', roleId);
    if (!roleId) {
      console.log('❌ No roleId, exiting');
      return;
    }
    
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.region) params.append('region', filters.region);
      if (filters.sector) params.append('sector', filters.sector);
      if (useAI) params.append('use_ai', 'true');
      params.append('role', roleId);
      
      const apiUrl = `http://localhost:8000/api/companies/?${params.toString()}`;
      console.log('📡 Fetching from:', apiUrl);

      const response = await fetch(
        apiUrl,
        { credentials: 'include' }
      );
      
      console.log('📥 Response status:', response.status, response.ok);

      if (response.ok) {
        const data = await response.json();
        const companies = data.results || data;
        setCompanies(companies);
        setAiFallback(data.ai_fallback === true);
      } else {
        throw new Error('Failed to load companies');
      }
    } catch (err) {
      console.error('❌ Search error:', err);
      setError('Failed to load buyers. Please try again.');
    } finally {
      setLoading(false);
      console.log('🏁 searchCompanies completed');
    }
  }, [buyerRoleId, filters, useAI]);

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({ ...prev, [filterName]: value }));
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (buyerRoleId) {
      searchCompanies(buyerRoleId);
    }
  };
  
  const resetFilters = () => {
    setFilters({
      search: '',
      region: '',
      sector: ''
    });
    setUseAI(false);
    setCurrentPage(1);
    setTimeout(() => {
      if (buyerRoleId) {
        searchCompanies(buyerRoleId);
      }
    }, 100);
  };

  
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

  
  const totalPages = Math.ceil(sortedCompanies.length / itemsPerPage);
  const paginatedCompanies = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return sortedCompanies.slice(start, start + itemsPerPage);
  }, [sortedCompanies, currentPage, itemsPerPage]);

  
  const exportColumns = [
    { key: 'name', label: 'Company Name' },
    { key: 'province', label: 'Province' },
    { key: 'sector_name', label: 'Sector' },
    { key: 'verification_status', label: 'Status' },
  ];

  
  const loadFilterOptions = useCallback(async () => {
    try {
      const [regionsRes, sectorsRes, rolesRes] = await Promise.all([
        fetch('http://localhost:8000/api/companies/regions/'),
        fetch('http://localhost:8000/api/sectors/'),
        fetch('http://localhost:8000/api/company-roles/')
      ]);

      if (regionsRes.ok) {
        const regionsData = await regionsRes.json();
        setFilterOptions(prev => ({
          ...prev,
          regions: regionsData.filter(r => r && r.trim() !== '')
        }));
      }
      if (sectorsRes.ok) {
        const sectorsData = await sectorsRes.json();
        setFilterOptions(prev => ({
          ...prev,
          sectors: sectorsData
        }));
      }
      
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
  }, []);

  
  useEffect(() => {
    loadFilterOptions();
  }, [loadFilterOptions]);

  
  useEffect(() => {
    if (buyerRoleId) {
      searchCompanies(buyerRoleId);
    }
  }, [buyerRoleId, debouncedSearch]); 

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

      {}
      <div className="filters-section">
        <form onSubmit={handleSearch} className="search-bar">
          <input
            type="text"
            placeholder="Search companies by name..."
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            className="search-input"
          />
          <button type="submit" className="btn-search">Search</button>
        </form>
        
        {}
        <div className="smart-search-toggle" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input 
                type="checkbox" 
                id="useAI" 
                checked={useAI} 
                onChange={(e) => setUseAI(e.target.checked)} 
                style={{ width: '16px', height: '16px' }}
            />
            <label htmlFor="useAI" style={{ cursor: 'pointer', fontWeight: '500', color: useAI ? 'var(--color-primary)' : 'inherit' }}>
                Enable AI Smart Search
            </label>
        </div>

        <div className="filters-grid">

          <select
            value={filters.region}
            onChange={(e) => {
              handleFilterChange('region', e.target.value);
              setTimeout(() => {
                if (buyerRoleId) searchCompanies(buyerRoleId);
              }, 100);
            }}
            className="filter-select"
          >
            <option value="">All Regions</option>
            {filterOptions.regions.map(region => (
              <option key={region} value={region}>{region}</option>
            ))}
          </select>

          <select
            value={filters.sector}
            onChange={(e) => {
              handleFilterChange('sector', e.target.value);
              setTimeout(() => {
                if (buyerRoleId) searchCompanies(buyerRoleId);
              }, 100);
            }}
            className="filter-select"
          >
            <option value="">All Sectors</option>
            {filterOptions.sectors.map(sector => (
              <option key={sector.id} value={sector.id}>{sector.name}</option>
            ))}
          </select>



          <button onClick={resetFilters} className="reset-btn">
            Reset Filters
          </button>
        </div>
      </div>

      {}
      {useAI && aiFallback && !loading && (
        <div style={{
          backgroundColor: '#fff3cd',
          border: '1px solid #ffecb5',
          borderRadius: '8px',
          padding: '0.75rem 1rem',
          marginBottom: '1rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          color: '#856404'
        }}>
          {/* <span>ℹ️</span> */}
          <span>AI Smart Search is currently unavailable. Showing text search results instead.</span>
        </div>
      )}

      {}
      {error && (
        <div className="error-message">
          {/* <span>⚠️</span> */}
          <p>{error}</p>
        </div>
      )}

      {}
      {loading && (
        <div className="companies-section">
          <div className="companies-grid">
            {[1,2,3,4,5,6,7,8].map(i => <SkeletonCard key={i} />)}
          </div>
        </div>
      )}

      {}
      {!loading && !error && (
        <div className="companies-section">
          <div className="results-header">
            <h2>Results</h2>
            <span className="results-count">{companies.length} companies found</span>
          </div>

          {companies.length === 0 ? (
            <EmptyState
              title="No companies found"
              description="No companies match your search criteria. Try adjusting your filters."
              actionLabel="Clear Filters"
              onAction={resetFilters}
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
                        <span className="value">{company.province || 'N/A'}, {company.country}</span>
                      </div>
                      <div className="info-row">
                        <span className="label">Sector:</span>
                        <span className="value">{company.sector_name || 'N/A'}</span>
                      </div>
                      <div className="info-row">
                        <span className="label">Role:</span>
                        <span className="value">{company.role_name || 'N/A'}</span>
                      </div>
                      {company.type_name && (
                        <div className="info-row">
                          <span className="label">Type:</span>
                          <span className="value">{company.type_name}</span>
                        </div>
                      )}
                    </div>

                    <div className="card-footer">
                      <Link to={`/trade-directory/company/${company.id}`} className="btn-primary">
                        View Profile
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
              
              {}
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={setCurrentPage}
                totalItems={companies.length}
                itemsPerPage={itemsPerPage}
              />
            </>
          )}
        </div>
      )}
    </div>
    </>
  );
};

export default FindBuyers;
