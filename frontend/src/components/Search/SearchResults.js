import React, { useEffect, useState, useCallback } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Filter, BarChart2, Package, ChevronRight, AlertCircle, Lock, Zap, Search } from 'lucide-react';
import Navbar from '../Layout/Navbar';
import searchService from '../../services/searchService';
import SummaryView from './SummaryView';
import DataDashboard from './DataDashboard';
import { useAuth } from '../../context/AuthContext';

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
    const [scopeMismatch, setScopeMismatch] = useState(null);

    // ── Paywall State ──────────────────────────────────────────────────────────
    const { isAuthenticated, refreshUser } = useAuth();
    const [accessState, setAccessState] = useState('NO_ACCESS');
    const [paywallPrice, setPaywallPrice] = useState(500);
    const [totalProfilesCount, setTotalProfilesCount] = useState(0);
    const [purchaseLoading, setPurchaseLoading] = useState(false);
    
    // Server-resolved context
    const [serverSubcatId, setServerSubcatId] = useState(null);
    const [serverVariantName, setServerVariantName] = useState(null);

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
                if (variantName) params.set('variant_name', variantName);
                if (subcatId) params.set('subcat_id', subcatId);
                navigate(`/search/results?${params.toString()}`, { replace: true });
                return;
            }

            if (data.scope_mismatch) {
                setScopeMismatch(data.scope_mismatch);
                setNeedsDisambig(false);
                setIsBroadSearch(false);
                setVariants([]);
                setResults([]);
                setMarketSnapshot(null);
            } else if (data.needs_disambiguation) {
                setScopeMismatch(null);
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
                setScopeMismatch(null);
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
                
                setAccessState(data.access_state || 'NO_ACCESS');
                setPaywallPrice(data.paywall_price || 500);
                setTotalProfilesCount(data.total_profiles_count || (data.results ? data.results.length : 0));
                
                setServerSubcatId(data.active_subcat_id || null);
                setServerVariantName(data.active_variant || null);

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

    // ── Paywall Purchase Logic ──────────────────────────────────────────────
    const handlePurchase = async () => {
        if (!isAuthenticated) {
            navigate('/login');
            return;
        }

        setPurchaseLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/subscriptions/purchase-access/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    access_type: (subcatId || serverSubcatId) ? 'PRODUCT' : 'HS_CODE',
                    hscode: hsCode || initialQuery || query,
                    subcat_id: subcatId || serverSubcatId,
                    product_name: variantName || serverVariantName
                })
            });
            const data = await res.json();
            
            if (!res.ok) {
                alert(`Purchase failed: ${data.error || data.message || 'Unknown error'}`);
                if (res.status === 402) {
                    navigate('/subscription'); 
                }
            } else {
                await refreshUser();
                fetchResults(); // Refresh data smoothly
            }
        } catch (err) {
            alert('Network error during purchase.');
        } finally {
            setPurchaseLoading(false);
        }
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
        <div className="min-h-screen bg-slate-50 font-sans">
            <Navbar />

            {/* Search bar */}
            <div className="bg-white border-b-2 border-slate-100 sticky top-0 z-10 shadow-sm">
                <div className="max-w-7xl mx-auto px-4 md:px-8 w-full py-3 md:py-4" >
                    <form onSubmit={handleSearch} className="w-full relative">
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            className="w-full pl-5 pr-24 sm:pr-28 py-3 rounded-full border-2 border-slate-200 focus:border-emerald-500 focus:ring-0 transition-all font-medium text-slate-700 placeholder-slate-400"
                            placeholder="Search again..."
                            style={{ fontSize: '1rem' }}
                            aria-label="Search query"
                        />
                        <button
                            type="submit"
                            aria-label="Search"
                            className="absolute right-1.5 top-1.5 bottom-1.5 inline-flex items-center justify-center gap-1.5 px-4 sm:px-5 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white rounded-full font-bold text-sm shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-300"
                        >
                            <Search size={16} aria-hidden="true" />
                            <span className="hidden sm:inline">Search</span>
                        </button>
                    </form>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 md:px-8 w-full flex flex-col md:flex-row gap-8" className="max-w-7xl mx-auto px-6 py-8 flex items-start gap-8">

                {/* Left Sidebar: Filters (hidden during disambiguation) */}
                {!needsDisambig && (
                    <aside className="w-64 hidden md:block space-y-6 flex-shrink-0">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-bold text-slate-700 flex items-center gap-2 text-lg">
                                <Filter size={20} /> Filters
                            </h3>
                            {selectedCountry && (
                                <button onClick={clearFilters} className="text-sm text-emerald-600 hover:text-emerald-800 font-medium">
                                    Reset
                                </button>
                            )}
                        </div>

                        {availableCountries.length > 0 && (
                            <div className="border-b-2 border-slate-100 pb-4">
                                <h4 className="text-sm font-bold text-slate-700 py-2">Country</h4>
                                <select
                                    value={tempCountry}
                                    onChange={(e) => setTempCountry(e.target.value)}
                                    className="w-full mt-2 block rounded-lg border-2 border-slate-200 py-2 pl-2 pr-8 text-sm focus:border-emerald-500 focus:outline-none"
                                >
                                    <option value="">All Countries</option>
                                    {availableCountries.map(c => (
                                        <option key={c} value={c}>{c}</option>
                                    ))}
                                </select>
                            </div>
                        )}

                        <div className="border-b-2 border-slate-100 pb-4">
                            <h4 className="text-sm font-bold text-slate-700 py-2">Price Range ($/MT)</h4>
                            <div className="flex items-center gap-2 mt-2">
                                <input
                                    type="number"
                                    placeholder="Min"
                                    value={tempPriceMin}
                                    onChange={(e) => setTempPriceMin(e.target.value)}
                                    className="w-full rounded-lg border-2 border-slate-200 py-2 px-2 text-sm focus:border-emerald-500 focus:outline-none"
                                />
                                <span className="text-slate-400 font-bold">-</span>
                                <input
                                    type="number"
                                    placeholder="Max"
                                    value={tempPriceMax}
                                    onChange={(e) => setTempPriceMax(e.target.value)}
                                    className="w-full rounded-lg border-2 border-slate-200 py-2 px-2 text-sm focus:border-emerald-500 focus:outline-none"
                                />
                            </div>
                        </div>

                        <div className="border-b-2 border-slate-100 pb-4">
                            <h4 className="text-sm font-bold text-slate-700 py-2">Min. Trade Volume (MT)</h4>
                            <div className="mt-2">
                                <input
                                    type="number"
                                    placeholder="e.g. 500"
                                    value={tempVolumeMin}
                                    onChange={(e) => setTempVolumeMin(e.target.value)}
                                    className="w-full rounded-lg border-2 border-slate-200 py-2 px-3 text-sm focus:border-emerald-500 focus:outline-none"
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

                    {/* ── Scope Mismatch Banner ──────────────────────── */}
                    {scopeMismatch && !loading && (
                        <div className="text-center py-16 bg-white rounded-xl border-2 border-blue-100 p-8 shadow-sm">
                            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔄</div>
                            <h2 className="text-xl font-bold text-slate-900 mb-3">
                                No {scopeMismatch.current_scope} data for "{scopeMismatch.product}"
                            </h2>
                            <p className="font-medium text-slate-500 max-w-lg mx-auto mb-6 leading-relaxed">
                                In the past {scopeMismatch.year_max - scopeMismatch.year_min + 1} year{scopeMismatch.year_max - scopeMismatch.year_min > 0 ? 's' : ''} ({scopeMismatch.year_min}–{scopeMismatch.year_max}), <strong className="text-slate-700">{scopeMismatch.product}</strong> wasn't {scopeMismatch.current_label}.
                                However, it was <strong className="text-emerald-600">{scopeMismatch.alt_label}</strong> ({scopeMismatch.alt_records.toLocaleString()} records found).
                            </p>
                            <button
                                onClick={() => {
                                    const newScope = scopeMismatch.alt_scope.toUpperCase();
                                    const newIntent = newScope === 'IMPORT' ? 'BUY' : 'SELL';
                                    setScopeMismatch(null);
                                    const params = new URLSearchParams(location.search);
                                    params.set('scope', newScope);
                                    params.set('intent', newIntent);
                                    navigate(`/search/results?${params.toString()}`, { replace: true });
                                }}
                                className="px-8 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-md transition-all hover:-translate-y-0.5"
                            >
                                Switch to Analyse {scopeMismatch.alt_scope === 'import' ? 'Imports' : 'Exports'} →
                            </button>
                        </div>
                    )}

                    {/* ── Broad Search Warning ──────────────────────────── */}
                    {isBroadSearch && !loading && !scopeMismatch && (
                        <div className="text-center py-16 text-slate-400 bg-white rounded-xl border-2 border-amber-100 p-8 shadow-sm">
                            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🌐</div>
                            <h2 className="text-xl font-bold text-slate-900 mb-2">Search is too broad</h2>
                            <p className="font-medium text-slate-500 max-w-md mx-auto">
                                No specific high-confidence product match was found for "{query}".
                                Try being more specific with the product name.
                            </p>
                        </div>
                    )}

                    {/* ── Disambiguation Panel ───────────────────────────── */}
                    {needsDisambig && !loading && !scopeMismatch && (
                        <div>
                            <div className="flex items-center gap-3 mb-6">
                                <AlertCircle size={22} className="text-amber-500" />
                                <div>
                                    <h2 className="text-xl font-bold text-slate-900">
                                        Multiple products matched "{query}"
                                    </h2>
                                    <p className="text-sm text-slate-500 mt-0.5">
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
                                        className="text-left p-5 bg-white rounded-xl border-2 border-slate-100 hover:border-emerald-500 hover:shadow-md transition-all group"
                                        style={{ cursor: 'pointer' }}
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <div>
                                                <div className="flex items-center gap-2 mb-1.5">
                                                    <Package size={16} className="text-emerald-500 flex-shrink-0" />
                                                    <span className="font-bold text-slate-900 group-hover:text-emerald-700 transition-colors text-sm">
                                                        {v.name}
                                                    </span>
                                                </div>
                                                <div className="text-xs text-slate-400">
                                                    {v.category ? `${v.category} · ` : ''}HS {v.hs_code}
                                                </div>
                                            </div>
                                            <div className="flex flex-col items-end gap-1">
                                                {v.is_drill_down && (
                                                    <span className="text-xs font-bold text-emerald-500 bg-emerald-50 rounded-full px-2 py-0.5">Drill Down ›</span>
                                                )}
                                                <ChevronRight size={16} className="text-slate-300 group-hover:text-emerald-500 flex-shrink-0 mt-1" />
                                            </div>
                                        </div>
                                    </button>
                                ))}
                            </div>

                            {/* Pagination Controls */}
                            {variants.length > DISAMBIG_PAGE_SIZE && (
                                <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-100">
                                    <p className="text-sm text-slate-500">
                                        Showing {((disambigPage - 1) * DISAMBIG_PAGE_SIZE) + 1}–{Math.min(disambigPage * DISAMBIG_PAGE_SIZE, variants.length)} of {variants.length} matches
                                    </p>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setDisambigPage(p => Math.max(1, p - 1))}
                                            disabled={disambigPage === 1}
                                            className="px-4 py-2 rounded-lg border-2 border-slate-200 text-sm font-bold text-slate-600 hover:border-emerald-500 hover:text-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
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
                                                            : 'border-2 border-slate-200 text-slate-600 hover:border-emerald-500 hover:text-emerald-700'
                                                    }`}
                                                >
                                                    {p}
                                                </button>
                                            ))
                                        }
                                        <button
                                            onClick={() => setDisambigPage(p => Math.min(Math.ceil(variants.length / DISAMBIG_PAGE_SIZE), p + 1))}
                                            disabled={disambigPage >= Math.ceil(variants.length / DISAMBIG_PAGE_SIZE)}
                                            className="px-4 py-2 rounded-lg border-2 border-slate-200 text-sm font-bold text-slate-600 hover:border-emerald-500 hover:text-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                                        >
                                            Next →
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* ── Normal Results ─────────────────────────────────── */}
                    {!needsDisambig && !isBroadSearch && !scopeMismatch && (
                        <div className="flex flex-col">

                            {/* ── Tab Pill Buttons for Intent Mapping ──────────────── */}
                            {showPills && (
                                <div className="mb-6">
                                    <h3 className="text-slate-500 font-bold uppercase tracking-wide text-xs mb-3">Select Trade Direction</h3>
                                    <div className="flex flex-wrap gap-3">
                                        <button
                                            onClick={() => handleRawTabClick('IMPORT', 'BUY')}
                                            className={`px-5 py-2.5 rounded-full font-bold text-sm transition-all shadow-sm ${scope === 'IMPORT' && overrideIntent === 'BUY' ? 'bg-emerald-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:border-emerald-500 hover:text-emerald-600'}`}
                                        >
                                            Foreign Suppliers
                                        </button>
                                        <button
                                            onClick={() => handleRawTabClick('EXPORT', 'SELL')}
                                            className={`px-5 py-2.5 rounded-full font-bold text-sm transition-all shadow-sm ${scope === 'EXPORT' && overrideIntent === 'SELL' ? 'bg-emerald-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:border-emerald-500 hover:text-emerald-600'}`}
                                        >
                                            Foreign Buyers
                                        </button>
                                        <button
                                            onClick={() => handleRawTabClick('IMPORT', 'SELL')}
                                            className={`px-5 py-2.5 rounded-full font-bold text-sm transition-all shadow-sm ${scope === 'IMPORT' && overrideIntent === 'SELL' ? 'bg-emerald-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:border-emerald-500 hover:text-emerald-600'}`}
                                        >
                                            Pakistani Buyers
                                        </button>
                                        <button
                                            onClick={() => handleRawTabClick('EXPORT', 'BUY')}
                                            className={`px-5 py-2.5 rounded-full font-bold text-sm transition-all shadow-sm ${scope === 'EXPORT' && overrideIntent === 'BUY' ? 'bg-emerald-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:border-emerald-500 hover:text-emerald-600'}`}
                                        >
                                            Pakistani Suppliers
                                        </button>
                                    </div>
                                </div>
                            )}

                            <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                                <h2 className="text-2xl font-bold text-slate-800 font-primary">
                                    {loading ? 'Searching...' : (() => {
                                        if (activeIntent === 'UNKNOWN') {
                                            const total = accessState === 'NO_ACCESS' && totalProfilesCount > 0 ? totalProfilesCount : sortedResults.length;
                                            return `${total} Suppliers & Buyers found for "${query}"`;
                                        }
                                        const count = accessState === 'NO_ACCESS' && totalProfilesCount > 0 ? totalProfilesCount : sortedResults.length;
                                        return `${count} ${entityLabel} found for "${query}"`;
                                    })()}
                                </h2>

                                {!loading && !error && sortedResults.length > 0 && (
                                    <div className="flex items-center gap-2">
                                        {accessState === 'NO_ACCESS' && (
                                            <span className="text-sm font-bold text-amber-500 bg-amber-50 px-3 py-1.5 rounded-lg mr-2 border border-amber-200 shadow-sm flex items-center gap-1.5">
                                                <Lock size={14} /> Showing 2 previews
                                            </span>
                                        )}
                                        <span className="text-sm font-medium text-slate-500">Sort by:</span>
                                        <select
                                            value={sortBy}
                                            onChange={(e) => setSortBy(e.target.value)}
                                            className="rounded-lg border-2 border-slate-200 py-1.5 pl-3 pr-8 text-sm focus:border-emerald-500 focus:outline-none font-medium text-slate-700 bg-white"
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
                                <div className="text-center py-20 text-slate-400 flex flex-col items-center justify-center">
                                    <div className="radar-container">
                                        <div className="radar-sweep"></div>
                                        <div className="radar-ring" style={{ animationDelay: '0s' }}></div>
                                        <div className="radar-ring" style={{ animationDelay: '1s' }}></div>
                                        <div className="radar-core"></div>
                                    </div>
                                    <p className="font-bold text-slate-500 tracking-wide animate-pulse-opacity">Searching trade records...</p>
                                </div>
                            )}

                            {error && (
                                <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
                                    {error}
                                </div>
                            )}

                            {!loading && !error && sortedResults.length === 0 && (
                                <div className="text-center py-16 text-slate-400">
                                    <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📭</div>
                                    <p className="font-medium text-slate-600">No {entityLabel.toLowerCase()} found matching your filters</p>
                                    <p className="text-sm mt-1">Try adjusting the price, volume, or country.</p>
                                </div>
                            )}

                            {!loading && !error && sortedResults.map((supplier, idx) => {
                                const isLocked = accessState === 'NO_ACCESS';
                                
                                return (
                                <div
                                    key={idx}
                                    className={`action-card bg-white mb-4 transition-all relative overflow-hidden group ${isLocked ? 'pointer-events-none border-slate-200 shadow-sm' : 'hover:border-emerald-500 shadow-md cursor-default'}`}
                                    style={{ padding: '1.5rem', marginBottom: '1.5rem' }}
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <h3 className="text-xl font-bold text-slate-900 group-hover:text-emerald-700 transition-colors">
                                                    {supplier.name}
                                                </h3>
                                            </div>
                                            <div className="text-sm text-slate-500 mb-4 font-medium">{supplier.country}</div>

                                            <div className="flex gap-8 text-sm text-slate-700">
                                                <div>
                                                    <span className="block text-slate-400 text-xs uppercase font-bold tracking-wider">Avg Price</span>
                                                    <span className="font-bold text-lg text-slate-800">${supplier.avg_price.toFixed(2)}/MT</span>
                                                </div>
                                                <div>
                                                    <span className="block text-slate-400 text-xs uppercase font-bold tracking-wider">Volume</span>
                                                    <span className="font-bold text-lg text-slate-800">{supplier.total_volume.toLocaleString()} MT</span>
                                                </div>
                                                <div>
                                                    <span className="block text-slate-400 text-xs uppercase font-bold tracking-wider">Shipments</span>
                                                    <span className="font-bold text-lg text-slate-800">{supplier.shipment_count}</span>
                                                </div>
                                                {supplier.volume_fit !== 'N/A' && supplier.volume_fit && (
                                                    <div>
                                                        <span className="block text-slate-400 text-xs uppercase font-bold tracking-wider">Volume Fit</span>
                                                        <span className={`font-bold text-sm ${supplier.volume_fit === 'Strong' ? 'text-emerald-600' :
                                                            supplier.volume_fit === 'Good' ? 'text-blue-600' :
                                                                supplier.volume_fit === 'Partial' ? 'text-amber-600' : 'text-slate-500'
                                                            }`}>{supplier.volume_fit}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        <div className="flex flex-col gap-3">
                                            {!isLocked ? (
                                                <>
                                                    <Link
                                                        to={`/search/supplier/${encodeURIComponent(supplier.name)}?q=${encodeURIComponent(query)}&scope=${encodeURIComponent(scope)}${subcatId ? `&subcat_id=${encodeURIComponent(subcatId)}` : ''}${variantName ? `&variant_name=${encodeURIComponent(variantName)}` : ''}${overrideIntent ? `&intent=${encodeURIComponent(overrideIntent)}` : ''}`}
                                                        className="px-6 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-bold rounded-lg transition-all shadow-md shadow-emerald-500/20 text-center text-sm block"
                                                    >
                                                        View Deal
                                                    </Link>
                                                    <button
                                                        onClick={() => toggleCompare(supplier.name)}
                                                        className={`px-4 py-2 border-2 text-sm font-bold rounded-md transition-colors ${selectedSuppliers.includes(supplier.name)
                                                                ? 'bg-emerald-50 border-emerald-500 text-emerald-700'
                                                                : 'bg-white border-slate-200 text-slate-700 hover:border-emerald-500 hover:text-emerald-600'
                                                            }`}>
                                                        {selectedSuppliers.includes(supplier.name) ? 'Added ✓' : 'Compare'}
                                                    </button>
                                                </>
                                            ) : (
                                                <div className="flex flex-col gap-3 ml-6 flex-shrink-0 opacity-40 blur-sm pointer-events-none">
                                                    <div className="w-[120px] h-[36px] bg-emerald-500 rounded-lg"></div>
                                                    <div className="w-[120px] h-[38px] bg-slate-200 rounded-lg"></div>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="mt-5 pt-4 border-t-2 border-slate-50 flex items-center text-xs text-slate-400 gap-4 font-medium">
                                        <span className="flex items-center gap-1">
                                            <BarChart2 size={14} /> Based on {supplier.shipment_count} shipments
                                        </span>
                                        <span>Last active: {supplier.last_shipment_date}</span>
                                    </div>
                                </div>
                            )})}

                            {/* Inline Teaser CTA (Unified Paywall Integration) */}
                            {!loading && !error && accessState === 'NO_ACCESS' && sortedResults.length > 0 && (
                                <div className="mt-8 bg-gradient-to-br from-emerald-50 via-white to-teal-50/30 p-8 pt-10 rounded-2xl border border-emerald-200 shadow-[0_10px_35px_rgba(16,185,129,0.08)] overflow-hidden relative group">
                                    <div className="absolute -top-12 -right-12 opacity-5 pointer-events-none transform group-hover:scale-110 transition-transform duration-700">
                                        <Zap size={200} />
                                    </div>
                                    
                                    <div className="relative z-10 text-center max-w-lg mx-auto">
                                        <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center mx-auto mb-5 border border-emerald-100 text-emerald-600 rotate-3">
                                            <Lock size={28} />
                                        </div>
                                        
                                        <h3 className="text-3xl font-black text-slate-900 mb-3 tracking-tight">
                                            Unlock Refined Intelligence
                                        </h3>
                                        
                                        <p className="text-slate-600 mb-8 font-medium leading-relaxed">
                                            You're currently viewing restricted previews. Unlock to instantly reveal all supply chain metrics, pricing analytics, and actionable 'View Deal' links for {variantName || serverVariantName || query || 'this product'}.
                                        </p>

                                        <div className="flex flex-col gap-3 items-center">
                                            {isAuthenticated ? (
                                                <button
                                                    onClick={handlePurchase}
                                                    disabled={purchaseLoading}
                                                    className="w-full md:w-auto px-10 py-4 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white font-bold rounded-xl shadow-[0_8px_20px_rgba(16,185,129,0.3)] hover:shadow-[0_10px_25px_rgba(16,185,129,0.4)] transition-all hover:-translate-y-1 flex items-center justify-center gap-3 text-lg"
                                                >
                                                    {purchaseLoading ? (
                                                        <>
                                                            <span className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
                                                            <span>Processing Securely...</span>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Zap size={20} className="fill-white/20" />
                                                            <span>Unlock for {(paywallPrice).toLocaleString()} Tokens</span>
                                                        </>
                                                    )}
                                                </button>
                                            ) : (
                                                <button
                                                    onClick={() => navigate('/login')}
                                                    className="w-full md:w-auto px-10 py-4 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-xl shadow-xl transition-all hover:-translate-y-1 flex items-center justify-center gap-2 text-lg"
                                                >
                                                    Sign in to Unlock
                                                </button>
                                            )}
                                            <span className="text-xs text-slate-400 font-medium tracking-wide mt-2">
                                                Tokens will be deducted from your account balance.
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </main>

                {/* Right Panel: Market Snapshot */}
                {!needsDisambig && (
                    <aside className="w-72 hidden lg:block space-y-6 flex-shrink-0">
                        {marketSnapshot && (
                            <div className="stat-card flex-col items-start gap-4">
                                <h4 className="font-bold text-slate-800 mb-2 w-full border-b-2 border-slate-100 pb-2">Market Snapshot</h4>
                                <div className="space-y-4 w-full">
                                    <div>
                                        <div className="text-xs text-slate-500 uppercase font-bold">Global Avg Price</div>
                                        <div className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Courier New, monospace' }}>
                                            ${marketSnapshot.avg_price_global.toFixed(2)}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-slate-500 uppercase font-bold">
                                            {activeIntent === 'SELL' ? 'Top Destination' : 'Top Origin'}
                                        </div>
                                        <div className="text-lg font-bold text-slate-900">{marketSnapshot.top_country}</div>
                                    </div>
                                    {searchEngine && (
                                        <div className="text-xs text-slate-400 pt-2 border-t border-slate-100">
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
                <div className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-slate-200 shadow-[0_-4px_20px_rgba(0,0,0,0.05)] p-4 z-50 transform transition-transform duration-300">
                    <div className="max-w-7xl mx-auto flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="h-10 w-10 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600">
                                <BarChart2 size={20} />
                            </div>
                            <div>
                                <p className="text-sm text-slate-500 font-bold uppercase tracking-wider">Comparing</p>
                                <p className="text-slate-900 font-bold">
                                    {selectedSuppliers[0]}
                                    {selectedSuppliers.length > 1 && <span className="text-emerald-600 ml-1">(+{selectedSuppliers.length - 1} more)</span>}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => setSelectedSuppliers([])}
                                className="px-4 py-2 text-sm font-bold text-slate-500 hover:text-slate-800 transition-colors"
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
