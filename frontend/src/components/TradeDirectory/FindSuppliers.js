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
import './FindSuppliers.css';

const FindSuppliers = () => {
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
  
  // Debounce search
  const debouncedSearch = useDebounce(filters.search, 300);
  
  // Filter options loaded from backend
  const [filterOptions, setFilterOptions] = useState({
    regions: [],
    sectors: []
  });
  
  // State for supplier role ID
  const [supplierRoleId, setSupplierRoleId] = useState(null);

  const searchCompanies = useCallback(async (roleIdToUse) => {
    // Use passed roleId or fall back to state
    const roleId = roleIdToUse || supplierRoleId;
    console.log('🔍 searchCompanies called with roleId:', roleId);
    if (!roleId) {
      console.log('❌ No roleId, exiting');
      return; // Don't search without supplier role
    }
    
    setLoading(true);
    setError(null);

    try {
      // Build query params
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.region) params.append('region', filters.region);
      if (filters.sector) params.append('sector', filters.sector);
      params.append('role', roleId); // Always filter by supplier role
      
      const apiUrl = `http://localhost:8000/api/companies/?${params.toString()}`;
      console.log('📡 Fetching from:', apiUrl);

      const response = await fetch(
        apiUrl,
        { credentials: 'include' }
      );
      
      console.log('📥 Response status:', response.status, response.ok);

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Raw API response:', data);
        console.log('📊 Data type:', Array.isArray(data) ? 'Array' : typeof data);
        console.log('📈 Data length/keys:', Array.isArray(data) ? data.length : Object.keys(data));
        
        const companies = data.results || data;
        console.log('🏢 Companies to set:', companies);
        console.log('🏢 Companies count:', Array.isArray(companies) ? companies.length : 'not an array');
        
        setCompanies(companies); // Handle paginated or non-paginated response
        console.log('✨ setCompanies called with:', companies.length, 'companies');
      } else {
        throw new Error('Failed to load companies');
      }
    } catch (err) {
      console.error('❌ Search error:', err);
      setError('Failed to load suppliers. Please try again.');
    } finally {
      setLoading(false);
      console.log('🏁 searchCompanies completed');
    }
  }, [supplierRoleId, filters]);

  const loadFilterOptions = useCallback(async () => {
    try {
      const [regionsRes, sectorsRes, rolesRes] = await Promise.all([
        fetch('http://localhost:8000/api/companies/regions/', { credentials: 'include' }),
        fetch('http://localhost:8000/api/sectors/', { credentials: 'include' }),
        fetch('http://localhost:8000/api/company-roles/', { credentials: 'include' })
      ]);

      if (regionsRes.ok && sectorsRes.ok && rolesRes.ok) {
        const [regions, sectors, roles] = await Promise.all([
          regionsRes.json(),
          sectorsRes.json(),
          rolesRes.json()
        ]);

        setFilterOptions({ 
          regions: regions.filter(r => r && r.trim() !== ''), 
          sectors
        });
        
        console.log('🔍 Available roles:', roles);
        // Prioritize "Suppliers" (plural) over "Supplier" (singular)
        const supplierRole = roles.find(r => r.name.toLowerCase() === 'suppliers') ||
                             roles.find(r => r.name.toLowerCase() === 'supplier');
        if (supplierRole) {
          console.log('✅ Found supplier role:', supplierRole);
          setSupplierRoleId(supplierRole.id);
          // Call searchCompanies directly with the role ID
          searchCompanies(supplierRole.id);
        } else {
          console.error('❌ Supplier role not found in backend');
          setError('System configuration error: Supplier role missing');
        }
      }
    } catch (err) {
      console.error('Failed to load filter options:', err);
    }
  }, [searchCompanies]);

  // Load filter options on component mount
  useEffect(() => {
    loadFilterOptions();
  }, [loadFilterOptions]);

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({ ...prev, [filterName]: value }));
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (supplierRoleId) {
      searchCompanies(supplierRoleId);
    }
  };

  const resetFilters = () => {
    setFilters({
      search: '',
      region: '',
      sector: ''
    });
    setCurrentPage(1);
    // Trigger search with reset values after state update
    setTimeout(() => {
      if (supplierRoleId) {
        searchCompanies(supplierRoleId);
      }
    }, 100);
  };

  // Sorted companies
  const sortedCompanies = useMemo(() => {
    const sorted = [...companies];
    const [field, direction] = sortBy.split('_');
    sorted.sort((a, b) => {
      let valA, valB;
      if (field === 'name') {
        valA = (a.name || '').toLowerCase();
        valB = (b.name || '').toLowerCase();
      } else {
        valA = (a.name || '').toLowerCase();
        valB = (b.name || '').toLowerCase();
      }
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
    { key: 'country', label: 'Country' },
    { key: 'sector_name', label: 'Sector' },
    { key: 'verification_status', label: 'Status' },
  ];

  return (
    <>
      <Navbar />
      <div className="find-suppliers-container">
      <Breadcrumb />
      
      <div className="header">
        <div>
          <h1>Find Suppliers</h1>
          <p className="subtitle">Discover verified agricultural suppliers from Pakistan</p>
        </div>
        <div className="header-actions" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <SortSelector value={sortBy} onChange={setSortBy} />
          <ExportButton 
            data={companies} 
            columns={exportColumns} 
            filename="suppliers-list"
            title="Suppliers Export"
          />
        </div>
      </div>

      {/* Filters Section */}
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

        <div className="filters-grid">
          <select
            value={filters.region}
            onChange={(e) => {
              handleFilterChange('region', e.target.value);
              // Auto-trigger search after state update
              setTimeout(() => {
                if (supplierRoleId) searchCompanies(supplierRoleId);
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
              // Auto-trigger search after state update
              setTimeout(() => {
                if (supplierRoleId) searchCompanies(supplierRoleId);
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

      {/* Error Message */}
      {error && (
        <div className="error-message">
          <span>⚠️</span>
          <p>{error}</p>
        </div>
      )}

      {/* Loading State - now with skeletons */}
      {loading && (
        <div className="companies-section">
          <div className="companies-grid">
            {[1,2,3,4,5,6,7,8].map(i => <SkeletonCard key={i} />)}
          </div>
        </div>
      )}

      {/* Companies Grid */}
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
        </div>
      )}
    </div>
    </>
  );
};

export default FindSuppliers;
