import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, X, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Navbar from '../Layout/Navbar';


const API_BASE = process.env.REACT_APP_API_BASE_URL;

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [query, setQuery] = useState('');
  const [scope, setScope] = useState(null);  // null = no scope filter selected

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
      const isNumeric = /^[\d.]+$/.test(q);
      const endpoint = isNumeric
        ? `${API_BASE}/api/search/hs-code-tree/?q=${encodeURIComponent(q)}`
        : `${API_BASE}/api/search/autocomplete/?q=${encodeURIComponent(q)}`;

      const res = await fetch(endpoint);
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
    if (suggestion.is_final !== undefined) {
      if (!suggestion.is_final) {
        setQuery(suggestion.hs_code);
        inputRef.current?.focus();
        return;
      } else {
        setQuery(suggestion.hs_code);
        setSelectedHsCode(suggestion.hs_code);
        setSelectedProductName(suggestion.name);
        setShowSuggestions(false);
        navigate(`/search/results?q=${encodeURIComponent(suggestion.hs_code)}&hs_code=${encodeURIComponent(suggestion.hs_code)}`);
        return;
      }
    }

    setQuery(suggestion.name);
    setSelectedHsCode(suggestion.hs_code);
    setSelectedProductName(suggestion.name);
    setShowSuggestions(false);
    navigate(`/search/results?q=${encodeURIComponent(suggestion.name)}&hs_code=${encodeURIComponent(suggestion.hs_code)}`);
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

    const isHsCode = /^[\d.]+$/.test(query.trim());
    const params = new URLSearchParams({ q: query });

    if (isHsCode) {
      // HS Code search: skip scope entirely — the 4-tab pill UI handles direction
      params.set('hs_code', selectedHsCode || query.trim());
    } else {
      // Only add scope if user explicitly selected one
      if (scope) params.set('scope', scope);
      if (selectedHsCode) params.set('hs_code', selectedHsCode);
    }
    navigate(`/search/results?${params.toString()}`);
  };

  const handlePillClick = (text) => {
    setQuery(text);
    setSelectedHsCode(null);
    setSelectedProductName(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-16 md:py-24">
        <div className="max-w-4xl mx-auto text-center relative z-10 mb-16">
          <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight mb-8">
            What are you looking for, <span className="text-emerald-600">{user?.name || user?.email?.split('@')[0]}</span>?
          </h1>

          {/* Search Bar + Autocomplete */}
          <form onSubmit={handleSearch} className="relative w-full mx-auto mb-8">
            <div className="relative group shadow-2xl shadow-slate-200/50 rounded-full">
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                placeholder="Try 'Import Dextrose from China under $700'..."
                className="w-full h-16 pl-16 pr-32 rounded-full border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 text-lg transition-all"
                autoComplete="off"
              />
              <div className="absolute left-6 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-emerald-500 transition-colors">
                <Search size={26} />
              </div>

              {/* Clear button */}
              {query && (
                <button
                  type="button"
                  onClick={clearQuery}
                  className="absolute right-[8.5rem] top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <X size={20} />
                </button>
              )}

              <button
                type="submit"
                className="absolute right-2 top-2 bottom-2 px-8 bg-emerald-500 hover:bg-emerald-400 text-slate-900 rounded-full font-bold transition-all shadow-lg shadow-emerald-500/20"
              >
                Search
              </button>
            </div>

            {/* Product Disambiguation Banner */}
            {selectedProductName && (
              <div className="mt-4 flex items-center justify-center gap-2 text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-full py-2 px-5 inline-flex mx-auto shadow-sm">
                <span className="font-bold">Searching exactly for:</span>
                <span>{selectedProductName}</span>
                <button
                  type="button"
                  onClick={clearQuery}
                  className="text-emerald-500 hover:text-emerald-700 ml-1"
                >
                  <X size={16} />
                </button>
              </div>
            )}

            {/* Autocomplete Dropdown */}
            {showSuggestions && (
              <div
                ref={suggestionsRef}
                className="absolute z-50 top-full mt-4 w-full bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden text-left"
              >
                <div className="px-6 py-3 text-xs font-bold text-slate-400 uppercase tracking-widest border-b border-slate-50 bg-slate-50/50">
                  Product Matches
                </div>
                {suggestions.map((s, i) => (
                  <button
                    key={s.hs_code + i}
                    type="button"
                    onClick={() => handleSelectSuggestion(s)}
                    className="w-full flex items-center justify-between px-6 py-4 hover:bg-emerald-50/50 transition-colors border-b border-slate-50 last:border-0 group"
                  >
                    <div className="flex flex-col items-start gap-1">
                      <span className="font-bold text-slate-800 group-hover:text-emerald-700 transition-colors">
                        {s.name}
                      </span>
                      <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                        {s.category} • HS {s.hs_code}
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      {s.total_volume > 0 && (
                        <span className="text-xs font-bold text-slate-600 bg-slate-100 rounded-lg px-3 py-1">
                          {s.total_volume.toLocaleString()} MT
                        </span>
                      )}
                      {s.is_final === false && (
                        <span className="text-xs font-bold text-emerald-700 bg-emerald-100 rounded-lg px-3 py-1">
                          Drill Down
                        </span>
                      )}
                      <ChevronRight size={18} className="text-slate-300 group-hover:text-emerald-500 transition-colors" />
                    </div>
                  </button>
                ))}
                {loadingSuggestions && (
                  <div className="px-6 py-4 text-sm font-medium text-slate-400 text-center animate-pulse">
                    Searching global database...
                  </div>
                )}
              </div>
            )}
          </form>

          {/* Scope Toggle */}
          <div className="flex justify-center gap-3 mb-10 mt-12">
            <button
              type="button"
              onClick={() => setScope(scope === 'IMPORT' ? null : 'IMPORT')}
              className={`px-8 py-3 rounded-full font-bold transition-all ${scope === 'IMPORT'
                ? 'bg-emerald-500 text-slate-900 shadow-lg shadow-emerald-500/20'
                : 'bg-white text-slate-600 border border-slate-200 hover:border-emerald-400 hover:text-emerald-600'
                }`}
            >
              Analyze Imports
            </button>
            <button
              type="button"
              onClick={() => setScope(scope === 'EXPORT' ? null : 'EXPORT')}
              className={`px-8 py-3 rounded-full font-bold transition-all ${scope === 'EXPORT'
                ? 'bg-emerald-500 text-slate-900 shadow-lg shadow-emerald-500/20'
                : 'bg-white text-slate-600 border border-slate-200 hover:border-emerald-400 hover:text-emerald-600'
                }`}
            >
              Analyze Exports
            </button>
          </div>

          {/* Intent Pills */}
          <div className="flex flex-wrap justify-center gap-3 mb-12">
            {['I want to buy', 'I want to sell', 'Find suppliers', 'Find buyers'].map((pill) => (
              <button
                key={pill}
                onClick={() => handlePillClick(pill)}
                className="px-5 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:border-emerald-500 hover:text-emerald-600 hover:shadow-md transition-all"
              >
                {pill}
              </button>
            ))}
          </div>

          {/* Example Queries */}
          <div className="text-slate-500 text-sm">
            <p className="mb-3 font-bold uppercase tracking-widest text-xs text-slate-400">Example Intelligence Queries</p>
            <div className="flex flex-wrap justify-center gap-6 text-slate-500 font-medium">
              <span className="cursor-pointer hover:text-emerald-600 transition-colors" onClick={() => setQuery("Dextrose suppliers in Pakistan")}>"Dextrose suppliers in Pakistan"</span>
              <span className="text-slate-300">•</span>
              <span className="cursor-pointer hover:text-emerald-600 transition-colors" onClick={() => setQuery("Buy Urea 46%")}>"Buy Urea 46%"</span>
              <span className="text-slate-300">•</span>
              <span className="cursor-pointer hover:text-emerald-600 transition-colors" onClick={() => setQuery("Who sells PVC Resin?")}>"Who sells PVC Resin?"</span>
            </div>
          </div>
        </div>

        {/* Features Section - Palantir Glass Card style */}
        <div className="mt-20">
          <h2 className="text-2xl font-bold text-slate-900 mb-8 text-center">Intelligence Toolkit</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { title: 'Verified Directory', desc: 'Secure access to PAR-verified global trading entities.' },
              { title: 'Direct Contacts', desc: 'Acquire direct intelligence and decision-maker access.' },
              { title: 'Entity Profiles', desc: 'Deep-dive analysis into corporate trading portfolios.' },
              { title: 'Token Engine', desc: 'Flexible credit infrastructure for premium querying.' }
            ].map((f, i) => (
              <div key={i} className="bg-white p-6 rounded-3xl border border-slate-100 shadow-xl shadow-slate-200/40 hover:-translate-y-1 transition-transform">
                <div className="w-10 h-10 bg-emerald-100 text-emerald-600 flex items-center justify-center rounded-xl mb-4 text-xl font-bold">✓</div>
                <h4 className="font-bold text-slate-900 mb-2">{f.title}</h4>
                <p className="text-sm text-slate-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-24 bg-slate-900 rounded-[2.5rem] p-12 text-center relative overflow-hidden shadow-2xl">
          <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-blue-500/10 mix-blend-overlay"></div>
          <div className="relative z-10">
            <h2 className="text-3xl md:text-4xl font-extrabold text-white mb-4">Master Your Supply Chain</h2>
            <p className="text-slate-400 text-lg mb-10 max-w-2xl mx-auto">Deploy advanced queries to isolate high-value global counterparties instantly.</p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <button
                onClick={() => navigate('/trade-directory/find-suppliers')}
                className="px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-bold rounded-2xl transition-all shadow-lg shadow-emerald-500/20"
              >
                Scan Global Directory
              </button>
              <button
                onClick={() => navigate('/subscription')}
                className="px-8 py-4 bg-slate-800 hover:bg-slate-700 text-white font-bold rounded-2xl border border-slate-700 transition-all"
              >
                Review Capabilities
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
