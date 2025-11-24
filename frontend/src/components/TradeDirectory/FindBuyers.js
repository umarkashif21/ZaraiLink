import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './FindBuyers.css';

const FindBuyers = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    search: '',
    region: '',
    sector: '',
    type: '',
    role: 'Buyer' // Default role set to Buyer
  });

  // Filter options state
  const [regions, setRegions] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [types, setTypes] = useState([]);
  // Roles not needed as filter since this is specific to Buyers

  useEffect(() => {
    loadFilterOptions();
    searchCompanies();
  }, []);

  const loadFilterOptions = async () => {
    try {
      const [regionsRes, sectorsRes, typesRes] = await Promise.all([
        fetch('http://localhost:8000/api/companies/regions/'),
        fetch('http://localhost:8000/api/sectors/'),
        fetch('http://localhost:8000/api/company-types/')
      ]);

      if (regionsRes.ok) setRegions(await regionsRes.json());
      if (sectorsRes.ok) setSectors(await sectorsRes.json());
      if (typesRes.ok) setTypes(await typesRes.json());
    } catch (err) {
      console.error('Failed to load filter options', err);
    }
  };

  const searchCompanies = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.region) params.append('region', filters.region);
      if (filters.sector) params.append('sector', filters.sector);
      if (filters.type) params.append('type', filters.type);
      params.append('role', 'Buyer'); // Enforce Buyer role

      const response = await fetch(
        `http://localhost:8000/api/companies/?${params.toString()}`,
        { credentials: 'include' }
      );

      if (response.ok) {
        const data = await response.json();
        setCompanies(data.results || data);
      } else {
        throw new Error('Failed to load buyers');
      }
    } catch (err) {
      setError('Failed to load buyers. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSearch = (e) => {
    e.preventDefault();
    searchCompanies();
  };

  const handleReset = () => {
    setFilters({
      search: '',
      region: '',
      sector: '',
      type: '',
      role: 'Buyer'
    });
    // Trigger search after state update would require useEffect dependency or separate call
    // For simplicity, we'll just reload with initial state logic if we were using it, 
    // but here we need to manually trigger search with reset values
    // A better way is to pass the reset values directly to search
    // But since searchCompanies uses state, we might need to wait or pass args.
    // Let's just set state and let the user click search or use a timeout/effect.
    // Actually, let's just call search with explicit empty params + buyer role
    
    // Quick fix: just set filters and let user search, or force reload
    // Ideally:
    setFilters({
        search: '',
        region: '',
        sector: '',
        type: '',
        role: 'Buyer'
    });
    setTimeout(() => {
        // This is a bit hacky but works for simple cases without refactoring searchCompanies to accept args
        // Better: refactor searchCompanies to take params, but keeping it consistent with FindSuppliers structure
        // Let's just reload the page or re-fetch manually
        // Re-fetching manually with default values:
        fetchCompaniesWithParams({ role: 'Buyer' });
    }, 0);
  };

  const fetchCompaniesWithParams = async (customFilters) => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        // Add custom filters
        Object.entries(customFilters).forEach(([key, value]) => {
            if(value) params.append(key, value);
        });
        
        const response = await fetch(
            `http://localhost:8000/api/companies/?${params.toString()}`,
            { credentials: 'include' }
        );
        if (response.ok) {
            const data = await response.json();
            setCompanies(data.results || data);
        }
      } catch (err) {
          console.error(err);
      } finally {
          setLoading(false);
      }
  };

  return (
    <>
      <Navbar />
      <div className="find-buyers-container">
      <div className="header">
        <h1>Find Buyers</h1>
        <p className="subtitle">Connect with verified agricultural buyers and distributors</p>
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
          <select name="region" value={filters.region} onChange={handleFilterChange}>
            <option value="">All Regions</option>
            {regions.map(r => (
              <option key={r.id} value={r.name}>{r.name}</option>
            ))}
          </select>

          <select name="sector" value={filters.sector} onChange={handleFilterChange}>
            <option value="">All Sectors</option>
            {sectors.map(s => (
              <option key={s.id} value={s.name}>{s.name}</option>
            ))}
          </select>

          <select name="type" value={filters.type} onChange={handleFilterChange}>
            <option value="">All Company Types</option>
            {types.map(t => (
              <option key={t.id} value={t.name}>{t.name}</option>
            ))}
          </select>

          <button type="button" onClick={handleReset} className="btn-reset">
            Reset Filters
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading buyers...</p>
        </div>
      ) : (
        <div className="companies-grid">
          {companies.length > 0 ? (
            companies.map(company => (
              <div key={company.id} className="company-card">
                <div className="card-header">
                  <h3>{company.name}</h3>
                  {company.verification_status === 'verified' && (
                    <span className="verified-badge">✓ Verified</span>
                  )}
                </div>
                
                <div className="card-body">
                  <div className="info-row">
                    <span className="label">Location:</span>
                    <span className="value">{company.city || company.district}, {company.province}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Sector:</span>
                    <span className="value">{company.sector_name}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Type:</span>
                    <span className="value">{company.company_type_name}</span>
                  </div>
                </div>

                <div className="card-footer">
                  <Link to={`/trade-directory/company/${company.id}`} className="btn-view-profile">
                    View Profile
                  </Link>
                </div>
              </div>
            ))
          ) : (
            <div className="no-results">
              <h3>No buyers found</h3>
              <p>Try adjusting your search or filters to find what you're looking for.</p>
            </div>
          )}
        </div>
      )}
    </div>
    </>
  );
};

export default FindBuyers;
