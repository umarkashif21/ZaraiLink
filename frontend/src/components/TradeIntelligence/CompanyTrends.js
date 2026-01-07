import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { LineChart, Line, ComposedChart, Area, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Navbar from '../Layout/Navbar';
import ExportButton from '../Common/ExportButton';
import './TradeIntelligence.css';

const CompanyTrends = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const loc = useLocation();
  const [trds, setTrds] = useState(null);
  const [load, setLoad] = useState(true);
  const [error, setError] = useState(null);

  
  const companyName = decodeURIComponent(id);
  const tab = loc.pathname.split('/').pop();

  useEffect(() => {
    loadTrds();
  }, [id]);

  const loadTrds = async () => {
    setLoad(true);
    setError(null);
    try {
      
      const res = await fetch(`http://localhost:8000/api/company/${id}/trends/?_t=${new Date().getTime()}`, {
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        setTrds(data);
      } else {
        setError('Could not load trends');
      }
    } catch (err) {
      console.error('Failed to load trends:', err);
      setError('Failed to load trends data');
    } finally {
      setLoad(false);
    }
  };

  const navTab = (t) => {
    navigate(`/trade-intelligence/company/${id}/${t}`);
  };

  const fmtCurr = (v) => {
    if (!v) return '';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(v);
  };

  
  const volumePriceTrend = trds?.volume_price_trend || [];
  const quarterlyVolume = trds?.quarterly_volume || [];

  if (load) {
    return (
      <>
        <Navbar />
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading trends...</p>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="company-detail-container">
        <div className="company-detail-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h1>{companyName}</h1>
              <p>Trade Intelligence Profile</p>
            </div>
            {volumePriceTrend && volumePriceTrend.length > 0 && (
              <ExportButton
                data={volumePriceTrend.map(t => ({
                  period: `${t.month_name} ${t.year}`,
                  product: t.product_name || 'All Products',
                  volume: t.volume,
                  avg_price: t.avg_price,
                  yoy_volume_growth: t.yoy_volume_growth,
                  yoy_price_growth: t.yoy_price_growth,
                }))}
                columns={[
                  { key: 'period', label: 'Period' },
                  { key: 'product', label: 'Product' },
                  { key: 'volume', label: 'Volume (MT)' },
                  { key: 'avg_price', label: 'Avg Price (USD)' },
                  { key: 'yoy_volume_growth', label: 'YoY Volume Growth %' },
                  { key: 'yoy_price_growth', label: 'YoY Price Growth %' },
                ]}
                filename={`trends-${companyName}`}
                title={`${companyName} - Trade Trends`}
              />
            )}
          </div>
        </div>

        <div className="tab-navigation">
          <button
            className={`tab-button ${tab === 'overview' ? 'active' : ''}`}
            onClick={() => navTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab-button ${tab === 'products' ? 'active' : ''}`}
            onClick={() => navTab('products')}
          >
            Products
          </button>
          <button
            className={`tab-button ${tab === 'partners' ? 'active' : ''}`}
            onClick={() => navTab('partners')}
          >
            Partners
          </button>
          <button
            className={`tab-button ${tab === 'trends' ? 'active' : ''}`}
            onClick={() => navTab('trends')}
          >
            Trends
          </button>
        </div>

        <div className="tab-content">
          <h2>Trade Trends & Analytics</h2>

          {error ? (
            <div className="empty-state">
              <p>{error}</p>
            </div>
          ) : !volumePriceTrend || volumePriceTrend.length === 0 ? (
            <div className="empty-state">
              <p>No trend data available</p>
            </div>
          ) : (
            <>
              <div style={{ marginTop: '2rem' }}>
                <h3>Monthly Volume vs Avg Price (Recent Data)</h3>
                <table className="products-table" style={{ marginTop: '1rem' }}>
                  <thead>
                    <tr>
                      <th>Period</th>
                      <th>Volume (MT)</th>
                      <th>Avg Price</th>
                      <th>YoY Volume Growth</th>
                      <th>YoY Price Growth</th>
                    </tr>
                  </thead>
                  <tbody>
                    {volumePriceTrend.map((t, idx) => (
                      <tr key={idx}>
                        <td>
                          <strong>
                            {new Date(t.month).toLocaleString('en-US', { month: 'long', year: 'numeric' })}
                          </strong>
                        </td>
                        <td>{t.volume > 0 ? `${new Intl.NumberFormat('en-US').format(t.volume)} MT` : '-'}</td>
                        <td>{t.avg_price > 0 ? fmtCurr(t.avg_price) : '-'}</td>
                        <td>
                          {t.yoy_volume_growth !== null && !isNaN(parseFloat(t.yoy_volume_growth)) ? (
                            <span className={`growth-badge ${parseFloat(t.yoy_volume_growth) >= 0 ? 'positive' : 'negative'}`}>
                              {parseFloat(t.yoy_volume_growth) >= 0 ? '+' : ''}
                              {parseFloat(t.yoy_volume_growth).toFixed(2)}%
                            </span>
                          ) : '-'}
                        </td>
                        <td>
                          {t.yoy_price_growth !== null && !isNaN(parseFloat(t.yoy_price_growth)) ? (
                            <span className={`growth-badge ${parseFloat(t.yoy_price_growth) >= 0 ? 'positive' : 'negative'}`}>
                              {parseFloat(t.yoy_price_growth) >= 0 ? '+' : ''}
                              {parseFloat(t.yoy_price_growth).toFixed(2)}%
                            </span>
                          ) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {}
              {quarterlyVolume.filter(q => q.yoy_growth !== null && q.yoy_growth !== undefined && !isNaN(parseFloat(q.yoy_growth))).length > 0 && (
                <div style={{ marginTop: '2rem' }}>
                  <h3>YoY Volume Growth By Quarter</h3>
                  <div className="info-cards-grid" style={{ marginTop: '1rem' }}>
                    {quarterlyVolume.filter(q => q.yoy_growth !== null && q.yoy_growth !== undefined && !isNaN(parseFloat(q.yoy_growth))).map((q, idx) => (
                      <div key={idx} className="info-card">
                        <h4>{q.year}-Q{q.quarter}</h4>
                        <div className="info-card-value" style={{
                          color: parseFloat(q.yoy_growth) >= 0 ? '#22c55e' : '#ef4444'
                        }}>
                          {`${parseFloat(q.yoy_growth) >= 0 ? '+' : ''}${parseFloat(q.yoy_growth).toFixed(2)}%`}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {}
              {volumePriceTrend.filter(t => t.month && (parseFloat(t.volume) > 0 || parseFloat(t.avg_price) > 0)).length > 0 && (
                <div style={{ marginTop: '2rem' }}>
                  <h3>Volume & Price Trend Over Time</h3>
                  <div style={{ width: '100%', height: 350, marginTop: '1rem' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart
                        data={volumePriceTrend.filter(t => t.month && (parseFloat(t.volume) > 0 || parseFloat(t.avg_price) > 0)).map(t => {
                          const date = new Date(t.month);
                          const monthName = date.toLocaleString('en-US', { month: 'short' });
                          const year = date.getFullYear();
                          return {
                            name: `${monthName} ${year}`,
                            volume: parseFloat(t.volume) || 0,
                            price: parseFloat(t.avg_price) || 0,
                          };
                        })}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                        <YAxis 
                          yAxisId="left" 
                          tickFormatter={(v) => {
                            const num = parseFloat(v);
                            if (isNaN(num)) return '0';
                            if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
                            return num.toFixed(0);
                          }}
                          label={{ value: 'Volume (MT)', angle: -90, position: 'insideLeft', style: { fontSize: 11 } }}
                        />
                        <YAxis 
                          yAxisId="right" 
                          orientation="right" 
                          tickFormatter={(v) => {
                            const num = parseFloat(v);
                            if (isNaN(num)) return '$0';
                            return `$${num.toFixed(0)}`;
                          }}
                          label={{ value: 'Price (USD)', angle: 90, position: 'insideRight', style: { fontSize: 11 } }}
                        />
                        <Tooltip 
                          formatter={(value, name) => [
                            name === 'volume' 
                              ? `${new Intl.NumberFormat('en-US').format(value)} MT`
                              : `$${new Intl.NumberFormat('en-US').format(value)}`,
                            name === 'volume' ? 'Volume' : 'Avg Price'
                          ]}
                        />
                        <Legend />
                        <Bar 
                          yAxisId="left" 
                          dataKey="volume" 
                          fill="#10b981" 
                          name="Volume (MT)" 
                          radius={[4, 4, 0, 0]}
                          opacity={0.8}
                        />
                        <Line 
                          yAxisId="right" 
                          type="monotone" 
                          dataKey="price" 
                          stroke="#ef4444" 
                          name="Avg Price (USD)" 
                          strokeWidth={2}
                          dot={{ r: 3 }}
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
              
              {}
              {quarterlyVolume.filter(q => q.quarter && parseFloat(q.vol) > 0).length > 0 && (
                <div style={{ marginTop: '2rem' }}>
                  <h3>Quarterly Volume Trend</h3>
                  <div style={{ width: '100%', height: 300, marginTop: '1rem' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={quarterlyVolume.filter(q => q.quarter && parseFloat(q.vol) > 0).map(q => {
                          const date = new Date(q.quarter);
                          const year = date.getFullYear();
                          const quarter = Math.floor(date.getMonth() / 3) + 1;
                          return {
                            name: `Q${quarter} ${year}`,
                            volume: parseFloat(q.vol) || 0,
                          };
                        })}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                        <YAxis 
                          tickFormatter={(v) => {
                            const num = parseFloat(v);
                            if (isNaN(num)) return '0 MT';
                            if (num >= 1000) return `${(num / 1000).toFixed(0)}K MT`;
                            return `${num.toFixed(0)} MT`;
                          }}
                          label={{ value: 'Volume (MT)', angle: -90, position: 'insideLeft', style: { fontSize: 11 } }}
                        />
                        <Tooltip 
                          formatter={(value) => [`${new Intl.NumberFormat('en-US').format(value)} MT`, 'Quarterly Volume']}
                        />
                        <Legend />
                        <Line 
                          type="monotone" 
                          dataKey="volume" 
                          stroke="#3b82f6" 
                          name="Quarterly Volume (MT)" 
                          strokeWidth={2}
                          dot={{ r: 4 }}
                          activeDot={{ r: 6 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default CompanyTrends;

