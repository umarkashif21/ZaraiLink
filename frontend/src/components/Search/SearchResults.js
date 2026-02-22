import React, { useEffect, useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Filter, CheckCircle, BarChart2, TrendingUp, TrendingDown, Globe, FileText } from 'lucide-react';
import Navbar from '../Layout/Navbar';
import '../Dashboard/Dashboard.css'; // Import shared styles
import searchService from '../../services/searchService';

const SearchResults = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const queryParams = new URLSearchParams(location.search);
    const initialQuery = queryParams.get('q') || '';
    const initialScope = queryParams.get('scope') || 'WORLDWIDE';

    const [query, setQuery] = useState(initialQuery);
    const [scope, setScope] = useState(initialScope);
    const [results, setResults] = useState([]);
    const [matchedSubcategories, setMatchedSubcategories] = useState([]);
    const [marketSnapshot, setMarketSnapshot] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [parsedIntent, setParsedIntent] = useState('BUY');

    // Country Comparison (Family 7)
    const [isCountryComparison, setIsCountryComparison] = useState(false);
    const [countryComparison, setCountryComparison] = useState([]);
    const [expandedCountry, setExpandedCountry] = useState(null);
    const [countryWarnings, setCountryWarnings] = useState([]);
    const [countryDataContext, setCountryDataContext] = useState(null);

    // Transaction Evidence (Family 8)
    const [isBuyerEvidence, setIsBuyerEvidence] = useState(false);
    const [evidenceTransactions, setEvidenceTransactions] = useState([]);
    const [buyerSummary, setBuyerSummary] = useState(null);
    const [similarBuyers, setSimilarBuyers] = useState([]);
    const [buyerFound, setBuyerFound] = useState(false);

    // Filters State
    const [selectedSubcategory, setSelectedSubcategory] = useState(null);
    const [selectedCountry, setSelectedCountry] = useState(null);
    const [availableCountries, setAvailableCountries] = useState([]);



    useEffect(() => {
        const fetchResults = async () => {
            setLoading(true);
            setError(null);
            try {
                const filters = { scope };
                if (selectedSubcategory) filters.subcategory_id = selectedSubcategory;
                if (selectedCountry) filters.country = selectedCountry;

                const data = await searchService.search(query, filters);

                if (data.results) {
                    setResults(data.results);
                    setMatchedSubcategories(data.matched_subcategories || []);
                    setMarketSnapshot(data.market_snapshot);
                    if (data.parsed_query && data.parsed_query.intent) {
                        setParsedIntent(data.parsed_query.intent);
                    }

                    // Reset all special-family states
                    setIsCountryComparison(false);
                    setCountryComparison([]);
                    setCountryWarnings([]);
                    setCountryDataContext(null);
                    setIsBuyerEvidence(false);
                    setEvidenceTransactions([]);
                    setBuyerSummary(null);
                    setSimilarBuyers([]);
                    setBuyerFound(false);

                    // Family 7 — Country Comparison
                    if (data.type === 'country_comparison' && data.country_comparison) {
                        setIsCountryComparison(true);
                        setCountryComparison(data.country_comparison);
                        setCountryWarnings(data.country_warnings || []);
                        setCountryDataContext(data.data_context || null);
                    }

                    // Family 8 — Transaction Evidence
                    if (data.type === 'transaction_evidence') {
                        setIsBuyerEvidence(true);
                        setEvidenceTransactions(data.transactions || []);
                        setBuyerSummary(data.buyer_summary || null);
                        setSimilarBuyers(data.similar_buyers || []);
                        setBuyerFound(data.buyer_found || false);
                    }

                    // Extract unique countries for filter if not already set
                    const countries = [...new Set(data.results.map(s => s.country).filter(Boolean))].sort();
                    setAvailableCountries(countries);
                } else {
                    setResults([]);
                    setMatchedSubcategories([]);
                    setAvailableCountries([]);
                    setIsCountryComparison(false);
                    setCountryComparison([]);
                }
            } catch (err) {
                console.error("Search failed", err);
                setError("Failed to fetch search results. Please try again.");
            } finally {
                setLoading(false);
            }
        };

        if (query) {
            fetchResults();
        }
    }, [query, scope, selectedSubcategory, selectedCountry]);

    // Handle new search from top bar
    const handleSearch = (e) => {
        e.preventDefault();
        // Reset filters on new search
        setSelectedSubcategory(null);
        setSelectedCountry(null);
        navigate(`/search/results?q=${encodeURIComponent(query)}&scope=${scope}`);
    };

    const clearFilters = () => {
        setSelectedSubcategory(null);
        setSelectedCountry(null);
    };

    return (
        <div className="dashboard-wrapper">
            <Navbar />

            {/* Search & Filter Bar (sticky below navbar) */}
            <div className="bg-white border-b-2 border-gray-100 sticky top-0 z-10 shadow-sm">
                <div className="dashboard-container" style={{ padding: '1rem 2rem', maxWidth: '1400px', margin: '0 auto' }}>
                    <form onSubmit={handleSearch} className="w-full relative">
                        <input
                            type="text"
                            value={query} onChange={(e) => setQuery(e.target.value)}
                            className="w-full pl-4 pr-10 py-3 rounded-full border-2 border-gray-200 focus:border-emerald-500 focus:ring-0 transition-all font-medium text-gray-700 placeholder-gray-400"
                            placeholder="Search details..."
                            style={{ fontSize: '1rem' }}
                        />
                    </form>
                </div>
            </div>

            <div className="dashboard-container flex gap-8" style={{ paddingTop: '2rem' }}>

                {/* Left Sidebar: Filters */}
                <aside className="w-64 hidden md:block space-y-6 flex-shrink-0">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-bold text-gray-700 flex items-center gap-2 text-lg">
                            <Filter size={20} /> Filters
                        </h3>
                        {(selectedSubcategory || selectedCountry) && (
                            <button onClick={clearFilters} className="text-sm text-emerald-600 hover:text-emerald-800 font-medium">
                                Reset
                            </button>
                        )}
                    </div>

                    {/* Product Filter */}
                    {matchedSubcategories.length > 0 && (
                        <div className="border-b-2 border-gray-100 pb-4">
                            <h4 className="flex items-center justify-between w-full text-sm font-bold text-gray-700 py-2">
                                Product
                            </h4>
                            <select
                                value={selectedSubcategory || ""}
                                onChange={(e) => setSelectedSubcategory(e.target.value ? parseInt(e.target.value) : null)}
                                className="w-full mt-2 block rounded-lg border-2 border-gray-200 py-2 pl-2 pr-8 text-sm focus:border-emerald-500 focus:outline-none transition-colors"
                            >
                                <option value="">All Products</option>
                                {matchedSubcategories.map(sub => (
                                    <option key={sub.id} value={sub.id}>
                                        {sub.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}

                    {/* Country Filter */}
                    {availableCountries.length > 0 && (
                        <div className="border-b-2 border-gray-100 pb-4">
                            <h4 className="flex items-center justify-between w-full text-sm font-bold text-gray-700 py-2">
                                Country
                            </h4>
                            <select
                                value={selectedCountry || ""}
                                onChange={(e) => setSelectedCountry(e.target.value || null)}
                                className="w-full mt-2 block rounded-lg border-2 border-gray-200 py-2 pl-2 pr-8 text-sm focus:border-emerald-500 focus:outline-none transition-colors"
                            >
                                <option value="">All Countries</option>
                                {availableCountries.map(country => (
                                    <option key={country} value={country}>
                                        {country}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}

                </aside>

                {/* Main Content: Results */}
                <main className="flex-1 space-y-4">

                    {loading && <div className="text-center py-10 text-gray-500">Loading results...</div>}
                    {error && <div className="text-red-500 py-10">{error}</div>}

                    {/* ── FAMILY 7: Country Comparison Table ── */}
                    {!loading && !error && isCountryComparison && (
                        <div>
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg">
                                    <Globe size={22} />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-800">Supply Source Countries</h2>
                                    <p className="text-sm text-gray-500 font-medium">{countryComparison.length} countries found for "{query}"</p>
                                </div>
                            </div>

                            {/* Data context note — always shown for Family 7 */}
                            {countryDataContext && (
                                <div className="flex items-start gap-2 mb-4 px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-700 font-medium">
                                    <span className="mt-0.5 flex-shrink-0">ℹ️</span>
                                    <span>{countryDataContext.note}</span>
                                </div>
                            )}

                            {/* Country filter warning — always shown for Family 7 */}
                            {countryWarnings.map((w, wi) => (
                                <div key={wi} className="flex items-start gap-2 mb-4 px-4 py-3 bg-amber-50 border border-amber-300 rounded-lg text-xs text-amber-800 font-medium">
                                    <span className="mt-0.5 flex-shrink-0">⚠️</span>
                                    <span>{w.message}</span>
                                </div>
                            ))}

                            {/* Empty state — with market entry cards if available */}
                            {countryComparison.length === 0 && (() => {
                                const notApplicable = countryWarnings.find(w => w.code === 'country_filter_not_applicable');
                                const staticNotes = notApplicable?.market_entry_notes || [];
                                return (
                                    <div>
                                        {staticNotes.length > 0 ? (
                                            <div>
                                                <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">
                                                    Market Entry Intelligence
                                                </p>
                                                <div className="grid grid-cols-1 gap-4 mb-6" style={{ gridTemplateColumns: `repeat(${staticNotes.length}, minmax(0, 1fr))` }}>
                                                    {staticNotes.map((item, i) => (
                                                        <div key={i} className="bg-white border-2 border-gray-100 rounded-xl p-5 shadow-sm">
                                                            <div className="flex items-center gap-2 mb-3">
                                                                <Globe size={16} className="text-emerald-500" />
                                                                <span className="font-bold text-gray-900 text-base">{item.country}</span>
                                                                {item.notes.tariff_tier === 'Home Market' && (
                                                                    <span className="ml-auto text-xs bg-blue-100 text-blue-700 font-bold px-2 py-0.5 rounded-full">Home</span>
                                                                )}
                                                            </div>
                                                            <div className="space-y-2 text-xs text-gray-600">
                                                                <div className="flex items-start gap-2">
                                                                    <span className="font-bold text-gray-700 w-20 flex-shrink-0">Tariff:</span>
                                                                    <span>{item.notes.tariff_tier}</span>
                                                                </div>
                                                                <div className="flex items-start gap-2">
                                                                    <span className="font-bold text-gray-700 w-20 flex-shrink-0">Lead Time:</span>
                                                                    <span>{item.notes.typical_lead_time}</span>
                                                                </div>
                                                                <div className="flex items-start gap-2">
                                                                    <span className="font-bold text-gray-700 w-20 flex-shrink-0">Packaging:</span>
                                                                    <span>{item.notes.packaging_note}</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                                <p className="text-xs text-gray-400 text-center">
                                                    No import transaction data found for these countries. Showing static trade intelligence only.
                                                </p>
                                            </div>
                                        ) : (
                                            <div className="text-center py-16 text-gray-400 font-medium">
                                                No country data found for this product.
                                            </div>
                                        )}
                                    </div>
                                );
                            })()}

                            {countryComparison.length > 0 && <div className="bg-white rounded-xl shadow-sm border-2 border-gray-100 overflow-hidden mb-8">
                                <div className="overflow-x-auto">
                                    <table className="w-full text-left text-sm text-gray-700">
                                        <thead className="bg-gray-50 text-gray-500 font-bold uppercase text-xs tracking-wider border-b-2 border-gray-100">
                                            <tr>
                                                <th className="px-5 py-4">#</th>
                                                <th className="px-5 py-4">Country</th>
                                                <th className="px-5 py-4">Total Volume</th>
                                                <th className="px-5 py-4">Avg Price</th>
                                                <th className="px-5 py-4">Suppliers</th>
                                                <th className="px-5 py-4">YoY Growth</th>
                                                <th className="px-5 py-4">Last Active</th>
                                                <th className="px-5 py-4">Details</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100">
                                            {countryComparison.map((c, idx) => (
                                                <React.Fragment key={c.country}>
                                                    <tr
                                                        className="hover:bg-gray-50 transition-colors cursor-pointer"
                                                        onClick={() => setExpandedCountry(expandedCountry === c.country ? null : c.country)}
                                                    >
                                                        <td className="px-5 py-4 text-gray-400 font-bold">{idx + 1}</td>
                                                        <td className="px-5 py-4">
                                                            <span className="font-bold text-gray-900 text-base">{c.country}</span>
                                                        </td>
                                                        <td className="px-5 py-4 font-bold text-gray-800 font-sans">
                                                            {c.total_volume.toLocaleString(undefined, { maximumFractionDigits: 0 })} MT
                                                        </td>
                                                        <td className="px-5 py-4 font-bold text-gray-800 font-sans">
                                                            ${c.avg_price.toFixed(2)}/MT
                                                        </td>
                                                        <td className="px-5 py-4">
                                                            <span className="px-2 py-1 bg-indigo-50 text-indigo-700 font-bold rounded text-xs border border-indigo-100">
                                                                {c.supplier_count}
                                                            </span>
                                                        </td>
                                                        <td className="px-5 py-4">
                                                            {c.demand_growth_pct === 0 ? (
                                                                <span className="text-gray-400 font-medium text-xs">Flat</span>
                                                            ) : (
                                                                <span className={`flex items-center gap-1 font-bold text-sm ${c.demand_growth_pct > 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                                                                    {c.demand_growth_pct > 0
                                                                        ? <TrendingUp size={14} />
                                                                        : <TrendingDown size={14} />}
                                                                    {c.demand_growth_pct > 0 ? '+' : ''}{c.demand_growth_pct}%
                                                                </span>
                                                            )}
                                                        </td>
                                                        <td className="px-5 py-4 text-gray-400 text-xs font-medium">
                                                            {c.last_active || '—'}
                                                        </td>
                                                        <td className="px-5 py-4">
                                                            <button className="text-xs text-emerald-600 font-bold hover:text-emerald-800 transition-colors">
                                                                {expandedCountry === c.country ? 'Hide ▲' : 'Show ▼'}
                                                            </button>
                                                        </td>
                                                    </tr>

                                                    {/* Expanded: top suppliers + market entry notes */}
                                                    {expandedCountry === c.country && (
                                                        <tr>
                                                            <td colSpan={8} className="px-5 py-0 bg-emerald-50 border-b border-emerald-100">
                                                                <div className="py-4 space-y-4">
                                                                    {/* Top suppliers */}
                                                                    <div>
                                                                        <p className="text-xs font-bold text-emerald-800 uppercase tracking-wider mb-3">
                                                                            Top Suppliers in {c.country}
                                                                        </p>
                                                                        {c.top_buyers.length === 0 ? (
                                                                            <p className="text-xs text-gray-400">No supplier data available.</p>
                                                                        ) : (
                                                                            <div className="flex flex-wrap gap-3">
                                                                                {c.top_buyers.map((b, bi) => (
                                                                                    <Link
                                                                                        key={bi}
                                                                                        to={`/search/supplier/${encodeURIComponent(b.name)}?q=${encodeURIComponent(query)}`}
                                                                                        className="flex-shrink-0 bg-white border border-emerald-200 rounded-lg p-3 hover:border-emerald-500 hover:shadow-sm transition-all"
                                                                                        style={{ textDecoration: 'none', minWidth: '180px' }}
                                                                                    >
                                                                                        <p className="font-bold text-gray-900 text-sm mb-1 truncate">{b.name}</p>
                                                                                        <p className="text-xs text-gray-500">
                                                                                            <span className="font-bold text-gray-700">{b.volume.toLocaleString(undefined, { maximumFractionDigits: 0 })} MT</span>
                                                                                            {' · '}
                                                                                            <span>${b.avg_price.toFixed(0)}/MT</span>
                                                                                            {' · '}
                                                                                            <span>{b.shipment_count} shipments</span>
                                                                                        </p>
                                                                                    </Link>
                                                                                ))}
                                                                            </div>
                                                                        )}
                                                                    </div>

                                                                    {/* Market entry notes */}
                                                                    {c.market_entry && Object.keys(c.market_entry).length > 0 && (
                                                                        <div className="border-t border-emerald-200 pt-3">
                                                                            <p className="text-xs font-bold text-emerald-800 uppercase tracking-wider mb-2">
                                                                                Trade Notes
                                                                            </p>
                                                                            <div className="flex flex-wrap gap-4 text-xs text-gray-600">
                                                                                {c.market_entry.tariff_tier && (
                                                                                    <span><span className="font-bold text-gray-700">Tariff:</span> {c.market_entry.tariff_tier}</span>
                                                                                )}
                                                                                {c.market_entry.typical_lead_time && (
                                                                                    <span><span className="font-bold text-gray-700">Lead Time:</span> {c.market_entry.typical_lead_time}</span>
                                                                                )}
                                                                                {c.market_entry.packaging_note && (
                                                                                    <span><span className="font-bold text-gray-700">Packaging:</span> {c.market_entry.packaging_note}</span>
                                                                                )}
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    )}
                                                </React.Fragment>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>}

                            {/* Secondary: all buyers below */}
                            {results.length > 0 && (
                                <div>
                                    <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center gap-2">
                                        <BarChart2 size={18} /> All {parsedIntent === 'SELL' ? 'Buyers' : 'Suppliers'} ({results.length})
                                    </h3>
                                    {results.map((supplier, idx) => (
                                        <div key={idx} className="action-card bg-white mb-4 hover:border-emerald-500 transition-all cursor-default relative overflow-visible group" style={{ padding: '1.25rem', marginBottom: '1rem' }}>
                                            <div className="flex justify-between items-center">
                                                <div>
                                                    <h3 className="text-lg font-bold text-gray-900 group-hover:text-emerald-700 transition-colors">{supplier.name}</h3>
                                                    <div className="text-sm text-gray-500 font-medium">{supplier.country}</div>
                                                    <div className="flex gap-6 text-sm text-gray-700 mt-2">
                                                        <span><span className="text-gray-400 text-xs uppercase font-bold">Avg Price </span><span className="font-bold">${supplier.avg_price.toFixed(2)}/MT</span></span>
                                                        <span><span className="text-gray-400 text-xs uppercase font-bold">Volume </span><span className="font-bold">{supplier.total_volume.toLocaleString()} MT</span></span>
                                                        <span><span className="text-gray-400 text-xs uppercase font-bold">Shipments </span><span className="font-bold">{supplier.shipment_count}</span></span>
                                                    </div>
                                                </div>
                                                <Link
                                                    to={`/search/supplier/${encodeURIComponent(supplier.name)}?q=${encodeURIComponent(query)}`}
                                                    className="stat-action text-center flex-shrink-0"
                                                    style={{ textDecoration: 'none' }}
                                                >
                                                    View Profile
                                                </Link>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* ── FAMILY 8: Transaction Evidence / Buyer Verification ── */}
                    {!loading && !error && isBuyerEvidence && (
                        <div>
                            {/* Header */}
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg">
                                    <FileText size={22} />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-800">Transaction Evidence</h2>
                                    <p className="text-sm text-gray-500 font-medium">{evidenceTransactions.length} records found for "{query}"</p>
                                </div>
                            </div>

                            {/* Buyer Summary Card */}
                            {buyerSummary && (
                                <div className="bg-white rounded-xl border-2 border-gray-100 p-5 mb-5 shadow-sm">
                                    <div className="flex items-center flex-wrap gap-2 mb-4">
                                        <h3 className="text-lg font-bold text-gray-900">{buyerSummary.buyer_name}</h3>
                                        <span className={`px-2.5 py-1 text-xs font-bold rounded-full ${
                                            buyerSummary.verification_status === 'Verified'
                                                ? 'bg-emerald-100 text-emerald-700'
                                                : 'bg-amber-100 text-amber-700'
                                        }`}>{buyerSummary.verification_status}</span>
                                        {buyerSummary.repeat_buyer && (
                                            <span className="px-2.5 py-1 text-xs bg-blue-100 text-blue-700 font-bold rounded-full">↻ Repeat Buyer</span>
                                        )}
                                    </div>
                                    <div className="grid grid-cols-2 gap-4" style={{ gridTemplateColumns: 'repeat(4, minmax(0, 1fr))' }}>
                                        <div>
                                            <p className="text-xs text-gray-400 font-bold uppercase tracking-wider mb-1">Total Volume</p>
                                            <p className="font-bold text-gray-900">{buyerSummary.total_volume.toLocaleString(undefined, { maximumFractionDigits: 0 })} MT</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-gray-400 font-bold uppercase tracking-wider mb-1">Avg Price</p>
                                            <p className="font-bold text-gray-900">${buyerSummary.avg_price.toFixed(2)}/MT</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-gray-400 font-bold uppercase tracking-wider mb-1">Shipments</p>
                                            <p className="font-bold text-gray-900">{buyerSummary.shipment_count}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-gray-400 font-bold uppercase tracking-wider mb-1">First Purchase</p>
                                            <p className="font-bold text-gray-900">{buyerSummary.first_purchase_date ? String(buyerSummary.first_purchase_date) : '—'}</p>
                                        </div>
                                    </div>
                                    <div className="mt-3 pt-3 border-t border-gray-100 flex gap-4 text-xs text-gray-500 font-medium">
                                        <span>Unique sellers: <span className="font-bold text-gray-700">{buyerSummary.unique_sellers}</span></span>
                                        <span>Months active: <span className="font-bold text-gray-700">{buyerSummary.months_active}</span></span>
                                        <span>Last purchase: <span className="font-bold text-gray-700">{buyerSummary.last_purchase_date ? String(buyerSummary.last_purchase_date) : '—'}</span></span>
                                    </div>
                                </div>
                            )}

                            {/* No exact match — suggest similar buyers */}
                            {!buyerFound && similarBuyers.length > 0 && (
                                <div className="mb-5 px-4 py-3 bg-amber-50 border border-amber-300 rounded-lg">
                                    <p className="text-sm font-bold text-amber-800 mb-2">⚠️ No exact match found. Did you mean:</p>
                                    <div className="flex flex-wrap gap-2">
                                        {similarBuyers.map((b, i) => (
                                            <span key={i} className="text-xs bg-white border border-amber-300 text-amber-800 font-bold px-3 py-1.5 rounded-lg">
                                                {b}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* True empty state */}
                            {evidenceTransactions.length === 0 && !buyerSummary && similarBuyers.length === 0 && (
                                <div className="text-center py-16 text-gray-400 font-medium">
                                    No transaction records found for this query.
                                </div>
                            )}

                            {/* Transaction table */}
                            {evidenceTransactions.length > 0 && (
                                <div className="bg-white rounded-xl shadow-sm border-2 border-gray-100 overflow-hidden mb-8">
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-left text-sm text-gray-700">
                                            <thead className="bg-gray-50 text-gray-500 font-bold uppercase text-xs tracking-wider border-b-2 border-gray-100">
                                                <tr>
                                                    <th className="px-4 py-3">Seller</th>
                                                    <th className="px-4 py-3">Buyer</th>
                                                    <th className="px-4 py-3">Qty (MT)</th>
                                                    <th className="px-4 py-3">Price ($/MT)</th>
                                                    <th className="px-4 py-3">Date</th>
                                                    <th className="px-4 py-3">Origin</th>
                                                    <th className="px-4 py-3">Shipping Agent</th>
                                                    <th className="px-4 py-3">Ref</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-100">
                                                {evidenceTransactions.map((tx, i) => (
                                                    <tr key={tx.id || i} className="hover:bg-gray-50 transition-colors">
                                                        <td className="px-4 py-3 font-medium text-gray-900 max-w-xs" style={{ maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{tx.seller}</td>
                                                        <td className="px-4 py-3 text-gray-700 max-w-xs" style={{ maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{tx.buyer}</td>
                                                        <td className="px-4 py-3 font-bold text-gray-800">{tx.qty_mt.toLocaleString(undefined, { maximumFractionDigits: 1 })}</td>
                                                        <td className="px-4 py-3 font-bold text-gray-800">${tx.usd_per_mt.toFixed(2)}</td>
                                                        <td className="px-4 py-3 text-gray-500 text-xs font-medium">{String(tx.date)}</td>
                                                        <td className="px-4 py-3 text-gray-500 text-xs">{tx.origin_country}</td>
                                                        <td className="px-4 py-3 text-gray-400 text-xs" style={{ maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{tx.shipping_agent || '—'}</td>
                                                        <td className="px-4 py-3 text-gray-400 text-xs font-mono">{tx.tx_reference || '—'}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* ── STANDARD Results (Families 1–6, 9) ── */}
                    {!loading && !error && !isCountryComparison && !isBuyerEvidence && (
                        <div>
                            <h2 className="text-2xl font-bold text-gray-800 mb-6 font-primary">
                                {results.length} {parsedIntent === 'SELL' ? 'Buyers' : 'Suppliers'} found for "{query}"
                            </h2>

                            {results.map((supplier, idx) => (
                                <div key={idx} className="action-card bg-white mb-4 hover:border-emerald-500 transition-all cursor-default relative overflow-visible group" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <h3 className="text-xl font-bold text-gray-900 group-hover:text-emerald-700 transition-colors">{supplier.name}</h3>
                                                {supplier.badges && supplier.badges.includes('Top Ranked') && (
                                                    <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs font-bold rounded-full flex items-center gap-1">
                                                        <CheckCircle size={12} /> Top Supplier
                                                    </span>
                                                )}
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
                                            </div>
                                        </div>

                                        <div className="flex flex-col gap-3">
                                            <Link
                                                to={`/search/supplier/${encodeURIComponent(supplier.name)}?q=${encodeURIComponent(query)}`}
                                                className="stat-action text-center"
                                                style={{ textDecoration: 'none' }}
                                            >
                                                View Deal
                                            </Link>
                                            <button className="px-4 py-2 bg-white border-2 border-gray-200 text-gray-700 text-sm font-bold rounded-md hover:border-emerald-500 hover:text-emerald-600 transition-colors">
                                                Compare
                                            </button>
                                        </div>
                                    </div>

                                    {/* Evidence / Footer */}
                                    <div className="mt-5 pt-4 border-t-2 border-gray-50 flex items-center text-xs text-gray-400 gap-4 font-medium">
                                        <span className="flex items-center gap-1"><BarChart2 size={14} /> Based on {supplier.shipment_count} shipments</span>
                                        <span>Last active: {supplier.last_shipment_date}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </main>

                {/* Right Panel: Market Snapshot */}
                <aside className="w-72 hidden lg:block space-y-6 flex-shrink-0">
                    {marketSnapshot && (
                        <div className="stat-card flex-col items-start gap-4">
                            <h4 className="font-bold text-gray-800 mb-2 w-full border-b-2 border-gray-100 pb-2">Market Snapshot</h4>
                            <div className="space-y-4 w-full">
                                <div>
                                    <div className="text-xs text-gray-500 uppercase font-bold">Global Avg Price</div>
                                    <div className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Courier New, monospace' }}>${marketSnapshot.avg_price_global.toFixed(2)}</div>
                                </div>
                                <div>
                                    <div className="text-xs text-gray-500 uppercase font-bold">{isCountryComparison ? 'Top Supply Source' : (parsedIntent === 'SELL' ? 'Top Destination' : 'Top Origin')}</div>
                                    <div className="text-lg font-bold text-gray-900">{marketSnapshot.top_country}</div>
                                </div>
                            </div>

                            <div className="mt-4 pt-4 border-t-2 border-gray-100 w-full">
                                <button className="w-full py-2 bg-emerald-50 text-emerald-700 text-sm font-bold rounded hover:bg-emerald-100 transition-colors">
                                    View Full Market Report
                                </button>
                            </div>
                        </div>
                    )}
                </aside>

            </div>
        </div>
    );
};

export default SearchResults;
