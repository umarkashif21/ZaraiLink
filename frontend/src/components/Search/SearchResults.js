import React, { useEffect, useState, useCallback } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Filter, BarChart2, Package, ChevronRight, AlertCircle } from 'lucide-react';
import Navbar from '../Layout/Navbar';
import '../Dashboard/Dashboard.css';
import searchService from '../../services/searchService';
import SummaryView from './SummaryView';
import DataDashboard from './DataDashboard';

const API_BASE = process.env.REACT_APP_API_BASE_URL;

const SearchResults = () => {
    const location = useLocation();
    const navigate = useNavigate();

    // Derive everything from location.search so drill-down navigation works correctly.
    // We re-read these on every render (location changes on every navigation).
    const getParams = () => new URLSearchParams(location.search);
    const _p = getParams();
    const initialQuery      = _p.get('q') || '';
    const initialScope      = _p.get('scope') || null;            // null = no scope (HS code mode)
    const initialHsCode     = _p.get('hs_code') || null;
    const initialSubcatId   = _p.get('subcat_id') || null;
    const initialVariantName = _p.get('variant_name') || null;
    const initialIntent     = _p.get('intent') || null;
    const isDashboardMode   = _p.get('mode') === 'dashboard'; // Forced by SummaryView "View Trade Data" click

    const [query, setQuery]               = useState(initialQuery);
    const [inputValue, setInputValue]     = useState(initialQuery); // Local draft — does NOT trigger search
    const [scope, setScope]               = useState(initialScope);
    const [hsCode, setHsCode]             = useState(initialHsCode);
    const [subcatId, setSubcatId]         = useState(initialSubcatId);
    const [variantName, setVariantName]   = useState(initialVariantName);
    const [overrideIntent, setOverrideIntent] = useState(initialIntent);

    // KEY FIX: sync state from URL whenever the user navigates (e.g. drill-down click)
    useEffect(() => {
        const p = new URLSearchParams(location.search);
        const newQuery = p.get('q') || '';
        setQuery(newQuery);
        setInputValue(newQuery); // Keep the search bar in sync with URL navigations
        setScope(p.get('scope') || null);
        setHsCode(p.get('hs_code') || null);
        setSubcatId(p.get('subcat_id') || null);
        setVariantName(p.get('variant_name') || null);
        setOverrideIntent(p.get('intent') || null);
    }, [location.search]);

    // Strict check: true if no scope is selected (dedicated HS/Category mode), 
    // OR if it's purely digits/dots, OR if it's an exact category bridge match.
    const isRawHsCodeMode = (!scope || scope === 'null') || (query && hsCode && query === hsCode) || (query ? /^[\d.]+$/.test(query) : false);

    const [sortBy, setSortBy] = useState('relevance');

    const [priceMin, setPriceMin] = useState(_p.get('price_min') || '');
    const [priceMax, setPriceMax] = useState(_p.get('price_max') || '');
    const [volumeMin, setVolumeMin] = useState(_p.get('volume_min') || '');

    const [tempCountry, setTempCountry] = useState(_p.get('country') || '');
    const [tempPriceMin, setTempPriceMin] = useState(_p.get('price_min') || '');
    const [tempPriceMax, setTempPriceMax] = useState(_p.get('price_max') || '');
    const [tempVolumeMin, setTempVolumeMin] = useState(_p.get('volume_min') || '');

    const [results, setResults] = useState([]);
    const [marketSnapshot, setMarketSnapshot] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [parsedIntent, setParsedIntent] = useState('BUY');
    const [needsDisambig, setNeedsDisambig] = useState(false);
    const [isBroadSearch, setIsBroadSearch] = useState(false);
    const [parsedQueryInfo, setParsedQueryInfo] = useState(null);
    const [variants, setVariants] = useState([]);
    const [disambigPage, setDisambigPage] = useState(1);
    const DISAMBIG_PAGE_SIZE = 12;
    const [availableCountries, setAvailableCountries] = useState([]);
    const [selectedCountry, setSelectedCountry] = useState(null);
    const [searchEngine, setSearchEngine] = useState('');

    // ── Comparison State ───────────────────────────────────────────────────
    const [selectedSuppliers, setSelectedSuppliers] = useState([]);

    const toggleCompare = (supplierName) => {
        setSelectedSuppliers(prev => {
            if (prev.includes(supplierName)) {
                return prev.filter(name => name !== supplierName);
            }
            if (prev.length >= 4) {
                alert("You can only compare up to 4 suppliers at once.");
                return prev;
            }
            return [...prev, supplierName];
        });
    };

    const handleRawTabClick = (newScope, newIntent) => {
        setScope(newScope);
        setOverrideIntent(newIntent);
        
        // Update URL
        const params = new URLSearchParams(location.search);
        params.set('scope', newScope);
        params.set('intent', newIntent);
        navigate(`/search/results?${params.toString()}`, { replace: true });
    };

    const fetchResults = useCallback(async () => {
        if (!query || isRawHsCodeMode) return;
        setLoading(true);
        setError(null);
        try {
            const filters = {};
            // Only send scope for non-HS-code searches or when a pill tab was clicked
            if (scope) filters.scope = scope;
            if (hsCode) filters.hs_code = hsCode;
            if (subcatId) filters.subcat_id = subcatId;
            if (variantName) filters.variant_name = variantName;
            if (selectedCountry) filters.country = selectedCountry;
            if (overrideIntent) filters.intent = overrideIntent;

            const data = await searchService.search(query, filters);

            if (data.is_category_bridge) {
                // Backend matched an exact category! Fast-track to HS Code navigation.
                const params = new URLSearchParams({ q: data.hs_code, hs_code: data.hs_code });
                navigate(`/search/results?${params.toString()}`, { replace: true });
                return;
            }

            if (data.needs_disambiguation) {
                setNeedsDisambig(true);
                setIsBroadSearch(false);
                setVariants(data.variants || []);
                setDisambigPage(1);  // reset to first page on new disambiguation
                setResults([]);
                setMarketSnapshot(null);
                setParsedQueryInfo(data.parsed_query || null);
            } else if (data.is_broad_search) {
                setNeedsDisambig(false);
                setIsBroadSearch(true);
                setVariants([]);
                setResults([]);
                setMarketSnapshot(null);
            } else {
                setNeedsDisambig(false);
                setIsBroadSearch(false);
                setVariants([]);
                setResults(data.results || []);
                setMarketSnapshot(data.market_snapshot);
                setSearchEngine(data.search_engine || '');
                if (data.parsed_query?.intent) {
                    // Only update parsedIntent if backend returns a definite intent
                    // AND we don't already have overrideIntent or explicit intent
                    const backendIntent = data.parsed_query.intent;
                    if (backendIntent && backendIntent !== 'UNKNOWN') {
                        setParsedIntent(backendIntent);
                    } else {
                        setParsedIntent('UNKNOWN');
                    }
                } else if (!overrideIntent) {
                    // No backend intent and no override — stay UNKNOWN to show pills
                    setParsedIntent('UNKNOWN');
                }
                const countries = [
                    ...new Set((data.results || []).map(s => s.country).filter(Boolean))
                ].sort();
                setAvailableCountries(countries);
            }
        } catch (err) {
            console.error('Search failed', err);
            setError('Failed to fetch search results. Please try again.');
        } finally {
            setLoading(false);
        }
    }, [query, scope, hsCode, subcatId, variantName, selectedCountry, overrideIntent]);

    useEffect(() => {
        fetchResults();
    }, [fetchResults]);

    // ── When user picks a variant from the disambiguation panel ───────────
    const handleVariantPick = (variant) => {
        // Drill-down node (e.g. '1702') — navigate tree, don't go to results yet
        if (variant.is_drill_down) {
            const params = new URLSearchParams({ q: variant.hs_code, hs_code: variant.hs_code });
            navigate(`/search/results?${params.toString()}`);
            return;
        }

        // For HS code flows, do NOT send scope — the 4-tab pill UI handles direction.
        const queryParamsObj = {
            q: query,
            hs_code: variant.hs_code,
            subcat_id: variant.id,
            variant_name: variant.name,
        };

        // Only carry scope for normal text searches
        if (!isRawHsCodeMode && scope) {
            queryParamsObj.scope = scope;
        }

        // Preserve external country constraint
        if (selectedCountry) {
            queryParamsObj.country = selectedCountry;
        } else if (parsedQueryInfo && parsedQueryInfo.country) {
            queryParamsObj.country = parsedQueryInfo.country;
        } else if (_p.get('country')) {
            queryParamsObj.country = _p.get('country');
        }

        const params = new URLSearchParams(queryParamsObj);
        navigate(`/search/results?${params.toString()}`);
        setHsCode(variant.hs_code);
        setSubcatId(String(variant.id));
        setVariantName(variant.name);
        setNeedsDisambig(false);
    };

    // ── New search from top bar ────────────────────────────────────────────
    const handleSearch = (e) => {
        e.preventDefault();
        const trimmedInput = inputValue.trim();
        if (!trimmedInput) return; // Don't search on empty input
        setSelectedCountry(null);
        setPriceMin('');
        setPriceMax('');
        setVolumeMin('');
        setTempCountry('');
        setTempPriceMin('');
        setTempPriceMax('');
        setTempVolumeMin('');
        setHsCode(null);
        setSubcatId(null);      // Clear variant pin from previous disambiguation click
        setVariantName(null);   // Clear variant name pin from previous disambiguation click
        setOverrideIntent(null);
        
        const params = new URLSearchParams();
        params.set('q', trimmedInput);
        if (scope && scope !== 'null') {
            params.set('scope', scope);
        }
        navigate(`/search/results?${params.toString()}`);
        // Note: setQuery will be synced via the location.search useEffect above
    };

    const applyFilters = () => {
        setSelectedCountry(tempCountry || null);
        setPriceMin(tempPriceMin);
        setPriceMax(tempPriceMax);
        setVolumeMin(tempVolumeMin);
    };

    const clearFilters = () => {
        setSelectedCountry(null);
        setPriceMin('');
        setPriceMax('');
        setVolumeMin('');
        setTempCountry('');
        setTempPriceMin('');
        setTempPriceMax('');
        setTempVolumeMin('');
    };

    // ── Entity type label ──────────────────────────────────────────────────
    const activeIntent = overrideIntent || parsedIntent;
    
    // Only show pills if scope is missing, OR if the intent couldn't be detected (UNKNOWN).
    // If we have both a valid scope and a known intent, hide the pills.
    const showPills = !scope || scope === 'null' || activeIntent === 'UNKNOWN';
    
    const entityLabel = activeIntent === 'SELL' ? 'Buyers'
        : activeIntent === 'UNKNOWN' ? 'Suppliers & Buyers'
        : 'Suppliers';

    // ── Local Frontend Filtering & Sorting ─────────────────────────────────
    let sortedResults = results.filter((r) => {
        if (selectedCountry && r.country !== selectedCountry) return false;
        if (priceMin && r.avg_price < parseFloat(priceMin)) return false;
        if (priceMax && r.avg_price > parseFloat(priceMax)) return false;
        if (volumeMin && r.total_volume < parseFloat(volumeMin)) return false;
        return true;
    });

    if (sortBy === 'price_asc') {
        sortedResults.sort((a, b) => (a.avg_price || Infinity) - (b.avg_price || Infinity));
    } else if (sortBy === 'price_desc') {
        sortedResults.sort((a, b) => (b.avg_price || 0) - (a.avg_price || 0));
    } else if (sortBy === 'volume_desc') {
        sortedResults.sort((a, b) => (b.total_volume || 0) - (a.total_volume || 0));
    }

    useEffect(() => {
        if (priceMin || priceMax) {
            console.log(`[FILTER] Price range applied: $${priceMin || '0'}-$${priceMax || 'any'}, suppliers before: ${results.length}, after: ${sortedResults.length}`);
        }
    }, [priceMin, priceMax, results.length, sortedResults.length]);

    // ── HS Code Dual-Track Routing ─────────────────────────────────────────
    // Leaf HS codes in our DB are always 7 raw digits (e.g. 1701.991 = 1701991).
    // Anything with fewer than 7 digits — even if it has a dot (e.g. 1704.9 = 5 digits)
    // — is still a navigational parent and should show SummaryView.
    if (isRawHsCodeMode) {
        const queryDigits = (hsCode || query).replace(/\./g, '');
        const isNumeric = /^\d+$/.test(queryDigits);
        
        if (isDashboardMode || (isNumeric && queryDigits.length >= 7)) {
            // Leaf numeric code OR forced dashboard mode → go straight to DataDashboard
            return <DataDashboard />;
        } else if (queryDigits.length > 0) {
            // Still navigating (short numeric code or an alphabet category name like "Other")
            return <SummaryView />;
        }
    }

    return (
        <div className="dashboard-wrapper">
            <Navbar />

            {/* Search bar */}
            <div className="bg-white border-b-2 border-gray-100 sticky top-0 z-10 shadow-sm">
                <div className="dashboard-container" style={{ padding: '1rem 2rem', maxWidth: '1400px', margin: '0 auto' }}>
                    <form onSubmit={handleSearch} className="w-full relative">
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            className="w-full pl-4 pr-10 py-3 rounded-full border-2 border-gray-200 focus:border-emerald-500 focus:ring-0 transition-all font-medium text-gray-700 placeholder-gray-400"
                            placeholder="Search again..."
                            style={{ fontSize: '1rem' }}
                        />
                    </form>
                </div>
            </div>

            <div className="dashboard-container flex gap-8" style={{ paddingTop: '2rem' }}>

                {/* Left Sidebar: Filters (hidden during disambiguation) */}
                {!needsDisambig && (
                    <aside className="w-64 hidden md:block space-y-6 flex-shrink-0">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-bold text-gray-700 flex items-center gap-2 text-lg">
                                <Filter size={20} /> Filters
                            </h3>
                            {selectedCountry && (
                                <button onClick={clearFilters} className="text-sm text-emerald-600 hover:text-emerald-800 font-medium">
                                    Reset
                                </button>
                            )}
                        </div>

                        {availableCountries.length > 0 && (
                            <div className="border-b-2 border-gray-100 pb-4">
                                <h4 className="text-sm font-bold text-gray-700 py-2">Country</h4>
                                <select
                                    value={tempCountry}
                                    onChange={(e) => setTempCountry(e.target.value)}
                                    className="w-full mt-2 block rounded-lg border-2 border-gray-200 py-2 pl-2 pr-8 text-sm focus:border-emerald-500 focus:outline-none"
                                >
                                    <option value="">All Countries</option>
                                    {availableCountries.map(c => (
                                        <option key={c} value={c}>{c}</option>
                                    ))}
                                </select>
                            </div>
                        )}

                        <div className="border-b-2 border-gray-100 pb-4">
                            <h4 className="text-sm font-bold text-gray-700 py-2">Price Range ($/MT)</h4>
                            <div className="flex items-center gap-2 mt-2">
                                <input
                                    type="number"
                                    placeholder="Min"
                                    value={tempPriceMin}
                                    onChange={(e) => setTempPriceMin(e.target.value)}
                                    className="w-full rounded-lg border-2 border-gray-200 py-2 px-2 text-sm focus:border-emerald-500 focus:outline-none"
                                />
                                <span className="text-gray-400 font-bold">-</span>
                                <input
                                    type="number"
                                    placeholder="Max"
                                    value={tempPriceMax}
                                    onChange={(e) => setTempPriceMax(e.target.value)}
                                    className="w-full rounded-lg border-2 border-gray-200 py-2 px-2 text-sm focus:border-emerald-500 focus:outline-none"
                                />
                            </div>
                        </div>

                        <div className="border-b-2 border-gray-100 pb-4">
                            <h4 className="text-sm font-bold text-gray-700 py-2">Min. Trade Volume (MT)</h4>
                            <div className="mt-2">
                                <input
                                    type="number"
                                    placeholder="e.g. 500"
                                    value={tempVolumeMin}
                                    onChange={(e) => setTempVolumeMin(e.target.value)}
                                    className="w-full rounded-lg border-2 border-gray-200 py-2 px-3 text-sm focus:border-emerald-500 focus:outline-none"
                                />
                            </div>
                        </div>

                        <button
                            onClick={applyFilters}
                            className="w-full py-2.5 bg-emerald-600 outline outline-emerald-700 hover:bg-emerald-700 text-white font-bold rounded-xl transition-all shadow-sm"
                        >
                            Apply Filters
                        </button>
                    </aside>
                )}

                {/* Main Content */}
                <main className="flex-1 space-y-4">

                    {/* ── Broad Search Warning ──────────────────────────── */}
                    {isBroadSearch && !loading && (
                        <div className="text-center py-16 text-gray-400 bg-white rounded-xl border-2 border-amber-100 p-8 shadow-sm">
                            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🌐</div>
                            <h2 className="text-xl font-bold text-gray-900 mb-2">Search is too broad</h2>
                            <p className="font-medium text-gray-500 max-w-md mx-auto">
                                No specific high-confidence product match was found for "{query}".
                                Try being more specific with the product name.
                            </p>
                        </div>
                    )}

                    {/* ── Disambiguation Panel ───────────────────────────── */}
                    {needsDisambig && !loading && (
                        <div>
                            <div className="flex items-center gap-3 mb-6">
                                <AlertCircle size={22} className="text-amber-500" />
                                <div>
                                    <h2 className="text-xl font-bold text-gray-900">
                                        Multiple products matched "{query}"
                                    </h2>
                                    <p className="text-sm text-gray-500 mt-0.5">
                                        Select the exact product you're looking for to see accurate prices and suppliers.
                                    </p>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {variants
                                    .slice((disambigPage - 1) * DISAMBIG_PAGE_SIZE, disambigPage * DISAMBIG_PAGE_SIZE)
                                    .map((v) => (
                                    <button
                                        key={v.hs_code + (v.id || 'drill')}
                                        onClick={() => handleVariantPick(v)}
                                        className="text-left p-5 bg-white rounded-xl border-2 border-gray-100 hover:border-emerald-500 hover:shadow-md transition-all group"
                                        style={{ cursor: 'pointer' }}
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <div>
                                                <div className="flex items-center gap-2 mb-1.5">
                                                    <Package size={16} className="text-emerald-500 flex-shrink-0" />
                                                    <span className="font-bold text-gray-900 group-hover:text-emerald-700 transition-colors text-sm">
                                                        {v.name}
                                                    </span>
                                                </div>
                                                <div className="text-xs text-gray-400">
                                                    {v.category ? `${v.category} · ` : ''}HS {v.hs_code}
                                                </div>
                                            </div>
                                            <div className="flex flex-col items-end gap-1">
                                                {v.is_drill_down && (
                                                    <span className="text-xs font-bold text-indigo-500 bg-indigo-50 rounded-full px-2 py-0.5">Drill Down ›</span>
                                                )}
                                                <ChevronRight size={16} className="text-gray-300 group-hover:text-emerald-500 flex-shrink-0 mt-1" />
                                            </div>
                                        </div>
                                    </button>
                                ))}
                            </div>

                            {/* Pagination Controls */}
                            {variants.length > DISAMBIG_PAGE_SIZE && (
                                <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-100">
                                    <p className="text-sm text-gray-500">
                                        Showing {((disambigPage - 1) * DISAMBIG_PAGE_SIZE) + 1}–{Math.min(disambigPage * DISAMBIG_PAGE_SIZE, variants.length)} of {variants.length} matches
                                    </p>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setDisambigPage(p => Math.max(1, p - 1))}
                                            disabled={disambigPage === 1}
                                            className="px-4 py-2 rounded-lg border-2 border-gray-200 text-sm font-bold text-gray-600 hover:border-emerald-500 hover:text-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                                        >
                                            ← Prev
                                        </button>
                                        {Array.from({ length: Math.ceil(variants.length / DISAMBIG_PAGE_SIZE) }, (_, i) => i + 1)
                                            .filter(p => Math.abs(p - disambigPage) <= 2)
                                            .map(p => (
                                                <button
                                                    key={p}
                                                    onClick={() => setDisambigPage(p)}
                                                    className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                                                        p === disambigPage
                                                            ? 'bg-emerald-600 text-white border-2 border-emerald-600'
                                                            : 'border-2 border-gray-200 text-gray-600 hover:border-emerald-500 hover:text-emerald-700'
                                                    }`}
                                                >
                                                    {p}
                                                </button>
                                            ))
                                        }
                                        <button
                                            onClick={() => setDisambigPage(p => Math.min(Math.ceil(variants.length / DISAMBIG_PAGE_SIZE), p + 1))}
                                            disabled={disambigPage >= Math.ceil(variants.length / DISAMBIG_PAGE_SIZE)}
                                            className="px-4 py-2 rounded-lg border-2 border-gray-200 text-sm font-bold text-gray-600 hover:border-emerald-500 hover:text-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                                        >
                                            Next →
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* ── Normal Results ─────────────────────────────────── */}
                    {!needsDisambig && !isBroadSearch && (
                        <div className="flex flex-col">

                            {/* ── Tab Pill Buttons for Intent Mapping ──────────────── */}
                            {showPills && (
                                <div className="mb-6">
                                    <h3 className="text-gray-500 font-bold uppercase tracking-wide text-xs mb-3">Select Trade Direction</h3>
                                    <div className="flex flex-wrap gap-3">
                                        <button
                                            onClick={() => handleRawTabClick('IMPORT', 'BUY')}
                                            className={`px-5 py-2.5 rounded-full font-bold text-sm transition-all shadow-sm ${scope === 'IMPORT' && overrideIntent === 'BUY' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:border-indigo-500 hover:text-indigo-600'}`}
                                        >
                                            Foreign Suppliers
                                        </button>
                                        <button
                                            onClick={() => handleRawTabClick('EXPORT', 'SELL')}
                                            className={`px-5 py-2.5 rounded-full font-bold text-sm transition-all shadow-sm ${scope === 'EXPORT' && overrideIntent === 'SELL' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:border-indigo-500 hover:text-indigo-600'}`}
                                        >
                                            Foreign Buyers
                                        </button>
                                        <button
                                            onClick={() => handleRawTabClick('IMPORT', 'SELL')}
                                            className={`px-5 py-2.5 rounded-full font-bold text-sm transition-all shadow-sm ${scope === 'IMPORT' && overrideIntent === 'SELL' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:border-indigo-500 hover:text-indigo-600'}`}
                                        >
                                            Pakistani Buyers
                                        </button>
                                        <button
                                            onClick={() => handleRawTabClick('EXPORT', 'BUY')}
                                            className={`px-5 py-2.5 rounded-full font-bold text-sm transition-all shadow-sm ${scope === 'EXPORT' && overrideIntent === 'BUY' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:border-indigo-500 hover:text-indigo-600'}`}
                                        >
                                            Pakistani Suppliers
                                        </button>
                                    </div>
                                </div>
                            )}

                            <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                                <h2 className="text-2xl font-bold text-gray-800 font-primary">
                                    {loading ? 'Searching...' : (() => {
                                        if (activeIntent === 'UNKNOWN') {
                                            const supplierCount = sortedResults.filter(r => r.type === 'Supplier').length;
                                            const buyerCount = sortedResults.filter(r => r.type === 'Buyer').length;
                                            return `${supplierCount} Suppliers & ${buyerCount} Buyers found for "${query}"`;
                                        }
                                        return `${sortedResults.length} ${entityLabel} found for "${query}"`;
                                    })()}
                                </h2>

                                {!loading && !error && sortedResults.length > 0 && (
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-medium text-gray-500">Sort by:</span>
                                        <select
                                            value={sortBy}
                                            onChange={(e) => setSortBy(e.target.value)}
                                            className="rounded-lg border-2 border-gray-200 py-1.5 pl-3 pr-8 text-sm focus:border-emerald-500 focus:outline-none font-medium text-gray-700 bg-white"
                                        >
                                            <option value="relevance">Relevance</option>
                                            <option value="price_asc">Price: Low to High</option>
                                            <option value="price_desc">Price: High to Low</option>
                                            <option value="volume_desc">Volume: Highest First</option>
                                        </select>
                                    </div>
                                )}
                            </div>

                            {loading && (
                                <div className="text-center py-16 text-gray-400">
                                    <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🔍</div>
                                    <p className="font-medium">Searching trade records...</p>
                                </div>
                            )}

                            {error && (
                                <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
                                    {error}
                                </div>
                            )}

                            {!loading && !error && sortedResults.length === 0 && (
                                <div className="text-center py-16 text-gray-400">
                                    <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📭</div>
                                    <p className="font-medium text-gray-600">No {entityLabel.toLowerCase()} found matching your filters</p>
                                    <p className="text-sm mt-1">Try adjusting the price, volume, or country.</p>
                                </div>
                            )}

                            {!loading && !error && sortedResults.map((supplier, idx) => (
                                <div
                                    key={idx}
                                    className="action-card bg-white mb-4 hover:border-emerald-500 transition-all cursor-default relative overflow-visible group"
                                    style={{ padding: '1.5rem', marginBottom: '1.5rem' }}
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <h3 className="text-xl font-bold text-gray-900 group-hover:text-emerald-700 transition-colors">
                                                    {supplier.name}
                                                </h3>
                                            </div>
                                            <div className="text-sm text-gray-500 mb-4 font-medium">{supplier.country}</div>

                                            <div className="flex gap-8 text-sm text-gray-700">
                                                <div>
                                                    <span className="block text-gray-400 text-xs uppercase font-bold tracking-wider">Avg Price</span>
                                                    <span className="font-bold text-lg text-gray-800">${supplier.avg_price.toFixed(2)}/MT</span>
                                                </div>
                                                <div>
                                                    <span className="block text-gray-400 text-xs uppercase font-bold tracking-wider">Volume</span>
                                                    <span className="font-bold text-lg text-gray-800">{supplier.total_volume.toLocaleString()} MT</span>
                                                </div>
                                                <div>
                                                    <span className="block text-gray-400 text-xs uppercase font-bold tracking-wider">Shipments</span>
                                                    <span className="font-bold text-lg text-gray-800">{supplier.shipment_count}</span>
                                                </div>
                                                {supplier.volume_fit !== 'N/A' && supplier.volume_fit && (
                                                    <div>
                                                        <span className="block text-gray-400 text-xs uppercase font-bold tracking-wider">Volume Fit</span>
                                                        <span className={`font-bold text-sm ${supplier.volume_fit === 'Strong' ? 'text-emerald-600' :
                                                            supplier.volume_fit === 'Good' ? 'text-blue-600' :
                                                                supplier.volume_fit === 'Partial' ? 'text-amber-600' : 'text-gray-500'
                                                            }`}>{supplier.volume_fit}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        <div className="flex flex-col gap-3">
                                            <Link
                                                to={`/search/supplier/${encodeURIComponent(supplier.name)}?q=${encodeURIComponent(query)}&scope=${encodeURIComponent(scope)}${subcatId ? `&subcat_id=${encodeURIComponent(subcatId)}` : ''}${variantName ? `&variant_name=${encodeURIComponent(variantName)}` : ''}${overrideIntent ? `&intent=${encodeURIComponent(overrideIntent)}` : ''}`}
                                                className="stat-action text-center"
                                                style={{ textDecoration: 'none' }}
                                            >
                                                View Deal
                                            </Link>
                                            <button
                                                onClick={() => toggleCompare(supplier.name)}
                                                className={`px-4 py-2 border-2 text-sm font-bold rounded-md transition-colors ${selectedSuppliers.includes(supplier.name)
                                                        ? 'bg-emerald-50 border-emerald-500 text-emerald-700'
                                                        : 'bg-white border-gray-200 text-gray-700 hover:border-emerald-500 hover:text-emerald-600'
                                                    }`}>
                                                {selectedSuppliers.includes(supplier.name) ? 'Added ✓' : 'Compare'}
                                            </button>
                                        </div>
                                    </div>

                                    <div className="mt-5 pt-4 border-t-2 border-gray-50 flex items-center text-xs text-gray-400 gap-4 font-medium">
                                        <span className="flex items-center gap-1">
                                            <BarChart2 size={14} /> Based on {supplier.shipment_count} shipments
                                        </span>
                                        <span>Last active: {supplier.last_shipment_date}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </main>

                {/* Right Panel: Market Snapshot */}
                {!needsDisambig && (
                    <aside className="w-72 hidden lg:block space-y-6 flex-shrink-0">
                        {marketSnapshot && (
                            <div className="stat-card flex-col items-start gap-4">
                                <h4 className="font-bold text-gray-800 mb-2 w-full border-b-2 border-gray-100 pb-2">Market Snapshot</h4>
                                <div className="space-y-4 w-full">
                                    <div>
                                        <div className="text-xs text-gray-500 uppercase font-bold">Global Avg Price</div>
                                        <div className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Courier New, monospace' }}>
                                            ${marketSnapshot.avg_price_global.toFixed(2)}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500 uppercase font-bold">
                                            {activeIntent === 'SELL' ? 'Top Destination' : 'Top Origin'}
                                        </div>
                                        <div className="text-lg font-bold text-gray-900">{marketSnapshot.top_country}</div>
                                    </div>
                                    {searchEngine && (
                                        <div className="text-xs text-gray-400 pt-2 border-t border-gray-100">
                                            Powered by {searchEngine === 'opensearch' ? '🏎 OpenSearch' : '🗄 Trade DB'}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </aside>
                )}
            </div>

            {/* ── Sticky Compare Bar ────────────────────────────────────────────── */}
            {selectedSuppliers.length > 0 && (
                <div className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-gray-200 shadow-[0_-4px_20px_rgba(0,0,0,0.05)] p-4 z-50 transform transition-transform duration-300">
                    <div className="max-w-7xl mx-auto flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="h-10 w-10 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600">
                                <BarChart2 size={20} />
                            </div>
                            <div>
                                <p className="text-sm text-gray-500 font-bold uppercase tracking-wider">Comparing</p>
                                <p className="text-gray-900 font-bold">
                                    {selectedSuppliers[0]}
                                    {selectedSuppliers.length > 1 && <span className="text-emerald-600 ml-1">(+{selectedSuppliers.length - 1} more)</span>}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => setSelectedSuppliers([])}
                                className="px-4 py-2 text-sm font-bold text-gray-500 hover:text-gray-800 transition-colors"
                            >
                                Clear
                            </button>
                            <Link
                                to={`/search/compare?suppliers=${encodeURIComponent(selectedSuppliers.join(','))}&q=${encodeURIComponent(query)}&scope=${encodeURIComponent(scope)}&intent=${encodeURIComponent(parsedIntent)}${subcatId ? `&subcat_id=${encodeURIComponent(subcatId)}` : ''}${variantName ? `&variant_name=${encodeURIComponent(variantName)}` : ''}`}
                                className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold rounded-lg shadow-md transition-all flex items-center gap-2"
                                style={{ textDecoration: 'none' }}
                            >
                                Compare Now <ChevronRight size={16} />
                            </Link>
                        </div>
                    </div>
                </div>
            )}

        </div>
    );
};

export default SearchResults;
