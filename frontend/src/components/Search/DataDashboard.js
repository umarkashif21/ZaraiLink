import React, { useEffect, useState, useMemo } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import { Filter, AlertCircle, TrendingUp, BarChart2, ChevronRight, Lock, Zap } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API_BASE = process.env.REACT_APP_API_BASE_URL;

const PILLS = [
    { id: 'FOREIGN_SUPPLIERS',   label: 'Foreign Suppliers',   sub: 'Import Data → Sellers',      scope: 'IMPORT', intent: 'BUY'  },
    { id: 'FOREIGN_BUYERS',      label: 'Foreign Buyers',      sub: 'Export Data → Buyers',       scope: 'EXPORT', intent: 'SELL' },
    { id: 'PAKISTANI_BUYERS',    label: 'Pakistani Buyers',    sub: 'Import Data → Local Buyers', scope: 'IMPORT', intent: 'SELL' },
    { id: 'PAKISTANI_SUPPLIERS', label: 'Pakistani Suppliers', sub: 'Export Data → Local Sellers',scope: 'EXPORT', intent: 'BUY'  },
];

const DataDashboard = () => {
    const location  = useLocation();
    const navigate  = useNavigate();
    const { isAuthenticated, refreshUser } = useAuth();

    const qp = useMemo(() => new URLSearchParams(location.search), [location.search]);

    const rawQuery      = qp.get('q') || '';
    const hsCodeParam   = qp.get('hs_code') || '';
    const displayTarget = hsCodeParam || rawQuery;

    // Don't default to IMPORT blindly — the product may be EXPORT-only.
    const activePill = qp.get('dashboard_intent') || null;

    const selectedRefinements = useMemo(() => {
        const refines = qp.get('refines');
        if (refines) return refines.split(',').filter(Boolean);
        const variant = qp.get('variant_name');
        if (variant) return [variant];
        return [];
    }, [qp]);

    const selectedSubcatIds = useMemo(() => {
        const ids = qp.get('refine_ids');
        if (ids) return ids.split(',').filter(Boolean).map(Number);
        return [];
    }, [qp]);

    const [hsDescription, setHsDescription]   = useState('');
    const [totalShipments, setTotalShipments] = useState(0);
    const [sidebarCounts, setSidebarCounts]           = useState([]);
    const [sidebarImportCounts, setSidebarImportCounts] = useState([]);
    const [sidebarExportCounts, setSidebarExportCounts] = useState([]);
    const [sidebarSearch, setSidebarSearch]   = useState('');
    const [tradeDirection, setTradeDirection] = useState(null);
    const [profiles, setProfiles]             = useState([]);
    const [loading, setLoading]               = useState(true);
    const [error, setError]                   = useState(null);
    const [selectedEntities, setSelectedEntities] = useState([]);
    const [totalProfilesCount, setTotalProfilesCount] = useState(0);
    const [refreshKey, setRefreshKey]         = useState(0);

    const [accessState, setAccessState]       = useState('NO_ACCESS');
    const [purchaseLoading, setPurchaseLoading] = useState(false);

    const currentTokenCost = selectedRefinements.length > 0
        ? selectedRefinements.length * 500
        : 5000;

    const switchPill = (pillId) => {
        const p = new URLSearchParams(location.search);
        p.set('dashboard_intent', pillId);
        // ⚠️  Do NOT delete refines or variant_name here.
        // The product filter (e.g. "Yazee") must survive pill switches so the
        // user can check which trade direction the product actually exists in.
        navigate(`/search/results?${p.toString()}`, { replace: true });
        setSelectedEntities([]);
    };

    const toggleRefinement = (sc) => {
        const name = typeof sc === 'string' ? sc : sc.name;
        const scId = typeof sc === 'string' ? null : sc.subcat_id;
        const p = new URLSearchParams(location.search);
        const currentNames = selectedRefinements;
        const currentIds   = selectedSubcatIds;
        const isSelected = currentNames.includes(name);
        const nextNames = isSelected ? currentNames.filter(n => n !== name) : [...currentNames, name];
        const nextIds   = isSelected ? currentIds.filter(id => id !== scId) : (scId != null ? [...currentIds, scId] : currentIds);
        nextNames.length ? p.set('refines', nextNames.join(',')) : p.delete('refines');
        nextIds.length   ? p.set('refine_ids', nextIds.join(',')) : p.delete('refine_ids');
        p.delete('variant_name');
        navigate(`/search/results?${p.toString()}`, { replace: true });
    };

    const clearRefinements = () => {
        const p = new URLSearchParams(location.search);
        p.delete('refines');
        p.delete('refine_ids');
        p.delete('variant_name');
        navigate(`/search/results?${p.toString()}`, { replace: true });
    };

    useEffect(() => {
        if (!displayTarget) return;

        // Don't fetch until user picks a pill — the product may be EXPORT-only.
        if (!activePill) {
            setLoading(false);
            return;
        }

        const controller = new AbortController();

        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const params = new URLSearchParams({
                    q:      displayTarget,
                    intent: activePill,
                });
                if (selectedRefinements.length > 0) {
                    params.set('subcat', selectedRefinements.join(','));
                }
                const res = await fetch(
                    `${API_BASE}/api/search/hs-dashboard/?${params.toString()}`,
                    { 
                        signal: controller.signal,
                        credentials: 'include'
                    }
                );
                if (!res.ok) throw new Error(`Server error: ${res.status}`);
                const data = await res.json();
                
                setHsDescription(data.hs_description || rawQuery);
                setTotalShipments(data.total_shipments || 0);
                setTradeDirection(data.trade_direction || null);
                setSidebarCounts(data.sidebar_counts || []);
                setSidebarImportCounts(data.sidebar_import_counts || []);
                setSidebarExportCounts(data.sidebar_export_counts || []);
                setProfiles(data.visible_profiles || []); 
                setTotalProfilesCount(data.total_profiles_count || (data.visible_profiles ? data.visible_profiles.length : 0));
                setAccessState(data.access_state || 'NO_ACCESS');

                // If the backend ignored the variant_name (it was a category label, not a
                // real subcategory), clear it from the URL so we don't show a stale filter.
                if (data.subcat_filter_ignored) {
                    const p = new URLSearchParams(location.search);
                    p.delete('variant_name');
                    p.delete('refines');
                    navigate(`/search/results?${p.toString()}`, { replace: true });
                }
            } catch (err) {
                if (err.name === 'AbortError') return;
                setError(err.message);
            } finally {
                if (!controller.signal.aborted) setLoading(false);
            }
        };

        fetchData();

        return () => controller.abort();
    }, [displayTarget, activePill, selectedRefinements.join(','), refreshKey]);

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
                    access_type: selectedRefinements.length > 0 ? 'PRODUCT' : 'HS_CODE',
                    hscode: displayTarget,
                    product_name: selectedRefinements.length > 0 ? selectedRefinements.join(',') : null
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
                setRefreshKey(prev => prev + 1);
            }
        } catch (err) {
            alert('Network error during purchase.');
        } finally {
            setPurchaseLoading(false);
        }
    };

    const pill        = PILLS.find(p => p.id === activePill) || null;
    const entityLabel = activePill?.includes('SUPPLIER') ? 'Suppliers' : 'Buyers';

    // No pill selected → combined totals so user can see all product volumes.
    const isImportPill = activePill === 'FOREIGN_SUPPLIERS' || activePill === 'PAKISTANI_BUYERS';
    const isExportPill = activePill === 'FOREIGN_BUYERS'    || activePill === 'PAKISTANI_SUPPLIERS';
    const activeSidebarCounts = isImportPill ? sidebarImportCounts
                              : isExportPill ? sidebarExportCounts
                              : sidebarCounts;

    const dealUrl = (name) => {
        const params = new URLSearchParams({
            q:      rawQuery,
            scope:  pill.scope,
            intent: pill.intent,
        });
        if (selectedRefinements.length > 0) {
            params.set('variant_name', selectedRefinements[0]);
        }
        // Pass the DB subcat_id so the backend fast-path returns exact ProductItem IDs
        if (selectedSubcatIds.length > 0) {
            params.set('subcat_id', selectedSubcatIds[0]);
        }
        return `/search/supplier/${encodeURIComponent(name)}?${params.toString()}`;
    };

    const compareUrl = () => {
        const params = new URLSearchParams({
            suppliers: selectedEntities.join(','),
            q:         rawQuery,
            scope:     pill.scope,
            intent:    pill.intent,
        });
        if (selectedRefinements.length > 0) {
            params.set('variant_name', selectedRefinements[0]);
        }
        if (selectedSubcatIds.length > 0) {
            params.set('subcat_id', selectedSubcatIds[0]);
        }
        return `/search/compare?${params.toString()}`;
    };

    const toggleCompare = (name) => {
        setSelectedEntities(prev => {
            if (prev.includes(name)) return prev.filter(n => n !== name);
            if (prev.length >= 4) { alert('You can compare up to 4 at once.'); return prev; }
            return [...prev, name];
        });
    };

    return (
        <div className="dashboard-wrapper bg-slate-50 min-h-screen font-sans">
            <Navbar />

            <div className="bg-slate-900 border-b border-slate-800 sticky top-0 md:top-[64px] z-10 shadow-2xl">
                <div className="max-w-7xl mx-auto px-6 py-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <div className="text-emerald-500 font-bold tracking-widest text-[10px] uppercase mb-1">Market Intelligence</div>
                        <div className="flex items-center gap-3 mb-2">
                            <TrendingUp className="text-emerald-400" size={24} />
                            <h1 className="text-2xl font-black text-white tracking-tight">
                                {displayTarget}
                            </h1>
                        </div>
                        <p className="text-sm font-medium ml-9">
                            <span className="text-slate-300">{hsDescription}</span>
                            {activePill && (
                                <>
                                    <span className="text-slate-600 mx-2">•</span>
                                    <span className="text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded text-xs">{totalShipments.toLocaleString()} Shipments</span>
                                </>
                            )}
                            {selectedRefinements.length > 0 && (
                                <span className="ml-2 text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded text-xs font-bold">
                                    Filtered: {selectedRefinements.join(', ')}
                                </span>
                            )}
                        </p>
                    </div>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-bold rounded-xl border border-slate-700 transition-all text-sm shadow-lg flex items-center justify-center"
                    >
                        ← Dashboard
                    </button>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 py-6 flex gap-6">

                <div className="w-64 flex-shrink-0">
                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 sticky top-24">
                        <h3 className="font-bold text-slate-900 flex items-center gap-2 mb-4 pb-2 border-b border-slate-100 text-sm uppercase tracking-wide">
                            <Filter size={15} /> Refine by Product
                        </h3>

                        {loading && <p className="text-xs text-slate-400">Loading...</p>}
                        {!loading && sidebarCounts.length === 0 && (
                            <p className="text-xs text-slate-400">No subcategories found.</p>
                        )}

                        {activeSidebarCounts.length > 6 && (
                            <input
                                type="text"
                                value={sidebarSearch}
                                onChange={e => setSidebarSearch(e.target.value)}
                                placeholder="Filter products..."
                                className="w-full mb-3 px-2.5 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-400 bg-slate-50 text-slate-700 placeholder-slate-400"
                            />
                        )}

                        <div className="space-y-2 max-h-[55vh] overflow-y-auto pr-1">
                            {activeSidebarCounts
                                .filter(sc => !sidebarSearch || sc.name.toLowerCase().includes(sidebarSearch.toLowerCase()))
                                .map((sc, idx) => (
                                <label key={idx} className="flex items-start gap-2 cursor-pointer group">
                                    <input
                                        type="checkbox"
                                        checked={selectedRefinements.includes(sc.name)}
                                        onChange={() => toggleRefinement(sc)}
                                        className="mt-0.5 w-3.5 h-3.5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                                    />
                                    <div className="flex-1 flex justify-between items-start text-xs">
                                        <span className={`leading-tight ${
                                            sc.count === 0
                                                ? 'text-slate-400 line-through'
                                                : 'text-slate-700 group-hover:text-emerald-700'
                                        }`}>{sc.name}</span>
                                        <span className={`ml-2 font-bold px-1.5 py-0.5 rounded-full flex-shrink-0 ${
                                            sc.count === 0
                                                ? 'text-slate-300 bg-slate-50'
                                                : 'text-slate-400 bg-slate-100'
                                        }`}>{sc.count}</span>
                                    </div>
                                </label>
                            ))}
                            {sidebarSearch && activeSidebarCounts.filter(sc => sc.name.toLowerCase().includes(sidebarSearch.toLowerCase())).length === 0 && (
                                <p className="text-xs text-slate-400 text-center py-2">No match for "{sidebarSearch}"</p>
                            )}
                        </div>

                        {selectedRefinements.length > 0 && (
                            <button
                                onClick={clearRefinements}
                                className="w-full mt-3 py-1.5 text-xs font-bold text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                            >
                                Clear All
                            </button>
                        )}
                    </div>
                </div>

                <div className="flex-1 min-w-0">

                    <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/40 border border-slate-100 p-2 mb-6 grid grid-cols-2 md:grid-cols-4 gap-2">
                        {PILLS.map(p => (
                            <button
                                key={p.id}
                                onClick={() => switchPill(p.id)}
                                className={`flex flex-col items-start px-4 py-3 rounded-xl transition-all text-left ${
                                    activePill === p.id
                                        ? 'bg-emerald-500 text-slate-900 shadow-md shadow-emerald-500/20'
                                        : 'text-slate-500 hover:bg-slate-50 hover:text-emerald-700'
                                }`}
                            >
                                <span className="font-bold text-sm tracking-tight">{p.label}</span>
                                <span className={`text-xs mt-0.5 font-medium ${activePill === p.id ? 'text-emerald-900/70' : 'text-slate-400'}`}>{p.sub}</span>
                            </button>
                        ))}
                    </div>

                    {!loading && !error && activePill && (
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-xl font-bold text-slate-800">
                                {totalProfilesCount} {entityLabel} found for HS {displayTarget}
                                {selectedRefinements.length > 0 && (
                                    <span className="ml-2 text-sm font-normal text-slate-400">
                                        · filtered by {selectedRefinements.join(', ')}
                                    </span>
                                )}
                            </h2>
                        </div>
                    )}

                    {loading && (
                        <div className="flex justify-center items-center py-20 bg-white rounded-xl shadow-sm border border-slate-200">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mr-3"></div>
                            <span className="text-emerald-500 font-medium">Loading market records...</span>
                        </div>
                    )}

                    {error && (
                        <div className="bg-red-50 text-red-600 p-4 rounded-xl font-medium border border-red-200 flex items-center gap-2 text-sm">
                            <AlertCircle size={18} /> {error}
                        </div>
                    )}

                    {!activePill && !loading && (
                        <div className="bg-white rounded-xl shadow-sm border border-slate-200 py-16 text-center">
                            <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>👆</div>
                            <h3 className="text-slate-700 font-bold text-lg mb-2">Select a trade perspective above</h3>
                            <p className="text-slate-400 text-sm max-w-sm mx-auto">
                                {selectedRefinements.length > 0
                                    ? `"${selectedRefinements.join(', ')}" is filtered. Click a tab to see which direction this product trades in.`
                                    : 'Click Foreign Suppliers, Foreign Buyers, Pakistani Buyers, or Pakistani Suppliers to load results.'}
                            </p>
                        </div>
                    )}

                    {activePill && !loading && !error && profiles.length === 0 && (
                        <div className="bg-white rounded-xl shadow-sm border border-slate-200 py-16 text-center px-6">
                            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📭</div>
                            {selectedRefinements.length > 0 ? (
                                <>
                                    <h3 className="text-slate-700 font-bold text-base mb-2">
                                        No {entityLabel} for "{selectedRefinements.join(', ')}"
                                    </h3>
                                    <p className="text-slate-400 text-sm max-w-xs mx-auto">
                                        {tradeDirection === 'IMPORT'
                                            ? `"${selectedRefinements.join(', ')}" has no import records in our current dataset. Try the Foreign Buyers or Pakistani Suppliers tabs — it may only appear in export data.`
                                            : `"${selectedRefinements.join(', ')}" has no export records in our current dataset. Try the Foreign Suppliers or Pakistani Buyers tabs — it may only appear in import data.`
                                        }
                                    </p>
                                </>
                            ) : (
                                <>
                                    <h3 className="text-slate-600 font-bold mb-1">No {entityLabel} Found</h3>
                                    <p className="text-slate-400 text-sm">Try switching to a different tab.</p>
                                </>
                            )}
                        </div>
                    )}

                    {!loading && !error && profiles.map((entity, idx) => {
                        const isLocked = accessState === 'NO_ACCESS';
                        
                        return (
                        <div
                            key={idx}
                            className={`action-card bg-white mb-4 transition-all relative overflow-hidden group ${isLocked ? 'pointer-events-none border-slate-200 shadow-sm' : 'hover:border-emerald-500 shadow-md cursor-default'}`}
                            style={{ padding: '1.5rem', marginBottom: '1.5rem' }}
                        >
                            <div className="flex justify-between items-start">
                                <div className="w-full">
                                    <div className="flex items-center gap-3 mb-1">
                                        <h3 className="text-xl font-bold text-slate-900 group-hover:text-emerald-700 transition-colors">
                                            {entity.name}
                                        </h3>
                                    </div>
                                    <div className="text-sm text-slate-500 mb-4 font-medium">{entity.country}</div>

                                    <div className="flex gap-8 text-sm text-slate-700">
                                        <div>
                                            <span className="block text-slate-400 text-xs uppercase font-bold tracking-wider">Avg Price</span>
                                            <span className="font-bold text-lg text-slate-800">
                                                {entity.avg_price > 0 ? `$${entity.avg_price.toFixed(2)}/MT` : 'N/A'}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="block text-slate-400 text-xs uppercase font-bold tracking-wider">Volume</span>
                                            <span className="font-bold text-lg text-slate-800">{entity.total_volume ? entity.total_volume.toLocaleString() : 0} MT</span>
                                        </div>
                                        <div>
                                            <span className="block text-slate-400 text-xs uppercase font-bold tracking-wider">Shipments</span>
                                            <span className="font-bold text-lg text-slate-800">{entity.shipment_count}</span>
                                        </div>
                                        <div>
                                            <span className="block text-slate-400 text-xs uppercase font-bold tracking-wider">Avg Shipment</span>
                                            <span className="font-bold text-lg text-slate-800">{entity.avg_shipment_vol ? entity.avg_shipment_vol.toLocaleString() : 0} MT</span>
                                        </div>
                                    </div>
                                </div>

                                {!isLocked ? (
                                    <div className="flex flex-col gap-3 ml-6 flex-shrink-0">
                                        <Link
                                            to={dealUrl(entity.name)}
                                            className="px-6 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-bold rounded-lg transition-all shadow-md shadow-emerald-500/20 text-center text-sm block min-w-[120px]"
                                        >
                                            View Deal
                                        </Link>
                                        <button
                                            onClick={() => toggleCompare(entity.name)}
                                            className={`px-4 py-2 border-2 text-sm font-bold rounded-md transition-colors ${
                                                selectedEntities.includes(entity.name)
                                                    ? 'bg-emerald-50 border-emerald-500 text-emerald-700'
                                                    : 'bg-white border-slate-200 text-slate-700 hover:border-emerald-500 hover:text-emerald-600'
                                            }`}
                                        >
                                            {selectedEntities.includes(entity.name) ? 'Added ✓' : 'Compare'}
                                        </button>
                                    </div>
                                ) : (
                                    <div className="flex flex-col gap-3 ml-6 flex-shrink-0 opacity-40 blur-sm pointer-events-none">
                                        <div className="w-[120px] h-[36px] bg-emerald-500 rounded-lg"></div>
                                        <div className="w-[120px] h-[38px] bg-slate-200 rounded-lg"></div>
                                    </div>
                                )}
                            </div>

                            <div className="mt-5 pt-4 border-t-2 border-slate-50 flex items-center text-xs text-slate-400 gap-4 font-medium transition-all">
                                <span className="flex items-center gap-1">
                                    <BarChart2 size={14} /> Based on {entity.shipment_count} shipments
                                </span>
                                <span>Last active: {entity.last_shipment_date || 'N/A'}</span>
                            </div>
                        </div>
                    )})}

                    {!loading && !error && accessState === 'NO_ACCESS' && profiles.length > 0 && (
                        <div className="mt-8 bg-gradient-to-br from-emerald-50 via-white to-teal-50/30 p-8 pt-10 rounded-2xl border border-emerald-200 shadow-xl overflow-hidden relative group">
                            <div className="absolute -top-12 -right-12 opacity-5 pointer-events-none transform group-hover:scale-110 transition-transform duration-700">
                                <Zap size={200} />
                            </div>
                            
                            <div className="relative z-10 text-center max-w-lg mx-auto">
                                <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center mx-auto mb-5 border border-emerald-100 text-emerald-600 rotate-3">
                                    <Lock size={28} />
                                </div>
                                
                                <h3 className="text-3xl font-black text-slate-900 mb-3 tracking-tight">
                                    {selectedRefinements.length > 0 ? 'Unlock Refined Intelligence' : 'Unlock Category Intelligence'}
                                </h3>
                                
                                <p className="text-slate-600 mb-8 font-medium leading-relaxed">
                                    {selectedRefinements.length > 0 
                                        ? `You're currently viewing restricted previews. Unlock to instantly reveal all supply chain metrics, pricing analytics, and actionable 'View Deal' links for ${selectedRefinements.join(', ')}.`
                                        : `You're currently viewing restricted previews. Unlock to instantly reveal complete lists, in-depth pricing, and contact details for every company operating in HS ${displayTarget}.`}
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
                                                    <span>Unlock for {currentTokenCost.toLocaleString()} Tokens</span>
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
            </div>

            {selectedEntities.length > 0 && (
                <div className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-slate-200 shadow-[0_-4px_20px_rgba(0,0,0,0.05)] p-4 z-50">
                    <div className="max-w-7xl mx-auto flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="h-10 w-10 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600">
                                <BarChart2 size={20} />
                            </div>
                            <div>
                                <p className="text-sm text-slate-500 font-bold uppercase tracking-wider">Comparing</p>
                                <p className="text-slate-900 font-bold">
                                    {selectedEntities[0]}
                                    {selectedEntities.length > 1 && <span className="text-emerald-600 ml-1">(+{selectedEntities.length - 1} more)</span>}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => setSelectedEntities([])}
                                className="px-4 py-2 text-sm font-bold text-slate-500 hover:text-slate-800 transition-colors"
                            >
                                Clear
                            </button>
                            <Link
                                to={compareUrl()}
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

export default DataDashboard;
