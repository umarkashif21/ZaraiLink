import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X, ChevronRight, Hash } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_BASE_URL;

// Matches bare HS codes typed directly: "17", "1702", "1702.4", "170230", etc.
const HS_CODE_RE = /^\d{2,}(\.\d*)?$/;
const isHsCode = (str) => HS_CODE_RE.test(str.trim());

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

    // Derived: is the current free-typed query a bare HS code?
    const queryIsHsCode = isHsCode(query) && !selectedHsCode;

    // ── Debounced autocomplete fetch ──────────────────────────────────────
    const fetchSuggestions = useCallback(async (q) => {
        if (q.length < 2) {
            setSuggestions([]);
            setShowSuggestions(false);
            return;
        }
        setLoadingSuggestions(true);
        try {
            const res = await fetch(
                `${API_BASE}/api/search/autocomplete/?q=${encodeURIComponent(q)}`
            );
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
        setSelectedHsCode(null);
        setSelectedProductName(null);
        clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => fetchSuggestions(query), 250);
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

        const params = new URLSearchParams({ q: query, scope });

        if (selectedHsCode) {
            // User clicked an autocomplete suggestion
            params.set('hs_code', selectedHsCode);
        } else if (queryIsHsCode) {
            // User typed a raw HS code directly (e.g. "1702.4") and pressed Search
            params.set('hs_code', query.trim());
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

    // ── Split suggestions into groups ─────────────────────────────────────
    const hsCodeSuggestions = suggestions.filter((s) => s.match_type === 'hs_code');
    const nameSuggestions   = suggestions.filter((s) => s.match_type !== 'hs_code');

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
                            placeholder="Try 'Dextrose suppliers' or an HS code like '1702.4'..."
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

                    {/* HS code hint strip (shown when dropdown is closed) */}
                    {queryIsHsCode && !showSuggestions && (
                        <div className="mt-2 flex items-center justify-center gap-2 text-sm text-teal-700 bg-teal-50 border border-teal-200 rounded-full py-1.5 px-4">
                            <Hash size={14} className="text-teal-500" />
                            <span>HS code detected — press Search to find matching products</span>
                        </div>
                    )}

                    {/* Selected-product confirmation banner */}
                    {selectedProductName && (
                        <div className="mt-2 flex items-center justify-center gap-2 text-sm text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-full py-1.5 px-4">
                            <span className="font-medium">Searching for:</span>
                            <span>{selectedProductName}</span>
                            {selectedHsCode && (
                                <span className="text-xs bg-teal-100 text-teal-700 rounded-full px-2 py-0.5 font-mono">
                                    HS {selectedHsCode}
                                </span>
                            )}
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
                            {/* ── HS code matches ── */}
                            {hsCodeSuggestions.length > 0 && (
                                <>
                                    <div className="px-4 py-2 text-xs font-semibold text-teal-600 uppercase tracking-wide border-b border-teal-50 flex items-center gap-1.5">
                                        <Hash size={11} />
                                        HS Code Matches
                                    </div>
                                    {hsCodeSuggestions.map((s, i) => (
                                        <SuggestionRow
                                            key={`hs-${s.hs_code}-${i}`}
                                            suggestion={s}
                                            onSelect={handleSelectSuggestion}
                                            isHsMatch
                                        />
                                    ))}
                                </>
                            )}

                            {/* ── Name matches ── */}
                            {nameSuggestions.length > 0 && (
                                <>
                                    <div
                                        className={`px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wide border-b border-gray-50 ${
                                            hsCodeSuggestions.length > 0 ? 'border-t border-gray-100' : ''
                                        }`}
                                    >
                                        Product Matches
                                    </div>
                                    {nameSuggestions.map((s, i) => (
                                        <SuggestionRow
                                            key={`nm-${s.hs_code}-${i}`}
                                            suggestion={s}
                                            onSelect={handleSelectSuggestion}
                                            isHsMatch={false}
                                        />
                                    ))}
                                </>
                            )}

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
                    {['WORLDWIDE', 'PAKISTAN'].map((s) => (
                        <button
                            key={s}
                            type="button"
                            onClick={() => setScope(s)}
                            className={`px-6 py-2 rounded-full font-medium transition-all ${
                                scope === s
                                    ? 'bg-indigo-600 text-white shadow-md'
                                    : 'bg-white text-gray-600 border border-gray-200 hover:border-indigo-500'
                            }`}
                        >
                            {s.charAt(0) + s.slice(1).toLowerCase()}
                        </button>
                    ))}
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
                        <span>•</span>
                        <span className="font-mono">"1702.4"</span>
                    </div>
                </div>

            </div>
        </div>
    );
};

// ── Reusable suggestion row ───────────────────────────────────────────────────
const SuggestionRow = ({ suggestion: s, onSelect, isHsMatch }) => (
    <button
        type="button"
        onClick={() => onSelect(s)}
        className={`w-full flex items-center justify-between px-4 py-3 transition-colors group ${
            isHsMatch ? 'hover:bg-teal-50' : 'hover:bg-indigo-50'
        }`}
    >
        <div className="flex flex-col items-start">
            <div className="flex items-center gap-2">
                <span
                    className={`font-medium text-gray-900 ${
                        isHsMatch ? 'group-hover:text-teal-700' : 'group-hover:text-indigo-700'
                    }`}
                >
                    {s.name}
                </span>
                {isHsMatch && (
                    <span className="inline-flex items-center gap-0.5 text-xs bg-teal-100 text-teal-700 rounded-full px-2 py-0.5 font-semibold">
                        <Hash size={10} />
                        HS
                    </span>
                )}
            </div>
            <span className="text-xs text-gray-400">
                {s.category} · <span className="font-mono">{s.hs_code}</span>
            </span>
        </div>
        <div className="flex items-center gap-3">
            {s.total_volume > 0 && (
                <span className="text-xs text-gray-500 bg-gray-100 rounded-full px-2 py-0.5">
                    {s.total_volume.toLocaleString()} MT
                </span>
            )}
            <ChevronRight
                size={16}
                className={`text-gray-300 ${
                    isHsMatch ? 'group-hover:text-teal-400' : 'group-hover:text-indigo-400'
                }`}
            />
        </div>
    </button>
);

export default SearchHome;
