import React, { useEffect, useState } from 'react';
import { useParams, useSearchParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, BarChart2, TrendingUp, TrendingDown, FileText } from 'lucide-react';
// Recharts imports removed
// import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import searchService from '../../services/searchService';

const DealDetail = () => {
    const { name } = useParams(); // supplier name might need decoding
    const [searchParams] = useSearchParams();
    const query = searchParams.get('q') || '';
    const navigate = useNavigate();

    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchDetails = async () => {
            setLoading(true);
            try {
                const decodedName = decodeURIComponent(name);
                const result = await searchService.getSupplierDetails(decodedName, query);
                setData(result);
            } catch (err) {
                console.error("Failed to fetch supplier details", err);
                setError("Could not load supplier details.");
            } finally {
                setLoading(false);
            }
        };
        if (name) fetchDetails();
    }, [name, query]);

    if (loading) return <div className="flex justify-center items-center min-h-screen">Loading details...</div>;
    if (error) return <div className="flex justify-center items-center min-h-screen text-red-500">{error}</div>;
    if (!data) return null;

    const { supplier, comparables, market_context } = data;

    // Derived data
    const avgShipmentSize = supplier.stats.shipment_count > 0
        ? Math.round(supplier.stats.total_volume / supplier.stats.shipment_count)
        : 0;

    // Helper for Price Trend Bars (Quick Stats)
    // Normalize last 6 months of price data for the mini-chart
    const priceTrendData = supplier.sparkline.slice(-6).map(d => d.price);
    const maxPrice = Math.max(...priceTrendData, 1);
    const minPrice = Math.min(...priceTrendData, 0);
    // Simple normalization for visualization
    const normalizedBars = priceTrendData.map(p => {
        const range = maxPrice - minPrice || 1;
        return ((p - minPrice) / range) * 0.8 + 0.2; // Keep at least 20% height
    });

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            {/* Header / Breadcrumb */}
            <header className="bg-white border-b sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <Link to={`/search/results?q=${query}`} className="flex items-center text-gray-500 hover:text-indigo-600 mb-2">
                        <ArrowLeft size={16} className="mr-1" /> Back to Results
                    </Link>
                    <div className="flex justify-between items-start">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                                {supplier.name}
                                <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs font-semibold rounded-full flex items-center gap-1">
                                    <CheckCircle size={12} /> Verified Supplier
                                </span>
                                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs font-semibold rounded-full flex items-center gap-1">
                                    Top Supplier in Category
                                </span>
                            </h1>
                            <p className="text-gray-500 mt-1">Dextrose Anhydrous — Jan 2025 to Dec 2025</p>
                        </div>
                        <div className="flex gap-3">
                            <span className="px-3 py-1 bg-white border border-gray-300 rounded-full text-xs font-medium text-gray-700 shadow-sm">
                                250 Tokens
                            </span>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">

                {/* Top Key Stats Bar */}
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 grid grid-cols-1 md:grid-cols-3 gap-8 divide-x divide-gray-100">
                    <div className="flex items-center gap-4 px-4">
                        <div className="p-3 bg-gray-50 text-gray-600 rounded"><BarChart2 size={24} /></div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase font-medium">Volume Traded</p>
                            <p className="text-xl font-bold text-gray-900 flex items-end gap-1">
                                {supplier.stats.total_volume.toLocaleString()} MT
                                <TrendingUp size={16} className="text-green-500 mb-1" />
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 px-4">
                        <div className="p-3 bg-gray-50 text-gray-600 rounded"><FileText size={24} /></div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase font-medium">Shipments</p>
                            <p className="text-xl font-bold text-gray-900 flex items-end gap-1">
                                {supplier.stats.shipment_count}
                                <TrendingUp size={16} className="text-green-500 mb-1" />
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 px-4">
                        <div className="p-3 bg-gray-50 text-gray-600 rounded"><TrendingUp size={24} /></div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase font-medium">Avg Price</p>
                            <p className="text-xl font-bold text-gray-900 flex items-end gap-1">
                                ${supplier.stats.avg_price.toFixed(0)}/MT
                                <TrendingDown size={16} className="text-red-500 mb-1" />
                            </p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* LEFT SIDEBAR (FILTERS & INSIGHTS) - Cols 3/12 */}
                    <div className="lg:col-span-3 space-y-6">

                        {/* Filters */}
                        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="font-semibold text-gray-800 text-sm">Filters</h3>
                                <button className="text-xs text-gray-500 hover:text-indigo-600 flex items-center gap-1">
                                    Refresh
                                </button>
                            </div>
                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs font-medium text-gray-600 block mb-1.5">Date Range</label>
                                    <select className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50">
                                        <option>All Time</option>
                                        <option>Last 12 Months</option>
                                        <option>YTD</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs font-medium text-gray-600 block mb-1.5">Countries</label>
                                    <select className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50">
                                        <option>All Countries</option>
                                        {supplier.filters?.countries?.map((c, idx) => (
                                            <option key={idx} value={c}>{c}</option>
                                        )) || <option disabled>No countries</option>}
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs font-medium text-gray-600 block mb-1.5 flex justify-between">
                                        <span>Volume Range (MT)</span>
                                        <span className="text-gray-400">0 - 500</span>
                                    </label>
                                    <input type="range" className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer" />
                                </div>
                                <div>
                                    <label className="text-xs font-medium text-gray-600 block mb-1.5 flex justify-between">
                                        <span>Price Range ($/MT)</span>
                                        <span className="text-gray-400">50 - 1500</span>
                                    </label>
                                    <input type="range" className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer" />
                                </div>
                            </div>
                        </div>

                        {/* Quick Stats */}
                        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                            <h3 className="font-semibold text-gray-800 text-sm mb-3">Quick Stats</h3>
                            <div className="space-y-4">
                                <div className="p-3 bg-gray-50 rounded border border-gray-100 text-center">
                                    <p className="text-xs text-gray-500 mb-1">Average Shipment Size</p>
                                    <p className="text-lg font-bold text-gray-900">{avgShipmentSize} MT</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 mb-2">Price Trend (Last 6 Months)</p>
                                    <div className="h-8 bg-gray-100 rounded flex items-end justify-between px-1 pb-1">
                                        {normalizedBars.length > 0 ? normalizedBars.map((h, i) => (
                                            <div key={i} className="w-1 bg-indigo-300 rounded-t" style={{ height: `${h * 100}%` }}></div>
                                        )) : <span className="text-xs text-gray-400 p-1">No recent data</span>}
                                    </div>
                                    <p className="text-xs text-green-600 mt-1 flex items-center gap-1">
                                        <TrendingUp size={10} /> {market_context.price_trend || "Stable"}
                                    </p>
                                </div>
                                <div className="border-t border-gray-100 pt-3">
                                    <p className="text-xs text-gray-500 mb-1">Countries Supplied</p>
                                    <div className="flex flex-wrap gap-1">
                                        {supplier.filters?.countries?.slice(0, 5).map(c => (
                                            <span key={c} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">{c}</span>
                                        )) || <span className="text-xs text-gray-400">N/A</span>}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Typical Shipment Sizes */}
                        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                            <h3 className="font-semibold text-gray-800 text-sm mb-3">Typical Shipment Sizes</h3>
                            <div className="space-y-2 text-xs">
                                <div className="flex justify-between items-center py-1 border-b border-gray-50">
                                    <span className="font-medium text-gray-700">Quantity (MT)</span>
                                    <span className="font-medium text-gray-700">Avg Price</span>
                                </div>
                                {supplier.shipment_sizes ? supplier.shipment_sizes.map((item, idx) => (
                                    <div key={idx} className="flex justify-between items-center py-1">
                                        <span className="text-gray-600">{item.range} <span className="text-gray-400 text-[10px]">({item.count})</span></span>
                                        <span className="text-gray-900">${item.avg_price.toFixed(0)}/MT</span>
                                    </div>
                                )) : <p className="text-gray-400">No data available</p>}
                            </div>
                        </div>

                    </div>

                    {/* MAIN CONTENT - Cols 9/12 */}
                    <div className="lg:col-span-9 space-y-6">

                        {/* Transaction History Table */}
                        <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
                            <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                                <div>
                                    <h3 className="text-lg font-bold text-gray-800">Historical Shipments</h3>
                                    <p className="text-sm text-gray-500">Complete transaction history</p>
                                </div>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm text-gray-600">
                                    <thead className="bg-gray-50 text-gray-700 font-semibold uppercase text-xs">
                                        <tr>
                                            <th className="px-6 py-3">Buyer</th>
                                            <th className="px-6 py-3">Country</th>
                                            <th className="px-6 py-3">Quantity (MT)</th>
                                            <th className="px-6 py-3">Price (USD/MT)</th>
                                            <th className="px-6 py-3 text-right">Date</th>
                                            <th className="px-6 py-3 text-right">Trend</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {supplier.history.slice(0, 10).map((tx, idx) => (
                                            <tr key={tx.id || idx} className="hover:bg-gray-50 transition-colors">
                                                <td className="px-6 py-4 font-medium text-gray-900">{tx.buyer}</td>
                                                <td className="px-6 py-4">{tx.country}</td>
                                                <td className="px-6 py-4">{tx.quantity.toLocaleString()}</td>
                                                <td className="px-6 py-4">
                                                    <span className="bg-gray-100 px-2 py-1 rounded text-gray-700 font-medium">
                                                        ${tx.price.toFixed(2)}
                                                    </span>
                                                    <span className="text-xs text-gray-400 ml-2">Below market</span>
                                                </td>
                                                <td className="px-6 py-4 text-right">{tx.date}</td>
                                                <td className="px-6 py-4 text-right">
                                                    <BarChart2 size={16} className="text-gray-400 inline" />
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Supplier Insights Box */}
                        <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                            <h4 className="font-bold text-gray-800 mb-2">Supplier Insights</h4>
                            <p className="text-sm text-gray-600 mb-6 leading-relaxed">
                                Over the past year, <span className="font-semibold">{supplier.name}</span> consistently delivered 20-50 MT shipments to every month, with prices averaging 5% below market average. Their reliable delivery schedule and competitive pricing have made them the top supplier in this subcategory by volume, with particularly strong relationships in South Asian markets.
                            </p>
                            <div className="grid grid-cols-4 gap-4 text-center">
                                <div>
                                    <p className="text-xs text-gray-500 uppercase mb-1">Reliability Score</p>
                                    <p className="text-lg font-bold text-gray-900">94/100</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 uppercase mb-1">On-Time Delivery</p>
                                    <p className="text-lg font-bold text-gray-900">98%</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 uppercase mb-1">Repeat Buyers</p>
                                    <p className="text-lg font-bold text-gray-900">82%</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 uppercase mb-1">Market Position</p>
                                    <p className="text-lg font-bold text-gray-900">#1</p>
                                </div>
                            </div>
                        </div>

                        {/* Comparable Suppliers (Horizontal) */}
                        <div>
                            <h4 className="font-bold text-gray-800 mb-4">Comparable Suppliers</h4>
                            <p className="text-xs text-gray-500 mb-4 -mt-3">Similar suppliers in this category for comparison</p>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                {comparables && comparables.length > 0 ? comparables.slice(0, 3).map((comp, idx) => (
                                    <div key={idx} className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer"
                                        onClick={() => navigate(`/search/supplier/${encodeURIComponent(comp.name)}?q=${encodeURIComponent(query)}`)}
                                    >
                                        <h5 className="font-bold text-gray-900 text-sm mb-2">{comp.name}</h5>
                                        <div className="space-y-1 text-xs text-gray-600 mb-3">
                                            <div className="flex justify-between">
                                                <span>Volume Traded:</span>
                                                <span className="font-medium text-gray-900">{comp.total_volume.toLocaleString()} MT</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span>Avg Price:</span>
                                                <span className="font-medium text-gray-900">${comp.avg_price.toFixed(0)}/MT</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span>Shipments:</span>
                                                <span className="font-medium text-gray-900">{comp.shipment_count}</span>
                                            </div>
                                        </div>
                                        {/* Decorative mini-sparkline (randomized as backend doesn't provide sparkline for comps yet) */}
                                        <div className="h-6 bg-gray-50 rounded flex items-end px-1 gap-1">
                                            {[...Array(10)].map((_, i) => (
                                                <div key={i} className={`w-full bg-gray-300 rounded-t`} style={{ height: `${Math.random() * 80 + 20}%` }}></div>
                                            ))}
                                        </div>
                                    </div>
                                )) : <p className="text-gray-500 text-sm">No comparable suppliers found.</p>}
                            </div>
                        </div>

                        {/* Who Else Is Buying Box */}
                        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                            <h4 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                                <span className="bg-gray-100 p-1 rounded-full"><i className="lucide-users"></i></span>
                                Who Else is Buying From Them?
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="border border-gray-100 p-4 rounded bg-gray-50">
                                    <p className="text-xs text-gray-500 font-medium mb-1">Recent Buyers (Last 30 Days)</p>
                                    <p className="text-2xl font-bold text-gray-900">{supplier.buyer_insights?.recent_buyers || 0}</p>
                                    <p className="text-xs text-gray-400 mt-1">Active in last month</p>
                                </div>
                                <div className="border border-gray-100 p-4 rounded bg-gray-50">
                                    <p className="text-xs text-gray-500 font-medium mb-1">Total Active Relationships</p>
                                    <p className="text-2xl font-bold text-gray-900">{supplier.buyer_insights?.total_relationships || 0}</p>
                                    <p className="text-xs text-gray-400 mt-1">Lifetime unique buyers</p>
                                </div>
                            </div>
                        </div>

                        {/* Take Action */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
                            <button className="flex flex-col items-center justify-center p-6 bg-white border border-gray-200 rounded-lg hover:border-indigo-500 hover:shadow-md transition-all group">
                                <div className="p-3 bg-gray-50 text-gray-600 rounded-full mb-3 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
                                    <FileText size={24} />
                                </div>
                                <span className="font-bold text-gray-900 text-sm">Contact Supplier</span>
                                <span className="text-xs text-gray-500 mt-1">Reach out for quote</span>
                            </button>
                            <button className="flex flex-col items-center justify-center p-6 bg-white border border-gray-200 rounded-lg hover:border-indigo-500 hover:shadow-md transition-all group">
                                <div className="p-3 bg-gray-50 text-gray-600 rounded-full mb-3 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
                                    <BarChart2 size={24} />
                                </div>
                                <span className="font-bold text-gray-900 text-sm">View Full Trade Ledger</span>
                                <span className="text-xs text-gray-500 mt-1">See full shipment history</span>
                            </button>
                            <button className="flex flex-col items-center justify-center p-6 bg-white border border-gray-200 rounded-lg hover:border-indigo-500 hover:shadow-md transition-all group">
                                <div className="p-3 bg-gray-50 text-gray-600 rounded-full mb-3 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
                                    <TrendingUp size={24} />
                                </div>
                                <span className="font-bold text-gray-900 text-sm">Market Context</span>
                                <span className="text-xs text-gray-500 mt-1">Check current price trends</span>
                            </button>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
};

export default DealDetail;
