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
    sector: '',
    type: '',
    role: ''
  });
  
  // Filter options loaded from backend
  const [filterOptions, setFilterOptions] = useState({
    regions: [],
    sectors: [],
    types: [],
    roles: []
  });

  // Load filter options on component mount
  useEffect(() => {
    loadFilterOptions();
  }, []);

  // Load companies when filters change
  useEffect(() => {
    searchCompanies();
  }, [filters]);

  const loadFilterOptions = async () => {
    try {
      const [regionsRes, sectorsRes, typesRes, rolesRes] = await Promise.all([
        fetch('http://localhost:8000/api/companies/regions/', { credentials: 'include' }),
        fetch('http://localhost:8000/api/sectors/', { credentials: 'include' }),
        fetch('http://localhost:8000/api/company-types/', { credentials: 'include' }),
        fetch('http://localhost:8000/api/company-roles/', { credentials: 'include' })
      ]);

      if (regionsRes.ok && sectorsRes.ok && typesRes.ok && rolesRes.ok) {
        const [regions, sectors, types, roles] = await Promise.all([
          regionsRes.json(),
          sectorsRes.json(),
          typesRes.json(),
          rolesRes.json()
        ]);

        setFilterOptions({ regions, sectors, types, roles });
      }
    } catch (err) {
      console.error('Failed to load filter options:', err);
    }
  };

  const searchCompanies = async () => {
    setLoading(true);
    setError(null);

    try {
      // Build query params
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.region) params.append('region', filters.region);
      if (filters.sector) params.append('sector', filters.sector);
      if (filters.type) params.append('type', filters.type);
      if (filters.role) params.append('role', filters.role);

      const response = await fetch(
        `http://localhost:8000/api/companies/?${params.toString()}`,
        { credentials: 'include' }
      );

      if (response.ok) {
        const data = await response.json();
        setCompanies(data.results || data); // Handle paginated or non-paginated response
      } else {
        throw new Error('Failed to load companies');
      }
    } catch (err) {
      setError('Failed to load companies. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({ ...prev, [filterName]: value }));
  };

  const resetFilters = () => {
    setFilters({
      search: '',
      region: '',
      sector: '',
      type: '',
      role: ''
    });
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
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search companies by name..."
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filters-grid">
          <select
            value={filters.region}
            onChange={(e) => handleFilterChange('region', e.target.value)}
            className="filter-select"
          >
            <option value="">All Regions</option>
            {filterOptions.regions.map(region => (
              <option key={region} value={region}>{region}</option>
            ))}
          </select>

          <select
            value={filters.sector}
            onChange={(e) => handleFilterChange('sector', e.target.value)}
            className="filter-select"
          >
            <option value="">All Sectors</option>
            {filterOptions.sectors.map(sector => (
              <option key={sector.id} value={sector.id}>{sector.name}</option>
            ))}
          </select>

          <select
            value={filters.type}
            onChange={(e) => handleFilterChange('type', e.target.value)}
            className="filter-select"
          >
            <option value="">All Types</option>
            {filterOptions.types.map(type => (
              <option key={type.id} value={type.id}>{type.name}</option>
            ))}
          </select>

          <select
            value={filters.role}
            onChange={(e) => handleFilterChange('role', e.target.value)}
            className="filter-select"
          >
            <option value="">All Roles</option>
            {filterOptions.roles.map(role => (
              <option key={role.id} value={role.id}>{role.name}</option>
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
