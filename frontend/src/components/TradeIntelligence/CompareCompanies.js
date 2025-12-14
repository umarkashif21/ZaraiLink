import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const CompareCompanies = () => {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState([]);
  const [selectedCompanies, setSelectedCompanies] = useState(['', '']);
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingCompanies, setLoadingCompanies] = useState(true);
  const [error, setError] = useState(null);

  // Fetch available companies on mount
  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    setLoadingCompanies(true);
    try {
      const res = await fetch('http://localhost:8000/api/explorer/', {
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        const companyNames = (data.results || []).map(item => item.company).sort();
        setCompanies([...new Set(companyNames)]); // Remove duplicates
      }
    } catch (err) {
      console.error('Failed to load companies:', err);
      setError('Failed to load company list');
    } finally {
      setLoadingCompanies(false);
    }
  };

  const handleCompanyChange = (index, value) => {
    const newCompanies = [...selectedCompanies];
    newCompanies[index] = value;
    setSelectedCompanies(newCompanies);
  };

  const handleCompare = async () => {
    const validCompanies = selectedCompanies.filter(c => c.trim() !== '');
    
    if (validCompanies.length < 2) {
      setError('Please select at least 2 companies to compare');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch('http://localhost:8000/api/compare/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ companies: validCompanies })
      });

      if (res.ok) {
        const data = await res.json();
        setComparisonData(data);
      } else {
        setError('Failed to load comparison data');
      }
    } catch (err) {
      console.error('Comparison error:', err);
      setError('Failed to compare companies');
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = async () => {
    const validCompanies = selectedCompanies.filter(c => c.trim() !== '');
    
    try {
      const res = await fetch('http://localhost:8000/api/export-comparison-pdf/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ 
          companies: validCompanies,
          comparison_data: comparisonData 
        })
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `company-comparison-${Date.now()}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError('Failed to generate PDF');
      }
    } catch (err) {
      console.error('PDF export error:', err);
      setError('Failed to export PDF');
    }
  };

  return (
    <>
      <Navbar />
      <div className="company-detail-container">
        <div className="company-detail-header" style={{ textAlign: 'center' }}>
          <h1>Compare Companies</h1>
          <p>Side-by-side comparison of trade intelligence metrics</p>
        </div>

        <div className="tab-content">
          <h2>Select Companies to Compare</h2>
          
          {loadingCompanies ? (
            <div className="loading-container" style={{ padding: '2rem' }}>
              <div className="spinner"></div>
              <p>Loading companies...</p>
            </div>
          ) : (
            <>
              <div className="filters-grid" style={{ marginTop: '2rem' }}>
                {selectedCompanies.map((company, index) => (
                  <div key={index} className="filter-group">
                    <label>Company {index + 1}</label>
                    <select
                      value={company}
                      onChange={(e) => handleCompanyChange(index, e.target.value)}
                      style={{
                        padding: '0.75rem',
                        border: '2px solid #e2e8f0',
                        borderRadius: '8px',
                        fontSize: '1rem',
                        width: '100%',
                        background: 'white'
                      }}
                    >
                      <option value="">-- Select Company --</option>
                      {companies.map((comp, idx) => (
                        <option key={idx} value={comp}>{comp}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem', justifyContent: 'center' }}>
                <button 
                  onClick={handleCompare}
                  className="btn-primary"
                  disabled={loading}
                  style={{
                    padding: '0.75rem 2rem',
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    fontWeight: 600,
                    cursor: loading ? 'not-allowed' : 'pointer',
                    opacity: loading ? 0.7 : 1
                  }}
                >
                  {loading ? 'Comparing...' : 'Compare Companies'}
                </button>
                
                {comparisonData && (
                  <button 
                    onClick={handleExportPDF}
                    className="btn-secondary"
                    style={{
                      padding: '0.75rem 2rem',
                      background: 'white',
                      color: '#10b981',
                      border: '2px solid #10b981',
                      borderRadius: '8px',
                      fontSize: '1rem',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    📄 Export to PDF
                  </button>
                )}
              </div>
            </>
          )}

          {error && (
            <div style={{
              marginTop: '2rem',
              padding: '1rem',
              background: '#fed7d7',
              color: '#742a2a',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              {error}
            </div>
          )}

          {comparisonData && (
            <div style={{ marginTop: '3rem' }}>
              <h3>Comparison Results</h3>
              
              <div style={{ marginTop: '2rem' }}>
                <h4 style={{ marginBottom: '1rem' }}>Overview Metrics</h4>
                <div className="trade-ledger-table-container">
                  <table className="trade-ledger-table">
                    <thead>
                      <tr>
                        <th>Metric</th>
                        {selectedCompanies.filter(c => c).map((comp, idx) => (
                          <th key={idx}>{comp}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>Trade Volume</strong></td>
                        {comparisonData.companies?.map((comp, idx) => (
                          <td key={idx}>
                            ${comp.trade_volume?.toLocaleString() || 'N/A'}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Estimated Revenue</strong></td>
                        {comparisonData.companies?.map((comp, idx) => (
                          <td key={idx}>
                            ${comp.estimated_revenue?.toLocaleString() || 'N/A'}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Total Products</strong></td>
                        {comparisonData.companies?.map((comp, idx) => (
                          <td key={idx}>{comp.total_products || 0}</td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Total Partners</strong></td>
                        {comparisonData.companies?.map((comp, idx) => (
                          <td key={idx}>{comp.total_partners || 0}</td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Partner Diversity</strong></td>
                        {comparisonData.companies?.map((comp, idx) => (
                          <td key={idx}>
                            {comp.partner_diversity_score?.toFixed(2) || 'N/A'}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Active Since</strong></td>
                        {comparisonData.companies?.map((comp, idx) => (
                          <td key={idx}>
                            {comp.active_since ? new Date(comp.active_since).getFullYear() : 'N/A'}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>

                <h4 style={{ marginTop: '2rem', marginBottom: '1rem' }}>Network Influence</h4>
                <div className="info-cards-grid">
                  {comparisonData.companies?.map((comp, idx) => (
                    <div key={idx} className="info-card">
                      <h4>{selectedCompanies[idx]}</h4>
                      <div style={{ marginTop: '1rem' }}>
                        <div style={{ marginBottom: '0.5rem' }}>
                          <strong>PageRank:</strong> {comp.pagerank?.toFixed(4) || 'N/A'}
                        </div>
                        <div>
                          <strong>Network Degree:</strong> {comp.network_degree || 'N/A'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default CompareCompanies;
