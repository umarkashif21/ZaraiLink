import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import './TradeIntelligence.css';

const CompanyPartners = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [company, setCompany] = useState(null);
  const [partners, setPartners] = useState([]);
  const [loading, setLoading] = useState(true);

  const currentTab = location.pathname.split('/').pop();

  useEffect(() => {
    loadCompanyData();
    loadPartners();
  }, [id]);

  const loadCompanyData = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/trade-ledger/companies/${id}/`);
      if (response.ok) {
        const data = await response.json();
        setCompany(data);
      }
    } catch (err) {
      console.error('Failed to load company:', err);
    }
  };

  const loadPartners = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/trade-ledger/companies/${id}/partners/`);
      if (response.ok) {
        const data = await response.json();
        setPartners(data);
      }
    } catch (err) {
      console.error('Failed to load partners:', err);
    } finally {
      setLoading(false);
    }
  };

  const navigateToTab = (tab) => {
    navigate(`/trade-intelligence/company/${id}/${tab}`);
  };

  const formatCurrency = (value) => {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const getTopPartners = (count) => {
    return [...partners]
      .sort((a, b) => parseFloat(b.trade_volume) - parseFloat(a.trade_volume))
      .slice(0, count);
  };

  const getTopExportCountries = () => {
    return partners
      .filter(p => p.is_export)
      .sort((a, b) => parseFloat(b.trade_volume) - parseFloat(a.trade_volume))
      .slice(0, 5);
  };

  const getTopPorts = () => {
    return partners
      .filter(p => p.port_name)
      .sort((a, b) => parseFloat(b.trade_volume) - parseFloat(a.trade_volume))
      .slice(0, 5);
  };

  if (loading) {
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
        {/* Header */}
        {company && (
          <>
            <div className="company-detail-header">
              <h1>{company.company.name}</h1>
              <p>📍 {company.company.province}, {company.company.country}</p>
              <div className="company-tags">
                {company.is_exporter && <span className="company-tag">Exporter</span>}
                {company.is_importer && <span className="company-tag">Importer</span>}
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="tab-navigation">
              <button
                className={`tab-button ${currentTab === 'overview' ? 'active' : ''}`}
                onClick={() => navigateToTab('overview')}
              >
                Overview
              </button>
              <button
                className={`tab-button ${currentTab === 'products' ? 'active' : ''}`}
                onClick={() => navigateToTab('products')}
              >
                Products ({company.total_products || 0})
              </button>
              <button
                className={`tab-button ${currentTab === 'partners' ? 'active' : ''}`}
                onClick={() => navigateToTab('partners')}
              >
                Partners ({company.total_partners || 0})
              </button>
              <button
                className={`tab-button ${currentTab === 'trends' ? 'active' : ''}`}
                onClick={() => navigateToTab('trends')}
              >
                Trends
              </button>
            </div>
          </>
        )}

        {/* Tab Content - Partners */}
        <div className="tab-content">
          <h2>Partner Network</h2>

          {/* Key Metrics */}
          {company && (
            <div className="info-cards-grid">
              <div className="info-card">
                <h4>Partner Diversity Score</h4>
                <div className="info-card-value">{company.partner_diversity_score || 0}/100</div>
              </div>
              <div className="info-card">
                <h4>Total Partner Countries</h4>
                <div className="info-card-value">{company.total_partners || 0}</div>
              </div>
              <div className="info-card">
                <h4>Export Partners</h4>
                <div className="info-card-value">
                  {partners.filter(p => p.is_export).length}
                </div>
              </div>
              <div className="info-card">
                <h4>Import Partners</h4>
                <div className="info-card-value">
                  {partners.filter(p => !p.is_export).length}
                </div>
              </div>
            </div>
          )}

          {/* Top Exporting Countries */}
          <div style={{ marginTop: '2rem' }}>
            <h3>Top Exporting Countries</h3>
            {getTopExportCountries().length > 0 ? (
              <div className="partners-grid">
                {getTopExportCountries().map((partner, idx) => (
                  <div key={idx} className="partner-card">
                    <div className="partner-country">{partner.country}</div>
                    <div className="partner-volume">
                      {formatCurrency(partner.trade_volume)}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#718096', marginTop: '0.5rem' }}>
                      {parseFloat(partner.percentage_share).toFixed(1)}% of total
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#718096', marginTop: '1rem' }}>No export partners found</p>
            )}
          </div>

          {/* Top Ports of Entry */}
          <div style={{ marginTop: '2rem' }}>
            <h3>Top Ports of Entry</h3>
            {getTopPorts().length > 0 ? (
              <div className="partners-grid">
                {getTopPorts().map((partner, idx) => (
                  <div key={idx} className="partner-card">
                    <div className="partner-country">{partner.port_name}</div>
                    <div style={{ fontSize: '0.9rem', color: '#718096', marginTop: '0.3rem' }}>
                      {partner.country}
                    </div>
                    <div className="partner-volume" style={{ marginTop: '0.5rem' }}>
                      {formatCurrency(partner.trade_volume)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#718096', marginTop: '1rem' }}>No port information available</p>
            )}
          </div>

          {/* All Partners Table */}
          {partners.length > 0 && (
            <div style={{ marginTop: '2rem' }}>
              <h3>All Partners</h3>
              <table className="products-table" style={{ marginTop: '1rem' }}>
                <thead>
                  <tr>
                    <th>Country</th>
                    <th>Port</th>
                    <th>Type</th>
                    <th>Trade Volume</th>
                    <th>Share</th>
                  </tr>
                </thead>
                <tbody>
                  {partners.map((partner, idx) => (
                    <tr key={idx}>
                      <td><strong>{partner.country}</strong></td>
                      <td>{partner.port_name || 'N/A'}</td>
                      <td>
                        <span className={`growth-badge ${partner.is_export ? 'positive' : 'negative'}`}>
                          {partner.is_export ? 'Export' : 'Import'}
                        </span>
                      </td>
                      <td>{formatCurrency(partner.trade_volume)}</td>
                      <td>{parseFloat(partner.percentage_share).toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default CompanyPartners;
