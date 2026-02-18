import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Navbar from '../Layout/Navbar';
import './Dashboard.css';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [scope, setScope] = useState('WORLDWIDE');

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search/results?q=${encodeURIComponent(query)}&scope=${scope}`);
    }
  };

  const handlePillClick = (text) => {
    setQuery(text);
  };

  return (
    <div className="dashboard-wrapper">
      <Navbar />

      <div className="dashboard-container">
        { }
        <div className="hero-section">
          <h1 style={{ marginBottom: '2rem' }}>What are you looking for, {user?.name || user?.email?.split('@')[0]}?</h1>

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="relative w-full max-w-2xl mx-auto mb-8" style={{ maxWidth: '672px', margin: '0 auto 2rem auto', position: 'relative' }}>
            <div className="relative group">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Try 'Import Dextrose from China under $700'..."
                className="w-full h-14 pl-14 pr-4 rounded-full border-2 border-gray-200 shadow-sm focus:border-emerald-500 focus:ring-0 text-lg transition-all"
                style={{ paddingLeft: '3.5rem', borderRadius: '9999px', width: '100%', height: '3.5rem', border: '2px solid #e5e7eb', fontSize: '1.125rem' }}
              />
              <div className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-emerald-500 transition-colors" style={{ position: 'absolute', left: '1.25rem', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }}>
                <Search size={24} />
              </div>
              <button
                type="submit"
                className="absolute right-2 top-2 bottom-2 px-6 bg-emerald-600 hover:bg-emerald-700 text-white rounded-full font-medium transition-colors"
                style={{ position: 'absolute', right: '0.5rem', top: '0.5rem', bottom: '0.5rem', borderRadius: '9999px', backgroundColor: '#10b981', color: 'white', padding: '0 1.5rem', border: 'none', cursor: 'pointer', fontWeight: 500 }}
              >
                Search
              </button>
            </div>
          </form>

          {/* Scope Toggle */}
          <div className="flex justify-center gap-2 mb-8" style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginBottom: '2rem' }}>
            <button
              type="button"
              onClick={() => setScope('WORLDWIDE')}
              className={`px-6 py-2 rounded-full font-medium transition-all ${scope === 'WORLDWIDE'
                ? 'bg-emerald-600 text-white shadow-md'
                : 'bg-white text-gray-600 border border-gray-200 hover:border-emerald-500'
                }`}
              style={{
                padding: '0.5rem 1.5rem',
                borderRadius: '9999px',
                border: scope === 'WORLDWIDE' ? 'none' : '1px solid #e5e7eb',
                backgroundColor: scope === 'WORLDWIDE' ? '#10b981' : 'white',
                color: scope === 'WORLDWIDE' ? 'white' : '#4b5563',
                cursor: 'pointer',
                fontWeight: 500,
                boxShadow: scope === 'WORLDWIDE' ? '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)' : 'none'
              }}
            >
              Worldwide
            </button>
            <button
              type="button"
              onClick={() => setScope('PAKISTAN')}
              className={`px-6 py-2 rounded-full font-medium transition-all ${scope === 'PAKISTAN'
                ? 'bg-emerald-600 text-white shadow-md'
                : 'bg-white text-gray-600 border border-gray-200 hover:border-emerald-500'
                }`}
              style={{
                padding: '0.5rem 1.5rem',
                borderRadius: '9999px',
                border: scope === 'PAKISTAN' ? 'none' : '1px solid #e5e7eb',
                backgroundColor: scope === 'PAKISTAN' ? '#10b981' : 'white',
                color: scope === 'PAKISTAN' ? 'white' : '#4b5563',
                cursor: 'pointer',
                fontWeight: 500,
                boxShadow: scope === 'PAKISTAN' ? '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)' : 'none'
              }}
            >
              Pakistan
            </button>
          </div>

          {/* Intent Pills */}
          <div className="flex flex-wrap justify-center gap-3 mb-12" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '0.75rem', marginBottom: '2rem' }}>
            {['I want to buy', 'I want to sell', 'Find suppliers', 'Find buyers'].map((pill) => (
              <button
                key={pill}
                onClick={() => handlePillClick(pill)}
                className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm font-medium text-gray-600 hover:border-emerald-500 hover:text-emerald-600 transition-colors shadow-sm"
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '9999px',
                  border: '1px solid #e5e7eb',
                  backgroundColor: 'white',
                  color: '#4b5563',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  fontWeight: 500
                }}
              >
                {pill}
              </button>
            ))}
          </div>

          {/* Example Queries */}
          <div className="text-gray-500 text-sm text-center" style={{ textAlign: 'center', color: '#6b7280' }}>
            <p className="mb-2 font-medium uppercase tracking-wide" style={{ fontSize: '0.75rem', letterSpacing: '0.05em' }}>Example Queries</p>
            <div className="flex flex-wrap justify-center gap-4 text-gray-400" style={{ display: 'flex', justifyContent: 'center', gap: '1rem', color: '#9ca3af' }}>
              <span style={{ cursor: 'pointer' }} onClick={() => setQuery("Dextrose suppliers in Pakistan")}>"Dextrose suppliers in Pakistan"</span>
              <span>•</span>
              <span style={{ cursor: 'pointer' }} onClick={() => setQuery("Buy Urea 46%")}>"Buy Urea 46%"</span>
              <span>•</span>
              <span style={{ cursor: 'pointer' }} onClick={() => setQuery("Who sells PVC Resin?")}>"Who sells PVC Resin?"</span>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="features-section">
          <h2>Platform Features</h2>
          <div className="features-grid">
            <div className="feature-item">
              <span className="feature-icon">✓</span>
              <div>
                <h4>Verified Directory</h4>
                <p>Access to PAR-verified agricultural businesses</p>
              </div>
            </div>
            <div className="feature-item">
              <span className="feature-icon">✓</span>
              <div>
                <h4>Direct Contacts</h4>
                <p>Unlock key decision-maker contact information</p>
              </div>
            </div>
            <div className="feature-item">
              <span className="feature-icon">✓</span>
              <div>
                <h4>Company Profiles</h4>
                <p>Detailed profiles with products and trade data</p>
              </div>
            </div>
            <div className="feature-item">
              <span className="feature-icon">✓</span>
              <div>
                <h4>Token System</h4>
                <p>Flexible credit-based access to premium features</p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="cta-section">
          <div className="cta-content">
            <h2>Ready to grow your business?</h2>
            <p>Start exploring verified suppliers and unlock valuable contacts</p>
            <div className="cta-buttons">
              <button
                onClick={() => navigate('/trade-directory/find-suppliers')}
                className="btn-primary-cta"
              >
                Browse Directory
              </button>
              <button
                onClick={() => navigate('/subscription')}
                className="btn-secondary-cta"
              >
                View Plans
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
