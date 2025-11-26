import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
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
  
  // Filter options loaded from backend
  const [filterOptions, setFilterOptions] = useState({
    regions: [],
    sectors: []
  });
  
  // State for supplier role ID
  const [supplierRoleId, setSupplierRoleId] = useState(null);

  // Load filter options on component mount
  useEffect(() => {
    loadFilterOptions();
  }, []);

  const loadFilterOptions = async () => {
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

        setFilterOptions({ regions, sectors });
        
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
  };

  const searchCompanies = async (roleIdToUse) => {
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
  };

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
    // Trigger search with reset values after state update
    setTimeout(() => {
      if (supplierRoleId) {
        searchCompanies(supplierRoleId);
      }
    }, 100);
  };

  return (
    <>
      <Navbar />
      <div className="find-suppliers-container">
      <div className="header">
        <h1>Find Suppliers</h1>
        <p className="subtitle">Discover verified agricultural suppliers from Pakistan</p>
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

      {/* Loading State */}
      {loading && (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading companies...</p>
        </div>
      )}

      {/* Companies Grid */}
      {!loading && !error && (() => {
        console.log('🎨 Rendering companies section, companies state:', companies);
        console.log('🎨 Companies length:', companies.length);
        return true; // Just run the logs, don't affect rendering
      })()}
      
      {!loading && !error && (
        <div className="companies-section">
          <div className="results-header">
            <h2>Results</h2>
            <span className="results-count">{companies.length} companies found</span>
          </div>

          {companies.length === 0 ? (
            <div className="no-results">
              <p>No companies found matching your criteria.</p>
              <button onClick={resetFilters} className="btn-secondary">Clear Filters</button>
            </div>
          ) : (
            <div className="companies-grid">
              {companies.map(company => (
                <div key={company.id} className="company-card">
                  <div className="card-header">
                    <h3>{company.name}</h3>
                    <span className={`status-badge ${company.verification_status}`}>
                      {company.verification_status === 'verified' ? '✓ Verified' : 'Pending'}
                    </span>
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
          )}
        </div>
      )}
    </div>
    </>
  );
};

export default FindSuppliers;
