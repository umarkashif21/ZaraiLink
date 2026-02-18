import React, { useEffect, useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Filter, ChevronDown, CheckCircle, BarChart2 } from 'lucide-react';
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

                    // Extract unique countries for filter if not already set
                    const countries = [...new Set(data.results.map(s => s.country).filter(Boolean))].sort();
                    setAvailableCountries(countries);
                } else {
                    setResults([]);
                    setMatchedSubcategories([]);
                    setAvailableCountries([]); // Clear countries if no results
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
                    <h2 className="text-2xl font-bold text-gray-800 mb-6 font-primary">
                        {loading ? 'Searching...' : `${results.length} ${parsedIntent === 'SELL' ? 'Buyers' : 'Suppliers'} found for "${query}"`}
                    </h2>

                    {loading && <div className="text-center py-10 text-gray-500">Loading results...</div>}
                    {error && <div className="text-red-500 py-10">{error}</div>}

                    {!loading && !error && results.map((supplier, idx) => (
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
                                    <div className="text-xs text-gray-500 uppercase font-bold">{parsedIntent === 'SELL' ? 'Top Destination' : 'Top Origin'}</div>
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
