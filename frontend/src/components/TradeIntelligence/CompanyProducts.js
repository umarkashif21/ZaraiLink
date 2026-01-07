import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import Navbar from '../Layout/Navbar';
import ExportButton from '../Common/ExportButton';
import './TradeIntelligence.css';

const CompanyProducts = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const loc = useLocation();
  const query = new URLSearchParams(loc.search);
  const [direction, setDirection] = useState(query.get('direction') || 'import');
  const dateFrom = query.get('date_from') || '';
  const dateTo = query.get('date_to') || '';
  const [prods, setProds] = useState(null);
  const [load, setLoad] = useState(true);
  const [error, setError] = useState(null);

  
  const companyName = decodeURIComponent(id);
  const tab = loc.pathname.split('/').pop();

  useEffect(() => {
    loadProds();
  }, [id, direction, dateFrom, dateTo]);

  const loadProds = async () => {
    setLoad(true);
    setError(null);
    try {
      
      
      const res = await fetch(`http://localhost:8000/api/company/${id}/products/?direction=${direction}&date_from=${dateFrom}&date_to=${dateTo}&_t=${new Date().getTime()}`, {
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        
        if (data.product_performance) {
            data.product_performance = data.product_performance.map(p => ({
                ...p,
                volume: parseFloat(p.volume || p.total_volume || p.vol || 0)
            }));
        }
        setProds(data);
      } else {
        setError('Could not load products');
      }
    } catch (err) {
      console.error('Failed to load products:', err);
      setError('Failed to load products data');
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
      currency: v.currency || 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(v);
  };

  const fmtPct = (v) => {
    if (v === null || v === undefined) return '';
    return `${v >= 0 ? '+' : ''}${parseFloat(v).toFixed(2)}%`;
  };

  if (load) {
    return (
      <>
        <Navbar />
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading products...</p>
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
            {prods?.product_performance && prods.product_performance.length > 0 && (
              <ExportButton
                data={prods.product_performance.map(p => ({
                  product_name: p.product_name,
                  hs_code: p.hs_code || '',
                  category: p.category_name || '',
                  avg_price: p.avg_price,
                  volume: p.volume,
                  unit: p.unit,
                  yoy_growth: p.yoy_growth,
                }))}
                columns={[
                  { key: 'product_name', label: 'Product Name' },
                  { key: 'hs_code', label: 'HS Code' },
                  { key: 'category', label: 'Category' },
                  { key: 'avg_price', label: 'Avg Price (USD)' },
                  { key: 'volume', label: 'Volume' },
                  { key: 'unit', label: 'Unit' },
                  { key: 'yoy_growth', label: 'YoY Growth %' },
                ]}
                filename={`products-${companyName}`}
                title={`${companyName} - Products`}
              />
            )}
          </div>
          
          <div className="filters-bar" style={{ marginTop: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
             <div className="filter-group">
                <label style={{ marginRight: '0.5rem', fontWeight: 500 }}>Direction:</label>
                <select 
                  value={direction} 
                  onChange={(e) => setDirection(e.target.value)}
                  style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #cbd5e0' }}
                >
                  <option value="import">Import (As Buyer)</option>
                  <option value="export">Export (As Seller)</option>
                </select>
             </div>
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
          <h2>Product Performance</h2>

          {error ? (
            <div className="empty-state">
              <p>{error}</p>
            </div>
          ) : !prods || !prods.product_performance || prods.product_performance.length === 0 ? (
            <div className="empty-state">
              <p>No products found</p>
            </div>
          ) : (
            <table className="products-table">
              <thead>
                <tr>
                  <th>Product Name</th>
                  <th>Category</th>
                  <th>Avg Price</th>
                  <th>{direction === 'import' ? 'Import Volume (MT)' : 'Export Volume (MT)'}</th>
                  <th>YoY Growth</th>
                </tr>
              </thead>
              <tbody>
                {prods.product_performance.map((p, idx) => (
                  <tr key={idx}>
                    <td>
                      <strong>{p.product_name}</strong>
                      {p.hs_code && (
                        <div style={{ fontSize: '0.85rem', color: '#718096' }}>
                          HS Code: {p.hs_code}
                        </div>
                      )}
                    </td>
                    <td>{p.subcat || p.category_name || '-'}</td>
                    <td>
                      {p.avg_price > 0 && !isNaN(p.avg_price) ? (
                        new Intl.NumberFormat('en-US', {
                          style: 'currency',
                          currency: p.currency || 'USD'
                        }).format(p.avg_price)
                      ) : '-'}
                    </td>
                    <td>
                      {p.volume > 0 && !isNaN(p.volume) ? (
                        `${new Intl.NumberFormat('en-US').format(p.volume)} ${p.unit || ''}`
                      ) : '-'}
                    </td>
                    <td>
                      {p.yoy_growth !== null && p.yoy_growth !== undefined && !isNaN(parseFloat(p.yoy_growth)) ? (
                        <span className={`growth-badge ${parseFloat(p.yoy_growth) >= 0 ? 'positive' : 'negative'}`}>
                          {parseFloat(p.yoy_growth) >= 0 ? '+' : ''}{parseFloat(p.yoy_growth).toFixed(2)}%
                        </span>
                      ) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {}
          {prods && prods.avg_price_trend && (
            <div style={{ marginTop: '2rem' }}>
              <h3>Avg Price Trend (Monthly)</h3>
              <p style={{ color: '#718096', fontSize: '0.9rem' }}>Trend for top product</p>
              {prods.avg_price_trend.length > 0 ? (
                <div style={{ width: '100%', height: 300, marginTop: '1rem' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={prods.avg_price_trend.map(t => ({
                      ...t,
                      month: new Date(t.month).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
                    }))} margin={{ top: 20, right: 30, left: 20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                      <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                      <YAxis 
                        tickFormatter={(v) => `$${v}`}
                        domain={['auto', 'auto']}
                      />
                      <Tooltip formatter={(v) => `$${new Intl.NumberFormat('en-US').format(v)}`} />
                      <Line type="monotone" dataKey="avg_price" stroke="#8884d8" strokeWidth={2} name="Avg Price (USD/MT)" dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="empty-state" style={{ marginTop: '1rem', padding: '2rem' }}>
                  <p>No price trend data available for the top product.</p>
                </div>
              )}
            </div>
          )}

          {prods && prods.product_performance && prods.product_performance.filter(p => p.volume > 0).length > 0 && (
            <div style={{ marginTop: '2rem' }}>
              <h3>Product Volume Distribution</h3>
              <div style={{ width: '100%', height: 350, marginTop: '1rem' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={prods.product_performance.filter(p => p.volume > 0).slice(0, 8).map(p => ({
                      name: p.product_name?.substring(0, 20) + (p.product_name?.length > 20 ? '...' : ''),
                      volume: parseFloat(p.volume) || 0,
                      value: (parseFloat(p.avg_price) || 0) * (parseFloat(p.volume) || 0),
                    }))}
                    margin={{ top: 40, right: 30, left: 20, bottom: 60 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45} 
                      textAnchor="end" 
                      interval={0}
                      tick={{ fontSize: 11 }}
                      height={80}
                    />
                    <YAxis
                      tickFormatter={(v) => {
                        const num = parseFloat(v);
                        if (isNaN(num)) return '0';
                        if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
                        return num.toFixed(0);
                      }}
                      label={{ value: 'Volume (MT)', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
                    />
                    <Tooltip 
                      formatter={(value, name) => [
                        name === 'volume' 
                          ? `${new Intl.NumberFormat('en-US').format(value)} MT`
                          : `$${new Intl.NumberFormat('en-US').format(value)}`,
                        name === 'volume' ? 'Volume' : 'Value'
                      ]}
                    />
                    <Legend />
                    <Bar dataKey="volume" fill="#10b981" name="Volume (MT)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
          
          {}
          {prods && prods.volume_share && prods.volume_share.filter(item => (parseFloat(item.volume) || parseFloat(item.share) || 0) > 0).length > 0 && (
            <div style={{ marginTop: '4rem' }}>
              <h3>Volume by Category</h3>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                {}
                <div style={{ width: '100%', height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                      <Pie
                        data={prods.volume_share.filter(item => (parseFloat(item.volume) || parseFloat(item.share) || 0) > 0).slice(0, 8).map((item) => ({
                          name: item.category || item.product_name || 'Unknown',
                          value: parseFloat(item.volume) || parseFloat(item.share) || 0,
                        }))}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
                          const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
                          const x = cx + radius * Math.cos(-midAngle * Math.PI / 180);
                          const y = cy + radius * Math.sin(-midAngle * Math.PI / 180);
                          return percent > 0.05 ? (
                            <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={11}>
                              {(percent * 100).toFixed(0)}%
                            </text>
                          ) : null;
                        }}
                        outerRadius={120}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {prods.volume_share.filter(item => (parseFloat(item.volume) || parseFloat(item.share) || 0) > 0).slice(0, 8).map((_, index) => (
                          <Cell key={`cell-${index}`} fill={['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#6366f1', '#14b8a6'][index % 8]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => `${new Intl.NumberFormat('en-US').format(value)} MT`} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {}
                <div style={{ 
                  display: 'flex', 
                  flexWrap: 'wrap', 
                  gap: '1rem', 
                  justifyContent: 'center', 
                  marginTop: '1rem',
                  maxWidth: '100%' 
                }}>
                  {prods.volume_share.filter(item => (parseFloat(item.volume) || parseFloat(item.share) || 0) > 0).slice(0, 8).map((item, index) => (
                    <div key={index} style={{ display: 'flex', alignItems: 'center', fontSize: '0.9rem', color: '#4a5568' }}>
                      <div style={{ 
                        width: '12px', 
                        height: '12px', 
                        backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#6366f1', '#14b8a6'][index % 8],
                        borderRadius: '2px',
                        marginRight: '8px'
                      }}></div>
                      <span>
                        {item.category || item.product_name || 'Unknown'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {}
          {prods && prods.co_trade_network && prods.co_trade_network.length > 0 && (
            <div style={{ marginTop: '2rem' }}>
              <h3>Product Co-Trade Network (GNN)</h3>
              <p style={{ color: '#718096', fontSize: '0.9rem' }}>Frequently traded together with top product</p>
              
              <div style={{ 
                width: '100%', 
                height: '450px', 
                background: '#f8fafc', 
                borderRadius: '8px',
                marginTop: '1rem',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                overflow: 'hidden'
              }}>
                <svg width="600" height="450" viewBox="0 0 600 450">
                  <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="42" refY="3.5" orient="auto">
                      <polygon points="0 0, 10 3.5, 0 7" fill="#cbd5e1" />
                    </marker>
                  </defs>
                  
                  {}
                  {prods.co_trade_network.slice(0, 5).map((_, idx) => {
                    const angle = (idx * (360 / Math.min(prods.co_trade_network.length, 5))) * (Math.PI / 180);
                    const x = 300 + 160 * Math.cos(angle);
                    const y = 225 + 160 * Math.sin(angle);
                    return (
                      <line 
                        key={`line-${idx}`} 
                        x1="300" y1="225" 
                        x2={x} y2={y} 
                        stroke="#cbd5e1" 
                        strokeWidth="2"
                        markerEnd="url(#arrowhead)"
                      />
                    );
                  })}
                  
                  {}
                  <circle cx="300" cy="225" r="60" fill="#3b82f6" />
                  <text x="300" y="225" dy=".3em" textAnchor="middle" fill="white" fontSize="11" fontWeight="bold">
                    {(prods.product_performance?.[0]?.product_name || 'Primary').substring(0, 10)}
                  </text>
                  
                  {}
                  {prods.co_trade_network.slice(0, 5).map((p, idx) => {
                    const angle = (idx * (360 / Math.min(prods.co_trade_network.length, 5))) * (Math.PI / 180);
                    const x = 300 + 160 * Math.cos(angle);
                    const y = 225 + 160 * Math.sin(angle);
                    return (
                      <g key={`node-${idx}`}>
                        <circle cx={x} cy={y} r="40" fill="white" stroke="#94a3b8" strokeWidth="2" />
                        <text x={x} y={y} dy="-0.2em" textAnchor="middle" fill="#1e293b" fontSize="9" fontWeight="bold">
                          {p.name?.substring(0, 10)}
                        </text>
                        <text x={x} y={y} dy="1em" textAnchor="middle" fill="#64748b" fontSize="8">
                          {p.frequency} trades
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>
          )}

          {}
          {prods && prods.product_clusters && (
            <div style={{ marginTop: '2rem' }}>
              <h3>Product Latent Clusters (GNN)</h3>
              <p style={{ color: '#718096', fontSize: '0.9rem' }}>Automated product categorization clusters</p>
              {prods.product_clusters.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginTop: '1rem' }}>
                    {prods.product_clusters.slice(0, 5).map((cluster, idx) => (
                    <div key={idx} style={{
                        background: 'white', border: '1px solid #e2e8f0',
                        borderRadius: '8px', padding: '1.5rem',
                        minWidth: '200px', flex: '1'
                    }}>
                        <h4 style={{ margin: 0, color: '#475569' }}>{cluster.cluster_tag}</h4>
                        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6', marginTop: '0.5rem' }}>
                        {cluster.count}
                        </div>
                        <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Products in cluster</div>
                    </div>
                    ))}
                </div>
              ) : (
                <div className="empty-state" style={{ marginTop: '1rem', padding: '2rem' }}>
                  <p>No AI product clusters generated for this company yet.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default CompanyProducts;
