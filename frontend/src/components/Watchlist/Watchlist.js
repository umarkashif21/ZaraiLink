import React, { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import Breadcrumb from '../Common/Breadcrumb';
import EmptyState from '../Common/EmptyState';
import SortSelector from '../Common/SortSelector';
import ExportButton from '../Common/ExportButton';
import useWatchlist from '../../hooks/useWatchlist';
import './Watchlist.css';

const Watchlist = () => {
  const navigate = useNavigate();
  const { watchlist, removeFromWatchlist, clearWatchlist } = useWatchlist();
  const [sortBy, setSortBy] = useState('date_desc');
  const [searchTerm, setSearchTerm] = useState('');

  
  const filteredWatchlist = useMemo(() => {
    if (!searchTerm) return watchlist;
    return watchlist.filter(item => 
      item.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [watchlist, searchTerm]);

  
  const sortedWatchlist = useMemo(() => {
    const sorted = [...filteredWatchlist];
    const [field, direction] = sortBy.split('_');
    
    sorted.sort((a, b) => {
      let valA, valB;
      if (field === 'name') {
        valA = (a.name || '').toLowerCase();
        valB = (b.name || '').toLowerCase();
      } else if (field === 'date') {
        valA = new Date(a.addedAt || 0).getTime();
        valB = new Date(b.addedAt || 0).getTime();
      } else {
        valA = (a.name || '').toLowerCase();
        valB = (b.name || '').toLowerCase();
      }
      
      if (direction === 'asc') return valA > valB ? 1 : -1;
      return valA < valB ? 1 : -1;
    });
    
    return sorted;
  }, [filteredWatchlist, sortBy]);

  
  const exportColumns = [
    { key: 'name', label: 'Company Name' },
    { key: 'addedAt', label: 'Added Date' },
  ];

  
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  
  const handleCompanyClick = (companyId) => {
    
    navigate(`/trade-intelligence/company/${encodeURIComponent(companyId)}/overview`);
  };

  return (
    <>
      <Navbar />
      <div className="watchlist-container">
        <Breadcrumb />
        
        <div className="watchlist-header">
          <div className="header-content">
            <h1>⭐ My Watchlist</h1>
            <p className="subtitle">
              Companies you're tracking ({watchlist.length} {watchlist.length === 1 ? 'company' : 'companies'})
            </p>
          </div>
          
          {watchlist.length > 0 && (
            <div className="header-actions">
              <SortSelector 
                value={sortBy} 
                onChange={setSortBy}
                options={[
                  { value: 'date_desc', label: 'Recently Added' },
                  { value: 'date_asc', label: 'Oldest First' },
                  { value: 'name_asc', label: 'Name (A-Z)' },
                  { value: 'name_desc', label: 'Name (Z-A)' },
                ]}
              />
              <ExportButton 
                data={watchlist.map(item => ({
                  ...item,
                  addedAt: formatDate(item.addedAt)
                }))} 
                columns={exportColumns} 
                filename="my-watchlist"
                title="Watchlist Export"
              />
              <button 
                className="btn-clear-all"
                onClick={() => {
                  if (window.confirm('Are you sure you want to clear your entire watchlist?')) {
                    clearWatchlist();
                  }
                }}
              >
                Clear All
              </button>
            </div>
          )}
        </div>

        {/* Search Bar */}
        {watchlist.length > 0 && (
          <div className="watchlist-search">
            <input
              type="text"
              placeholder="Search your watchlist..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            {searchTerm && (
              <button 
                className="clear-search" 
                onClick={() => setSearchTerm('')}
              >
                ✕
              </button>
            )}
          </div>
        )}

        {/* Empty State */}
        {watchlist.length === 0 ? (
          <EmptyState
            title="Your watchlist is empty"
            description="Start adding companies to your watchlist by clicking the ⭐ star icon on any company card."
            actionLabel="Find Companies"
            onAction={() => navigate('/trade-directory/find-suppliers')}
          />
        ) : filteredWatchlist.length === 0 ? (
          <EmptyState
            title="No matches found"
            description={`No companies match "${searchTerm}" in your watchlist.`}
            actionLabel="Clear Search"
            onAction={() => setSearchTerm('')}
          />
        ) : (
          <>
            {/* Results Count */}
            <div className="results-info">
              Showing {sortedWatchlist.length} of {watchlist.length} companies
            </div>

            {/* Watchlist Grid */}
            <div className="watchlist-grid">
              {sortedWatchlist.map((item, index) => (
                <div 
                  key={item.id || index} 
                  className="watchlist-card"
                  onClick={() => handleCompanyClick(item.name || item.id)}
                >
                  <div className="card-header">
                    <h3>{item.name || 'Unknown Company'}</h3>
                    <button
                      className="btn-remove"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFromWatchlist(item.id || item.name);
                      }}
                      title="Remove from watchlist"
                    >
                      ✕
                    </button>
                  </div>
                  
                  <div className="card-body">
                    <div className="meta-info">
                      <span className="meta-label">Added:</span>
                      <span className="meta-value">{formatDate(item.addedAt)}</span>
                    </div>
                    {item.sector && (
                      <div className="meta-info">
                        <span className="meta-label">Sector:</span>
                        <span className="meta-value">{item.sector}</span>
                      </div>
                    )}
                    {item.country && (
                      <div className="meta-info">
                        <span className="meta-label">Country:</span>
                        <span className="meta-value">{item.country}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="card-footer">
                    <span className="view-profile">View Profile →</span>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Quick Actions */}
        {watchlist.length > 0 && (
          <div className="quick-actions">
            <h3>Quick Actions</h3>
            <div className="action-buttons">
              <Link to="/trade-directory/find-suppliers" className="action-btn">
                Find More Suppliers
              </Link>
              <Link to="/trade-directory/find-buyers" className="action-btn">
                Find More Buyers
              </Link>
              <Link to="/trade-intelligence/ledger" className="action-btn">
                Trade Ledger
              </Link>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default Watchlist;
