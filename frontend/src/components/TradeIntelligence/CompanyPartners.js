import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Navbar from '../Layout/Navbar';
import ExportButton from '../Common/ExportButton';
import './TradeIntelligence.css';

const CompanyPartners = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const loc = useLocation();
  const [parts, setParts] = useState(null);
  const [load, setLoad] = useState(true);
  const [error, setError] = useState(null);
  const [similarCompanies, setSimilarCompanies] = useState([]);
  const [potentialSellers, setPotentialSellers] = useState([]);
  const [potentialBuyers, setPotentialBuyers] = useState([]);

  
  const companyName = decodeURIComponent(id);
  const tab = loc.pathname.split('/').pop();

  useEffect(() => {
    loadParts();
  }, [id]);

  const loadParts = async () => {
    setLoad(true);
    setError(null);
    try {
      
      const res = await fetch(`http://localhost:8000/api/company/${id}/partners/`, {
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        setParts(data);
      } else {
        setError('Could not load partners');
      }
    } catch (err) {
      console.error('Failed to load partners:', err);
      setError('Failed to load partners data');
    } finally {
      setLoad(false);
    }
  };

  
  const loadSimilarCompanies = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/company/${id}/similar/?method=combined`, {
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        setSimilarCompanies(data.similar_companies || []);
      }
    } catch (err) {
      console.error('Failed to load similar companies:', err);
    }
  };

  useEffect(() => {
    if (id) {
      loadSimilarCompanies();
      loadPotentialPartners();
    }
  }, [id]);

  
  const loadPotentialPartners = async () => {
    try {
      
      const sellersRes = await fetch(`http://localhost:8000/api/predict/sellers/${id}/?method=combined&top_k=5`, {
        credentials: 'include'
      });
      if (sellersRes.ok) {
        const sellersData = await sellersRes.json();
        
        setPotentialSellers(sellersData.results || []);
      }

      
      const buyersRes = await fetch(`http://localhost:8000/api/predict/buyers/${id}/?method=combined&top_k=5`, {
        credentials: 'include'
      });
      if (buyersRes.ok) {
        const buyersData = await buyersRes.json();
        
        setPotentialBuyers(buyersData.results || []);
      }
    } catch (err) {
      console.error('Failed to load potential partners:', err);
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
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(v);
  };

  
  const topPartners = parts?.top_partners || [];
  const tradeByCountry = parts?.trade_volume_by_country || [];

  if (load) {
    return (
      <>
        <Navbar />
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading partners...</p>
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
            {topPartners && topPartners.length > 0 && (
              <ExportButton
                data={topPartners.map(p => ({
                  partner: p.partner,
                  total_volume: p.total_volume,
                  transactions: p.transaction_count,
                }))}
                columns={[
                  { key: 'partner', label: 'Partner' },
                  { key: 'total_volume', label: 'Trade Volume (USD)' },
                  { key: 'transactions', label: 'Transactions' },
                ]}
                filename={`partners-${companyName}`}
                title={`${companyName} - Trade Partners`}
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
          <h2>Partner Network</h2>

          {error ? (
            <div className="empty-state">
              <p>{error}</p>
            </div>
          ) : (
            <>
              <div className="info-cards-grid">
                <div className="info-card">
                  <h4>Top Partners</h4>
                  <div className="info-card-value">{topPartners.length}</div>
                </div>
                <div className="info-card">
                  <h4>Countries</h4>
                  <div className="info-card-value">{tradeByCountry.length}</div>
                </div>
              </div>

              <div style={{ marginTop: '2rem' }}>
                <h3>Top Partners</h3>
                {topPartners.length > 0 ? (
                  <div className="partners-grid">
                    {topPartners.map((p, idx) => (
                      <div key={idx} className="partner-card">
                        <div className="partner-country">{p.partner}</div>
                        <div className="partner-volume">
                          {new Intl.NumberFormat('en-US').format(p.total_volume)} MT
                        </div>
                        <div style={{ fontSize: '0.85rem', color: '#718096', marginTop: '0.5rem' }}>
                          {p.transaction_count} transactions
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: '#718096', marginTop: '1rem' }}>No partners found</p>
                )}
              </div>

              <div style={{ marginTop: '2rem' }}>
                <h3>Trade Volume by Country</h3>
                {tradeByCountry.length > 0 ? (
                  <div className="partners-grid">
                    {tradeByCountry.map((c, idx) => (
                      <div key={idx} className="partner-card">
                        <div className="partner-country">{c.country}</div>
                        <div className="partner-volume">
                          {new Intl.NumberFormat('en-US').format(c.total_volume)} MT
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: '#718096', marginTop: '1rem' }}>No country data available</p>
                )}
              </div>

              {}
              {topPartners.filter(p => parseFloat(p.total_volume) > 0).length > 0 && (
                <div style={{ marginTop: '2rem' }}>
                  <h3>Partner Trade Volume</h3>
                  <div style={{ width: '100%', height: 300, marginTop: '1rem' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={topPartners.filter(p => parseFloat(p.total_volume) > 0).slice(0, 6).map(p => ({
                          name: p.partner?.substring(0, 15) + (p.partner?.length > 15 ? '...' : ''),
                          volume: parseFloat(p.total_volume) || 0,
                          transactions: parseInt(p.transaction_count) || 0,
                        }))}
                        margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
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
                            if (isNaN(num)) return '$0';
                            if (num >= 1000000) return `$${(num / 1000000).toFixed(1)}M`;
                            if (num >= 1000) return `$${(num / 1000).toFixed(0)}K`;
                            return `$${num.toFixed(0)}`;
                          }}
                        />
                        <Tooltip 
                          formatter={(value, name) => [
                            name === 'volume' 
                              ? `$${new Intl.NumberFormat('en-US').format(value)}`
                              : value,
                            name === 'volume' ? 'Trade Volume' : 'Transactions'
                          ]}
                        />
                        <Legend />
                        <Bar dataKey="volume" fill="#3b82f6" name="Trade Volume (USD)" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {}
              <div style={{ marginTop: '2rem' }}>
                <h3>AI-Predicted Potential Sellers</h3>
                <p style={{ color: '#718096', fontSize: '0.9rem', marginTop: '0.5rem' }}>Based on graph neural network analysis of trade patterns</p>
                {potentialSellers.length > 0 ? (
                  <div className="partners-grid" style={{ marginTop: '1rem' }}>
                    {potentialSellers.map((seller, idx) => (
                      <div 
                        key={idx} 
                        className="partner-card" 
                        style={{ cursor: 'pointer', transition: 'transform 0.2s' }}
                        onClick={() => navigate(`/trade-intelligence/company/${encodeURIComponent(seller.seller)}/overview`)}
                        onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-3px)'}
                        onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                      >
                        <div className="partner-country">{seller.seller}</div>
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center',
                          gap: '0.5rem',
                          marginTop: '0.5rem'
                        }}>
                          <span className="segment-badge" style={{ 
                            background: `hsl(${Math.floor((seller.final_confidence || 0) * 120)}, 70%, 45%)`,
                            color: 'white'
                          }}>
                            {((seller.final_confidence || 0) * 100).toFixed(0)}% Confidence
                          </span>
                        </div>
                        <div style={{ fontSize: '0.8rem', color: '#718096', marginTop: '0.5rem' }}>
                          Rank: #{seller.rank || '-'}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: '#718096', marginTop: '1rem' }}>
                    No potential sellers predicted.
                  </p>
                )}
              </div>

              {}
              <div style={{ marginTop: '2rem' }}>
                <h3>AI-Predicted Potential Buyers</h3>
                <p style={{ color: '#718096', fontSize: '0.9rem', marginTop: '0.5rem' }}>Based on graph neural network analysis of trade patterns</p>
                {potentialBuyers.length > 0 ? (
                  <div className="partners-grid" style={{ marginTop: '1rem' }}>
                    {potentialBuyers.map((buyer, idx) => (
                      <div 
                        key={idx} 
                        className="partner-card" 
                        style={{ cursor: 'pointer', transition: 'transform 0.2s' }}
                        onClick={() => navigate(`/trade-intelligence/company/${encodeURIComponent(buyer.buyer)}/overview`)}
                        onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-3px)'}
                        onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                      >
                        <div className="partner-country">{buyer.buyer}</div>
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center',
                          gap: '0.5rem',
                          marginTop: '0.5rem'
                        }}>
                          <span className="segment-badge" style={{ 
                            background: `hsl(${Math.floor((buyer.final_confidence || 0) * 120)}, 70%, 45%)`,
                            color: 'white'
                          }}>
                            {((buyer.final_confidence || 0) * 100).toFixed(0)}% Confidence
                          </span>
                        </div>
                        <div style={{ fontSize: '0.8rem', color: '#718096', marginTop: '0.5rem' }}>
                          Rank: #{buyer.rank || '-'}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: '#718096', marginTop: '1rem' }}>
                    No potential buyers predicted.
                  </p>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default CompanyPartners;

