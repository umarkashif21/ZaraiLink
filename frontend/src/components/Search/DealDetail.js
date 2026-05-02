import React, { useEffect, useState } from 'react';
import { useParams, useSearchParams, Link, useNavigate } from 'react-router-dom';
import { Download } from 'lucide-react';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import Navbar from '../Layout/Navbar';
import searchService from '../../services/searchService';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

// ─────────────────────────────────────────────────────────────────────────────
// Design tokens (matches the rest of the site)
// ─────────────────────────────────────────────────────────────────────────────
const C = {
    primary: '#10b981',
    primaryHover: '#059669',
    primaryLight: '#ecfdf5',
    primaryBorder: '#6ee7b7',
    primaryGlow: 'rgba(16,185,129,0.12)',
    textPrimary: '#0f172a',
    textSecondary: '#475569',
    textTertiary: '#94a3b8',
    border: '#e2e8f0',
    borderLight: '#f1f5f9',
    bg: '#f8fafc',
    card: '#ffffff',
    // Rich accent tiers
    accentBlue: '#3b82f6',
    accentPurple: '#8b5cf6',
    accentAmber: '#f59e0b',
    accentRose: '#f43f5e',
    accentCyan: '#06b6d4',
    // Gradient helpers
    gradientGreen: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    gradientCard: 'linear-gradient(145deg, #ffffff 0%, #f8fffc 100%)',
    gradientHero: 'linear-gradient(135deg, #0f172a 0%, #134e4a 100%)',
};

// ─────────────────────────────────────────────────────────────────────────────
// Role-aware label map
// ─────────────────────────────────────────────────────────────────────────────
const getLabels = (isBuyer) => ({
    volumeCard: isBuyer ? 'Total Volume Purchased' : 'Total Volume Traded',
    shipmentsCard: isBuyer ? 'Number of Orders' : 'Number of Shipments',
    priceCard: isBuyer ? 'Avg Purchase Price' : 'Average Price',
    counterpartyCard: isBuyer ? 'Total Unique Suppliers' : 'Total Unique Buyers',
    activePeriod: isBuyer ? 'Active Purchasing Period' : 'Active Period',
    primaryRegion: isBuyer ? 'Primary Import Sources' : 'Primary Sourcing Region',
    tradeSection: isBuyer ? 'Procurement Behavior' : 'Trade Behavior',
    shipmentSize: isBuyer ? 'Order Size Distribution' : 'Shipment Size Distribution',
    frequencyPattern: isBuyer ? 'Order Frequency' : 'Frequency Pattern',
    priceSection: isBuyer ? 'Price Sensitivity' : 'Price Positioning',
    marketPosLabel: isBuyer ? 'Purchase Price Tier' : 'Market Position',
    priceStabLabel: isBuyer ? 'Price Acceptance Consistency' : 'Price Stability',
    counterpartySection: isBuyer ? 'Top Suppliers' : 'Top Buyers',
    geoSubtitle: isBuyer ? 'Countries Ordered From' : 'Countries Supplied From',
    badgeLabel: isBuyer ? 'TOP BUYER IN CATEGORY' : 'TOP SUPPLIER IN CATEGORY',
    roleLabel: isBuyer ? 'Buyer' : 'Supplier',
    // Market & Pricing specific
    marketAvgVsEntity: isBuyer ? 'Average Purchase Price' : 'Market Average Price vs Entity Score',
    marketVolumeGeo: isBuyer ? 'Procurement Volume by Origin' : 'Market Volume by Origin Country',
    entityPricePos: isBuyer ? 'Buyer Price Positioning' : 'Supplier Price Positioning',
    benchmarkingChart: 'Supplier Benchmarking — Competitive Comparison',
    compSubtitle: isBuyer ? 'Compare suppliers for procurement decision-making' : 'Performance comparison against market competitors',
    compEntityHdr: 'Supplier Name',
    compVolHdr: isBuyer ? 'Total Volume Supplied (MT)' : 'Total Volume (MT)',
    compPriceHdr: isBuyer ? 'Average Purchase Price (USD/MT)' : 'Average Price (USD/MT)',
});

// ─────────────────────────────────────────────────────────────────────────────
// Mini SVG Price Trend Chart (Overview)
// ─────────────────────────────────────────────────────────────────────────────
const PriceMiniChart = ({ sparkline }) => {
    const valid = (sparkline || []).filter(s => s.price > 0).slice(-18);
    if (valid.length < 2) {
        return (
            <div style={{
                background: C.primaryLight, border: `1px solid ${C.primaryBorder}`,
                borderRadius: '0.5rem', height: '100px',
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'
            }}>
                <span style={{ fontSize: '1.25rem' }}>📈</span>
                <span style={{ fontSize: '0.725rem', color: C.textTertiary }}>Price Movement Chart</span>
            </div>
        );
    }
    const prices = valid.map(s => s.price);
    const minP = Math.min(...prices), maxP = Math.max(...prices), range = maxP - minP || 1;
    const n = prices.length;
    const pts = prices.map((p, i) => `${(i / (n - 1)) * 100},${76 - ((p - minP) / range) * 60}`).join(' ');
    const fill = [`0,80`, ...prices.map((p, i) => `${(i / (n - 1)) * 100},${76 - ((p - minP) / range) * 60}`), `100,80`].join(' ');
    return (
        <div style={{ background: C.primaryLight, border: `1px solid ${C.primaryBorder}`, borderRadius: '0.5rem', padding: '0.875rem' }}>
            <p style={{ fontSize: '0.65rem', color: C.primary, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 0.5rem' }}>
                Price Movement Chart
            </p>
            <svg viewBox="0 0 100 80" preserveAspectRatio="none" style={{ width: '100%', height: '60px', display: 'block' }}>
                <defs>
                    <linearGradient id="pgDeal" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={C.primary} stopOpacity="0.25" />
                        <stop offset="100%" stopColor={C.primary} stopOpacity="0.02" />
                    </linearGradient>
                </defs>
                <polygon points={fill} fill="url(#pgDeal)" />
                <polyline points={pts} fill="none" stroke={C.primary} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.25rem' }}>
                <span style={{ fontSize: '0.6rem', color: C.textTertiary }}>Low: ${minP.toFixed(0)}/MT</span>
                <span style={{ fontSize: '0.6rem', color: C.textTertiary }}>High: ${maxP.toFixed(0)}/MT</span>
            </div>
        </div>
    );
};

// ─────────────────────────────────────────────────────────────────────────────
// Overview Tab
// ─────────────────────────────────────────────────────────────────────────────
const OverviewTab = ({ supplier, isBuyer, navigateTab }) => {
    const ov = supplier.overview || {};
    const spk = supplier.sparkline || [];
    const L = getLabels(isBuyer);

    const card = { background: C.card, border: `1px solid ${C.border}`, borderRadius: '0.75rem', padding: '1.5rem' };
    const sec = { fontSize: '0.8125rem', fontWeight: 800, color: C.textPrimary, margin: '0 0 1.25rem', letterSpacing: '-0.01em' };
    const lbl = { fontSize: '0.7rem', color: C.textSecondary, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', margin: '0 0 0.2rem' };
    const val = { fontSize: '0.9375rem', fontWeight: 800, color: C.textPrimary, margin: 0 };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* ── Activity Summary ── */}
            <section style={card}>
                <h3 style={sec}>Activity Summary</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', rowGap: '1.25rem', columnGap: '3rem' }}>
                    {[
                        [L.activePeriod, ov.active_period],
                        ['Last Active', ov.last_active],
                        [L.shipmentSize.replace(' Distribution', ' Size'), ov.typical_shipment_size],
                        [L.primaryRegion, ov.primary_region],
                    ].map(([label, value]) => (
                        <div key={label}>
                            <p style={lbl}>{label}</p>
                            <p style={val}>{value || 'N/A'}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── Price Positioning / Price Sensitivity ── */}
            <section style={card}>
                <h3 style={sec}>{L.priceSection}</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2.5rem', alignItems: 'start' }}>
                    <div>
                        <p style={lbl}>{L.marketPosLabel}</p>
                        <p style={{ fontSize: '1.125rem', fontWeight: 800, color: C.textPrimary, margin: '0 0 0.2rem' }}>
                            {ov.market_position_label || 'Mid-Range Competitive'}
                        </p>
                        <p style={{ fontSize: '0.8rem', color: C.textSecondary, margin: '0 0 1.5rem', lineHeight: 1.55 }}>
                            {isBuyer
                                ? ov.market_position_desc?.replace('Pricing positioned', 'Typically purchasing') || 'Purchasing in the middle price tier for this product category'
                                : ov.market_position_desc || 'Pricing positioned in the middle tier for this product category'
                            }
                        </p>
                        <p style={lbl}>{L.priceStabLabel}</p>
                        <p style={{ fontSize: '0.875rem', fontWeight: 700, color: C.textPrimary, margin: 0 }}>
                            {ov.price_stability || 'Stable'}
                        </p>
                    </div>
                    <div>
                        <p style={lbl}>Price Trend Indicator</p>
                        <PriceMiniChart sparkline={spk} />
                    </div>
                </div>
            </section>

            {/* ── Trade / Procurement Behavior ── */}
            <section style={card}>
                <h3 style={sec}>{L.tradeSection}</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2.5rem', alignItems: 'start' }}>
                    {/* Size Distribution */}
                    <div>
                        <p style={lbl}>{L.shipmentSize}</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem', marginTop: '0.5rem' }}>
                            {(ov.size_distribution || []).map((s, i) => (
                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                    <span style={{ fontSize: '0.75rem', color: '#4b5563', fontWeight: 500, width: '148px', flexShrink: 0 }}>{s.range}</span>
                                    <div style={{ flex: 1, background: '#f3f4f6', borderRadius: '999px', height: '7px', overflow: 'hidden' }}>
                                        <div style={{ width: `${s.pct}%`, background: C.primary, height: '100%', borderRadius: '999px', opacity: 0.7 }} />
                                    </div>
                                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: C.textPrimary, width: '30px', textAlign: 'right', flexShrink: 0 }}>{s.pct}%</span>
                                </div>
                            ))}
                            {(!ov.size_distribution || ov.size_distribution.length === 0) && (
                                <p style={{ fontSize: '0.8rem', color: C.textTertiary }}>No size data available</p>
                            )}
                        </div>
                    </div>

                    {/* Frequency + Behavioral */}
                    <div>
                        <p style={lbl}>{L.frequencyPattern}</p>
                        <p style={{ fontSize: '0.9375rem', fontWeight: 800, color: C.textPrimary, margin: '0 0 0.2rem' }}>
                            {ov.frequency_label || '—'}
                        </p>
                        <p style={{ fontSize: '0.8125rem', color: C.textSecondary, margin: '0 0 1.5rem' }}>
                            {ov.frequency_desc?.replace('shipments', isBuyer ? 'orders' : 'shipments') || ''}
                        </p>

                    </div>
                </div>
            </section>

            {/* ── Top Counterparties + Geographic Presence ── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <section style={card}>
                    <h3 style={sec}>{L.counterpartySection}</h3>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                        {(ov.top_counterparties || []).map((cp, i, arr) => (
                            <div key={i} style={{
                                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                padding: '0.5625rem 0',
                                borderBottom: i < arr.length - 1 ? `1px solid ${C.border}` : 'none',
                            }}>
                                <span style={{ fontSize: '0.8125rem', color: cp.is_others ? C.textTertiary : '#374151', fontWeight: 500, paddingRight: '0.5rem' }}>
                                    {(cp.name || '').replace(/\[|\]/g, '')}
                                </span>
                                <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: cp.is_others ? C.textTertiary : C.textPrimary, whiteSpace: 'nowrap' }}>
                                    {(cp.volume_mt || 0).toLocaleString()} MT
                                </span>
                            </div>
                        ))}
                        {(!ov.top_counterparties || ov.top_counterparties.length === 0) && (
                            <p style={{ fontSize: '0.8rem', color: C.textTertiary }}>No data available</p>
                        )}
                    </div>
                    {ov.top_counterparties_note && (
                        <p style={{ fontSize: '0.75rem', color: C.textTertiary, margin: '1rem 0 0', fontStyle: 'italic' }}>
                            {ov.top_counterparties_note}
                        </p>
                    )}
                </section>

                <section style={card}>
                    <h3 style={{ ...sec, marginBottom: '0.25rem' }}>Geographic Presence</h3>
                    <p style={{ fontSize: '0.75rem', color: C.textSecondary, margin: '0 0 1.25rem' }}>
                        {L.geoSubtitle}
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {(ov.geo_presence || []).slice(0, 5).map((geo, i) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <span style={{ fontSize: '0.8125rem', color: '#374151', fontWeight: 500, width: '72px', flexShrink: 0 }}>{geo.country}</span>
                                <div style={{ flex: 1, background: '#f3f4f6', borderRadius: '999px', height: '7px', overflow: 'hidden' }}>
                                    <div style={{ width: `${geo.pct}%`, background: C.primary, height: '100%', borderRadius: '999px', opacity: 0.7 }} />
                                </div>
                                <span style={{ fontSize: '0.725rem', color: C.textPrimary, whiteSpace: 'nowrap', width: '110px', textAlign: 'right', flexShrink: 0 }}>
                                    {(geo.volume_mt || 0).toLocaleString()} MT ({geo.pct}%)
                                </span>
                            </div>
                        ))}
                        {(!ov.geo_presence || ov.geo_presence.length === 0) && (
                            <p style={{ fontSize: '0.8rem', color: C.textTertiary }}>No geographic data</p>
                        )}
                    </div>
                    {ov.geo_summary && (
                        <p style={{ fontSize: '0.75rem', color: C.textTertiary, margin: '1rem 0 0', fontStyle: 'italic' }}>
                            {isBuyer ? ov.geo_summary.replace('sourced', 'ordered').replace('suppliers', 'sources') : ov.geo_summary}
                        </p>
                    )}
                </section>
            </div>

            {/* ── CTA Footer ── */}
            <section style={{
                ...card,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                background: C.primaryLight, border: `1px solid ${C.primaryBorder}`,
            }}>
                <div>
                    <h4 style={{ fontSize: '0.9375rem', fontWeight: 800, color: C.textPrimary, margin: '0 0 0.3rem' }}>
                        Ready to explore deeper insights?
                    </h4>
                    <p style={{ fontSize: '0.8125rem', color: C.textSecondary, margin: 0 }}>
                        {isBuyer
                            ? 'Access procurement analytics, price benchmarks, and order history'
                            : 'Access detailed pricing analytics, market trends, and transaction history'
                        }
                    </p>
                </div>
                <button
                    onClick={() => navigateTab('pricing')}
                    style={{
                        background: C.primary, color: 'white', border: 'none', borderRadius: '0.5rem',
                        padding: '0.625rem 1.25rem', fontSize: '0.875rem', fontWeight: 700,
                        cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.375rem',
                        whiteSpace: 'nowrap', flexShrink: 0, transition: 'background 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = C.primaryHover}
                    onMouseLeave={e => e.currentTarget.style.background = C.primary}
                >
                    {isBuyer ? 'View Procurement Data →' : 'View Market & Pricing →'}
                </button>
            </section>
        </div>
    );
};

// ─────────────────────────────────────────────────────────────────────────────
// Market & Pricing Tab (Fully implemented from backend data)
// ─────────────────────────────────────────────────────────────────────────────
const MarketPricingTab = ({ supplier, isBuyer, query, variantName }) => {
    const mk = supplier.market_pricing;
    if (!mk) return <PlaceholderTab label="Market Data Loading..." />;

    const L = getLabels(isBuyer);
    const card = {
        background: C.gradientCard,
        border: `1px solid ${C.border}`,
        borderRadius: '0.875rem',
        padding: '1.75rem',
        boxShadow: '0 1px 6px rgba(15,23,42,0.06)',
        marginBottom: '0',
    };
    const sec = {
        fontSize: '0.875rem', fontWeight: 800, color: C.textPrimary,
        margin: '0 0 1.25rem', letterSpacing: '-0.01em',
        display: 'flex', alignItems: 'center', gap: '0.5rem',
    };
    const lbl = { fontSize: '0.65rem', color: C.textTertiary, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 0.25rem' };
    const val = { fontSize: '1.125rem', fontWeight: 800, color: C.textPrimary, margin: 0 };

    const fmtMoney = n => n ? `$${n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}` : '—';
    const fmtVol = n => n ? `${Math.round(n).toLocaleString()} MT` : '—';

    // Formatting for Tooltips
    const ChartTooltip = ({ active, payload, label, suffix = '' }) => {
        if (active && payload && payload.length) {
            return (
                <div style={{ background: '#fff', border: `1px solid ${C.border}`, padding: '0.5rem', borderRadius: '0.25rem', boxShadow: '0 2px 4px rgba(0,0,0,0.05)', fontSize: '0.75rem' }}>
                    <p style={{ margin: '0 0 0.2rem', fontWeight: 700, color: C.textPrimary }}>{label}</p>
                    <p style={{ margin: 0, color: payload[0].color || C.primary }}>
                        {payload[0].name}: {payload[0].value.toLocaleString()} {suffix}
                    </p>
                </div>
            );
        }
        return null;
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* ── 1. Market Overview ── */}
            <section style={{ ...card, background: C.gradientHero, borderTop: 'none', borderColor: 'transparent' }}>
                <h3 style={{ ...sec, color: 'white', marginBottom: '1.25rem', fontSize: '0.8125rem', opacity: 0.9 }}>
                    🌐 Market Overview — {variantName || query}
                </h3>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    {[
                        { label: 'Total Market Volume', value: fmtVol(mk.overview.total_volume), sub: 'All sources tracked', color: '#34d399' },
                        { label: 'Total Transactions', value: (mk.overview.total_transactions?.toLocaleString() || 0), sub: 'Across the market', color: '#60a5fa' },
                        { label: 'Trade Direction', value: `${mk.overview.trade_direction} 100%`, sub: 'Market majority', color: '#a78bfa' },
                        { label: 'Top Trade Route', value: mk.overview.top_route, sub: 'By volume traded', color: '#fbbf24' },
                    ].map((item, i) => (
                        <div key={i} style={{ borderLeft: `3px solid ${item.color}`, paddingLeft: '1rem' }}>
                            <p style={{ ...lbl, color: 'rgba(255,255,255,0.55)' }}>{item.label}</p>
                            <p style={{ ...val, fontSize: '1.25rem', color: 'white' }}>{item.value}</p>
                            <p style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', marginTop: '0.1rem' }}>{item.sub}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── 2. Price Intelligence ── */}
            <section style={card}>
                <h3 style={sec}>Price Intelligence</h3>
                <div style={{ background: 'linear-gradient(145deg, #f0fdf4 0%, #ecfdf5 100%)', borderRadius: '0.625rem', padding: '1.25rem', marginBottom: '1rem', border: `1px solid ${C.primaryBorder}` }}>
                    <p style={{ ...lbl, color: C.primaryHover }}>Monthly Market Price Trend</p>
                    <div style={{ width: '100%', height: '180px', marginTop: '1rem' }}>
                        <ResponsiveContainer>
                            <LineChart data={mk.price_intelligence.trend} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                <XAxis dataKey="date" tick={{ fontSize: 10, fill: C.textSecondary }} tickFormatter={val => new Date(val).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })} axisLine={false} tickLine={false} />
                                <YAxis tick={{ fontSize: 10, fill: C.textSecondary }} axisLine={false} tickLine={false} tickFormatter={val => `$${val}`} />
                                <Tooltip content={<ChartTooltip suffix="USD/MT" />} />
                                <Line type="monotone" dataKey="price" stroke={C.primary} strokeWidth={2} dot={false} activeDot={{ r: 4 }} name="Avg Price" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                    <div style={{ background: 'linear-gradient(135deg, #eff6ff, #dbeafe)', border: `1px solid #bfdbfe`, borderRadius: '0.5rem', padding: '0.875rem' }}>
                        <p style={{ ...lbl, color: '#3b82f6' }}>Minimum Price</p>
                        <p style={{ ...val, color: '#1d4ed8' }}>{fmtMoney(mk.price_intelligence.min)}/MT</p>
                        <p style={{ fontSize: '0.6rem', color: '#93c5fd', margin: '0.25rem 0 0' }}>Recorded over period</p>
                    </div>
                    <div style={{ background: 'linear-gradient(135deg, #f0fdf4, #dcfce7)', border: `1px solid #bbf7d0`, borderRadius: '0.5rem', padding: '0.875rem' }}>
                        <p style={{ ...lbl, color: C.primaryHover }}>Maximum Price</p>
                        <p style={{ ...val, color: '#047857' }}>{fmtMoney(mk.price_intelligence.max)}/MT</p>
                        <p style={{ fontSize: '0.6rem', color: '#86efac', margin: '0.25rem 0 0' }}>Recorded over period</p>
                    </div>
                    <div style={{ background: 'linear-gradient(135deg, #fefce8, #fef9c3)', border: `1px solid #fde68a`, borderRadius: '0.5rem', padding: '0.875rem' }}>
                        <p style={{ ...lbl, color: '#d97706' }}>Typical Range (Median)</p>
                        <p style={{ ...val, color: '#92400e' }}>{fmtMoney(mk.price_intelligence.median)}/MT</p>
                        <p style={{ fontSize: '0.6rem', color: C.textTertiary, margin: '0.25rem 0 0' }}>Middle point pricing</p>
                    </div>
                </div>
            </section>

            {/* ── 3. Supplier Price Positioning ── */}
            <section style={card}>
                <h3 style={sec}>{L.entityPricePos}</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', alignItems: 'center', gap: '2rem' }}>
                    <div>
                        <p style={lbl}>Market Average Price</p>
                        <p style={{ ...val, fontSize: '1.25rem' }}>{fmtMoney(mk.positioning.market_avg)}/MT</p>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem' }}>
                            <p style={{ fontSize: '0.7rem', fontWeight: 700, margin: 0 }}>Price Differential</p>
                            <span style={{
                                background: mk.positioning.differential_pct <= 0 ? C.primaryLight : '#fef2f2',
                                color: mk.positioning.differential_pct <= 0 ? C.primaryHover : '#ef4444',
                                fontSize: '0.65rem', fontWeight: 800, padding: '0.2rem 0.5rem', borderRadius: '0.2rem',
                                border: `1px solid ${mk.positioning.differential_pct <= 0 ? C.primaryBorder : '#fca5a5'}`
                            }}>
                                {mk.positioning.differential_pct > 0 ? '+' : ''}{mk.positioning.differential_pct}% {
                                    mk.positioning.differential_pct <= 0 ? 'Below Market' : 'Above Market'
                                }
                            </span>
                        </div>
                        <p style={{ fontSize: '0.65rem', color: C.primary, marginTop: '0.5rem', fontStyle: 'italic', fontWeight: 600 }}>
                            * This entity offers {mk.positioning.differential_pct <= 0 ? 'competitive' : 'premium'} pricing compared to market average.
                        </p>
                    </div>
                    <div>
                        <p style={lbl}>Entity Overall Avg Price</p>
                        <p style={{ ...val, fontSize: '1.25rem' }}>{fmtMoney(mk.positioning.entity_avg)}/MT</p>
                    </div>
                    <div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                <span style={{ fontSize: '0.6rem', color: C.accentBlue, fontWeight: 700 }}>Market Average</span>
                                <div style={{ height: '14px', width: '100%', background: 'linear-gradient(90deg, #3b82f6, #60a5fa)', borderRadius: '4px' }} />
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                <span style={{ fontSize: '0.6rem', color: mk.positioning.differential_pct <= 0 ? C.primaryHover : '#ef4444', fontWeight: 700 }}>Entity Positioning</span>
                                <div style={{
                                    height: '14px',
                                    width: `${Math.min(100, Math.max(10, ((mk.positioning.entity_avg / (mk.positioning.market_avg || 1)) * 100)))}%`,
                                    background: mk.positioning.differential_pct <= 0 ? C.gradientGreen : 'linear-gradient(90deg, #f43f5e, #fb7185)',
                                    borderRadius: '4px',
                                    boxShadow: mk.positioning.differential_pct <= 0 ? '0 0 8px rgba(16,185,129,0.4)' : '0 0 8px rgba(244,63,94,0.4)'
                                }} />
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── 4. Country-Level Pricing & Sourcing ── */}
            <section style={card}>
                <h3 style={sec}>Country-Level Pricing & Sourcing</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                    <div>
                        <p style={{ ...lbl, marginBottom: '1rem' }}>Average Price by Origin Country</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {mk.country_pricing.slice(0, 5).map((c, i) => {
                                const COLORS = [C.primary, C.accentBlue, C.accentPurple, C.accentAmber, C.accentCyan];
                                const col = COLORS[i % COLORS.length];
                                return (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: C.textPrimary, width: '70px', flexShrink: 0 }}>{c.country}</span>
                                        <div style={{ flex: 1, height: '22px', background: '#f1f5f9', borderRadius: '4px', position: 'relative', overflow: 'hidden' }}>
                                            <div style={{
                                                position: 'absolute', top: 0, left: 0, bottom: 0,
                                                width: `${(c.avg_price / Math.max(...mk.country_pricing.map(x => x.avg_price))) * 100}%`,
                                                background: `linear-gradient(90deg, ${col}22, ${col}55)`,
                                                borderLeft: `3px solid ${col}`,
                                            }} />
                                            <span style={{ position: 'absolute', left: '0.5rem', top: '50%', transform: 'translateY(-50%)', fontSize: '0.7rem', fontWeight: 700, color: C.textPrimary }}>
                                                ${c.avg_price.toLocaleString(undefined, { maximumFractionDigits: 0 })}/MT
                                            </span>
                                        </div>
                                    </div>
                                );
                            })
                            }
                        </div>
                    </div>
                    <div>
                        <p style={{ ...lbl, marginBottom: '1rem' }}>{L.marketVolumeGeo}</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {mk.country_pricing.slice(0, 5).map((c, i) => {
                                const COLORS = [C.primary, C.accentBlue, C.accentPurple, C.accentAmber, C.accentCyan];
                                const col = COLORS[i % COLORS.length];
                                return (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: C.textPrimary, width: '70px', flexShrink: 0 }}>{c.country}</span>
                                        <div style={{ flex: 1, height: '22px', background: '#f1f5f9', borderRadius: '4px', position: 'relative', overflow: 'hidden', display: 'flex' }}>
                                            <div style={{
                                                width: `${c.share_pct}%`,
                                                background: `linear-gradient(90deg, ${col}, ${col}bb)`,
                                                borderRadius: '4px',
                                                display: 'flex', alignItems: 'center', paddingLeft: '0.5rem',
                                                transition: 'width 0.5s ease',
                                            }}>
                                                {c.share_pct > 15 && <span style={{ fontSize: '0.6rem', fontWeight: 700, color: '#fff' }}>{fmtVol(c.volume)}</span>}
                                            </div>
                                        </div>
                                        <span style={{ fontSize: '0.7rem', color: col, fontWeight: 700, width: '35px', textAlign: 'right' }}>{c.share_pct}%</span>
                                    </div>
                                );
                            })
                            }
                        </div>
                    </div>
                </div>
            </section>

            {/* ── 5. Supply Chain Flow ── */}
            <section style={card}>
                <h3 style={sec}>Supply Chain Flow (Trade Routes)</h3>
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                        <thead>
                            <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                                <th style={{ padding: '0.75rem 0.5rem', ...lbl }}>Source Country</th>
                                <th style={{ padding: '0.75rem 0.5rem', ...lbl }}>Destination Country</th>
                                <th style={{ padding: '0.75rem 0.5rem', ...lbl, textAlign: 'right' }}>Total Volume (MT)</th>
                                <th style={{ padding: '0.75rem 0.5rem', ...lbl, textAlign: 'right' }}>% of Market</th>
                                <th style={{ padding: '0.75rem 0.5rem', ...lbl, textAlign: 'right' }}>Avg Price (USD/MT)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(mk.supply_chain || []).map((row, i) => (
                                <tr key={i} style={{ borderBottom: `1px solid #f3f4f6` }}>
                                    <td style={{ padding: '0.5rem', fontSize: '0.8125rem', color: C.textPrimary }}>{row.source}</td>
                                    <td style={{ padding: '0.5rem', fontSize: '0.8125rem', color: C.textPrimary }}>{row.destination}</td>
                                    <td style={{ padding: '0.5rem', fontSize: '0.8125rem', color: C.textPrimary, textAlign: 'right', fontWeight: 600 }}>{row.volume.toLocaleString()}</td>
                                    <td style={{ padding: '0.5rem', fontSize: '0.8125rem', color: C.textSecondary, textAlign: 'right' }}>{row.share_pct}%</td>
                                    <td style={{ padding: '0.5rem', fontSize: '0.8125rem', color: C.textPrimary, textAlign: 'right' }}>${row.avg_price.toLocaleString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>

            {/* ── 6. Demand & Volume Trends ── */}
            <section style={card}>
                <h3 style={sec}>Demand & Volume Trends</h3>
                <div style={{ background: 'linear-gradient(145deg, #f0fdf4 0%, #ecfdf5 100%)', borderRadius: '0.625rem', padding: '1.25rem', marginBottom: '1rem', border: `1px solid ${C.primaryBorder}` }}>
                    <p style={{ ...lbl, color: C.primaryHover }}>Monthly Volume (MT) over Time</p>
                    <div style={{ width: '100%', height: '180px', marginTop: '1rem' }}>
                        <ResponsiveContainer>
                            <BarChart data={mk.price_intelligence.trend} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#d1fae5" />
                                <XAxis dataKey="date" tick={{ fontSize: 10, fill: C.textSecondary }} tickFormatter={val => new Date(val).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })} axisLine={false} tickLine={false} />
                                <YAxis tick={{ fontSize: 10, fill: C.textSecondary }} axisLine={false} tickLine={false} />
                                <Tooltip content={<ChartTooltip suffix="MT" />} cursor={{ fill: 'rgba(16,185,129,0.07)' }} />
                                <Bar dataKey="volume" fill="url(#volGrad)" radius={[4, 4, 0, 0]} name="Volume">
                                    <defs>
                                        <linearGradient id="volGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor={C.primary} stopOpacity={0.9} />
                                            <stop offset="100%" stopColor={C.primaryHover} stopOpacity={0.6} />
                                        </linearGradient>
                                    </defs>
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', textAlign: 'center' }}>
                    <div>
                        <p style={lbl}>Trend Direction</p>
                        <p style={{ ...val, color: mk.demand_trends.trend_direction_pct >= 0 ? C.primaryHover : '#ef4444' }}>
                            {mk.demand_trends.trend_direction_pct >= 0 ? 'Growing' : 'Declining'}
                        </p>
                    </div>
                    <div style={{ borderLeft: `1px solid ${C.border}`, borderRight: `1px solid ${C.border}` }}>
                        <p style={lbl}>Peak Demand Period</p>
                        <p style={val}>{mk.demand_trends.peak_period ? new Date(mk.demand_trends.peak_period).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : '—'}</p>
                    </div>
                    <div>
                        <p style={lbl}>Low Demand Period</p>
                        <p style={val}>{mk.demand_trends.low_period ? new Date(mk.demand_trends.low_period).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : '—'}</p>
                    </div>
                </div>
            </section>

            {/* ── 7. Competitive Comparison ── */}
            <section style={card}>
                <h3 style={sec}>{L.benchmarkingChart}</h3>
                <p style={{ fontSize: '0.8rem', color: C.textSecondary, marginTop: '-0.75rem', marginBottom: '1.5rem' }}>
                    {L.compSubtitle}
                </p>

                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                        <thead>
                            <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                                <th style={{ padding: '0.75rem 0.5rem', ...lbl, width: '40px' }}>Rank</th>
                                <th style={{ padding: '0.75rem 0.5rem', ...lbl }}>{L.compEntityHdr}</th>
                                <th style={{ padding: '0.75rem 0.5rem', ...lbl }}>{L.compVolHdr}</th>
                                <th style={{ padding: '0.75rem 0.5rem', ...lbl, textAlign: 'right' }}>{L.compPriceHdr}</th>
                                <th style={{ padding: '0.75rem 0.5rem', ...lbl, textAlign: 'right' }}>Price vs Market</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(mk.benchmarks || []).slice(0, 10).map((row, i) => {
                                const maxVol = mk.benchmarks[0]?.volume || row.volume || 1;
                                const barWidth = Math.max((row.volume / maxVol) * 100, 2);
                                const rankColors = ['#f59e0b', '#94a3b8', '#b45309'];
                                return (
                                    <tr key={i} style={{ borderBottom: `1px solid ${C.borderLight}`, background: row.is_current ? 'linear-gradient(90deg, #f0fdf4, #ecfdf5)' : i % 2 === 0 ? '#fafafa' : 'white' }}>
                                        <td style={{ padding: '0.625rem 0.5rem', fontSize: '0.8125rem' }}>
                                            <span style={{
                                                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                                width: '22px', height: '22px', borderRadius: '50%',
                                                background: i < 3 ? rankColors[i] : C.borderLight,
                                                color: i < 3 ? 'white' : C.textSecondary,
                                                fontSize: '0.65rem', fontWeight: 800,
                                            }}>{i + 1}</span>
                                        </td>
                                        <td style={{ padding: '0.625rem 0.5rem', fontSize: '0.8125rem', color: row.is_current ? C.primaryHover : C.textPrimary, fontWeight: row.is_current ? 700 : 500 }}>
                                            {row.name} {row.is_current && <span style={{ fontSize: '0.6rem', background: C.primaryLight, color: C.primaryHover, padding: '0.1rem 0.35rem', borderRadius: '0.2rem', fontWeight: 700 }}>YOU</span>}
                                        </td>
                                        <td style={{ padding: '0.625rem 0.5rem', fontSize: '0.8125rem', color: C.textPrimary, fontWeight: 600, minWidth: '150px' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <span style={{ width: '65px', color: C.accentBlue, fontWeight: 700 }}>{row.volume.toLocaleString()}</span>
                                                <div style={{ flex: 1, background: '#e2e8f0', height: '6px', borderRadius: '999px', maxWidth: '100px', overflow: 'hidden' }}>
                                                    <div style={{ background: row.is_current ? C.gradientGreen : `linear-gradient(90deg, ${C.accentBlue}, ${C.accentCyan})`, height: '100%', borderRadius: '999px', width: `${barWidth}%`, transition: 'width 0.5s' }} />
                                                </div>
                                            </div>
                                        </td>
                                        <td style={{ padding: '0.625rem 0.5rem', fontSize: '0.8125rem', color: C.textPrimary, textAlign: 'right', fontWeight: 600 }}>${row.avg_price.toLocaleString()}</td>
                                        <td style={{ padding: '0.625rem 0.5rem', textAlign: 'right' }}>
                                            <span style={{
                                                fontSize: '0.75rem', fontWeight: 800,
                                                color: row.price_diff <= 0 ? C.primaryHover : '#ef4444',
                                                background: row.price_diff <= 0 ? '#dcfce7' : '#fee2e2',
                                                padding: '0.15rem 0.4rem', borderRadius: '0.25rem',
                                            }}>
                                                {row.price_diff > 0 ? '+' : ''}{row.price_diff}%
                                            </span>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// Company Tab (Fully implemented from backend company_intel data)
// ─────────────────────────────────────────────────────────────────────────────
const CompanyTab = ({ supplier, isBuyer }) => {
    const cp = supplier.company_intel;
    if (!cp) return <PlaceholderTab label="Company Data Loading..." />;

    // eslint-disable-next-line no-unused-vars
    const L = getLabels(isBuyer);
    const card = {
        background: C.gradientCard,
        border: `1px solid ${C.border}`,
        borderRadius: '0.875rem',
        padding: '1.75rem',
        marginBottom: '1.5rem',
        boxShadow: '0 1px 6px rgba(15,23,42,0.06)',
    };
    const sec = { fontSize: '0.9rem', fontWeight: 800, color: C.textPrimary, margin: '0 0 1.25rem', letterSpacing: '-0.01em', display: 'flex', alignItems: 'center', gap: '0.5rem' };
    const lbl = { fontSize: '0.65rem', color: C.textTertiary, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 0.25rem' };
    const val = { fontSize: '1.25rem', fontWeight: 800, color: C.textPrimary, margin: 0 };

    const fmtMoney = n => n ? `$${(n / 1000000).toFixed(1)}M` : '—';
    const fmtVol = n => n ? `${Math.round(n).toLocaleString()} MT` : '—';

    const PIE_COLORS = [C.primary, '#3b82f6', '#8b5cf6', '#f59e0b', '#f43f5e'];

    return (
        <div style={{ display: 'flex', flexDirection: 'column' }}>

            {/* ── 1. Company Overview ── */}
            <section style={{ ...card, padding: '1.25rem 1.5rem', borderTop: `4px solid ${C.primary}` }}>
                <h3 style={{ ...sec, marginBottom: '1rem', fontSize: '0.8125rem' }}>
                    Company Overview — {supplier.name}
                </h3>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div>
                        <p style={lbl}>Total Volume Traded (All time)</p>
                        <p style={{ ...val, fontSize: '1.5rem' }}>{fmtVol(cp.overview.total_volume)}</p>
                        <p style={{ fontSize: '0.65rem', color: C.textTertiary, marginTop: '0.1rem' }}>Across all products</p>
                    </div>
                    <div>
                        <p style={lbl}>Total Transactions</p>
                        <p style={val}>{cp.overview.total_transactions?.toLocaleString() || 0}</p>
                        <p style={{ fontSize: '0.65rem', color: C.textTertiary, marginTop: '0.1rem' }}>Since Jan 2023</p>
                    </div>
                    <div>
                        <p style={lbl}>Estimated Trade Value</p>
                        <p style={val}>{fmtMoney(cp.overview.trade_value)}</p>
                        <p style={{ fontSize: '0.65rem', color: C.textTertiary, marginTop: '0.1rem' }}>USD (Approx)</p>
                    </div>
                    <div>
                        <p style={lbl}>Trade Direction</p>
                        <p style={val}>{cp.overview.trade_direction_label}</p>
                        <p style={{ fontSize: '0.65rem', color: C.textTertiary, marginTop: '0.1rem' }}>{cp.overview.trade_direction_pct}% export focus</p>
                    </div>
                </div>
            </section>

            {/* ── 2. Product Portfolio (Core Capabilities) ── */}
            <section style={card}>
                <h3 style={sec}>Product Portfolio</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                    {/* Left List */}
                    <div>
                        <p style={{ ...lbl, marginBottom: '1rem' }}>Top Products by Volume</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {cp.portfolio.top.map((p, i) => (
                                <div key={i} style={{ borderBottom: i < cp.portfolio.top.length - 1 ? `1px solid ${C.borderLight}` : 'none', paddingBottom: '0.625rem' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <p style={{ fontSize: '0.8125rem', fontWeight: 700, color: C.textPrimary, margin: 0 }}>{p.product}</p>
                                        <p style={{ fontSize: '0.8125rem', fontWeight: 800, color: C.accentBlue, margin: 0 }}>{p.volume.toLocaleString()} MT</p>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.35rem' }}>
                                        <span style={{ fontSize: '0.65rem', color: C.primary, fontWeight: 600 }}>{p.share_pct}% of portfolio</span>
                                        <span style={{ fontSize: '0.65rem', color: C.accentPurple, fontWeight: 600 }}>Avg: ${p.avg_price}/MT</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                    {/* Right Chart */}
                    <div>
                        <p style={{ ...lbl, marginBottom: '0.2rem' }}>Portfolio Distribution</p>
                        <div style={{ background: '#f9fafb', borderRadius: '0.5rem', height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie data={cp.portfolio.top} dataKey="volume" outerRadius={80} innerRadius={50} stroke="none">
                                        {cp.portfolio.top.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip content={({ active, payload }) => {
                                        if (active && payload && payload.length) {
                                            const d = payload[0].payload;
                                            return (
                                                <div style={{ background: '#fff', border: `1px solid ${C.border}`, padding: '0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem' }}>
                                                    <p style={{ margin: '0 0 0.2rem', fontWeight: 700 }}>{d.product}</p>
                                                    <p style={{ margin: 0 }}>{d.share_pct}% ({d.volume.toLocaleString()} MT)</p>
                                                </div>
                                            );
                                        } return null;
                                    }} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                        <div style={{ marginTop: '1rem', background: `linear-gradient(135deg, ${C.primaryLight}, #dbeafe)`, padding: '0.875rem', borderRadius: '0.625rem', border: `1px solid ${C.primaryBorder}` }}>
                            <p style={{ fontSize: '0.7rem', fontWeight: 700, margin: '0 0 0.25rem', color: C.textPrimary }}>Specialization Insight</p>
                            <p style={{ fontSize: '0.7rem', color: C.textSecondary, margin: 0, lineHeight: 1.6 }}>
                                Company specializes in {cp.portfolio.all_count} distinct core categories. Their highest volume is {cp.portfolio.top[0]?.product}.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── 3. Partner Network ── */}
            <section style={card}>
                <h3 style={sec}>Partner Network</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                    {/* Left List */}
                    <div>
                        <p style={{ ...lbl, marginBottom: '1rem' }}>Top {isBuyer ? 'Suppliers' : 'Buyers'} (All Products)</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {cp.network.top.map((p, i) => {
                                const COLORS = [C.primary, C.accentBlue, C.accentPurple, C.accentAmber, C.accentCyan];
                                const col = COLORS[i % COLORS.length];
                                return (
                                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: `1px solid ${C.borderLight}`, paddingBottom: '0.5rem' }}>
                                        <span style={{ fontSize: '0.8125rem', color: C.textPrimary, fontWeight: 600 }}>{p.name}</span>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: col }}>{p.volume.toLocaleString()} MT</span>
                                            <span style={{ fontSize: '0.65rem', background: `${col}1a`, color: col, padding: '0.1rem 0.35rem', borderRadius: '0.2rem', fontWeight: 700 }}>{p.share_pct}%</span>
                                        </div>
                                    </div>
                                );
                            })}
                            {cp.network.total_count > 5 && (
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '0.5rem' }}>
                                    <span style={{ fontSize: '0.8125rem', color: C.textSecondary, fontWeight: 500 }}>
                                        +{cp.network.total_count - cp.network.top.length} other {isBuyer ? 'suppliers' : 'buyers'}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                    {/* Right Concentration Analysis */}
                    <div>
                        <p style={{ ...lbl, marginBottom: '0.2rem' }}>Relationship Concentration</p>
                        <div style={{ background: '#f9fafb', borderRadius: '0.5rem', height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={cp.network.top} layout="vertical" margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                                    <XAxis type="number" hide />
                                    <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 9, fill: C.textSecondary }} axisLine={false} tickLine={false} />
                                    <Tooltip cursor={{ fill: 'transparent' }} />
                                    <Bar dataKey="share_pct" fill={C.primary} radius={[0, 4, 4, 0]} barSize={12} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                        <div style={{ marginTop: '1rem', border: `1px solid ${C.border}`, padding: '1rem', borderRadius: '0.5rem' }}>
                            <p style={{ fontSize: '0.65rem', color: C.textTertiary, textTransform: 'uppercase', letterSpacing: '0.04em', margin: '0 0 0.2rem' }}>Relationship Level</p>
                            <p style={{ fontSize: '0.9375rem', fontWeight: 800, color: C.textPrimary, margin: '0 0 0.2rem' }}>
                                {cp.network.concentration_label}
                            </p>
                            <p style={{ fontSize: '0.7rem', color: C.textSecondary, margin: '0 0 0.5rem' }}>
                                Top 5 partners capture {cp.network.top_5_share_pct}% of total volume.
                            </p>

                        </div>
                    </div>
                </div>
            </section>

            {/* ── 4. Geographic Presence ── */}
            <section style={card}>
                <h3 style={sec}>Geographic Presence</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3rem' }}>
                    <div>
                        <p style={{ ...lbl, marginBottom: '1rem' }}>Export Destinations (by Volume)</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {cp.geography.exports.map((c, i) => {
                                const COLORS = [C.primary, C.accentBlue, C.accentPurple, C.accentAmber, C.accentCyan];
                                const col = COLORS[i % COLORS.length];
                                return (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: C.textPrimary, width: '80px', flexShrink: 0 }}>{c.country}</span>
                                        <div style={{ flex: 1, height: '20px', background: '#f1f5f9', borderRadius: '4px', position: 'relative', overflow: 'hidden' }}>
                                            <div style={{ position: 'absolute', top: 0, left: 0, bottom: 0, width: `${c.share_pct}%`, background: `linear-gradient(90deg, ${col}, ${col}99)` }} />
                                            <span style={{ position: 'absolute', left: '0.5rem', top: '50%', transform: 'translateY(-50%)', fontSize: '0.65rem', fontWeight: 700, color: '#fff', textShadow: '0 1px 2px rgba(0,0,0,0.3)' }}>
                                                {c.volume.toLocaleString()} MT
                                            </span>
                                        </div>
                                        <span style={{ fontSize: '0.7rem', color: col, fontWeight: 700, width: '35px', textAlign: 'right' }}>{c.share_pct}%</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                    <div>
                        <p style={{ ...lbl, marginBottom: '1rem' }}>Source Countries (Supply Origins)</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {cp.geography.sources.map((c, i) => (
                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: C.textPrimary, width: '80px' }}>{c.country}</span>
                                    <div style={{ flex: 1, height: '18px', background: '#e5e7eb', borderRadius: '2px', position: 'relative' }}>
                                        <div style={{ position: 'absolute', top: 0, left: 0, bottom: 0, width: `${c.share_pct}%`, background: '#d1d5db', borderRadius: '2px' }} />
                                        {c.share_pct > 15 && <span style={{ position: 'absolute', left: '0.5rem', top: '50%', transform: 'translateY(-50%)', fontSize: '0.65rem', fontWeight: 600, color: C.textPrimary }}>
                                            {c.volume.toLocaleString()} MT
                                        </span>}
                                    </div>
                                    <span style={{ fontSize: '0.7rem', color: C.textSecondary, width: '30px', textAlign: 'right' }}>{c.share_pct}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* ── 5. Activity & Growth Trends ── */}
            <section style={card}>
                <h3 style={sec}>Activity & Growth Trends</h3>
                <div style={{ background: 'linear-gradient(145deg, #f0fdf4 0%, #ecfdf5 100%)', borderRadius: '0.625rem', padding: '1.25rem', marginBottom: '1rem', border: `1px solid ${C.primaryBorder}` }}>
                    <p style={{ ...lbl, color: C.primaryHover }}>Quarterly Trade Volume (All Time)</p>
                    <div style={{ width: '100%', height: '180px', marginTop: '1rem' }}>
                        <ResponsiveContainer>
                            <AreaChart data={cp.trends.quarterly} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorVol" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={C.primary} stopOpacity={0.3} />
                                        <stop offset="95%" stopColor={C.primary} stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#d1fae5" />
                                <XAxis dataKey="qtr" tick={{ fontSize: 10, fill: C.textSecondary }} axisLine={false} tickLine={false} />
                                <YAxis tick={{ fontSize: 10, fill: C.textSecondary }} axisLine={false} tickLine={false} />
                                <Tooltip content={({ active, payload, label }) => {
                                    if (active && payload && payload.length) {
                                        return (
                                            <div style={{ background: '#fff', border: `1px solid ${C.border}`, padding: '0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem' }}>
                                                <p style={{ margin: '0 0 0.2rem', fontWeight: 700 }}>{label}</p>
                                                <p style={{ margin: 0, color: C.primary, fontWeight: 700 }}>{payload[0].value.toLocaleString()} MT</p>
                                            </div>
                                        );
                                    } return null;
                                }} />
                                <Area type="monotone" dataKey="volume" stroke={C.primary} strokeWidth={2} fillOpacity={1} fill="url(#colorVol)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', borderTop: `1px solid ${C.border}`, paddingTop: '1.25rem' }}>

                    <div style={{ borderLeft: `1px solid ${C.border}`, paddingLeft: '1rem' }}>
                        <p style={lbl}>Trend Direction</p>
                        <p style={val}>{cp.trends.trend_label}</p>
                        <p style={{ fontSize: '0.65rem', color: C.textTertiary, marginTop: '0.25rem' }}>Consistent volume</p>
                    </div>
                    <div style={{ borderLeft: `1px solid ${C.border}`, paddingLeft: '1rem' }}>
                        <p style={lbl}>Peak Quarter</p>
                        <p style={val}>{cp.trends.peak_qtr}</p>
                        <p style={{ fontSize: '0.65rem', color: C.textTertiary, marginTop: '0.25rem' }}>Highest MT traded</p>
                    </div>
                    <div style={{ borderLeft: `1px solid ${C.border}`, paddingLeft: '1rem' }}>
                        <p style={lbl}>Activity Status</p>
                        <p style={val}>{cp.trends.status}</p>
                        <p style={{ fontSize: '0.65rem', color: C.textTertiary, marginTop: '0.25rem' }}>Valid history tracked</p>
                    </div>
                </div>
            </section>

            {/* ── 6. Buyer/Supplier Behavior (Trust & Reliability Signals) ── */}
            <section style={card}>
                <h3 style={sec}>{isBuyer ? 'Supplier Behavior' : 'Buyer Behavior'}</h3>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                    <div style={{ border: `1px solid ${C.border}`, borderRadius: '0.25rem', padding: '1rem' }}>
                        <p style={lbl}>Total Unique {isBuyer ? 'Suppliers' : 'Buyers'}</p>
                        <p style={{ fontSize: '1.875rem', fontWeight: 800, color: C.textPrimary, margin: '0' }}>
                            {cp.behavior.unique_partners}
                        </p>
                        <p style={{ fontSize: '0.65rem', color: C.textTertiary, margin: '0.25rem 0 0' }}>Across verified data</p>
                    </div>
                    <div style={{ border: `1px solid ${C.border}`, borderRadius: '0.25rem', padding: '1rem' }}>
                        <p style={lbl}>Repeat Partner Ratio</p>
                        <p style={{ fontSize: '1.875rem', fontWeight: 800, color: C.textPrimary, margin: '0' }}>
                            {cp.behavior.repeat_ratio_pct}%
                        </p>
                        <p style={{ fontSize: '0.65rem', color: C.textTertiary, margin: '0.25rem 0 0' }}>% with >1 transaction</p>
                    </div>

                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem', marginTop: '1rem' }}>
                    <div style={{ border: `1px solid ${C.border}`, borderRadius: '0.25rem', padding: '1rem', background: '#f8fafc' }}>
                        <p style={lbl}>Long-Term Partners (>1 year)</p>
                        <p style={{ fontSize: '1.25rem', fontWeight: 800, color: C.textPrimary, margin: '0' }}>
                            {cp.behavior.long_term_partners} {isBuyer ? 'suppliers' : 'buyers'}
                        </p>
                        <p style={{ fontSize: '0.65rem', color: C.textSecondary, margin: '0.25rem 0 0' }}>Presenting >12 months engagement</p>
                    </div>

                </div>
            </section>

            {/* ── 7. Product <-> Partner Mapping ── */}
            <section style={card}>
                <h3 style={sec}>Product ↔ Partner Mapping</h3>
                <p style={{ fontSize: '0.75rem', color: C.textSecondary, marginBottom: '1rem' }}>
                    Top {isBuyer ? 'supplier' : 'buyer'} relationships by product category — shows which counterparties buy/sell which products.
                </p>
                <div style={{ overflowX: 'auto', border: `1px solid ${C.border}`, borderRadius: '0.5rem' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                        <thead>
                            <tr style={{ background: '#f9fafb', borderBottom: `1px solid ${C.border}` }}>
                                <th style={{ padding: '0.75rem 1rem', ...lbl }}>Product</th>
                                <th style={{ padding: '0.75rem 1rem', ...lbl }}>Top {isBuyer ? 'Supplier' : 'Buyer'} #1</th>
                                <th style={{ padding: '0.75rem 1rem', ...lbl, textAlign: 'right' }}>Volume</th>
                                <th style={{ padding: '0.75rem 1rem', ...lbl }}>Top {isBuyer ? 'Supplier' : 'Buyer'} #2</th>
                                <th style={{ padding: '0.75rem 1rem', ...lbl, textAlign: 'right' }}>Volume</th>
                                <th style={{ padding: '0.75rem 1rem', ...lbl }}>Top {isBuyer ? 'Supplier' : 'Buyer'} #3</th>
                                <th style={{ padding: '0.75rem 1rem', ...lbl, textAlign: 'right' }}>Volume</th>
                            </tr>
                        </thead>
                        <tbody>
                            {cp.mapping.map((row, i) => (
                                <tr key={i} style={{ borderBottom: `1px solid ${C.border}` }}>
                                    <td style={{ padding: '0.75rem 1rem', fontSize: '0.75rem', fontWeight: 600, color: C.textPrimary }}>
                                        {row.product}
                                    </td>
                                    {/* Partner 1 */}
                                    <td style={{ padding: '0.75rem 1rem', fontSize: '0.75rem', color: C.textSecondary }}>{row.partners[0]?.name || '—'}</td>
                                    <td style={{ padding: '0.75rem 1rem', fontSize: '0.75rem', color: C.textPrimary, textAlign: 'right', fontWeight: 600 }}>{row.partners[0]?.volume ? row.partners[0].volume.toLocaleString() + ' MT' : '—'}</td>
                                    {/* Partner 2 */}
                                    <td style={{ padding: '0.75rem 1rem', fontSize: '0.75rem', color: C.textSecondary }}>{row.partners[1]?.name || '—'}</td>
                                    <td style={{ padding: '0.75rem 1rem', fontSize: '0.75rem', color: C.textPrimary, textAlign: 'right', fontWeight: 600 }}>{row.partners[1]?.volume ? row.partners[1].volume.toLocaleString() + ' MT' : '—'}</td>
                                    {/* Partner 3 */}
                                    <td style={{ padding: '0.75rem 1rem', fontSize: '0.75rem', color: C.textSecondary }}>{row.partners[2]?.name || '—'}</td>
                                    <td style={{ padding: '0.75rem 1rem', fontSize: '0.75rem', color: C.textPrimary, textAlign: 'right', fontWeight: 600 }}>{row.partners[2]?.volume ? row.partners[2].volume.toLocaleString() + ' MT' : '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

            </section>

        </div>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// Transactions Tab (Fully implemented)
// ─────────────────────────────────────────────────────────────────────────────
const TransactionsTab = ({ supplier, isBuyer, query, variantName }) => {
    const [searchParams] = useSearchParams();
    const scopeParam = searchParams.get('scope') || '';
    const intentParam = searchParams.get('intent') || '';
    const subcatIdParam = searchParams.get('subcat_id') || null;

    // eslint-disable-next-line no-unused-vars
    const L = getLabels(isBuyer);
    const card = { background: C.card, border: `1px solid ${C.border}`, borderRadius: '0.75rem', padding: '1.5rem', marginBottom: '1.5rem' };
    const sec = { fontSize: '0.9rem', fontWeight: 800, color: C.textPrimary, margin: '0 0 1.25rem', letterSpacing: '-0.01em' };
    const lbl = { fontSize: '0.65rem', color: C.textSecondary, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', margin: '0 0 0.2rem' };
    // eslint-disable-next-line no-unused-vars
    const val = { fontSize: '1.25rem', fontWeight: 800, color: C.textPrimary, margin: 0 };
    const fmtMoney = n => n ? `$${n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}` : '—';

    // State for filtering
    const [filters, setFilters] = useState({
        start_date: '',
        end_date: '',
        buyer: '',
        seller: '',
        country: 'All Countries',
        min_qty: '',
        max_qty: '',
        min_price: '',
        max_price: ''
    });

    const [page, setPage] = useState(1);
    const [pageSize] = useState(15);
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState(null);
    const [txError, setTxError] = useState(null);

    const loadData = async (currentPage, currentFilters) => {
        setLoading(true);
        try {
            const actualFilters = { ...currentFilters };
            if (actualFilters.country === 'All Countries') delete actualFilters.country;
            // Clean empty strings
            Object.keys(actualFilters).forEach(key => {
                if (actualFilters[key] === '') delete actualFilters[key];
            });

            const result = await searchService.getSupplierTransactions(
                supplier.name,
                query,
                scopeParam,
                subcatIdParam,
                variantName,
                intentParam,
                currentPage,
                pageSize,
                actualFilters
            );
            setData(result);
        } catch (err) {
            console.error('Failed to load transactions', err);
            setTxError(err?.response?.data?.error || 'Failed to load transactions. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData(page, filters);
        // eslint-disable-next-line
    }, [page]);

    const handleFilterChange = (e) => {
        const { name, value } = e.target;
        setFilters(prev => ({ ...prev, [name]: value }));
    };

    const applyFilters = () => {
        setPage(1);
        loadData(1, filters);
    };

    const resetFilters = () => {
        const defaultFilters = { start_date: '', end_date: '', buyer: '', seller: '', country: 'All Countries', min_qty: '', max_qty: '', min_price: '', max_price: '' };
        setFilters(defaultFilters);
        setPage(1);
        loadData(1, defaultFilters);
    };

    const exportCSV = () => {
        if (!data || !data.records.length) return;
        const headers = ["Date", "Buyer", "Seller", "Country", "Quantity (MT)", "Price (USD/MT)"];
        const rows = data.records.map(r => [
            r.date, `"${r.buyer}"`, `"${r.seller}"`, r.country, r.quantity, r.price
        ]);
        const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `Transactions_${supplier.name}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    if (loading && !data) return <PlaceholderTab label="Loading Transactions..." />;
    if (txError) return (
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: '0.75rem', padding: '3rem 2rem', textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⚠️</div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: C.textPrimary, marginBottom: '0.5rem' }}>Could not load transactions</h3>
            <p style={{ fontSize: '0.8125rem', color: C.textSecondary, maxWidth: '400px', margin: '0 auto 1rem' }}>{txError}</p>
            <button onClick={() => { setTxError(null); loadData(page, filters); }} style={{ padding: '0.5rem 1rem', background: '#1e293b', color: 'white', border: 'none', borderRadius: '0.25rem', cursor: 'pointer', fontWeight: 700, fontSize: '0.8125rem' }}>Retry</button>
        </div>
    );
    if (!data) return <PlaceholderTab label="Loading Transactions..." />;

    const inputStyle = { width: '100%', padding: '0.5rem', fontSize: '0.8125rem', border: `1px solid ${C.border}`, borderRadius: '0.25rem' };
    const btnBase = { padding: '0.5rem 1rem', fontSize: '0.8125rem', fontWeight: 700, borderRadius: '0.25rem', cursor: 'pointer', border: 'none' };

    return (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
            {/* ── Summary ── */}
            <section style={{ ...card, background: C.gradientHero, border: 'none', padding: '1.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                    <h3 style={{ ...sec, margin: 0, color: 'white', opacity: 0.95 }}>Transaction Data Summary</h3>
                    <p style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.45)', margin: 0 }}>Results update based on applied filters</p>
                </div>
                <div style={{ display: 'flex', gap: '3rem' }}>
                    {[
                        { label: 'Total Transactions', value: data.summary.total_transactions?.toLocaleString(), color: '#34d399' },
                        { label: 'Total Volume', value: `${data.summary.total_volume?.toLocaleString()} MT`, color: '#60a5fa' },
                        { label: 'Average Price', value: `${fmtMoney(data.summary.average_price)}/MT`, color: '#fbbf24' },
                    ].map((item, i) => (
                        <div key={i} style={{ borderLeft: `3px solid ${item.color}`, paddingLeft: '1rem' }}>
                            <p style={{ ...lbl, color: 'rgba(255,255,255,0.5)', margin: '0 0 0.25rem' }}>{item.label}</p>
                            <p style={{ fontSize: '1.75rem', fontWeight: 900, color: 'white', margin: 0, letterSpacing: '-0.03em' }}>{item.value}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── Filters ── */}
            <section style={card}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3 style={{ ...sec, margin: 0 }}>Filters & Search</h3>
                    <span style={{ fontSize: '0.75rem', color: C.textSecondary, cursor: 'pointer' }}>Hide Filters ^</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1.5fr 1.5fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                    <div>
                        <p style={lbl}>Date Range</p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <input type="date" name="start_date" value={filters.start_date} onChange={handleFilterChange} style={inputStyle} />
                            <span style={{ color: C.border }}>—</span>
                            <input type="date" name="end_date" value={filters.end_date} onChange={handleFilterChange} style={inputStyle} />
                        </div>
                    </div>
                    <div>
                        <p style={lbl}>Buyer</p>
                        <input type="text" name="buyer" placeholder="🔍 Search buyer name..." value={filters.buyer} onChange={handleFilterChange} style={inputStyle} />
                    </div>
                    <div>
                        <p style={lbl}>Seller</p>
                        <input type="text" name="seller" placeholder="🔍 Search seller name..." value={filters.seller} onChange={handleFilterChange} style={inputStyle} />
                    </div>
                    <div>
                        <p style={{ ...lbl, marginTop: '0.5rem' }}>Country</p>
                        <select name="country" value={filters.country} onChange={handleFilterChange} style={inputStyle}>
                            <option>All Countries</option>
                            {supplier.filters?.countries?.map((c, i) => <option key={i} value={c}>{c}</option>)}
                        </select>
                    </div>
                    <div>
                        <p style={{ ...lbl, marginTop: '0.5rem' }}>Quantity (MT)</p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <input type="number" name="min_qty" placeholder="Min" value={filters.min_qty} onChange={handleFilterChange} style={inputStyle} />
                            <span style={{ color: C.border }}>—</span>
                            <input type="number" name="max_qty" placeholder="Max" value={filters.max_qty} onChange={handleFilterChange} style={inputStyle} />
                        </div>
                    </div>
                    <div>
                        <p style={{ ...lbl, marginTop: '0.5rem' }}>Price (USD/MT)</p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <input type="number" name="min_price" placeholder="Min" value={filters.min_price} onChange={handleFilterChange} style={inputStyle} />
                            <span style={{ color: C.border }}>—</span>
                            <input type="number" name="max_price" placeholder="Max" value={filters.max_price} onChange={handleFilterChange} style={inputStyle} />
                        </div>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <button onClick={applyFilters} style={{ ...btnBase, background: '#1e293b', color: 'white' }}>Apply Filters</button>
                    <button onClick={resetFilters} style={{ ...btnBase, background: 'white', color: C.textPrimary, border: `1px solid ${C.border}` }}>Reset</button>
                </div>
            </section>

            {/* ── Top Lists ── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                <div style={{ ...card, marginBottom: 0, padding: '1.25rem' }}>
                    <h3 style={{ ...sec, margin: '0 0 1rem' }}>Top {isBuyer ? 'Sellers' : 'Buyers'} by Quantity</h3>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                        {data.top_entities.map((cp, i) => {
                            const COLORS = [C.primary, C.accentBlue, C.accentPurple, C.accentAmber, C.accentCyan];
                            const col = COLORS[i % COLORS.length];
                            return (
                                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.625rem 0', borderBottom: i < 4 ? `1px solid ${C.borderLight}` : 'none' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: col, flexShrink: 0 }} />
                                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: C.textPrimary }}>{cp.name}</span>
                                    </div>
                                    <span style={{ fontSize: '0.75rem', fontWeight: 800, color: col }}>{cp.volume.toLocaleString()} MT</span>
                                </div>
                            );
                        })}
                        {!data.top_entities.length && <p style={{ fontSize: '0.75rem', color: C.textTertiary }}>No data</p>}
                    </div>
                </div>
                <div style={{ ...card, marginBottom: 0, padding: '1.25rem' }}>
                    <h3 style={{ ...sec, margin: '0 0 1rem' }}>Top {isBuyer ? 'Origin' : 'Destination'} Countries by Quantity</h3>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                        {data.top_countries.map((cp, i) => {
                            const COLORS = [C.accentBlue, C.accentPurple, C.accentAmber];
                            const col = COLORS[i % COLORS.length];
                            return (
                                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.625rem 0', borderBottom: i < 2 ? `1px solid ${C.borderLight}` : 'none' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span style={{ fontSize: '0.8rem' }}>🌍</span>
                                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: C.textPrimary }}>{cp.name}</span>
                                    </div>
                                    <span style={{ fontSize: '0.75rem', fontWeight: 800, color: col }}>{cp.volume.toLocaleString()} MT</span>
                                </div>
                            );
                        })}
                        {!data.top_countries.length && <p style={{ fontSize: '0.75rem', color: C.textTertiary }}>No data</p>}
                    </div>
                </div>
            </div>

            {/* ── Records Table ── */}
            <section style={{ ...card, padding: 0, overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 1.5rem', borderBottom: `1px solid ${C.border}` }}>
                    <h3 style={{ ...sec, margin: 0 }}>Transaction Records</h3>
                    <button onClick={exportCSV} style={{ ...btnBase, background: C.gradientGreen, color: 'white', boxShadow: '0 2px 8px rgba(16,185,129,0.3)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        ⬇ Export CSV
                    </button>
                </div>
                <div style={{ overflowX: 'auto', opacity: loading ? 0.5 : 1, transition: 'opacity 0.2s' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                        <thead>
                            <tr style={{ background: C.gradientHero, borderBottom: `1px solid ${C.border}` }}>
                                <th style={{ padding: '0.75rem 1.5rem', ...lbl, color: 'rgba(255,255,255,0.6)' }}>Date</th>
                                <th style={{ padding: '0.75rem 1.5rem', ...lbl, color: 'rgba(255,255,255,0.6)' }}>Buyer</th>
                                <th style={{ padding: '0.75rem 1.5rem', ...lbl, color: 'rgba(255,255,255,0.6)' }}>Seller</th>
                                <th style={{ padding: '0.75rem 1.5rem', ...lbl, color: 'rgba(255,255,255,0.6)' }}>Country</th>
                                <th style={{ padding: '0.75rem 1.5rem', ...lbl, textAlign: 'right', color: 'rgba(255,255,255,0.6)' }}>Quantity (MT)</th>
                                <th style={{ padding: '0.75rem 1.5rem', ...lbl, textAlign: 'right', color: 'rgba(255,255,255,0.6)' }}>Price (USD/MT)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.records.map((r, i) => (
                                <tr key={i} style={{ borderBottom: `1px solid ${C.borderLight}`, background: i % 2 === 0 ? '#fafafa' : 'white', transition: 'background 0.15s' }}
                                    onMouseEnter={e => e.currentTarget.style.background = '#f0fdf4'}
                                    onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? '#fafafa' : 'white'}
                                >
                                    <td style={{ padding: '0.75rem 1.5rem', fontSize: '0.75rem', color: C.textSecondary, fontWeight: 600, whiteSpace: 'nowrap' }}>
                                        {r.date !== '-' ? new Date(r.date).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' }) : '-'}
                                    </td>
                                    <td style={{ padding: '0.75rem 1.5rem', fontSize: '0.75rem', color: C.accentBlue, fontWeight: 700 }}>{r.buyer}</td>
                                    <td style={{ padding: '0.75rem 1.5rem', fontSize: '0.75rem', color: C.primaryHover, fontWeight: 600 }}>{r.seller}</td>
                                    <td style={{ padding: '0.75rem 1.5rem', fontSize: '0.75rem' }}>
                                        <span style={{ background: `${C.accentAmber}18`, color: C.accentAmber, fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.4rem', borderRadius: '0.25rem' }}>
                                            {r.country}
                                        </span>
                                    </td>
                                    <td style={{ padding: '0.75rem 1.5rem', fontSize: '0.75rem', color: C.textPrimary, textAlign: 'right', fontWeight: 800 }}>{r.quantity.toLocaleString()}</td>
                                    <td style={{ padding: '0.75rem 1.5rem', fontSize: '0.75rem', textAlign: 'right', fontWeight: 800, color: C.accentPurple }}>
                                        {r.price ? `$${Math.round(r.price).toLocaleString()}` : '—'}
                                    </td>
                                </tr>
                            ))}
                            {!data.records.length && (
                                <tr><td colSpan="6" style={{ padding: '2rem', textAlign: 'center', color: C.textTertiary, fontSize: '0.875rem' }}>No transactions found for these filters.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.5rem', background: '#f8fafc', borderTop: `1px solid ${C.border}` }}>
                    <span style={{ fontSize: '0.75rem', color: C.textSecondary }}>
                        Showing {data.total_count ? ((page - 1) * pageSize) + 1 : 0}-{Math.min(page * pageSize, data.total_count)} of {data.total_count} transactions
                    </span>
                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                        <button
                            disabled={page === 1} onClick={() => setPage(p => p - 1)}
                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', background: 'white', border: `1px solid ${C.border}`, borderRadius: '0.25rem', cursor: page === 1 ? 'not-allowed' : 'pointer' }}
                        >Previous</button>

                        {/* Page Numbers mapping (Simplified for UI look) */}
                        {[...Array(Math.ceil(data.total_count / pageSize) || 1).keys()].slice(Math.max(0, page - 3), page + 2).map(n => (
                            <button
                                key={n + 1}
                                onClick={() => setPage(n + 1)}
                                style={{
                                    padding: '0.25rem 0.5rem', fontSize: '0.75rem', cursor: 'pointer', borderRadius: '0.25rem',
                                    background: page === n + 1 ? '#1e293b' : 'white',
                                    color: page === n + 1 ? 'white' : C.textSecondary,
                                    border: `1px solid ${page === n + 1 ? '#1e293b' : C.border}`
                                }}
                            >
                                {n + 1}
                            </button>
                        ))}

                        <button
                            disabled={page >= Math.ceil(data.total_count / pageSize) || data.total_count === 0} onClick={() => setPage(p => p + 1)}
                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', background: 'white', border: `1px solid ${C.border}`, borderRadius: '0.25rem', cursor: (page >= Math.ceil(data.total_count / pageSize) || data.total_count === 0) ? 'not-allowed' : 'pointer' }}
                        >Next</button>
                    </div>
                </div>
            </section>
        </div>
    );
};

// ─────────────────────────────────────────────────────────────────────────────
// Placeholder for tabs not yet built
// ─────────────────────────────────────────────────────────────────────────────
const PlaceholderTab = ({ label }) => (
    <div style={{
        background: C.card, border: `1px solid ${C.border}`, borderRadius: '0.75rem',
        padding: '4rem 2rem', textAlign: 'center',
    }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🔧</div>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: C.textPrimary, marginBottom: '0.5rem' }}>{label}</h3>
        <p style={{ fontSize: '0.875rem', color: C.textSecondary }}>
            This section is coming soon. Use the Overview tab for now.
        </p>
    </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────
const DealDetail = () => {
    const { name } = useParams();
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    const query = searchParams.get('q') || '';
    const scopeParam = searchParams.get('scope') || '';
    const intentParam = searchParams.get('intent') || '';   // BUY | SELL
    const subcatIdParam = searchParams.get('subcat_id') || null;
    const variantName = searchParams.get('variant_name') || null;
    const activeTab = searchParams.get('tab') || 'overview';

    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            try {
                const result = await searchService.getSupplierDetails(
                    decodeURIComponent(name), query, scopeParam, subcatIdParam, variantName, intentParam
                );
                setData(result);
            } catch (err) {
                console.error('Failed to fetch details', err);
                const msg = err?.response?.data?.error || 'Could not load details. Please try again.';
                setError(msg);
            } finally {
                setLoading(false);
            }
        };
        if (name) load();
    }, [name, query, scopeParam, subcatIdParam, variantName, intentParam]);

    const navigateTab = (tab) => {
        const params = new URLSearchParams(searchParams);
        params.set('tab', tab);
        navigate(`?${params.toString()}`, { replace: true });
    };

    // ── PDF Generation ──────────────────────────────────────────────────────
    const generateIntelligenceReport = () => {
        if (!data) return;
        const { supplier } = data;
        const isBuyer = data.type === 'BUYER';
        const L = getLabels(isBuyer);
        const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
        const pageW = doc.internal.pageSize.width;
        const pageH = doc.internal.pageSize.height;
        const green = [16, 185, 129], dark = [26, 26, 26], gray = [107, 114, 128], light = [236, 253, 245];
        const today = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        // eslint-disable-next-line no-control-regex
        const clean = v => (v == null ? 'N/A' : String(v).replace(/[^\x00-\x7F]/g, ''));
        const fmtNum = (n, d = 0) => { const f = parseFloat(n); return isNaN(f) ? 'N/A' : f.toFixed(d); };
        const fmtMoney = n => { const f = parseFloat(n); return isNaN(f) ? 'N/A' : `$${f.toFixed(2)}`; };

        const drawHeader = title => {
            doc.setFillColor(...green); doc.rect(0, 0, pageW, 18, 'F');
            doc.setFont('helvetica', 'bold'); doc.setFontSize(11); doc.setTextColor(255, 255, 255);
            doc.text('ZaraiLink Trade Intelligence', 14, 11);
            doc.setFontSize(8); doc.setFont('helvetica', 'normal');
            doc.text('zarailink.com', pageW - 14, 11, { align: 'right' });
            doc.setFontSize(15); doc.setFont('helvetica', 'bold'); doc.setTextColor(...dark);
            doc.text(title, 14, 28);
            doc.setDrawColor(...green); doc.setLineWidth(0.6); doc.line(14, 31, pageW - 14, 31);
        };
        const drawFooter = n => {
            doc.setFontSize(7); doc.setFont('helvetica', 'normal'); doc.setTextColor(...gray);
            doc.text(`ZaraiLink Intelligence Report  •  ${today}  •  Page ${n}`, pageW / 2, pageH - 6, { align: 'center' });
        };

        // Page 1
        drawHeader(`${L.roleLabel} Intelligence Report`); drawFooter(1);
        doc.setFillColor(...light);
        doc.roundedRect(14, 35, pageW - 28, 68, 4, 4, 'F');
        doc.setDrawColor(...green); doc.setLineWidth(0.4);
        doc.roundedRect(14, 35, pageW - 28, 68, 4, 4, 'S');
        doc.setFontSize(18); doc.setFont('helvetica', 'bold'); doc.setTextColor(...dark);
        doc.text(clean(supplier.name), 20, 48);

        const stats = supplier.stats || {};
        const profStats = [
            ['Product / Query', clean(query)],
            ['Total Volume', `${fmtNum(stats.total_volume)} MT`],
            ['Total Shipments', clean(stats.shipment_count)],
            [isBuyer ? 'Avg Purchase Price' : 'Average Price', `${fmtMoney(stats.avg_price)} / MT`],
            ['Last Active', clean(stats.last_shipment_date)],
            ['Active Period', clean(supplier.overview?.active_period)],
        ];
        const colW = (pageW - 28) / 3;
        profStats.forEach(([k, v], i) => {
            const col = i % 3, row = Math.floor(i / 3), x = 20 + col * colW, y = 55 + row * 16;
            doc.setFontSize(7); doc.setFont('helvetica', 'normal'); doc.setTextColor(...gray); doc.text(k.toUpperCase(), x, y);
            doc.setFontSize(9); doc.setFont('helvetica', 'bold'); doc.setTextColor(...dark); doc.text(v, x, y + 5);
        });

        const intel = supplier.intelligence;
        let y1 = 112;
        if (intel) {
            doc.setFontSize(12); doc.setFont('helvetica', 'bold'); doc.setTextColor(...green);
            doc.text('Intelligence Snapshot', 14, y1); y1 += 6;
            doc.setFontSize(8.5); doc.setFont('helvetica', 'normal'); doc.setTextColor(...dark);
            const summary = clean(supplier.name) + ' ' + clean(intel.generated_summary);
            const lines = doc.splitTextToSize(summary, pageW - 28);
            doc.text(lines, 14, y1); y1 += lines.length * 5 + 4;
            autoTable(doc, {
                startY: y1,
                head: [['Metric', 'Value', 'Rating']],
                body: [
                    [isBuyer ? 'Repeat Suppliers' : 'Repeat Buyers', `${clean(intel.repeat_ratio)}%`, clean(intel.repeat_label)],
                    [isBuyer ? 'Supplier Concentration' : 'Buyer Concentration', `${clean(intel.concentration_ratio)}%`, clean(intel.concentration_label)],
                    [isBuyer ? 'Price Sensitivity' : 'Pricing Power', clean(intel.pricing_label), ''],
                    [isBuyer ? 'Procurement Momentum' : 'Market Momentum', clean(intel.momentum_label), ''],
                ],
                theme: 'grid',
                headStyles: { fillColor: green, textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 8 },
                bodyStyles: { fontSize: 8, textColor: dark },
                alternateRowStyles: { fillColor: light },
                margin: { left: 14, right: 14 },
            });
        }

        // Page 2 — Transactions
        doc.addPage(); drawHeader(isBuyer ? 'Recent Orders' : 'Recent Transactions'); drawFooter(2);
        const history = supplier.history || [];
        const txRows = history.slice(0, 20).map(tx => {
            const totalVal = (parseFloat(tx.quantity) || 0) * (parseFloat(tx.price) || 0);
            return [
                clean(tx.date),
                clean(tx.origin_country || tx.destination_country || tx.country || 'N/A'),
                `${fmtNum(tx.quantity)} MT`,
                fmtMoney(tx.price),
                totalVal > 0 ? `$${Math.round(totalVal).toLocaleString()}` : 'N/A',
            ];
        });
        if (txRows.length > 0) {
            autoTable(doc, {
                startY: 36,
                head: [['Date', isBuyer ? 'Origin Country' : 'Dest. Country', 'Quantity (MT)', 'Price ($/MT)', 'Total Value']],
                body: txRows, theme: 'grid',
                headStyles: { fillColor: green, textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 7.5 },
                bodyStyles: { fontSize: 7.5, textColor: dark },
                alternateRowStyles: { fillColor: light },
                margin: { left: 14, right: 14 },
                columnStyles: { 2: { halign: 'right' }, 3: { halign: 'right' }, 4: { halign: 'right' } },
            });
        }

        const safeName = clean(supplier.name).replace(/[^a-z0-9]/gi, '_').substring(0, 30);
        const safeProduct = clean(variantName || query).replace(/[^a-z0-9]/gi, '_').substring(0, 20);
        doc.save(`ZaraiLink_${safeName}_${safeProduct}_${new Date().toISOString().split('T')[0]}.pdf`);
    };

    // ── Guards ──────────────────────────────────────────────────────────────
    if (loading) return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', color: C.textSecondary, fontWeight: 500 }}>
            Loading details...
        </div>
    );
    if (error) return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', flexDirection: 'column', gap: '1rem' }}>
            <span style={{ fontSize: '2rem' }}>⚠️</span>
            <p style={{ color: '#ef4444', fontWeight: 600 }}>{error}</p>
        </div>
    );
    if (!data) return null;

    const { supplier, type } = data;
    const isBuyer = type === 'BUYER';
    const L = getLabels(isBuyer);
    const ov = supplier.overview || {};

    const uniqueRelationships = isBuyer
        ? supplier.supplier_insights?.total_relationships
        : supplier.buyer_insights?.total_relationships;

    // eslint-disable-next-line no-unused-vars
    const isTopEntity = (supplier.stats?.shipment_count >= 15) || (supplier.stats?.total_volume >= 3000);

    const TABS = [
        { key: 'overview', label: 'Overview' },
        { key: 'pricing', label: isBuyer ? 'Procurement & Pricing' : 'Market & Pricing' },
        { key: 'company', label: 'Company' },
        { key: 'transactions', label: isBuyer ? 'Order History' : 'Transactions' },
    ];

    const kpiCards = [
        {
            label: L.volumeCard,
            value: `${(supplier.stats?.total_volume || 0).toLocaleString()} MT`,
        },
        {
            label: L.shipmentsCard,
            value: supplier.stats?.shipment_count || 0,
            sub: ov.active_period ? `Over ${ov.active_period.match(/\((.+?)\)/)?.[1] || 'period'}` : 'Over active period',
        },
        {
            label: L.priceCard,
            value: `$${(supplier.stats?.avg_price || 0).toFixed(0)}/MT`,
        },
        {
            label: L.counterpartyCard,
            value: uniqueRelationships ?? '—',
            sub: (uniqueRelationships >= 5) ? 'Diversified relationships' : 'Concentrated relationships',
        },
    ];

    return (
        <div style={{ background: C.bg, minHeight: '100vh' }}>
            <Navbar />

            {/* ── Page Header ── */}
            <div style={{ background: 'white', borderBottom: `1px solid ${C.border}` }}>
                <div style={{ maxWidth: '1140px', margin: '0 auto', padding: '1rem 2rem 1.5rem' }}>

                    {/* Back button + Breadcrumb row */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.25rem' }}>
                        <button
                            onClick={() => navigate(-1)}
                            style={{
                                display: 'flex', alignItems: 'center', gap: '0.35rem',
                                background: 'transparent', border: `1.5px solid ${C.border}`,
                                borderRadius: '0.375rem', padding: '0.3rem 0.75rem',
                                fontSize: '0.75rem', fontWeight: 700, color: C.textSecondary,
                                cursor: 'pointer', transition: 'all 0.15s', flexShrink: 0,
                            }}
                            onMouseEnter={e => { e.currentTarget.style.borderColor = C.primary; e.currentTarget.style.color = C.primary; }}
                            onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textSecondary; }}
                        >
                            ← Back
                        </button>
                        <nav style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.75rem', color: C.textSecondary, flexWrap: 'wrap' }}>
                            <Link to="/" style={{ color: C.textSecondary, textDecoration: 'none' }}>Home</Link>
                            <span style={{ color: C.border }}>›</span>
                            <Link to="/trade-intelligence" style={{ color: C.textSecondary, textDecoration: 'none' }}>Trade Intelligence</Link>
                            <span style={{ color: C.border }}>›</span>
                            <Link
                                to={`/search/results?q=${encodeURIComponent(query)}${scopeParam ? `&scope=${scopeParam}` : ''}${intentParam ? `&intent=${intentParam}` : ''}${subcatIdParam ? `&subcat_id=${encodeURIComponent(subcatIdParam)}` : ''}${variantName ? `&variant_name=${encodeURIComponent(variantName)}` : ''}`}
                                style={{ color: C.textSecondary, textDecoration: 'none' }}
                            >
                                {L.roleLabel} Deal
                            </Link>
                            <span style={{ color: C.border }}>›</span>
                            <span style={{ color: C.textPrimary, fontWeight: 600 }}>{variantName || query}</span>
                        </nav>
                    </div>

                    {/* Name + Badges + Action row */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                        <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', flexWrap: 'wrap', marginBottom: '0.375rem' }}>
                                <h1 style={{ fontSize: '1.875rem', fontWeight: 900, color: C.textPrimary, margin: 0, letterSpacing: '-0.02em' }}>
                                    {supplier.name}
                                </h1>
                            </div>
                            <p style={{ color: C.textSecondary, fontSize: '0.875rem', fontWeight: 500, margin: 0 }}>
                                {variantName || query} — {ov.active_period || 'N/A'}
                            </p>
                        </div>

                        <button
                            onClick={generateIntelligenceReport}
                            style={{
                                display: 'flex', alignItems: 'center', gap: '0.4rem',
                                background: 'white', border: `1.5px solid ${C.border}`, borderRadius: '0.4rem',
                                padding: '0.5rem 0.875rem', fontSize: '0.8rem', fontWeight: 700,
                                color: C.textSecondary, cursor: 'pointer', whiteSpace: 'nowrap',
                                flexShrink: 0, transition: 'border-color 0.15s, color 0.15s',
                            }}
                            onMouseEnter={e => { e.currentTarget.style.borderColor = C.primary; e.currentTarget.style.color = C.primary; }}
                            onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textSecondary; }}
                        >
                            <Download size={13} /> Download Report
                        </button>
                    </div>
                </div>
            </div>

            <div style={{ maxWidth: '1140px', margin: '0 auto', padding: '2rem' }}>

                {/* ── 4 KPI Cards ── */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.75rem' }}>
                    {kpiCards.map((card, i) => (
                        <div key={i} style={{
                            background: 'white', border: `1px solid ${C.border}`,
                            borderRadius: '0.75rem', padding: '1.125rem 1.25rem',
                        }}>
                            <p style={{ fontSize: '0.7rem', color: C.textSecondary, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', margin: '0 0 0.5rem' }}>
                                {card.label}
                            </p>
                            <p style={{ fontSize: '1.625rem', fontWeight: 900, color: C.textPrimary, margin: '0 0 0.2rem', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
                                {card.value}
                            </p>
                            {card.sub && (
                                <p style={{ fontSize: '0.725rem', color: card.pos ? C.primary : C.textTertiary, fontWeight: 500, margin: 0 }}>
                                    {card.sub}
                                </p>
                            )}
                        </div>
                    ))}
                </div>

                {/* ── Tab Navigation ── Premium Style */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginBottom: '1.75rem', background: '#f8fafc', borderRadius: '0.625rem', padding: '0.3rem', border: `1px solid ${C.border}` }}>
                    {TABS.map(tab => (
                        <button
                            key={tab.key}
                            onClick={() => navigateTab(tab.key)}
                            style={{
                                background: activeTab === tab.key ? C.gradientGreen : 'transparent',
                                border: 'none',
                                borderRadius: '0.45rem',
                                padding: '0.5rem 1.125rem',
                                fontSize: '0.8125rem',
                                fontWeight: activeTab === tab.key ? 700 : 500,
                                color: activeTab === tab.key ? 'white' : C.textSecondary,
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                                boxShadow: activeTab === tab.key ? '0 2px 8px rgba(16,185,129,0.35)' : 'none',
                                letterSpacing: activeTab === tab.key ? '0' : '0',
                            }}
                            onMouseEnter={e => { if (activeTab !== tab.key) e.currentTarget.style.background = '#edf2f7'; }}
                            onMouseLeave={e => { if (activeTab !== tab.key) e.currentTarget.style.background = 'transparent'; }}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* ── Tab Content ── */}
                {activeTab === 'overview' && (
                    <OverviewTab supplier={supplier} isBuyer={isBuyer} navigateTab={navigateTab} />
                )}
                {activeTab === 'pricing' && (
                    <MarketPricingTab supplier={supplier} isBuyer={isBuyer} query={query} variantName={variantName} />
                )}
                {activeTab === 'company' && <CompanyTab supplier={supplier} isBuyer={isBuyer} />}
                {activeTab === 'transactions' && <TransactionsTab supplier={supplier} isBuyer={isBuyer} query={query} variantName={variantName} />}

            </div>
        </div>
    );
};

export default DealDetail;
