import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, X, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Navbar from '../Layout/Navbar';
import './Dashboard.css';

const API_BASE = process.env.REACT_APP_API_BASE_URL;

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [query, setQuery] = useState('');
  const scope = 'WORLDWIDE';

  // Autocomplete State
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedHsCode, setSelectedHsCode] = useState(null);
  const [selectedProductName, setSelectedProductName] = useState(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  const debounceRef = useRef(null);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // ── Debounced autocomplete fetch ──────────────────────────────────────
  const fetchSuggestions = useCallback(async (q) => {
    if (q.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    setLoadingSuggestions(true);
    try {
      const res = await fetch(`${API_BASE}/api/search/autocomplete/?q=${encodeURIComponent(q)}`);
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data);
        setShowSuggestions(data.length > 0);
      }
    } catch (err) {
      console.error('Autocomplete fetch error:', err);
    } finally {
      setLoadingSuggestions(false);
    }
  }, []);

  useEffect(() => {
    // Clear previous selection when user types freely
    setSelectedHsCode(null);
    setSelectedProductName(null);

    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchSuggestions(query);
    }, 250); // 250ms debounce

    return () => clearTimeout(debounceRef.current);
  }, [query, fetchSuggestions]);

  // ── Close suggestions on outside click ──────────────────────────────
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(e.target) &&
        !inputRef.current.contains(e.target)
      ) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // ── Handlers ─────────────────────────────────────────────────────────
  const handleSelectSuggestion = (suggestion) => {
    setQuery(suggestion.name);
    setSelectedHsCode(suggestion.hs_code);
    setSelectedProductName(suggestion.name);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const clearQuery = () => {
    setQuery('');
    setSelectedHsCode(null);
    setSelectedProductName(null);
    setSuggestions([]);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const params = new URLSearchParams({
      q: query,
      scope: scope
    });
    if (selectedHsCode) {
      params.set('hs_code', selectedHsCode);
    }
    navigate(`/search/results?${params.toString()}`);
  };

  const handlePillClick = (text) => {
    setQuery(text);
    setSelectedHsCode(null);
    setSelectedProductName(null);
  };

  return (
    <div className="dashboard-wrapper">
      <Navbar />

      <div className="dashboard-container">

        <div className="hero-section text-center relative z-10">
          <h1 style={{ marginBottom: '2rem' }}>
            What are you looking for, {user?.name || user?.email?.split('@')[0]}?
          </h1>

          {/* Search Bar + Autocomplete */}
          <form onSubmit={handleSearch} className="relative w-full max-w-2xl mx-auto mb-8" style={{ maxWidth: '672px', margin: '0 auto 2rem auto', position: 'relative' }}>
            <div className="relative group">
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                placeholder="Try 'Import Dextrose from China under $700'..."
                className="w-full h-14 pl-14 pr-24 rounded-full border-2 border-gray-200 shadow-sm focus:border-emerald-500 focus:ring-0 text-lg transition-all"
                style={{ paddingLeft: '3.5rem', paddingRight: '6rem', borderRadius: '9999px', width: '100%', height: '3.5rem', border: '2px solid #e5e7eb', fontSize: '1.125rem' }}
                autoComplete="off"
              />
              <div className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-emerald-500 transition-colors" style={{ position: 'absolute', left: '1.25rem', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }}>
                <Search size={24} />
              </div>

              {/* Clear button */}
              {query && (
                <button
                  type="button"
                  onClick={clearQuery}
                  className="absolute right-[5.5rem] top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  style={{ position: 'absolute', right: '5.5rem', top: '50%', transform: 'translateY(-50%)', background: 'transparent', border: 'none', cursor: 'pointer' }}
                >
                  <X size={18} color="#9ca3af" />
                </button>
              )}

              <button
                type="submit"
                className="absolute right-2 top-2 bottom-2 px-6 bg-emerald-600 hover:bg-emerald-700 text-white rounded-full font-medium transition-colors"
                style={{ position: 'absolute', right: '0.5rem', top: '0.5rem', bottom: '0.5rem', borderRadius: '9999px', backgroundColor: '#10b981', color: 'white', padding: '0 1.5rem', border: 'none', cursor: 'pointer', fontWeight: 500 }}
              >
                Search
              </button>
            </div>

            {/* Product Disambiguation Banner */}
            {selectedProductName && (
              <div className="mt-2 flex items-center justify-center gap-2 text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-full py-1.5 px-4 inline-flex mx-auto absolute left-0 right-0" style={{ marginTop: '0.5rem', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', backgroundColor: '#ecfdf5', color: '#065f46', border: '1px solid #10b981', borderRadius: '9999px', padding: '0.375rem 1rem', fontSize: '0.875rem' }}>
                <span className="font-medium">Searching exactly for:</span>
                <span>{selectedProductName}</span>
                <button
                  type="button"
                  onClick={clearQuery}
                  className="text-emerald-500 hover:text-emerald-700"
                  style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: 0 }}
                >
                  <X size={14} />
                </button>
              </div>
            )}

            {/* Autocomplete Dropdown */}
            {showSuggestions && (
              <div
                ref={suggestionsRef}
                className="absolute z-50 top-full mt-2 w-full bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden text-left"
                style={{ position: 'absolute', zIndex: 50, top: '100%', marginTop: '0.5rem', width: '100%', backgroundColor: 'white', borderRadius: '1rem', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)', border: '1px solid #f3f4f6', overflow: 'hidden', textAlign: 'left' }}
              >
                <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wide border-b border-gray-50" style={{ padding: '0.5rem 1rem', fontSize: '0.75rem', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '1px solid #f9fafb' }}>
                  Product Matches
                </div>
                {suggestions.map((s, i) => (
                  <button
                    key={s.hs_code + i}
                    type="button"
                    onClick={() => handleSelectSuggestion(s)}
                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-emerald-50 transition-colors group"
                    style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 1rem', background: 'transparent', border: 'none', borderBottom: '1px solid #f9fafb', cursor: 'pointer', textAlign: 'left' }}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#ecfdf5'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <div className="flex flex-col items-start" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                      <span className="font-medium text-gray-900" style={{ fontWeight: 500, color: '#111827' }}>
                        {s.name}
                      </span>
                      <span className="text-xs text-gray-400" style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                        {s.category} · HS {s.hs_code}
                      </span>
                    </div>
                    <div className="flex items-center gap-3" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      {s.total_volume > 0 && (
                        <span className="text-xs text-gray-500 bg-gray-100 rounded-full px-2 py-0.5" style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#f3f4f6', borderRadius: '9999px', padding: '0.125rem 0.5rem' }}>
                          {s.total_volume.toLocaleString()} MT
                        </span>
                      )}
                      <ChevronRight size={16} color="#d1d5db" />
                    </div>
                  </button>
                ))}
                {loadingSuggestions && (
                  <div className="px-4 py-3 text-sm text-gray-400 text-center" style={{ padding: '0.75rem 1rem', fontSize: '0.875rem', color: '#9ca3af', textAlign: 'center' }}>
                    Searching products...
                  </div>
                )}
              </div>
            )}
          </form>


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
