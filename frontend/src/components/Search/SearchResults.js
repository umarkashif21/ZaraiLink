import React, { useEffect, useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Filter, ChevronDown, CheckCircle, BarChart2 } from 'lucide-react';
import searchService from '../../services/searchService'; // Ensure this matches actual location

const SearchResults = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const queryParams = new URLSearchParams(location.search);
    const initialQuery = queryParams.get('q') || '';

    const [query, setQuery] = useState(initialQuery);
    const [results, setResults] = useState([]);
    const [matchedSubcategories, setMatchedSubcategories] = useState([]);
    const [marketSnapshot, setMarketSnapshot] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Filters State
    const [selectedSubcategory, setSelectedSubcategory] = useState(null);
    const [selectedCountry, setSelectedCountry] = useState(null);
    const [availableCountries, setAvailableCountries] = useState([]);



    useEffect(() => {
        const fetchResults = async () => {
            setLoading(true);
            setError(null);
            try {
                const filters = {};
                if (selectedSubcategory) filters.subcategory_id = selectedSubcategory;
                if (selectedCountry) filters.country = selectedCountry;

                const data = await searchService.search(query, filters);

                if (data.results) {
                    setResults(data.results);
                    setMatchedSubcategories(data.matched_subcategories || []);
                    setMarketSnapshot(data.market_snapshot);

                    // Extract unique countries for filter if not already set
                    // This should always update based on current results, not just if selectedCountry is null
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
    }, [query, selectedSubcategory, selectedCountry]);

    // Handle new search from top bar
    const handleSearch = (e) => {
        e.preventDefault();
        // Reset filters on new search
        setSelectedSubcategory(null);
        setSelectedCountry(null);
        // Update URL if needed, but for now just trigger effect via query state
        navigate(`/search/results?q=${encodeURIComponent(query)}`);
    };

    const clearFilters = () => {
        setSelectedSubcategory(null);
        setSelectedCountry(null);
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Top Bar */}
            <header className="bg-white shadow-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-4">
                    <Link to="/search" className="font-bold text-indigo-600 text-xl">ZaraiLink</Link>
                    <form onSubmit={handleSearch} className="flex-1 max-w-2xl relative">
                        <input
                            type="text"
                            value={query} onChange={(e) => setQuery(e.target.value)}
                            className="w-full pl-4 pr-10 py-2 rounded-full border border-gray-300 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                        />
                    </form>
                    {/* User Avatar Placeholder */}
                    <div className="w-8 h-8 bg-gray-200 rounded-full ml-auto"></div>
                </div>
            </header>

            <div className="flex-1 max-w-7xl mx-auto w-full px-4 py-6 flex gap-6">

                {/* Left Sidebar: Filters */}
                <aside className="w-64 hidden md:block space-y-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-gray-700 flex items-center gap-2">
                            <Filter size={18} /> Filters
                        </h3>
                        {(selectedSubcategory || selectedCountry) && (
                            <button onClick={clearFilters} className="text-sm text-indigo-600 hover:text-indigo-800">
                                Reset
                            </button>
                        )}
                    </div>

                    {/* Product Filter */}
                    {matchedSubcategories.length > 0 && (
                        <div className="border-b border-gray-200 pb-4">
                            <h4 className="flex items-center justify-between w-full text-sm font-medium text-gray-700 py-2">
                                Product
                            </h4>
                            <select
                                value={selectedSubcategory || ""}
                                onChange={(e) => setSelectedSubcategory(e.target.value ? parseInt(e.target.value) : null)}
                                className="w-full mt-2 block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm border"
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
                        <div className="border-b border-gray-200 pb-4">
                            <h4 className="flex items-center justify-between w-full text-sm font-medium text-gray-700 py-2">
                                Country
                            </h4>
                            <select
                                value={selectedCountry || ""}
                                onChange={(e) => setSelectedCountry(e.target.value || null)}
                                className="w-full mt-2 block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm border"
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
                    <h2 className="text-xl font-semibold text-gray-800 mb-4">
                        {loading ? 'Searching...' : `${results.length} Suppliers found for "${query}"`}
                    </h2>

                    {loading && <div className="text-center py-10">Loading results...</div>}
                    {error && <div className="text-red-500 py-10">{error}</div>}

                    {!loading && !error && results.map((supplier, idx) => (
                        <div key={idx} className="bg-white rounded-lg shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <h3 className="text-lg font-bold text-gray-900">{supplier.name}</h3>
                                        {supplier.badges && supplier.badges.includes('Top Ranked') && (
                                            <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded-full flex items-center gap-1">
                                                <CheckCircle size={12} /> Top Supplier
                                            </span>
                                        )}
                                    </div>
                                    <div className="text-sm text-gray-500 mb-3">{supplier.country}</div>

                                    <div className="flex gap-6 text-sm text-gray-700">
                                        <div>
                                            <span className="block text-gray-400 text-xs uppercase">Avg Price</span>
                                            <span className="font-semibold">${supplier.avg_price.toFixed(2)}/MT</span>
                                        </div>
                                        <div>
                                            <span className="block text-gray-400 text-xs uppercase">Volume</span>
                                            <span className="font-semibold">{supplier.total_volume.toLocaleString()} MT</span>
                                        </div>
                                        <div>
                                            <span className="block text-gray-400 text-xs uppercase">Shipments</span>
                                            <span className="font-semibold">{supplier.shipment_count}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex flex-col gap-2">
                                    <Link
                                        to={`/search/supplier/${encodeURIComponent(supplier.name)}?q=${encodeURIComponent(query)}`}
                                        className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 text-center"
                                    >
                                        View Deal
                                    </Link>
                                    <button className="px-4 py-2 bg-white border border-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-50">
                                        Compare
                                    </button>
                                </div>
                            </div>

                            {/* Evidence / Footer */}
                            <div className="mt-4 pt-3 border-t border-gray-50 flex items-center text-xs text-gray-400 gap-4">
                                <span className="flex items-center gap-1"><BarChart2 size={12} /> Based on {supplier.shipment_count} shipments</span>
                                <span>Last active: {supplier.last_shipment_date}</span>
                            </div>
                        </div>
                    ))}
                </main>

                {/* Right Panel: Market Snapshot */}
                <aside className="w-72 hidden lg:block space-y-6">
                    {marketSnapshot && (
                        <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-5">
                            <h4 className="font-semibold text-gray-800 mb-4 border-b pb-2">Market Snapshot</h4>
                            <div className="space-y-4">
                                <div>
                                    <div className="text-sm text-gray-500">Global Avg Price</div>
                                    <div className="text-xl font-bold text-gray-900">${marketSnapshot.avg_price_global.toFixed(2)}</div>
                                </div>
                                <div>
                                    <div className="text-sm text-gray-500">Active Suppliers</div>
                                    <div className="text-xl font-bold text-gray-900">{marketSnapshot.total_suppliers}</div>
                                    <div className="text-xs text-green-600 mt-1">+12% vs last month</div>
                                </div>
                                <div>
                                    <div className="text-sm text-gray-500">Top Origin</div>
                                    <div className="font-medium text-gray-900">{marketSnapshot.top_country}</div>
                                </div>
                            </div>

                            <div className="mt-6 pt-4 border-t">
                                <button className="w-full py-2 bg-gray-50 text-indigo-600 text-sm font-medium rounded hover:bg-gray-100">
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
