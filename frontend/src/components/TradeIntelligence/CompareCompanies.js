import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
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

  
  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    setLoadingCompanies(true);
    try {
      const res = await fetch('http://localhost:8000/api/explorer/?direction=both&limit=1000', {
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        const companyNames = (data.results || []).map(item => item.company).sort();
        setCompanies([...new Set(companyNames)]); 
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
    try {
      setLoading(true);
      
      const { default: jsPDF } = await import('jspdf');
      const { default: html2canvas } = await import('html2canvas');
      const { default: autoTable } = await import('jspdf-autotable');
      
      const doc = new jsPDF();
      const pageWidth = doc.internal.pageSize.getWidth();
      
      
      doc.setFontSize(18);
      doc.setTextColor(44, 62, 80);
      doc.text('Company Comparison Report', pageWidth / 2, 20, { align: 'center' });
      
      doc.setFontSize(10);
      doc.setTextColor(100);
      doc.text(`Generated: ${new Date().toLocaleDateString()}`, pageWidth / 2, 26, { align: 'center' });

      
      const companyNames = selectedCompanies.filter(c => c);
      const metrics = [
        { label: 'Trade Volume', key: 'trade_volume', fmt: val => val ? `$${val.toLocaleString()}` : '' },
        { label: 'Estimated Revenue', key: 'estimated_revenue', fmt: val => val ? `$${val.toLocaleString()}` : '' },
        { label: 'Total Products', key: 'total_products', fmt: val => val || '' },
        { label: 'Total Partners', key: 'total_partners', fmt: val => val || '' },
        { label: 'Partner Diversity', key: 'partner_diversity_score', fmt: val => val ? val.toFixed(2) : '' },
        { label: 'Active Since', key: 'active_since', fmt: val => val ? new Date(val).getFullYear() : '' },
        { label: 'PageRank', key: 'pagerank', fmt: val => val ? val.toFixed(4) : '' },
        { label: 'Network Degree', key: 'network_degree', fmt: val => val || '' },
      ];

      const tableBody = metrics.map(m => {
        const row = [m.label];
        comparisonData.companies.forEach(comp => {
          row.push(m.fmt(comp[m.key]));
        });
        return row;
      });

      
      autoTable(doc, {
        head: [['Metric', ...companyNames]],
        body: tableBody,
        startY: 35,
        theme: 'grid',
        headStyles: { fillColor: [16, 185, 129], textColor: 255, fontStyle: 'bold' },
        styles: { fontSize: 10, cellPadding: 3 },
        alternateRowStyles: { fillColor: [240, 253, 250] },
      });

      let finalY = doc.lastAutoTable.finalY + 10;

      
      
      const addChartToDoc = async (elementId, title) => {
        const element = document.getElementById(elementId);
        if (element) {
          if (finalY > 250) { 
             doc.addPage();
             finalY = 20;
          }
          
          doc.setFontSize(14);
          doc.setTextColor(0);
          doc.text(title, 14, finalY);
          finalY += 5;

          const canvas = await html2canvas(element, {
            scale: 2, 
            useCORS: true,
            logging: false
          });
          
          const imgData = canvas.toDataURL('image/png');
          const imgWidth = pageWidth - 28; 
          const imgHeight = (canvas.height * imgWidth) / canvas.width;
          
          doc.addImage(imgData, 'PNG', 14, finalY, imgWidth, imgHeight);
          finalY += imgHeight + 10;
        }
      };

      await addChartToDoc('chart-volume', 'Trade Volume Comparison');
      await addChartToDoc('chart-partners', 'Partners & Products Comparison');

      
      doc.save(`comparison_report_${Date.now()}.pdf`);
      
    } catch (err) {
      console.error('PDF export error:', err);
      setError('Failed to export PDF.');
    } finally {
      setLoading(false);
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
                            {comp.trade_volume > 0 ? `$${comp.trade_volume.toLocaleString()}` : ''}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Estimated Revenue</strong></td>
                        {comparisonData.companies?.map((comp, idx) => (
                          <td key={idx}>
                            {comp.estimated_revenue > 0 ? `$${comp.estimated_revenue.toLocaleString()}` : ''}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Total Products</strong></td>
                        {comparisonData.companies?.map((comp, idx) => (
                          <td key={idx}>{comp.total_products > 0 ? comp.total_products : ''}</td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Total Partners</strong></td>
                        {comparisonData.companies?.map((comp, idx) => (
                          <td key={idx}>{comp.total_partners > 0 ? comp.total_partners : ''}</td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Partner Diversity</strong></td>
                        {comparisonData.companies?.map((comp, idx) => (
                          <td key={idx}>
                            {comp.partner_diversity_score > 0 ? comp.partner_diversity_score.toFixed(2) : ''}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td><strong>Active Since</strong></td>
                        {comparisonData.companies?.map((comp, idx) => (
                          <td key={idx}>
                            {comp.active_since ? new Date(comp.active_since).getFullYear() : ''}
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
                      <h4>{selectedCompanies.filter(c => c)[idx]}</h4>
                      <div style={{ marginTop: '1rem' }}>
                        {typeof comp.pagerank === 'number' && comp.pagerank > 0 && (
                          <div style={{ marginBottom: '0.5rem' }}>
                            <strong>PageRank:</strong> {comp.pagerank.toFixed(4)}
                          </div>
                        )}
                        {comp.network_degree > 0 && (
                          <div>
                            <strong>Network Degree:</strong> {comp.network_degree}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {}
                <h4 style={{ marginTop: '2rem', marginBottom: '1rem' }}>Trade Volume Comparison</h4>
                <div id="chart-volume" style={{ width: '100%', height: 350, marginTop: '1rem', background: '#fff' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={comparisonData.companies?.map((comp, idx) => ({
                        name: selectedCompanies.filter(c => c)[idx]?.substring(0, 15) + (selectedCompanies.filter(c => c)[idx]?.length > 15 ? '...' : ''),
                        volume: parseFloat(comp.trade_volume) || 0,
                        revenue: parseFloat(comp.estimated_revenue) || 0,
                        partners: parseInt(comp.total_partners) || 0,
                        products: parseInt(comp.total_products) || 0
                      })) || []}
                      margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                      <XAxis 
                        dataKey="name" 
                        angle={-15} 
                        textAnchor="end" 
                        interval={0}
                        tick={{ fontSize: 11 }}
                        height={60}
                      />
                      <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`} />
                      <Tooltip 
                        formatter={(value, name) => [
                          name === 'volume' 
                            ? `${new Intl.NumberFormat('en-US').format(value)} MT`
                            : `$${new Intl.NumberFormat('en-US').format(value)}`,
                          name === 'volume' ? 'Trade Volume' : 'Revenue'
                        ]}
                      />
                      <Legend />
                      <Bar dataKey="volume" fill="#10b981" name="Trade Volume (MT)" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="revenue" fill="#3b82f6" name="Revenue (USD)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {}
                <h4 style={{ marginTop: '2rem', marginBottom: '1rem' }}>Partners & Products Comparison</h4>
                <div id="chart-partners" style={{ width: '100%', height: 300, marginTop: '1rem', background: '#fff' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={comparisonData.companies?.map((comp, idx) => ({
                        name: selectedCompanies.filter(c => c)[idx]?.substring(0, 20),
                        partners: parseInt(comp.total_partners) || 0,
                        products: parseInt(comp.total_products) || 0
                      })) || []}
                      margin={{ top: 20, right: 30, left: 20, bottom: 40 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                      <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="partners" fill="#f59e0b" name="Partners" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="products" fill="#8b5cf6" name="Products" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
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
