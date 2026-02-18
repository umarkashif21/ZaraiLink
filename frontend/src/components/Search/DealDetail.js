import React, { useEffect, useState } from 'react';
import { useParams, useSearchParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, BarChart2, TrendingUp, TrendingDown, FileText, Package, Globe, Calendar } from 'lucide-react';
import Navbar from '../Layout/Navbar';
import '../Dashboard/Dashboard.css'; // Shared styles for layout
import searchService from '../../services/searchService';

const DealDetail = () => {
    const { name } = useParams();
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
                console.error("Failed to fetch details", err);
                setError("Could not load details. Please try again.");
            } finally {
                setLoading(false);
            }
        };
        if (name) fetchDetails();
    }, [name, query]);

    if (loading) return <div className="flex justify-center items-center min-h-screen text-gray-500 font-medium">Loading details...</div>;
    if (error) return <div className="flex justify-center items-center min-h-screen text-red-500 font-medium">{error}</div>;
    if (!data) return null;

    const { supplier, comparables, market_context, type } = data;
    const isBuyer = type === 'BUYER';

    // Dynamic Labels
    const labels = isBuyer ? {
        titleType: "Buyer",
        verifiedBadge: "Verified Buyer",
        topBadge: "Top Buyer in Category",
        volume: "Volume Purchased",
        shipments: "Shipments Received",
        price: "Avg Purchase Price",
        countries: "Countries Sourced From",
        tableEntity: "Supplier",
        tableOrigin: "Origin",
        insightTitle: "Buyer Insights",
        insightText: `Consistently imports volume monthly, prefers competitive pricing, maintains long-term supplier relationships.`,
        ctaContact: "Connect With Buyer",
        ctaSub: "Offer Supply",
        ctaLedger: "View Purchase Ledger",
        ctaMarket: "Demand Context",
        compTitle: "Comparable Buyers",
        compSub: "Similar importers in this category"
    } : {
        titleType: "Supplier",
        verifiedBadge: "Verified Supplier",
        topBadge: "Top Supplier in Category",
        volume: "Volume Traded",
        shipments: "Shipments Sent",
        price: "Avg Selling Price",
        countries: "Countries Supplied",
        tableEntity: "Buyer",
        tableOrigin: "Destination",
        insightTitle: "Supplier Insights",
        insightText: `Delivers consistent volume monthly with competitive pricing. Strong relationships in key markets.`,
        ctaContact: "Contact Supplier",
        ctaSub: "Reach out for quote",
        ctaLedger: "View Sales Ledger",
        ctaMarket: "Market Context",
        compTitle: "Comparable Suppliers",
        compSub: "Similar exporters in this category"
    };

    // Derived data
    const avgShipmentSize = supplier.stats.shipment_count > 0
        ? Math.round(supplier.stats.total_volume / supplier.stats.shipment_count)
        : 0;

    // Helper for Price Trend (Quick Stats)
    const priceTrendData = supplier.sparkline.slice(-6).map(d => d.price);
    const maxPrice = Math.max(...priceTrendData, 1);
    const minPrice = Math.min(...priceTrendData, 0);
    const normalizedBars = priceTrendData.map(p => {
        const range = maxPrice - minPrice || 1;
        return ((p - minPrice) / range) * 0.8 + 0.2;
    });

    return (
        <div className="dashboard-wrapper pb-20">
            <Navbar />

            {/* Header */}
            <header className="bg-white border-b-2 border-gray-100 sticky top-0 z-10 shadow-sm">
                <div className="dashboard-container" style={{ padding: '1rem 2rem', maxWidth: '1400px', margin: '0 auto' }}>
                    <Link to={`/search/results?q=${encodeURIComponent(query)}`} className="flex items-center text-gray-500 hover:text-emerald-600 mb-2 font-medium transition-colors w-fit">
                        <ArrowLeft size={16} className="mr-1" /> Back to Results
                    </Link>
                    <div className="flex justify-between items-start">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                                {supplier.name}
                                {/* Removed Tags as per request, kept clean */}
                            </h1>
                            <p className="text-gray-500 mt-1 font-medium flex items-center gap-2">
                                <Package size={16} /> Data for: <span className="text-gray-800 font-bold">{query}</span>
                                <span className="mx-2">•</span>
                                <Calendar size={16} /> Last Active: {supplier.stats.last_shipment_date || 'N/A'}
                            </p>
                        </div>
                    </div>
                </div>
            </header>

            <div className="dashboard-container space-y-8" style={{ paddingTop: '2rem' }}>

                {/* Top Key Stats Bar - Keeping layout but ensuring clean font */}
                <div className="bg-white rounded-xl shadow-sm border-2 border-gray-100 p-6 grid grid-cols-1 md:grid-cols-3 gap-8 divide-x-2 divide-gray-100 items-center">
                    <div className="flex items-center gap-4 px-4 w-full">
                        <div className="p-4 bg-emerald-50 text-emerald-600 rounded-xl"><Package size={28} /></div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase font-bold tracking-wider">{labels.volume}</p>
                            <p className="text-2xl font-bold text-gray-900 flex items-end gap-2 font-sans">
                                {supplier.stats.total_volume.toLocaleString()} MT
                                <TrendingUp size={20} className="text-emerald-500 mb-1" />
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 px-4 w-full">
                        <div className="p-4 bg-indigo-50 text-indigo-600 rounded-xl"><Globe size={28} /></div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase font-bold tracking-wider">{labels.shipments}</p>
                            <p className="text-2xl font-bold text-gray-900 flex items-end gap-2 font-sans">
                                {supplier.stats.shipment_count}
                                <TrendingUp size={20} className="text-emerald-500 mb-1" />
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 px-4 w-full">
                        <div className="p-4 bg-orange-50 text-orange-600 rounded-xl"><TrendingUp size={28} /></div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase font-bold tracking-wider">{labels.price}</p>
                            <p className="text-2xl font-bold text-gray-900 flex items-end gap-2 font-sans">
                                ${supplier.stats.avg_price.toFixed(0)}/MT
                                {isBuyer ?
                                    <span className="text-sm font-normal text-gray-400">Paid</span> :
                                    <TrendingDown size={20} className="text-red-500 mb-1" />
                                }
                            </p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* LEFT SIDEBAR (FILTERS & INSIGHTS) - Cols 3/12 */}
                    <div className="lg:col-span-3 space-y-6">

                        {/* Filters - Reverted to clean style */}
                        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="font-bold text-gray-800 text-sm uppercase tracking-wide">Filters</h3>
                                <button className="text-xs text-gray-500 hover:text-emerald-600 flex items-center gap-1 font-medium transition-colors">
                                    Refresh
                                </button>
                            </div>
                            <div className="space-y-5">
                                <div>
                                    <label className="text-xs font-bold text-gray-600 block mb-2">Date Range</label>
                                    <select className="w-full text-sm border border-gray-300 rounded-md shadow-sm focus:border-emerald-500 focus:ring-emerald-500 bg-gray-50 py-2">
                                        <option>Last 3 Months</option>
                                        <option>Last 6 Months</option>
                                        <option>Last 12 Months</option>
                                        <option>All Time</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs font-bold text-gray-600 block mb-2">{labels.countries}</label>
                                    <select className="w-full text-sm border border-gray-300 rounded-md shadow-sm focus:border-emerald-500 focus:ring-emerald-500 bg-gray-50 py-2">
                                        <option>All Countries</option>
                                        {supplier.filters?.countries?.map((c, idx) => (
                                            <option key={idx} value={c}>{c}</option>
                                        )) || <option disabled>No countries</option>}
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs font-bold text-gray-600 block mb-2 flex justify-between">
                                        <span>Volume Range (MT)</span>
                                    </label>
                                    <input type="range" className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-500" />
                                </div>
                                <div>
                                    <label className="text-xs font-bold text-gray-600 block mb-2 flex justify-between">
                                        <span>Price Range ($/MT)</span>
                                    </label>
                                    <input type="range" className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-500" />
                                </div>
                            </div>
                        </div>

                        {/* Quick Stats - Reverted to clean style */}
                        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
                            <h3 className="font-bold text-gray-800 text-sm mb-4 uppercase tracking-wide">Quick Stats</h3>
                            <div className="space-y-4">
                                <div className="p-3 bg-gray-50 rounded-lg border border-gray-100 text-center">
                                    <p className="text-xs text-gray-500 mb-1 font-bold">{isBuyer ? 'Avg Order Size' : 'Avg Shipment Size'}</p>
                                    <p className="text-xl font-bold text-gray-900 font-sans">{avgShipmentSize} MT</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 mb-2 font-bold">{isBuyer ? 'Purchase Price Trend' : 'Selling Price Trend'}</p>
                                    <div className="h-10 bg-gray-50 rounded-lg flex items-end justify-between px-2 pb-2 border border-gray-100">
                                        {normalizedBars.length > 0 ? normalizedBars.map((h, i) => (
                                            <div key={i} className="w-1.5 bg-emerald-400 rounded-t" style={{ height: `${h * 100}%` }}></div>
                                        )) : <span className="text-xs text-gray-400 p-1">No recent data</span>}
                                    </div>
                                    <p className="text-xs text-emerald-600 mt-2 flex items-center gap-1 font-bold justify-center">
                                        <TrendingUp size={12} /> {market_context.price_trend || "Stable"}
                                    </p>
                                </div>
                                <div className="border-t border-gray-100 pt-3">
                                    <p className="text-xs text-gray-500 mb-2 font-bold">{labels.countries}</p>
                                    <div className="flex flex-wrap gap-2">
                                        {supplier.filters?.countries?.slice(0, 5).map(c => (
                                            <span key={c} className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded font-medium border border-gray-200">{c}</span>
                                        )) || <span className="text-xs text-gray-400">N/A</span>}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Typical Shipment Sizes - Reverted to clean style */}
                        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
                            <h3 className="font-bold text-gray-800 text-sm mb-4 uppercase tracking-wide">Typical {isBuyer ? 'Orders' : 'Sizes'}</h3>
                            <div className="space-y-2 text-xs">
                                <div className="flex justify-between items-center py-2 border-b border-gray-50">
                                    <span className="font-bold text-gray-700">Quantity (MT)</span>
                                    <span className="font-bold text-gray-700">Avg Price</span>
                                </div>
                                {supplier.shipment_sizes ? supplier.shipment_sizes.map((item, idx) => (
                                    <div key={idx} className="flex justify-between items-center py-2 border-b border-gray-50 last:border-0">
                                        <span className="text-gray-600 font-medium">{item.range} <span className="text-gray-400 text-[10px]">({item.count})</span></span>
                                        <span className="text-gray-900 font-bold font-sans">${item.avg_price.toFixed(0)}/MT</span>
                                    </div>
                                )) : <p className="text-gray-400">No data available</p>}
                            </div>
                        </div>

                    </div>

                    {/* MAIN CONTENT - Cols 9/12 */}
                    <div className="lg:col-span-9 space-y-8">

                        {/* Transaction History Table */}
                        <div className="bg-white rounded-xl shadow-sm border-2 border-gray-200 overflow-hidden">
                            <div className="px-6 py-5 border-b-2 border-gray-100 flex justify-between items-center bg-gray-50">
                                <div>
                                    <h3 className="text-lg font-bold text-gray-900">Historical Shipments</h3>
                                    <p className="text-sm text-gray-500 font-medium">Verified transaction history</p>
                                </div>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm text-gray-600">
                                    <thead className="bg-white text-gray-500 font-bold uppercase text-xs tracking-wider border-b-2 border-gray-100">
                                        <tr>
                                            <th className="px-6 py-4">{labels.tableEntity}</th>
                                            <th className="px-6 py-4">{labels.tableOrigin}</th>
                                            <th className="px-6 py-4">Quantity (MT)</th>
                                            <th className="px-6 py-4">Price (USD/MT)</th>
                                            <th className="px-6 py-4 text-right">Date</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {supplier.history.slice(0, 10).map((tx, idx) => (
                                            <tr key={tx.id || idx} className="hover:bg-gray-50 transition-colors">
                                                <td className="px-6 py-4 font-bold text-gray-900">{tx.seller || tx.buyer || 'Unknown'}</td>
                                                <td className="px-6 py-4 font-medium">{tx.origin_country || tx.country || tx.destination_country}</td>
                                                <td className="px-6 py-4 font-bold text-gray-800 font-sans">{tx.quantity.toLocaleString()}</td>
                                                <td className="px-6 py-4">
                                                    <span className="bg-emerald-50 px-2 py-1 rounded text-emerald-700 font-bold border border-emerald-100 font-sans">
                                                        ${tx.price.toFixed(2)}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-right font-medium text-gray-500 font-sans">{tx.date}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Insights Box */}
                        <div className="action-card bg-emerald-50 border-emerald-100" style={{ padding: '2rem', cursor: 'default', background: '#ecfdf5', borderColor: '#d1fae5' }}>
                            <h4 className="font-bold text-emerald-900 mb-3 text-lg flex items-center gap-2">
                                <span className="bg-emerald-200 p-1 rounded-full text-emerald-700"><CheckCircle size={16} /></span>
                                {labels.insightTitle}
                            </h4>
                            <p className="text-emerald-800 mb-6 leading-relaxed font-medium">
                                <span className="font-bold">{supplier.name}</span> {labels.insightText}
                            </p>
                            <div className="grid grid-cols-4 gap-4 text-center">
                                <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-sm">
                                    <p className="text-xs text-gray-500 uppercase mb-1 font-bold">{isBuyer ? 'Order Frequency' : 'Reliability Score'}</p>
                                    <p className="text-2xl font-bold text-gray-900 font-sans">High</p>
                                </div>
                                <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-sm">
                                    <p className="text-xs text-gray-500 uppercase mb-1 font-bold">{isBuyer ? 'Return Rate' : 'On-Time Delivery'}</p>
                                    <p className="text-2xl font-bold text-gray-900 font-sans">98%</p>
                                </div>
                                <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-sm">
                                    <p className="text-xs text-gray-500 uppercase mb-1 font-bold">{isBuyer ? 'Repeat Suppliers' : 'Repeat Buyers'}</p>
                                    <p className="text-2xl font-bold text-gray-900 font-sans">82%</p>
                                </div>
                                <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-sm">
                                    <p className="text-xs text-gray-500 uppercase mb-1 font-bold">Market Position</p>
                                    <p className="text-2xl font-bold text-gray-900 font-sans">#1</p>
                                </div>
                            </div>
                        </div>

                        {/* Comparables */}
                        <div>
                            <h4 className="font-bold text-gray-800 mb-4 text-xl">{labels.compTitle}</h4>
                            <p className="text-sm text-gray-500 mb-6 -mt-3 font-medium">{labels.compSub}</p>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                {comparables && comparables.length > 0 ? comparables.slice(0, 3).map((comp, idx) => (
                                    <div key={idx} className="action-card bg-white p-5 hover:border-emerald-500 transition-all cursor-pointer group"
                                        onClick={() => navigate(`/search/supplier/${encodeURIComponent(comp.name)}?q=${encodeURIComponent(query)}`)}
                                        style={{ padding: '1.5rem' }}
                                    >
                                        <h5 className="font-bold text-gray-900 text-lg mb-2 group-hover:text-emerald-700 transition-colors">{comp.name}</h5>
                                        <div className="space-y-2 text-xs text-gray-600 mb-4 font-medium">
                                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                                <span>Volume:</span>
                                                <span className="font-bold text-gray-900 font-sans">{comp.total_volume.toLocaleString()} MT</span>
                                            </div>
                                            <div className="flex justify-between border-b border-gray-100 pb-1">
                                                <span>Price:</span>
                                                <span className="font-bold text-gray-900 font-sans">${comp.avg_price.toFixed(0)}/MT</span>
                                            </div>
                                        </div>
                                    </div>
                                )) : <p className="text-gray-500 text-sm">No comparables found.</p>}
                            </div>
                        </div>

                        {/* Who Else Box -> Relationships */}
                        <div className="bg-white p-6 rounded-xl shadow-sm border-2 border-gray-200">
                            <h4 className="font-bold text-gray-800 mb-6 flex items-center gap-2 text-lg">
                                <span className="bg-emerald-100 p-1.5 rounded-full text-emerald-600"><TrendingUp size={18} /></span>
                                {isBuyer ? "Who are they buying from?" : "Who Else is Buying From Them?"}
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="border border-gray-200 p-5 rounded-xl bg-gray-50">
                                    <p className="text-xs text-gray-500 font-bold uppercase tracking-wide mb-2">Recent {isBuyer ? 'Suppliers' : 'Buyers'}</p>
                                    <p className="text-3xl font-bold text-gray-900 font-sans">{supplier.supplier_insights?.recent_buyers || supplier.supplier_insights?.recent_suppliers || 0}</p>
                                    <p className="text-xs text-emerald-600 mt-2 font-medium flex items-center gap-1"><CheckCircle size={10} /> Active in last month</p>
                                </div>
                                <div className="border border-gray-200 p-5 rounded-xl bg-gray-50">
                                    <p className="text-xs text-gray-500 font-bold uppercase tracking-wide mb-2">Total {isBuyer ? 'Suppliers' : 'Relationships'}</p>
                                    <p className="text-3xl font-bold text-gray-900 font-sans">{supplier.supplier_insights?.total_relationships || 0}</p>
                                    <p className="text-xs text-gray-400 mt-2 font-medium">Lifetime unique connections</p>
                                </div>
                            </div>
                        </div>

                        {/* Take Action */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
                            <button className="flex flex-col items-center justify-center p-6 bg-white border-2 border-gray-200 rounded-xl hover:border-emerald-500 hover:shadow-lg transition-all group bg-gradient-to-br from-white to-gray-50 hover:to-emerald-50 cursor-pointer">
                                <div className="p-4 bg-gray-100 text-gray-600 rounded-full mb-4 group-hover:bg-emerald-500 group-hover:text-white transition-all shadow-sm">
                                    <FileText size={28} />
                                </div>
                                <span className="font-bold text-gray-900 text-lg">{labels.ctaContact}</span>
                                <span className="text-xs text-gray-500 mt-1 font-medium group-hover:text-emerald-700">{labels.ctaSub}</span>
                            </button>
                            <button className="flex flex-col items-center justify-center p-6 bg-white border-2 border-gray-200 rounded-xl hover:border-emerald-500 hover:shadow-lg transition-all group bg-gradient-to-br from-white to-gray-50 hover:to-emerald-50 cursor-pointer">
                                <div className="p-4 bg-gray-100 text-gray-600 rounded-full mb-4 group-hover:bg-emerald-500 group-hover:text-white transition-all shadow-sm">
                                    <BarChart2 size={28} />
                                </div>
                                <span className="font-bold text-gray-900 text-lg">{labels.ctaLedger}</span>
                                <span className="text-xs text-gray-500 mt-1 font-medium group-hover:text-emerald-700">See full history</span>
                            </button>
                            <button className="flex flex-col items-center justify-center p-6 bg-white border-2 border-gray-200 rounded-xl hover:border-emerald-500 hover:shadow-lg transition-all group bg-gradient-to-br from-white to-gray-50 hover:to-emerald-50 cursor-pointer">
                                <div className="p-4 bg-gray-100 text-gray-600 rounded-full mb-4 group-hover:bg-emerald-500 group-hover:text-white transition-all shadow-sm">
                                    <TrendingUp size={28} />
                                </div>
                                <span className="font-bold text-gray-900 text-lg">{labels.ctaMarket}</span>
                                <span className="text-xs text-gray-500 mt-1 font-medium group-hover:text-emerald-700">Check trends</span>
                            </button>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
};

export default DealDetail;
