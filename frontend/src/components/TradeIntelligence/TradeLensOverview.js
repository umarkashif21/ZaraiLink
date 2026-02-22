import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Line } from 'react-chartjs-2';
import Navbar from '../Layout/Navbar';
import Breadcrumb from '../Common/Breadcrumb';

import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const TradeLensOverview = () => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState({ summary: {}, price_trend: [], supply_chain_flow: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [dateRange, setDateRange] = useState('');
  const [tradeType, setTradeType] = useState('BOTH');

  const loadOverviewData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (tradeType !== 'BOTH') params.append('trade_type', tradeType);

      const response = await fetch(
        `http://localhost:8000/api/trade-lens/products/${productId}/overview/?${params.toString()}`,
        { credentials: 'include' }
      );
      if (!response.ok) throw new Error('Failed to load overview data');
      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [productId, tradeType]);

  useEffect(() => {
    loadOverviewData();
  }, [loadOverviewData]);

  const fmtCurrency = (value) => {
    if (value === undefined || value === null) return '-';
    if (value >= 1000000000) return `$${(value / 1000000000).toFixed(1)}B`;
    if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
    return `$${value.toFixed(0)}`;
  };

  const fmtN = (value) => {
    if (value === undefined || value === null) return '-';
    return new Intl.NumberFormat('en-US').format(Math.round(value));
  };

  const tabs = [
    { id: 'overview', label: 'Overview', path: 'overview' },
    { id: 'comparison', label: 'Comparison', path: 'comparison' },
    { id: 'details', label: 'Details', path: 'details' },
  ];

  const s = data.summary || {};
  const totalQty = s.total_quantity || 0;
  const expQty = s.export_quantity || 0;
  const impQty = s.import_quantity || 0;

  const expPct = totalQty > 0 ? Math.round((expQty / totalQty) * 100) : 0;
  const impPct = totalQty > 0 ? Math.round((impQty / totalQty) * 100) : 0;

  const priceTrendData = {
    labels: data.price_trend?.map(d => d.month) || [],
    datasets: [
      {
        label: 'USD/MT',
        data: data.price_trend?.map(d => d.avg_price) || [],
        borderColor: '#64748b',
        backgroundColor: '#64748b',
        tension: 0.2,
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: '#111827'
      }
    ]
  };

  const lineOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0f172a', cornerRadius: 8, padding: 10,
        titleFont: { family: "'DM Sans', sans-serif", size: 13, weight: '600' },
        bodyFont: { family: "'DM Sans', sans-serif", size: 12 },
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#94a3b8', font: { family: "'DM Sans', sans-serif", size: 11, weight: '500' } }
      },
      y: {
        grid: { color: '#f1f5f9' },
        ticks: { color: '#94a3b8', font: { family: "'DM Sans', sans-serif", size: 11, weight: '500' } }
      }
    }
  };

  return (
    <>
      <Navbar />
      <div style={{ background: '#ffffff', minHeight: '100vh', paddingBottom: '4rem', fontFamily: "'DM Sans', 'Inter', sans-serif" }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 2rem' }}>

          {/* Header */}
          <div style={{ padding: '2rem 0', borderBottom: '1px solid #e2e8f0', marginBottom: '2rem' }}>
            <Breadcrumb />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginTop: '1rem' }}>
              <div>
                <h1 style={{ margin: 0, fontSize: '2.25rem', fontWeight: 700, color: '#111827', letterSpacing: '-0.02em' }}>
                  {data.product?.name || 'Loading...'}
                </h1>
                <p style={{ margin: '0.5rem 0 0', color: '#64748b', fontSize: '0.95rem' }}>
                  HS Code: {data.product?.hs_code || '---'} | Category: {data.product?.category || '---'}
                </p>
                <p style={{ margin: '0.2rem 0 0', color: '#64748b', fontSize: '0.95rem' }}>
                  Transaction Period: All Time
                </p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                <div style={{ display: 'flex', gap: '0.5rem', background: '#f1f5f9', padding: '0.25rem', borderRadius: '8px' }}>
                  <button style={{ padding: '0.5rem 1rem', background: '#111827', color: 'white', border: 'none', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer' }}>USD</button>
                  <button style={{ padding: '0.5rem 1rem', background: 'transparent', color: '#64748b', border: 'none', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer' }}>PKR</button>
                </div>
              </div>
            </div>

            <div style={{ display: 'inline-flex', background: '#f1f5f9', padding: '4px', borderRadius: '10px', marginTop: '2rem', gap: '4px', border: '1px solid #e2e8f0' }}>
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => navigate(`/trade-intelligence/lens/${productId}/${tab.path}`)}
                  style={{
                    background: tab.id === 'overview' ? 'white' : 'transparent',
                    border: 'none',
                    padding: '0.6rem 1.25rem',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    fontWeight: tab.id === 'overview' ? 600 : 500,
                    color: tab.id === 'overview' ? '#111827' : '#64748b',
                    borderRadius: '8px',
                    boxShadow: tab.id === 'overview' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                    transition: 'all 0.2s ease-in-out',
                    WebkitUserSelect: 'none'
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* Filters Row */}
            <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1.25rem', display: 'flex', gap: '2rem', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#111827' }}>Trade Type:</span>
                <select
                  value={tradeType}
                  onChange={(e) => setTradeType(e.target.value)}
                  style={{ padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid #cbd5e1', outline: 'none', background: '#f8fafc', fontSize: '0.9rem', minWidth: '150px' }}
                >
                  <option value="BOTH">Both</option>
                  <option value="IMPORT">Import</option>
                  <option value="EXPORT">Export</option>
                </select>
              </div>
            </div>

            {loading ? (
              <div style={{ padding: '4rem', textAlign: 'center', color: '#64748b', background: 'white', borderRadius: '12px', border: '1px solid #e2e8f0' }}>Loading Data...</div>
            ) : error ? (
              <div style={{ padding: '4rem', textAlign: 'center', color: '#ef4444', background: 'white', borderRadius: '12px', border: '1px solid #e2e8f0' }}>{error}</div>
            ) : (
              <>
                {/* 5-Column Summary Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1.25rem' }}>
                  <div style={{ background: 'white', padding: '1.5rem', borderRadius: '16px', border: '1px solid rgba(226, 232, 240, 0.6)', boxShadow: '0 12px 32px -4px rgba(0,0,0,0.04), 0 4px 12px -2px rgba(0,0,0,0.02)', transition: 'transform 0.2s ease, box-shadow 0.2s ease', cursor: 'default' }} onMouseOver={e => e.currentTarget.style.transform = 'translateY(-2px)'} onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}>
                    <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>Total Quantity</p>
                    <h2 style={{ margin: 0, fontSize: '2rem', fontWeight: 700, color: '#0f172a', textAlign: 'right', fontFeatureSettings: '"tnum"', letterSpacing: '-0.02em', lineHeight: 1.1 }}>{fmtN(s.total_quantity)}</h2>
                    <p style={{ margin: '0.25rem 0 0', fontSize: '0.75rem', color: '#94a3b8', textAlign: 'right', fontWeight: 500 }}>MT</p>
                  </div>
                  <div style={{ background: 'white', padding: '1.5rem', borderRadius: '16px', border: '1px solid rgba(226, 232, 240, 0.6)', boxShadow: '0 12px 32px -4px rgba(0,0,0,0.04), 0 4px 12px -2px rgba(0,0,0,0.02)', transition: 'transform 0.2s ease, box-shadow 0.2s ease', cursor: 'default' }} onMouseOver={e => e.currentTarget.style.transform = 'translateY(-2px)'} onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}>
                    <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>Total Trade Value</p>
                    <h2 style={{ margin: 0, fontSize: '2rem', fontWeight: 700, color: '#0f172a', textAlign: 'right', fontFeatureSettings: '"tnum"', letterSpacing: '-0.02em', lineHeight: 1.1 }}>{fmtCurrency(s.total_trade_value_usd)}</h2>
                  </div>
                  <div style={{ background: 'white', padding: '1.5rem', borderRadius: '16px', border: '1px solid rgba(226, 232, 240, 0.6)', boxShadow: '0 12px 32px -4px rgba(0,0,0,0.04), 0 4px 12px -2px rgba(0,0,0,0.02)', transition: 'transform 0.2s ease, box-shadow 0.2s ease', cursor: 'default' }} onMouseOver={e => e.currentTarget.style.transform = 'translateY(-2px)'} onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}>
                    <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>Weighted Avg Price</p>
                    <h2 style={{ margin: 0, fontSize: '2rem', fontWeight: 700, color: '#0f172a', textAlign: 'right', fontFeatureSettings: '"tnum"', letterSpacing: '-0.02em', lineHeight: 1.1 }}>${fmtN(s.weighted_avg_price)}</h2>
                    <p style={{ margin: '0.25rem 0 0', fontSize: '0.75rem', color: '#94a3b8', textAlign: 'right', fontWeight: 500 }}>per MT</p>
                  </div>
                  <div style={{ background: 'white', padding: '1.5rem', borderRadius: '16px', border: '1px solid rgba(226, 232, 240, 0.6)', boxShadow: '0 12px 32px -4px rgba(0,0,0,0.04), 0 4px 12px -2px rgba(0,0,0,0.02)', transition: 'transform 0.2s ease, box-shadow 0.2s ease', cursor: 'default' }} onMouseOver={e => e.currentTarget.style.transform = 'translateY(-2px)'} onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}>
                    <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>Total Transactions</p>
                    <h2 style={{ margin: 0, fontSize: '2rem', fontWeight: 700, color: '#0f172a', textAlign: 'right', fontFeatureSettings: '"tnum"', letterSpacing: '-0.02em', lineHeight: 1.1 }}>{fmtN(s.total_transactions)}</h2>
                  </div>
                  <div style={{ background: 'white', padding: '1.5rem', borderRadius: '16px', border: '1px solid rgba(226, 232, 240, 0.6)', boxShadow: '0 12px 32px -4px rgba(0,0,0,0.04), 0 4px 12px -2px rgba(0,0,0,0.02)', display: 'flex', flexDirection: 'column', justifyContent: 'center', transition: 'transform 0.2s ease, box-shadow 0.2s ease', cursor: 'default' }} onMouseOver={e => e.currentTarget.style.transform = 'translateY(-2px)'} onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}>
                    <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>Import vs Export</p>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', color: '#0f172a', fontFeatureSettings: '"tnum"' }}>
                      <span><span style={{ color: '#10b981', marginRight: 6 }}>●</span>Export:</span><span style={{ fontWeight: 600 }}>{expPct}%</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', color: '#0f172a', fontFeatureSettings: '"tnum"', marginTop: '0.3rem' }}>
                      <span><span style={{ color: '#3b82f6', marginRight: 6 }}>●</span>Import:</span><span style={{ fontWeight: 600 }}>{impPct}%</span>
                    </div>
                  </div>
                </div>

                {/* Middle Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: '1.25rem' }}>
                  {/* Price Trend Line */}
                  <div style={{ background: 'white', border: '1px solid rgba(226, 232, 240, 0.6)', borderRadius: '16px', padding: '1.5rem', boxShadow: '0 12px 32px -4px rgba(0,0,0,0.04), 0 4px 12px -2px rgba(0,0,0,0.02)' }}>
                    <h3 style={{ margin: '0 0 1.5rem 0', fontSize: '1.15rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.02em' }}>Price Trend Over Time</h3>
                    <div style={{ height: '300px' }}>
                      <Line data={{
                        ...priceTrendData,
                        datasets: [
                          {
                            ...priceTrendData.datasets[0],
                            borderColor: '#8b5cf6',
                            backgroundColor: 'rgba(139, 92, 246, 0.1)',
                            pointBackgroundColor: '#8b5cf6',
                            fill: true,
                          }
                        ]
                      }} options={lineOptions} />
                    </div>
                  </div>

                  {/* Export vs Import Visual Breakdown */}
                  <div style={{ background: 'white', border: '1px solid rgba(226, 232, 240, 0.6)', borderRadius: '16px', padding: '1.5rem', boxShadow: '0 12px 32px -4px rgba(0,0,0,0.04), 0 4px 12px -2px rgba(0,0,0,0.02)' }}>
                    <h3 style={{ margin: '0 0 2.5rem 0', fontSize: '1.15rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.02em' }}>Export vs Import Volumes</h3>

                    {/* Export Bar */}
                    <div style={{ marginBottom: '2.5rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                        <span style={{ fontWeight: 600, color: '#111827', display: 'flex', alignItems: 'center', gap: 6 }}><span style={{ color: '#10b981' }}>●</span> Export</span>
                        <span style={{ fontWeight: 700, fontSize: '1.2rem', color: '#111827' }}>{expPct}%</span>
                      </div>
                      <div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden', display: 'flex' }}>
                        <div style={{ width: `${expPct}%`, background: '#10b981', height: '100%', borderRadius: 4, transition: 'width 0.5s ease' }}></div>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem', fontSize: '0.85rem', color: '#64748b' }}>
                        <span>Quantity:</span>
                        <span style={{ fontFeatureSettings: '"tnum"', color: '#111827', fontWeight: 500 }}>{fmtN(expQty)} MT</span>
                      </div>
                    </div>

                    {/* Import Bar */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                        <span style={{ fontWeight: 600, color: '#111827', display: 'flex', alignItems: 'center', gap: 6 }}><span style={{ color: '#3b82f6' }}>●</span> Import</span>
                        <span style={{ fontWeight: 700, fontSize: '1.2rem', color: '#111827' }}>{impPct}%</span>
                      </div>
                      <div style={{ height: '20px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden', display: 'flex' }}>
                        <div style={{ width: `${impPct}%`, background: '#3b82f6', height: '100%', borderRadius: 4, transition: 'width 0.5s ease' }}></div>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem', fontSize: '0.85rem', color: '#64748b' }}>
                        <span>Quantity:</span>
                        <span style={{ fontFeatureSettings: '"tnum"', color: '#111827', fontWeight: 500 }}>{fmtN(impQty)} MT</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Bottom Route Table */}
                <div style={{ background: 'white', border: '1px solid rgba(226, 232, 240, 0.6)', borderRadius: '16px', overflow: 'hidden', boxShadow: '0 12px 32px -4px rgba(0,0,0,0.04), 0 4px 12px -2px rgba(0,0,0,0.02)' }}>
                  <div style={{ padding: '1.5rem', borderBottom: '1px solid #e2e8f0' }}>
                    <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.02em' }}>Supply Chain Flow (Top Routes)</h3>
                  </div>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                      <tr>
                        <th style={{ padding: '1rem 1.5rem', fontSize: '0.85rem', fontWeight: 600, color: '#111827' }}>Source Country</th>
                        <th style={{ padding: '1rem 1.5rem', fontSize: '0.85rem', fontWeight: 600, color: '#64748b', width: '40px' }}>&rarr;</th>
                        <th style={{ padding: '1rem 1.5rem', fontSize: '0.85rem', fontWeight: 600, color: '#111827' }}>Target Country</th>
                        <th style={{ padding: '1rem 1.5rem', fontSize: '0.85rem', fontWeight: 600, color: '#111827', textAlign: 'right' }}>Trade Volume</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.supply_chain_flow?.map((row, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '1rem 1.5rem', fontSize: '0.95rem', color: '#475569' }}>{row.source}</td>
                          <td style={{ padding: '1rem 1.5rem', fontSize: '1rem', color: '#94a3b8' }}>&rarr;</td>
                          <td style={{ padding: '1rem 1.5rem', fontSize: '0.95rem', color: '#475569' }}>{row.target}</td>
                          <td style={{ padding: '1rem 1.5rem', fontSize: '0.95rem', color: '#111827', fontWeight: 500, textAlign: 'right', fontFeatureSettings: '"tnum"' }}>{fmtN(row.value)} MT</td>
                        </tr>
                      ))}
                      {(!data.supply_chain_flow || data.supply_chain_flow.length === 0) && (
                        <tr>
                          <td colSpan="4" style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>No routing data found for selected filters.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                  <div style={{ padding: '1rem', textAlign: 'center', fontSize: '0.85rem', color: '#94a3b8', borderTop: '1px solid #e2e8f0' }}>
                    Showing top {data.supply_chain_flow?.length || 0} trade routes by volume
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default TradeLensOverview;
