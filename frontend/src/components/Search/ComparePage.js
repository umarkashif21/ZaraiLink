import React, { useEffect, useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle, TrendingUp, Package, Globe, Download } from 'lucide-react';
import searchService from '../../services/searchService';
import Navbar from '../Layout/Navbar';
import '../Dashboard/Dashboard.css';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

const ComparePage = () => {
    const location = useLocation();
    const queryParams = new URLSearchParams(location.search);
    const suppliersParam = queryParams.get('suppliers');
    const query = queryParams.get('q') || '';
    const scopeParam = queryParams.get('scope') || 'IMPORT';
    const intentParam = queryParams.get('intent') || 'BUY';
    const subcatIdParam = queryParams.get('subcat_id') || null;
    const variantNameParam = queryParams.get('variant_name') || null;

    const isBuyerMode = intentParam === 'SELL';

    const [suppliers, setSuppliers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchCompare = async () => {
            if (!suppliersParam) {
                setError("No suppliers selected for comparison.");
                setLoading(false);
                return;
            }
            try {
                const names = suppliersParam.split(',');
                const data = await searchService.compareSuppliers(names, query, scopeParam, subcatIdParam, variantNameParam, intentParam);
                setSuppliers(data || []);
            } catch (err) {
                console.error("Comparison fetch failed", err);
                setError("Failed to fetch comparison data.");
            } finally {
                setLoading(false);
            }
        };
        fetchCompare();
    }, [suppliersParam, query, scopeParam, subcatIdParam, variantNameParam]);

    // ── Winner Logic ──────────────────────────────────────────────
    const getWinners = () => {
        if (!suppliers.length) return {};
        let minPrice = Infinity;
        let maxVolume = -Infinity;
        let maxShipments = -Infinity;
        let mostRecentTime = 0;

        suppliers.forEach(s => {
            if (s.avg_price > 0 && s.avg_price < minPrice) minPrice = s.avg_price;
            if (s.total_volume > maxVolume) maxVolume = s.total_volume;
            if (s.shipment_count > maxShipments) maxShipments = s.shipment_count;
            if (s.last_active) {
                const t = new Date(s.last_active).getTime();
                if (t > mostRecentTime) mostRecentTime = t;
            }
        });

        return {
            price: minPrice,
            volume: maxVolume,
            shipments: maxShipments,
            recent: mostRecentTime
        };
    };

    const winners = getWinners();

    // ── Document Export Logic ─────────────────────────────────────────────
    const exportPDF = () => {
        const doc = new jsPDF('landscape');
        
        // --- 1. Header Section ---
        doc.setFillColor(16, 185, 129); // Emerald 500
        doc.rect(0, 0, doc.internal.pageSize.width, 25, 'F');
        
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(22);
        doc.setFont("helvetica", "bold");
        doc.text("ZaraiLink", 14, 17);
        
        doc.setFontSize(14);
        doc.setFont("helvetica", "normal");
        doc.text(isBuyerMode ? "Buyer Comparison Report" : "Supplier Comparison Report", 210, 16);

        // Date & Query Details
        doc.setTextColor(100, 100, 100);
        doc.setFontSize(10);
        doc.text(`Generated: ${new Date().toLocaleDateString()}`, 14, 35);
        doc.text(`Search Query: "${query}"`, 14, 42);
        if (subcatIdParam || variantNameParam) {
            doc.text(`Product Scope: ${variantNameParam || 'Specific Variant'}`, 14, 49);
        }

        // Helpers for clean formatting and sanity
        const formatCurrency = (val) => {
            const num = parseFloat(val);
            if (isNaN(num) || num <= 0 || num > 10000) return 'N/A';
            return `$${num.toFixed(2)}`;
        };

        const formatNumber = (val) => {
            const num = parseInt(val, 10);
            if (isNaN(num) || num < 0) return '0';
            return num.toLocaleString();
        };

        // --- 2. Comparison Table ---
        const cleanName = (name) => name ? name.replace(/[^\x00-\x7F]/g, "") : 'Unknown';

        const tableColumn = ["Metrics", ...suppliers.map(s => cleanName(s.name))];
        const tableRows = [
            ["Country", ...suppliers.map(s => s.country ? s.country.replace(/[^\x00-\x7F]/g, "") : 'N/A')],
            ["Avg Price ($/MT)", ...suppliers.map(s => {
                const val = parseFloat(s.avg_price);
                const str = formatCurrency(val);
                return `${str} ${val > 0 && val === winners.price ? '(Lowest *W*)' : ''}`;
            })],
            ["Total Volume (MT)", ...suppliers.map(s => {
                const str = formatNumber(s.total_volume);
                return `${str} ${s.total_volume === winners.volume && s.total_volume > 0 ? '(Highest *W*)' : ''}`;
            })],
            ["Shipments", ...suppliers.map(s => {
                const str = formatNumber(s.shipment_count);
                return `${str} ${s.shipment_count === winners.shipments && s.shipment_count > 0 ? '(Most *W*)' : ''}`;
            })],
            ["Last Active", ...suppliers.map(s => {
                const t = new Date(s.last_active || 0).getTime();
                return `${s.last_active || 'N/A'} ${t === winners.recent && winners.recent !== 0 ? '(Recent *W*)' : ''}`;
            })],
            ["Price Range ($/MT)", ...suppliers.map(s => {
                const minStr = formatCurrency(s.price_min);
                const maxStr = formatCurrency(s.price_max);
                return `${minStr} - ${maxStr}`;
            })],
            [isBuyerMode ? "Buys From" : "Ships To", ...suppliers.map(s => s.ships_to && s.ships_to.length > 0 ? s.ships_to.join(', ').replace(/[^\x00-\x7F]/g, "") : 'N/A')]
        ];

        // Sanitize tick marks in tableRows (helvetica hates unicode checkmarks)
        const sanitizeForPdf = (str) => {
            if (!str) return 'N/A';
            return str.replace(/\*W\*/g, "WINNER");
        };

        const cleanTableRows = tableRows.map(row => row.map(sanitizeForPdf));

        autoTable(doc, {
            startY: 55,
            head: [tableColumn],
            body: cleanTableRows,
            theme: 'grid',
            headStyles: { fillColor: [249, 250, 251], textColor: [50, 50, 50], fontStyle: 'bold' },
            bodyStyles: { textColor: [80, 80, 80] },
            alternateRowStyles: { fillColor: [252, 253, 253] }
        });

        // --- 3. Price Trend Section ---
        let finalY = doc.lastAutoTable.finalY + 15;
        doc.setFontSize(14);
        doc.setFont("helvetica", "bold");
        doc.setTextColor(50, 50, 50);
        doc.text("Historical Price Trends", 14, finalY);
        finalY += 10;

        suppliers.forEach(s => {
            // Check page break before rendering supplier block
            if (finalY > doc.internal.pageSize.height - 40) {
                doc.addPage();
                finalY = 20;
            }

            doc.setFontSize(11);
            doc.setFont("helvetica", "bold");
            doc.setTextColor(16, 185, 129); // Emerald 500
            doc.text(`${isBuyerMode ? 'Buyer' : 'Supplier'}: ${cleanName(s.name)}`, 14, finalY);
            finalY += 4;

            if (s.sparkline && s.sparkline.length > 0) {
                // Filter out bad data points (e.g. >10000 or NaN)
                const validPoints = s.sparkline.filter(sp => {
                    const p = parseFloat(sp.price);
                    return !isNaN(p) && p > 0 && p <= 10000;
                });

                if (validPoints.length > 0) {
                    const trendRows = validPoints.map(sp => [
                        sp.date ? sp.date.substring(0, 7) : 'Unknown',
                        formatCurrency(sp.price)
                    ]);

                    autoTable(doc, {
                        startY: finalY + 4,
                        head: [["Month", "Price ($/MT)"]],
                        body: trendRows,
                        theme: 'striped',
                        styles: { cellPadding: 2, fontSize: 9 },
                        headStyles: { fillColor: [230, 230, 230], textColor: [50, 50, 50] },
                        margin: { left: 14, right: 14 }
                    });
                    
                    finalY = doc.lastAutoTable.finalY + 12; // Update Y for next supplier
                } else {
                    doc.setFontSize(9);
                    doc.setFont("helvetica", "italic");
                    doc.setTextColor(100, 100, 100);
                    doc.text("Contains unrealistic or invalid data points.", 14, finalY + 5);
                    finalY += 14;
                }
            } else {
                doc.setFontSize(9);
                doc.setFont("helvetica", "italic");
                doc.setTextColor(100, 100, 100);
                doc.text("Not enough historical data.", 14, finalY + 5);
                finalY += 14;
            }
        });

        // --- 4. Footer ---
        const pageCount = doc.internal.getNumberOfPages();
        for (let i = 1; i <= pageCount; i++) {
            doc.setPage(i);
            const pageHeight = doc.internal.pageSize.height;
            doc.setFontSize(9);
            doc.setTextColor(150, 150, 150);
            const cleanFooter = "Generated by ZaraiLink Trade Intelligence Platform . zarailink.com";
            doc.text(cleanFooter, 14, pageHeight - 10);
        }

        // Save PDF
        let dateStr = new Date().toISOString().split('T')[0];
        let safeName = variantNameParam ? variantNameParam.replace(/[^a-z0-9]/gi, '_') : 'Product';
        doc.save(`ZaraiLink_Comparison_${safeName}_${dateStr}.pdf`);
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col pt-16">
                <Navbar />
                <div className="flex-1 flex items-center justify-center text-gray-400">
                    <p className="font-bold text-lg animate-pulse">Loading Comparison Engine...</p>
                </div>
            </div>
        );
    }

    if (error || !suppliers.length) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col pt-16">
                <Navbar />
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                        <p className="font-bold text-gray-700 text-lg mb-4">{error || "No data available."}</p>
                        <Link to={`/search/results?q=${encodeURIComponent(query)}&scope=${encodeURIComponent(scopeParam)}`} className="text-emerald-600 font-bold underline">← Return to Search Results</Link>
                    </div>
                </div>
            </div>
        );
    }

    // Build query params for routing specifically backward
    const backToResultsUrl = `/search/results?q=${encodeURIComponent(query)}&scope=${encodeURIComponent(scopeParam)}${subcatIdParam ? `&subcat_id=${encodeURIComponent(subcatIdParam)}` : ''}${variantNameParam ? `&variant_name=${encodeURIComponent(variantNameParam)}` : ''}`;

    return (
        <div className="min-h-screen bg-gray-50 pt-20 pb-24 font-primary">
            <Navbar />
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
                
                {/* Header */}
                <div className="mb-6 flex items-center justify-between">
                    <div>
                        <Link to={backToResultsUrl} className="inline-flex items-center text-sm font-bold text-gray-500 hover:text-emerald-600 transition-colors mb-2">
                            <ArrowLeft size={16} className="mr-1" /> Back to Results
                        </Link>
                        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">{isBuyerMode ? 'Buyer' : 'Supplier'} Comparison</h1>
                        <p className="text-gray-500 font-medium">Comparing {suppliers.length} matching {isBuyerMode ? 'buyers' : 'suppliers'} for "{query}"</p>
                    </div>
                    <button 
                        onClick={exportPDF}
                        className="flex items-center gap-2 px-5 py-2.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 hover:text-emerald-800 border border-emerald-200 font-bold rounded-xl transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
                    >
                        <Download size={18} /> Download PDF Report
                    </button>
                </div>

                {/* Table wrapper */}
                <div className="bg-white rounded-2xl shadow-sm border-2 border-gray-100 overflow-x-auto">
                    <table className="w-full text-left border-collapse min-w-[800px]">
                        <thead>
                            <tr className="border-b-2 border-gray-100 bg-gray-50">
                                <th className="p-4 w-48 font-bold text-gray-400 uppercase tracking-widest text-xs border-r border-gray-100 text-right">Metrics</th>
                                {suppliers.map((s, idx) => (
                                    <th key={idx} className="p-5 w-1/4 border-r border-gray-100 last:border-0 align-top">
                                        <h3 className="text-lg font-black text-gray-900 leading-tight mb-1">{s.name}</h3>
                                        <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">{s.country}</div>
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>

                            {/* Average Price Row */}
                            <tr className="border-b border-gray-100 hover:bg-emerald-50/30 transition-colors">
                                <td className="p-4 font-bold text-gray-500 text-sm border-r border-gray-100 text-right">Avg Price ($/MT)</td>
                                {suppliers.map((s, idx) => (
                                    <td key={idx} className="p-5 border-r border-gray-100 last:border-0">
                                        <div className="flex items-center gap-2">
                                            <span className={`text-xl font-black ${s.avg_price === winners.price ? 'text-emerald-600' : 'text-gray-900'}` }>
                                                ${parseFloat(s.avg_price).toFixed(2)}
                                            </span>
                                            {s.avg_price === winners.price && <span className="bg-emerald-100 text-emerald-700 text-[10px] uppercase font-black px-2 py-0.5 rounded-full tracking-wider flex items-center gap-1"><CheckCircle size={10} /> Lowest ✓</span>}
                                        </div>
                                    </td>
                                ))}
                            </tr>

                            {/* Total Volume Row */}
                            <tr className="border-b border-gray-100 hover:bg-emerald-50/30 transition-colors">
                                <td className="p-4 font-bold text-gray-500 text-sm border-r border-gray-100 text-right">Total Volume (MT)</td>
                                {suppliers.map((s, idx) => (
                                    <td key={idx} className="p-5 border-r border-gray-100 last:border-0">
                                        <div className="flex items-center gap-2">
                                            <span className={`text-lg font-bold ${s.total_volume === winners.volume ? 'text-emerald-600' : 'text-gray-700'}` }>
                                                {s.total_volume.toLocaleString()}
                                            </span>
                                            {s.total_volume === winners.volume && <span className="bg-emerald-100 text-emerald-700 text-[10px] uppercase font-black px-2 py-0.5 rounded-full tracking-wider flex items-center gap-1"><CheckCircle size={10} /> Highest ✓</span>}
                                        </div>
                                    </td>
                                ))}
                            </tr>

                            {/* Shipment Count Row */}
                            <tr className="border-b border-gray-100 hover:bg-emerald-50/30 transition-colors">
                                <td className="p-4 font-bold text-gray-500 text-sm border-r border-gray-100 text-right">Shipments</td>
                                {suppliers.map((s, idx) => (
                                    <td key={idx} className="p-5 border-r border-gray-100 last:border-0">
                                        <div className="flex items-center gap-2">
                                            <span className={`text-lg font-bold ${s.shipment_count === winners.shipments ? 'text-emerald-600' : 'text-gray-700'}` }>
                                                {s.shipment_count}
                                            </span>
                                            {s.shipment_count === winners.shipments && <span className="bg-emerald-100 text-emerald-700 text-[10px] uppercase font-black px-2 py-0.5 rounded-full tracking-wider flex items-center gap-1"><CheckCircle size={10} /> Most ✓</span>}
                                        </div>
                                    </td>
                                ))}
                            </tr>

                            {/* Last Active Row */}
                            <tr className="border-b border-gray-100 hover:bg-emerald-50/30 transition-colors bg-gray-50/30">
                                <td className="p-4 font-bold text-gray-500 text-sm border-r border-gray-100 text-right">Last Active</td>
                                {suppliers.map((s, idx) => {
                                    const t = s.last_active ? new Date(s.last_active).getTime() : 0;
                                    return (
                                        <td key={idx} className="p-5 border-r border-gray-100 last:border-0">
                                            <div className="flex items-center gap-2">
                                                <span className={`text-sm font-bold ${t === winners.recent && t !== 0 ? 'text-emerald-600' : 'text-gray-600'}` }>
                                                    {s.last_active || 'N/A'}
                                                </span>
                                                {t === winners.recent && t !== 0 && <span className="text-emerald-500 font-bold text-xs flex items-center gap-1"><CheckCircle size={12} /> Recent</span>}
                                            </div>
                                        </td>
                                    );
                                })}
                            </tr>

                            {/* Historic Price Range Row */}
                            <tr className="border-b border-gray-100 hover:bg-emerald-50/30 transition-colors">
                                <td className="p-4 font-bold text-gray-500 text-sm border-r border-gray-100 text-right">Historical Price Range</td>
                                {suppliers.map((s, idx) => (
                                    <td key={idx} className="p-5 border-r border-gray-100 last:border-0">
                                        <span className="text-sm font-bold text-gray-500">
                                            ${s.price_min.toFixed(0)} — ${s.price_max.toFixed(0)}
                                        </span>
                                    </td>
                                ))}
                            </tr>

                            {/* Ships To / Buys From Row */}
                            <tr className="border-b-2 border-gray-100 hover:bg-emerald-50/30 transition-colors">
                                <td className="p-4 font-bold text-gray-500 text-sm border-r border-gray-100 text-right">{isBuyerMode ? 'Buys From' : 'Ships To'}</td>
                                {suppliers.map((s, idx) => (
                                    <td key={idx} className="p-4 border-r border-gray-100 last:border-0 align-top">
                                        <div className="flex flex-wrap gap-1">
                                            {s.ships_to.map((country, cidx) => (
                                                <span key={cidx} className="text-xs font-bold text-gray-500 bg-gray-100 px-2 py-1 rounded-md">{country}</span>
                                            ))}
                                        </div>
                                    </td>
                                ))}
                            </tr>

                            {/* Price Trend Sparkline Row */}
                            <tr className="border-b-2 border-gray-100 hover:bg-emerald-50/30 transition-colors">
                                <td className="p-4 font-bold text-gray-500 text-sm border-r border-gray-100 text-right">
                                    <div className="flex justify-end items-center gap-2">
                                        Price Trend <TrendingUp size={16} className="text-emerald-500"/>
                                    </div>
                                    <p className="text-[10px] text-gray-400 mt-1 uppercase font-bold tracking-wider">Last 12 Months</p>
                                </td>
                                {suppliers.map((s, idx) => (
                                    <td key={idx} className="p-5 border-r border-gray-100 last:border-0">
                                        {s.sparkline && s.sparkline.length > 1 ? (
                                            <div className="h-20 w-full mt-2">
                                                <ResponsiveContainer width="100%" height="100%">
                                                    <LineChart data={s.sparkline}>
                                                        <YAxis domain={['dataMin', 'dataMax']} hide />
                                                        <Line 
                                                            type="monotone" 
                                                            dataKey="price" 
                                                            stroke="#10b981" 
                                                            strokeWidth={3} 
                                                            dot={{r: 2, fill: '#10b981', strokeWidth: 2, stroke: 'white'}}
                                                            activeDot={{r: 5}} 
                                                        />
                                                    </LineChart>
                                                </ResponsiveContainer>
                                            </div>
                                        ) : (
                                            <div className="h-20 w-full flex items-center justify-center text-xs font-bold text-gray-300">
                                                Not enough history
                                            </div>
                                        )}
                                    </td>
                                ))}
                            </tr>

                            {/* Action Row */}
                            <tr className="bg-gray-50/50">
                                <td className="p-4 border-r border-gray-100"></td>
                                {suppliers.map((s, idx) => (
                                    <td key={idx} className="p-5 border-r border-gray-100 last:border-0 text-center">
                                        <Link 
                                            to={`/search/supplier/${encodeURIComponent(s.name)}?q=${encodeURIComponent(query)}&scope=${encodeURIComponent(scopeParam)}${subcatIdParam ? `&subcat_id=${encodeURIComponent(subcatIdParam)}` : ''}${variantNameParam ? `&variant_name=${encodeURIComponent(variantNameParam)}` : ''}`} 
                                            className="w-full inline-block py-3 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-black rounded-xl transition-all shadow-sm shadow-emerald-600/20"
                                            style={{ textDecoration: 'none' }}
                                        >
                                            View Full Deal
                                        </Link>
                                    </td>
                                ))}
                            </tr>

                        </tbody>
                    </table>
                </div>

            </div>
        </div>
    );
};

export default ComparePage;
