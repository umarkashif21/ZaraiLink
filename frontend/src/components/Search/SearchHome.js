import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Hash, Package, Zap } from 'lucide-react';

const SearchHome = () => {
    const [query, setQuery] = useState('');
    const [scope, setScope] = useState('WORLDWIDE');
    const navigate = useNavigate();
    const inputRef = useRef(null);

    const searchMode = (() => {
        if (!query.trim()) return null;
        if (/^[\d.]+$/.test(query.trim())) return 'hscode';
        if (scope && scope !== 'WORLDWIDE') return 'ai';
        return 'product';
    })();

    const handleSearch = (e) => {
        e.preventDefault();
        const trimmed = query.trim();
        if (!trimmed) return;

        const isHsCode = /^[\d.]+$/.test(trimmed);
        const params = new URLSearchParams({ q: trimmed });

        if (isHsCode) {
            params.set('hs_code', trimmed);
        } else {
            params.set('scope', scope);
        }
        navigate(`/search/results?${params.toString()}`);
    };

    const handlePillClick = (text) => {
        setQuery(text);
        inputRef.current?.focus();
    };

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
            <div className="max-w-3xl w-full text-center space-y-8">

                {/* Hero Text */}
                <h1 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight">
                    What are you looking for today?
                </h1>

                {/* Search Bar */}
                <form onSubmit={handleSearch} className="relative w-full max-w-2xl mx-auto">
                    <div className="relative group">
                        <input
                            ref={inputRef}
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Try 'Import Dextrose Anhydrous from China under $700'..."
                            className="w-full h-14 pl-14 pr-28 sm:pr-32 rounded-full border-2 border-slate-200 shadow-sm focus:border-emerald-500 focus:ring-0 text-lg text-slate-700 placeholder-slate-400 transition-all"
                            autoComplete="off"
                            aria-label="Search query"
                        />
                        <div className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-emerald-500 transition-colors">
                            <Search size={24} aria-hidden="true" />
                        </div>

                        <button
                            type="submit"
                            aria-label="Search"
                            className="absolute right-2 top-2 bottom-2 inline-flex items-center justify-center gap-1.5 px-5 sm:px-6 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white rounded-full font-bold text-sm shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-300"
                        >
                            <Search size={16} aria-hidden="true" />
                            <span className="hidden sm:inline">Search</span>
                        </button>
                    </div>

                    {/* Search Mode Badge */}
                    {searchMode && (
                        <div className="mt-3 flex justify-center">
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
                </form>

                {/* Scope Toggle */}
                <div className="flex justify-center gap-2">
                    <button
                        type="button"
                        onClick={() => setScope('IMPORT')}
                        className={`px-6 py-2 rounded-full font-medium transition-all ${scope === 'IMPORT'
                            ? 'bg-emerald-600 text-white shadow-md'
                            : 'bg-white text-slate-600 border border-slate-200 hover:border-emerald-500'
                        }`}
                    >
                        Import
                    </button>
                    <button
                        type="button"
                        onClick={() => setScope('EXPORT')}
                        className={`px-6 py-2 rounded-full font-medium transition-all ${scope === 'EXPORT'
                            ? 'bg-emerald-600 text-white shadow-md'
                            : 'bg-white text-slate-600 border border-slate-200 hover:border-emerald-500'
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
                            className="px-4 py-2 bg-white border border-slate-200 rounded-full text-sm font-medium text-slate-600 hover:border-emerald-500 hover:text-emerald-600 transition-colors shadow-sm"
                        >
                            {pill}
                        </button>
                    ))}
                </div>

                {/* Example Queries */}
                <div className="pt-12 text-slate-500 text-sm">
                    <p className="mb-4 font-medium uppercase tracking-wide">Example Queries</p>
                    <div className="flex flex-wrap justify-center gap-4 text-slate-400">
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
