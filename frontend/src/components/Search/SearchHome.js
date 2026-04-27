import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X, ChevronRight, Hash, Package, Zap } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_BASE_URL;

const SearchHome = () => {
    const [query, setQuery] = useState('');
    const [scope, setScope] = useState('WORLDWIDE');
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [selectedHsCode, setSelectedHsCode] = useState(null);
    const [selectedProductName, setSelectedProductName] = useState(null);
    const [loadingSuggestions, setLoadingSuggestions] = useState(false);
    const navigate = useNavigate();
    const debounceRef = useRef(null);
    const inputRef = useRef(null);
    const suggestionsRef = useRef(null);

    // Dynamic search mode detection
    const searchMode = (() => {
        if (!query.trim()) return null;
        if (/^[\d.]+$/.test(query.trim())) return 'hscode';
        if (scope && scope !== 'WORLDWIDE') return 'ai';
        return 'product';
    })();

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
        }, 250); // 250ms debounce — feels instant

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
        // Non-leaf (drill-down) HS code — just update the input to let user drill further
        if (suggestion.is_final !== undefined && !suggestion.is_final) {
            setQuery(suggestion.hs_code);
            setSelectedHsCode(suggestion.hs_code);
            setSelectedProductName(null);
            // Keep suggestions open so user can drill down
            return;
        }

        // Leaf product with a specific human-readable name (e.g. "Dextrose Anhydrous")
        // → navigate as a text search so we get results filtered to that exact product.
        // This uses the proven text-search + variant_name backend path rather than
        // the HS-level DataDashboard which would show all 1702.3000 products.
        if (suggestion.is_final !== undefined && suggestion.is_final) {
            setQuery(suggestion.name);
            setSelectedHsCode(suggestion.hs_code);
            setSelectedProductName(suggestion.name);
            setShowSuggestions(false);
            const params = new URLSearchParams({
                q:            suggestion.name,
                hs_code:      suggestion.hs_code,
                variant_name: suggestion.name,
                scope:        scope || 'IMPORT',   // default to IMPORT so pills appear
            });
            navigate(`/search/results?${params.toString()}`);
            return;
        }

        // Plain text autocomplete (no is_final metadata)
        setQuery(suggestion.name);
        setSelectedHsCode(suggestion.hs_code);
        setSelectedProductName(suggestion.name);
        setShowSuggestions(false);
        inputRef.current?.focus();
    };

    const handleSearch = (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        const isHsCode = /^[\d.]+$/.test(query.trim());
        const params = new URLSearchParams({ q: query });

        if (isHsCode) {
            // HS Code search: skip scope — 4-tab pill UI handles direction
            params.set('hs_code', selectedHsCode || query.trim());
        } else {
            params.set('scope', scope);
            if (selectedHsCode) params.set('hs_code', selectedHsCode);
            if (selectedProductName) params.set('variant_name', selectedProductName);
        }
        navigate(`/search/results?${params.toString()}`);
    };

    const handlePillClick = (text) => {
        setQuery(text);
        setSelectedHsCode(null);
        setSelectedProductName(null);
    };

    const clearQuery = () => {
        setQuery('');
        setSelectedHsCode(null);
        setSelectedProductName(null);
        setSuggestions([]);
        setShowSuggestions(false);
        inputRef.current?.focus();
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
            <div className="max-w-3xl w-full text-center space-y-8">

                {/* Hero Text */}
                <h1 className="text-4xl md:text-5xl font-bold text-gray-900 tracking-tight">
                    What are you looking for today?
                </h1>

                {/* Search Bar + Autocomplete */}
                <form onSubmit={handleSearch} className="relative w-full max-w-2xl mx-auto">
                    <div className="relative group">
                        <input
                            ref={inputRef}
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                            placeholder="Try 'Import Dextrose Anhydrous from China under $700'..."
                            className="w-full h-14 pl-14 pr-24 rounded-full border-2 border-gray-200 shadow-sm focus:border-indigo-500 focus:ring-0 text-lg transition-all"
                            autoComplete="off"
                        />
                        <div className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-500 transition-colors">
                            <Search size={24} />
                        </div>

                        {/* Clear button */}
                        {query && (
                            <button
                                type="button"
                                onClick={clearQuery}
                                className="absolute right-[5.5rem] top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                            >
                                <X size={18} />
                            </button>
                        )}

                        <button
                            type="submit"
                            className="absolute right-2 top-2 bottom-2 px-6 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full font-medium transition-colors"
                        >
                            Search
                        </button>
                    </div>

                    {/* Product Disambiguation Banner */}
                    {selectedProductName && (
                        <div className="mt-2 flex items-center justify-center gap-2 text-sm text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-full py-1.5 px-4">
                            <span className="font-medium">Searching for:</span>
                            <span>{selectedProductName}</span>
                            <button
                                type="button"
                                onClick={clearQuery}
                                className="text-indigo-400 hover:text-indigo-600"
                            >
                                <X size={14} />
                            </button>
                        </div>
                    )}

                    {/* Search Mode Badge */}
                    {searchMode && !selectedProductName && (
                        <div className="mt-2 flex justify-center">
                            {searchMode === 'hscode' && (
                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-700 border border-blue-200">
                                    <Hash size={11} /> HS Code Mode — browsing by trade code
                                </span>
                            )}
                            {searchMode === 'product' && (
                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700 border border-emerald-200">
                                    <Package size={11} /> Product Search — browse matching variants
                                </span>
                            )}
                            {searchMode === 'ai' && (
                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-violet-100 text-violet-700 border border-violet-200">
                                    <Zap size={11} /> AI Query Mode — powered by natural language
                                </span>
                            )}
                        </div>
                    )}

                    {/* Autocomplete Dropdown */}
                    {showSuggestions && (
                        <div
                            ref={suggestionsRef}
                            className="absolute z-50 top-full mt-2 w-full bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden text-left"
                        >
                            <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wide border-b border-gray-50">
                                Product Matches
                            </div>
                            {suggestions.map((s, i) => (
                                <button
                                    key={s.hs_code + i}
                                    type="button"
                                    onClick={() => handleSelectSuggestion(s)}
                                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-indigo-50 transition-colors group"
                                >
                                    <div className="flex flex-col items-start text-left">
                                        <span className="font-medium text-gray-900 group-hover:text-indigo-700">
                                            {s.name}
                                        </span>
                                        <span className="text-xs text-gray-400">
                                            {s.category ? `${s.category} · ` : ''}HS {s.hs_code}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {s.total_volume > 0 && (
                                            <span className="text-xs text-gray-500 bg-gray-100 rounded-full px-2 py-0.5">
                                                {s.total_volume.toLocaleString()} MT
                                            </span>
                                        )}
                                        {s.is_final !== undefined && s.hs_code.replace('.', '').length < 8 && (
                                            <span className="text-xs font-bold text-indigo-500 bg-indigo-50 rounded-full px-2 py-0.5">
                                                Drill Down
                                            </span>
                                        )}
                                        <ChevronRight size={16} className="text-gray-300 group-hover:text-indigo-400" />
                                    </div>
                                </button>
                            ))}
                            {loadingSuggestions && (
                                <div className="px-4 py-3 text-sm text-gray-400 text-center">
                                    Searching products...
                                </div>
                            )}
                        </div>
                    )}
                </form>

                {/* Scope Toggle */}
                <div className="flex justify-center gap-2">
                    <button
                        type="button"
                        onClick={() => setScope('IMPORT')}
                        className={`px-6 py-2 rounded-full font-medium transition-all ${scope === 'IMPORT'
                            ? 'bg-indigo-600 text-white shadow-md'
                            : 'bg-white text-gray-600 border border-gray-200 hover:border-indigo-500'
                        }`}
                    >
                        Import
                    </button>
                    <button
                        type="button"
                        onClick={() => setScope('EXPORT')}
                        className={`px-6 py-2 rounded-full font-medium transition-all ${scope === 'EXPORT'
                            ? 'bg-indigo-600 text-white shadow-md'
                            : 'bg-white text-gray-600 border border-gray-200 hover:border-indigo-500'
                        }`}
                    >
                        Export
                    </button>
                </div>

                {/* Intent Pills */}
                <div className="flex flex-wrap justify-center gap-3">
                    {['I want to buy', 'I want to sell', 'Find suppliers', 'Find buyers'].map((pill) => (
                        <button
                            key={pill}
                            type="button"
                            onClick={() => handlePillClick(pill)}
                            className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm font-medium text-gray-600 hover:border-indigo-500 hover:text-indigo-600 transition-colors shadow-sm"
                        >
                            {pill}
                        </button>
                    ))}
                </div>

                {/* Example Queries */}
                <div className="pt-12 text-gray-500 text-sm">
                    <p className="mb-4 font-medium uppercase tracking-wide">Example Queries</p>
                    <div className="flex flex-wrap justify-center gap-4 text-gray-400">
                        <span>"Dextrose suppliers in Pakistan"</span>
                        <span>•</span>
                        <span>"Buy Urea 46%"</span>
                        <span>•</span>
                        <span>"Who sells PVC Resin?"</span>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default SearchHome;
