import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import { Filter, Search, AlertCircle, TrendingUp, BarChart2, ChevronRight } from 'lucide-react';
import '../Dashboard/Dashboard.css';

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

    const qp    = new URLSearchParams(location.search);
    const rawQuery = qp.get('q') || '';
    const hsCodeParam = qp.get('hs_code') || '';
    
    // The main target identifier (prefer hs_code if we routed from autocomplete)
    const displayTarget = hsCodeParam || rawQuery;

    const [activePill, setActivePill]           = useState(qp.get('dashboard_intent') || 'FOREIGN_SUPPLIERS');
    const [selectedRefinements, setSelectedRefinements] = useState(
        qp.get('refines') ? qp.get('refines').split(',').filter(Boolean) : []
    );

    const [hsDescription, setHsDescription] = useState('');
    const [totalShipments, setTotalShipments] = useState(0);
    const [sidebarCounts, setSidebarCounts]   = useState([]);
    const [profiles, setProfiles]             = useState([]);
    const [loading, setLoading]               = useState(true);
    const [error, setError]                   = useState(null);
    const [selectedEntities, setSelectedEntities] = useState([]);

    // Sync pill + refinements to URL
    useEffect(() => {
        const p = new URLSearchParams(location.search);
        let changed = false;
        if (p.get('dashboard_intent') !== activePill) { p.set('dashboard_intent', activePill); changed = true; }
        const refStr = selectedRefinements.join(',');
        if ((p.get('refines') || '') !== refStr) {
            refStr ? p.set('refines', refStr) : p.delete('refines');
            changed = true;
        }
        if (changed) navigate(`/search/results?${p.toString()}`, { replace: true });
    }, [activePill, selectedRefinements]); // eslint-disable-line

    // Fetch data
    useEffect(() => {
        if (!displayTarget) return;
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
                const res = await fetch(`${API_BASE}/api/search/hs-dashboard/?${params.toString()}`);
                if (!res.ok) throw new Error(`Server error: ${res.status}`);
                const data = await res.json();
                setHsDescription(data.hs_description || rawQuery);
                setTotalShipments(data.total_shipments || 0);
                // Only update sidebar counts when no refinement is active — keep full list visible
                if (selectedRefinements.length === 0) {
                    setSidebarCounts(data.sidebar_counts || []);
                }
                setProfiles(data.profiles || []);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [displayTarget, rawQuery, activePill, selectedRefinements]);

    const toggleRefinement = (name) => {
        setSelectedRefinements(prev =>
            prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name]
        );
    };

    const toggleCompare = (name) => {
        setSelectedEntities(prev => {
            if (prev.includes(name)) return prev.filter(n => n !== name);
            if (prev.length >= 4) { alert('You can compare up to 4 at once.'); return prev; }
            return [...prev, name];
        });
    };

    // Compute active pill metadata
    const pill = PILLS.find(p => p.id === activePill) || PILLS[0];
    const entityLabel = activePill.includes('SUPPLIER') ? 'Suppliers' : 'Buyers';

    // Filter profiles by selected refinements (sidebar cross-filter not supported for profiles — just show all)
    const visibleProfiles = profiles;

    // Build deal detail URL
    const dealUrl = (name) => {
        const params = new URLSearchParams({
            q:      rawQuery,
            scope:  pill.scope,
            intent: pill.intent,
        });
        return `/search/supplier/${encodeURIComponent(name)}?${params.toString()}`;
    };

    // Build compare URL
    const compareUrl = () => {
        const params = new URLSearchParams({
            suppliers: selectedEntities.join(','),
            q:         rawQuery,
            scope:     pill.scope,
            intent:    pill.intent,
        });
        return `/search/compare?${params.toString()}`;
    };

    return (
        <div className="dashboard-wrapper bg-gray-50 min-h-screen">
            <Navbar />

            {/* Header */}
            <div className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
                <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <TrendingUp className="text-indigo-600" size={22} />
                            <h1 className="text-xl font-bold text-gray-900">
                                Market Intelligence: <span className="text-indigo-600">{displayTarget}</span>
                            </h1>
                        </div>
                        <p className="text-sm text-gray-500 ml-7">
                            <span className="font-semibold text-gray-700">{hsDescription}</span>
                            {' · '}
                            <span className="text-indigo-600 font-bold">{totalShipments.toLocaleString()} total shipments</span>
                        </p>
                    </div>
                    <button
                        onClick={() => navigate('/search')}
                        className="text-indigo-600 font-bold hover:underline flex items-center gap-1 text-sm"
                    >
                        <Search size={14} /> New Search
                    </button>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 py-6 flex gap-6">

                {/* Left Sidebar — Refine by Product */}
                <div className="w-64 flex-shrink-0">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sticky top-24">
                        <h3 className="font-bold text-gray-900 flex items-center gap-2 mb-4 pb-2 border-b border-gray-100 text-sm uppercase tracking-wide">
                            <Filter size={15} /> Refine by Product
                        </h3>

                        {loading && <p className="text-xs text-gray-400">Loading...</p>}
                        {!loading && sidebarCounts.length === 0 && (
                            <p className="text-xs text-gray-400">No subcategories found.</p>
                        )}

                        <div className="space-y-2 max-h-[55vh] overflow-y-auto pr-1">
                            {sidebarCounts.map((sc, idx) => (
                                <label key={idx} className="flex items-start gap-2 cursor-pointer group">
                                    <input
                                        type="checkbox"
                                        checked={selectedRefinements.includes(sc.name)}
                                        onChange={() => toggleRefinement(sc.name)}
                                        className="mt-0.5 w-3.5 h-3.5 rounded border-gray-300 text-indigo-600"
                                    />
                                    <div className="flex-1 flex justify-between items-start text-xs">
                                        <span className="text-gray-700 group-hover:text-indigo-700 leading-tight">{sc.name}</span>
                                        <span className="ml-2 font-bold text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded-full flex-shrink-0">{sc.count}</span>
                                    </div>
                                </label>
                            ))}
                        </div>

                        {selectedRefinements.length > 0 && (
                            <button
                                onClick={() => setSelectedRefinements([])}
                                className="w-full mt-3 py-1.5 text-xs font-bold text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                            >
                                Clear All
                            </button>
                        )}
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-1 min-w-0">

                    {/* 4-Pill Switcher */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-2 mb-5 grid grid-cols-2 md:grid-cols-4 gap-2">
                        {PILLS.map(p => (
                            <button
                                key={p.id}
                                onClick={() => { setActivePill(p.id); setSelectedRefinements([]); setSelectedEntities([]); }}
                                className={`flex flex-col items-start px-3 py-2.5 rounded-lg transition-all text-left ${
                                    activePill === p.id
                                        ? 'bg-indigo-600 text-white shadow-md'
                                        : 'text-gray-500 hover:bg-indigo-50 hover:text-indigo-700'
                                }`}
                            >
                                <span className="font-bold text-sm">{p.label}</span>
                                <span className={`text-xs mt-0.5 ${activePill === p.id ? 'text-indigo-200' : 'text-gray-400'}`}>{p.sub}</span>
                            </button>
                        ))}
                    </div>

                    {/* Results header */}
                    {!loading && !error && (
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-xl font-bold text-gray-800">
                                {visibleProfiles.length} {entityLabel} found for HS {displayTarget}
                            </h2>
                        </div>
                    )}

                    {/* Loading */}
                    {loading && (
                        <div className="flex justify-center items-center py-20 bg-white rounded-xl shadow-sm border border-gray-200">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mr-3"></div>
                            <span className="text-indigo-500 font-medium">Loading market records...</span>
                        </div>
                    )}

                    {/* Error */}
                    {error && (
                        <div className="bg-red-50 text-red-600 p-4 rounded-xl font-medium border border-red-200 flex items-center gap-2 text-sm">
                            <AlertCircle size={18} /> {error}
                        </div>
                    )}

                    {/* Empty */}
                    {!loading && !error && visibleProfiles.length === 0 && (
                        <div className="bg-white rounded-xl shadow-sm border border-gray-200 py-16 text-center">
                            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📭</div>
                            <h3 className="text-gray-600 font-bold mb-1">No {entityLabel} Found</h3>
                            <p className="text-gray-400 text-sm">Try switching pills or clearing your refinements.</p>
                        </div>
                    )}

                    {/* Profile Cards */}
                    {!loading && !error && visibleProfiles.map((entity, idx) => (
                        <div
                            key={idx}
                            className="action-card bg-white mb-4 hover:border-emerald-500 transition-all cursor-default relative overflow-visible group"
                            style={{ padding: '1.5rem', marginBottom: '1.5rem' }}
                        >
                            <div className="flex justify-between items-start">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <h3 className="text-xl font-bold text-gray-900 group-hover:text-emerald-700 transition-colors">
                                            {entity.name}
                                        </h3>
                                    </div>
                                    <div className="text-sm text-gray-500 mb-4 font-medium">{entity.country}</div>

                                    <div className="flex gap-8 text-sm text-gray-700">
                                        <div>
                                            <span className="block text-gray-400 text-xs uppercase font-bold tracking-wider">Avg Price</span>
                                            <span className="font-bold text-lg text-gray-800">
                                                {entity.avg_price > 0 ? `$${entity.avg_price.toFixed(2)}/MT` : 'N/A'}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="block text-gray-400 text-xs uppercase font-bold tracking-wider">Volume</span>
                                            <span className="font-bold text-lg text-gray-800">{entity.total_volume.toLocaleString()} MT</span>
                                        </div>
                                        <div>
                                            <span className="block text-gray-400 text-xs uppercase font-bold tracking-wider">Shipments</span>
                                            <span className="font-bold text-lg text-gray-800">{entity.shipment_count}</span>
                                        </div>
                                        <div>
                                            <span className="block text-gray-400 text-xs uppercase font-bold tracking-wider">Avg Shipment</span>
                                            <span className="font-bold text-lg text-gray-800">{entity.avg_shipment_vol.toLocaleString()} MT</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex flex-col gap-3">
                                    <Link
                                        to={dealUrl(entity.name)}
                                        className="stat-action text-center"
                                        style={{ textDecoration: 'none' }}
                                    >
                                        View Deal
                                    </Link>
                                    <button
                                        onClick={() => toggleCompare(entity.name)}
                                        className={`px-4 py-2 border-2 text-sm font-bold rounded-md transition-colors ${
                                            selectedEntities.includes(entity.name)
                                                ? 'bg-emerald-50 border-emerald-500 text-emerald-700'
                                                : 'bg-white border-gray-200 text-gray-700 hover:border-emerald-500 hover:text-emerald-600'
                                        }`}
                                    >
                                        {selectedEntities.includes(entity.name) ? 'Added ✓' : 'Compare'}
                                    </button>
                                </div>
                            </div>

                            <div className="mt-5 pt-4 border-t-2 border-gray-50 flex items-center text-xs text-gray-400 gap-4 font-medium">
                                <span className="flex items-center gap-1">
                                    <BarChart2 size={14} /> Based on {entity.shipment_count} shipments
                                </span>
                                <span>Last active: {entity.last_shipment_date || 'N/A'}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Sticky Compare Bar */}
            {selectedEntities.length > 0 && (
                <div className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-gray-200 shadow-[0_-4px_20px_rgba(0,0,0,0.05)] p-4 z-50">
                    <div className="max-w-7xl mx-auto flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="h-10 w-10 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600">
                                <BarChart2 size={20} />
                            </div>
                            <div>
                                <p className="text-sm text-gray-500 font-bold uppercase tracking-wider">Comparing</p>
                                <p className="text-gray-900 font-bold">
                                    {selectedEntities[0]}
                                    {selectedEntities.length > 1 && <span className="text-emerald-600 ml-1">(+{selectedEntities.length - 1} more)</span>}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => setSelectedEntities([])}
                                className="px-4 py-2 text-sm font-bold text-gray-500 hover:text-gray-800 transition-colors"
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
