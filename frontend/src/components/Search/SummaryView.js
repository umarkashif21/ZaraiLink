import React, { useEffect, useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import { Package, ChevronRight } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_BASE_URL;

const SummaryView = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const queryParams = new URLSearchParams(location.search);
    const query = queryParams.get('q') || '';
    // Strip ALL dots, not just the first one
    const clean_q = query.replace(/\./g, '');

    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const isNumeric = /^\d+$/.test(clean_q);

    useEffect(() => {
        // Guard: if already 7+ raw digits it should be a DataDashboard, not SummaryView
        if (!clean_q || (isNumeric && clean_q.length >= 7)) return;

        const fetchSummary = async () => {
            setLoading(true);
            try {
                // Send the raw query (with dot preserved) so backend startswith matches correctly
                const res = await fetch(`${API_BASE}/api/search/hs-summary/?q=${encodeURIComponent(query)}`);
                if (!res.ok) throw new Error('Failed to fetch summary data');
                const data = await res.json();
                setResults(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchSummary();
    }, [clean_q]);

    if (isNumeric && clean_q.length >= 7) {
        return null;
    }

    return (
        <div className="dashboard-wrapper min-h-screen bg-gray-50 flex flex-col items-center">
            <Navbar />
            <div className="max-w-4xl w-full px-4 pt-10 pb-20 mt-12 bg-white shadow-xl rounded-xl border border-gray-100">
                <div className="text-center mb-10">
                    <h1 className="text-3xl font-bold text-gray-900 mb-3">
                        HS Category: <span className="text-indigo-600">{query}</span>
                    </h1>
                    <p className="text-gray-500 max-w-lg mx-auto">
                        This is a broad category. Select a specific 8-digit product from the sub-categories below to view deep-dive trade data, pricing, and suppliers.
                    </p>
                </div>

                {loading && (
                    <div className="flex justify-center items-center py-20 text-indigo-500">
                        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
                        <span className="ml-3 font-medium">Loading sub-categories...</span>
                    </div>
                )}

                {error && (
                    <div className="bg-red-50 text-red-600 p-4 rounded-lg text-center font-medium border border-red-200">
                        {error}
                    </div>
                )}

                {!loading && !error && results.length === 0 && (
                    <div className="text-center py-16 text-gray-400 border-2 border-dashed border-gray-200 rounded-xl">
                        <Package size={48} className="mx-auto mb-4 text-gray-300" />
                        <h3 className="font-bold text-lg text-gray-600">No data found</h3>
                        <p>No trade records found within this specific category.</p>
                        <button onClick={() => navigate('/search')} className="mt-4 text-indigo-600 font-bold hover:underline">
                            Return to Search
                        </button>
                    </div>
                )}

                {!loading && results.length > 0 && (
                    <div className="space-y-4">
                        {results.map((item, idx) => (
                            <div key={item.hs_code || idx} className="flex flex-col md:flex-row items-start md:items-center justify-between p-5 bg-gray-50 rounded-xl hover:bg-indigo-50 transition-colors border border-transparent hover:border-indigo-100">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <Package size={18} className="text-indigo-500" />
                                        <h3 className="text-lg font-bold text-gray-900">{item.name}</h3>
                                    </div>
                                    <div className="text-sm font-medium text-gray-500">
                                        HS Code: <span className="font-bold text-gray-700">{item.hs_code}</span>
                                    </div>
                                </div>
                                
                                <div className="flex flex-col items-end mt-4 md:mt-0 gap-2">
                                    <span className="bg-white px-3 py-1 rounded-full text-xs font-bold text-gray-600 border border-gray-200 shadow-sm">
                                        {item.count.toLocaleString()} shipments found
                                    </span>
                                    <Link 
                                        to={`/search/results?q=${encodeURIComponent(item.hs_code)}&hs_code=${encodeURIComponent(item.hs_code)}${item.is_leaf ? '&mode=dashboard' : ''}`}
                                        className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-5 rounded-lg flex items-center gap-1 transition-transform hover:scale-105"
                                        style={{ textDecoration: 'none' }}
                                    >
                                        View Trade Data <ChevronRight size={16} />
                                    </Link>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default SummaryView;
