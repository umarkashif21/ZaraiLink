import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const LinkPrediction = () => {
  const navigate = useNavigate();
  const [companyName, setCompanyName] = useState('');
  const [predictionType, setPredictionType] = useState('sellers'); 
  const [method, setMethod] = useState('combined');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [methods, setMethods] = useState([]);
  const [suggestions, setSuggestions] = useState([]);

  
  useEffect(() => {
    fetch('http://localhost:8000/api/predict/methods/', { credentials: 'include' })
      .then(res => res.json())
      .then(data => setMethods(data.methods || []))
      .catch(err => console.error('Failed to load methods:', err));
  }, []);

  
  useEffect(() => {
    fetch('http://localhost:8000/api/explorer/?direction=import&limit=1000', { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        const companies = data.results?.map(c => c.company) || [];
        setSuggestions(companies);
      })
      .catch(err => console.error('Failed to load suggestions:', err));
  }, []);

  const handlePredict = async () => {
    if (!companyName.trim()) {
      setError('Please enter a company name');
      return;
    }

    setLoading(true);
    setError(null);
    setResults([]);

    const endpoint = predictionType === 'sellers' 
      ? `http://localhost:8000/api/predict/sellers/${encodeURIComponent(companyName)}/?method=${method}&top_k=10`
      : `http://localhost:8000/api/predict/buyers/${encodeURIComponent(companyName)}/?method=${method}&top_k=10`;

    try {
      const res = await fetch(endpoint, { credentials: 'include' });
      const data = await res.json();
      
      if (data.error) {
        setError(data.error);
      } else {
        setResults(data.results || []);
      }
    } catch (err) {
      setError('Failed to fetch predictions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getScorePercentage = (score) => {
    if (typeof score === 'number') {
      
      
      const normalizedScore = Math.min(1, Math.max(0, score));
      return normalizedScore * 100;
    }
    return 0;
  };

  
  const getConfidenceTier = (score) => {
    if (score >= 0.7) return { label: 'High', color: '#22c55e', bgColor: '#dcfce7' };
    if (score >= 0.4) return { label: 'Medium', color: '#f59e0b', bgColor: '#fef3c7' };
    return { label: 'Low', color: '#6b7280', bgColor: '#f3f4f6' };
  };

  
  const getRankLabel = (rank) => {
    if (rank === 1) return '1st';
    if (rank === 2) return '2nd';
    if (rank === 3) return '3rd';
    return `${rank}th`;
  };

  return (
    <>
      <Navbar />
      <div className="trade-ledger-container">
        <div className="trade-ledger-header">
          <h1>Link Prediction</h1>
          <p>Discover potential trading partners using AI-powered predictions</p>
        </div>

        {}
        <div className="filters-section">
          <div className="filters-grid">
            <div className="filter-group">
              <label>Prediction Type</label>
              <select
                value={predictionType}
                onChange={(e) => setPredictionType(e.target.value)}
              >
                <option value="sellers">Find Potential Sellers</option>
                <option value="buyers">Find Potential Buyers</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Company Name</label>
              <input
                type="text"
                list="company-suggestions"
                placeholder="Enter company name..."
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
              />
              <datalist id="company-suggestions">
                {suggestions.map((name, idx) => (
                  <option key={idx} value={name} />
                ))}
              </datalist>
            </div>

            <div className="filter-group">
              <label>Method</label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value)}
              >
                {methods.map(m => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <button 
                onClick={handlePredict}
                disabled={loading}
                className="btn-primary"
                style={{ marginTop: '24px' }}
              >
                {loading ? 'Predicting...' : 'Predict'}
              </button>
            </div>
          </div>
        </div>

        {}
        {method && methods.length > 0 && (
          <div className="metrics-row" style={{ marginBottom: '20px' }}>
            <div className="metric-card" style={{ flex: 1 }}>
              <h3>Selected Method</h3>
              <p style={{ fontSize: '14px', color: '#666' }}>
                {methods.find(m => m.id === method)?.description || 'Combined approach using all methods'}
              </p>
            </div>
          </div>
        )}

        {}
        {error && (
          <div className="empty-state" style={{ background: '#fee2e2', color: '#dc2626' }}>
            <h2>Error</h2>
            <p>{error}</p>
          </div>
        )}

        {}
        {loading && (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Running prediction algorithms...</p>
          </div>
        )}

        {}
        {!loading && results.length > 0 && (
          <div className="companies-section">
            <div className="results-header">
              <h2>Predicted {predictionType === 'sellers' ? 'Sellers' : 'Buyers'}</h2>
              <span className="results-count">{results.length} recommendations</span>
            </div>

            <div className="companies-grid">
              {results.map((result, idx) => {
                const score = result.final_confidence || result.total_score || result.score || 0;
                const confidenceTier = getConfidenceTier(score);
                const rank = result.rank || idx + 1;
                
                return (
                  <div key={idx} className="company-card">
                    <div className="company-card-header">
                      <div>
                        <h3>{result.seller || result.buyer}</h3>
                        <p className="company-location">
                          {result.segment_tag && `${result.segment_tag}`}
                        </p>
                      </div>
                      <span 
                        className="company-badge" 
                        style={{ 
                          background: confidenceTier.bgColor,
                          color: confidenceTier.color,
                          fontWeight: 'bold'
                        }}
                      >
                        {getRankLabel(rank)}
                      </span>
                    </div>

                    <div className="company-stats">
                      <div className="stat-item">
                        <span className="stat-label">Confidence</span>
                        <span className="stat-value" style={{ color: confidenceTier.color }}>
                          {(score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="stat-item">
                        <span className="stat-label">Tier</span>
                        <span 
                          className="stat-value"
                          style={{ 
                            background: confidenceTier.bgColor,
                            color: confidenceTier.color,
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '12px'
                          }}
                        >
                          {confidenceTier.label}
                        </span>
                      </div>
                      {result.scores && (
                        <div className="stat-item">
                          <span className="stat-label">Methods Used</span>
                          <span className="stat-value">{Object.keys(result.scores).length}</span>
                        </div>
                      )}
                      {result.common_buyer_count && (
                        <div className="stat-item">
                          <span className="stat-label">Common Neighbors</span>
                          <span className="stat-value">{result.common_buyer_count}</span>
                        </div>
                      )}
                      {result.matching_products && (
                        <div className="stat-item">
                          <span className="stat-label">Matching Products</span>
                          <span className="stat-value">{result.matching_products}</span>
                        </div>
                      )}
                      {result.seller_connections && (
                        <div className="stat-item">
                          <span className="stat-label">Connections</span>
                          <span className="stat-value">{result.seller_connections}</span>
                        </div>
                      )}
                    </div>

                    {result.scores && (
                      <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
                        <strong>Score Breakdown:</strong>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginTop: '5px' }}>
                          {Object.entries(result.scores).map(([methodName, methodScore]) => (
                            <span key={methodName} style={{ 
                              background: '#e5e7eb', 
                              padding: '2px 6px', 
                              borderRadius: '4px' 
                            }}>
                              {methodName}: {(methodScore * 100).toFixed(0)}%
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {}
        {!loading && !error && results.length === 0 && companyName && (
          <div className="empty-state">
            <h2>No predictions yet</h2>
            <p>Click "Predict" to find potential trading partners</p>
          </div>
        )}
      </div>
    </>
  );
};

export default LinkPrediction;
