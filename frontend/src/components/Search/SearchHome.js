import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X, ChevronRight } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

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
        setQuery(suggestion.name);
        setSelectedHsCode(suggestion.hs_code);
        setSelectedProductName(suggestion.name);
        setShowSuggestions(false);
        inputRef.current?.focus();
    };

    const handleSearch = (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        const params = new URLSearchParams({
            q: query,
            scope,
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
                                    <div className="flex flex-col items-start">
                                        <span className="font-medium text-gray-900 group-hover:text-indigo-700">
                                            {s.name}
                                        </span>
                                        <span className="text-xs text-gray-400">
                                            {s.category} · HS {s.hs_code}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {s.total_volume > 0 && (
                                            <span className="text-xs text-gray-500 bg-gray-100 rounded-full px-2 py-0.5">
                                                {s.total_volume.toLocaleString()} MT
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
                        onClick={() => setScope('WORLDWIDE')}
                        className={`px-6 py-2 rounded-full font-medium transition-all ${scope === 'WORLDWIDE'
                            ? 'bg-indigo-600 text-white shadow-md'
                            : 'bg-white text-gray-600 border border-gray-200 hover:border-indigo-500'
                        }`}
                    >
                        Worldwide
                    </button>
                    <button
                        type="button"
                        onClick={() => setScope('PAKISTAN')}
                        className={`px-6 py-2 rounded-full font-medium transition-all ${scope === 'PAKISTAN'
                            ? 'bg-indigo-600 text-white shadow-md'
                            : 'bg-white text-gray-600 border border-gray-200 hover:border-indigo-500'
                        }`}
                    >
                        Pakistan
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
