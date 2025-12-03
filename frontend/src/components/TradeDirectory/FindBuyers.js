
import React, { useState, useEffect, useCallback } from 'react';
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
    sector: ''
  });

  // Filter options state
  const [regions, setRegions] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [buyerRoleId, setBuyerRoleId] = useState(null);

  const searchCompanies = useCallback(async () => {
    if (!buyerRoleId) {
      console.log('❌ No buyerRoleId, exiting searchCompanies');
      return;
    }
    
    console.log('🔍 searchCompanies called with buyerRoleId:', buyerRoleId);
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.region) params.append('region', filters.region);
      if (filters.sector) params.append('sector', filters.sector);
      params.append('role', buyerRoleId); // Use dynamic ID

      const apiUrl = `http://localhost:8000/api/companies/?${params.toString()}`;
      console.log('📡 Fetching from:', apiUrl);

      const response = await fetch(apiUrl, { credentials: 'include' });
      console.log('📥 Response status:', response.status, response.ok);

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Raw API response:', data);
        console.log('📊 Data type:', Array.isArray(data) ? 'Array' : typeof data);
        
        const companies = data.results || data;
        console.log('🏢 Companies to set:', companies.length, 'companies');
        setCompanies(companies);
      } else {
        throw new Error('Failed to load buyers');
      }
    } catch (err) {
      setError('Failed to load buyers. Please try again.');
      console.error('❌ Search error:', err);
    } finally {
      setLoading(false);
      console.log('🏁 searchCompanies completed');
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
        console.log('🔍 Available roles:', roles);
        // Prioritize "Buyers" (plural) over "Buyer" (singular)
        const buyerRole = roles.find(r => r.name.toLowerCase() === 'buyers') ||
                          roles.find(r => r.name.toLowerCase() === 'buyer');
        if (buyerRole) {
          console.log('✅ Found buyer role:', buyerRole);
          setBuyerRoleId(buyerRole.id);
        } else {
          console.error('❌ Buyer role not found in backend');
          setError('System configuration error: Buyer role missing');
        }
      }
    } catch (err) {
      console.error('Failed to load filter options', err);
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
      sector: ''
    });
    // Trigger search with reset values after state update
    setTimeout(() => {
      if (buyerRoleId) {
        searchCompanies();
      }
    }, 100);
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
          <select 
            name="region" 
            value={filters.region} 
            onChange={(e) => {
              handleFilterChange(e);
              // Auto-trigger search after state update
              setTimeout(() => {
                if (buyerRoleId) searchCompanies();
              }, 100);
            }}
          >
            <option value="">All Regions</option>
            {regions.map(region => (
              <option key={region} value={region}>{region}</option>
            ))}
          </select>

          <select 
            name="sector" 
            value={filters.sector} 
            onChange={(e) => {
              handleFilterChange(e);
              // Auto-trigger search after state update
              setTimeout(() => {
                if (buyerRoleId) searchCompanies();
              }, 100);
            }}
          >
            <option value="">All Sectors</option>
            {sectors.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
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
                  <h3>{company.name.toUpperCase()}</h3>
                  {company.verification_status === 'verified' && (
                    <span className="verified-badge">✓ Verified</span>
                  )}
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
