import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Navbar from '../Layout/Navbar';
import {
  UnlockConfirmModal,
  SuccessModal,
  InsufficientTokensModal,
  ErrorModal,
} from '../Common/Modal';
import './CompanyProfile.css';

const CompanyProfile = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { tokenBalance, refreshUser } = useAuth();

  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  
  const [selectedContact, setSelectedContact] = useState(null);
  const [unlocking, setUnlocking] = useState(false);

  
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [showInsufficientTokensModal, setShowInsufficientTokensModal] = useState(false);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [unlockedContactData, setUnlockedContactData] = useState(null);

  
  const [similarCompanies, setSimilarCompanies] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);

  useEffect(() => {
    loadCompanyData();
  }, [id]);

  useEffect(() => {
    if (activeTab === 'similar' && company?.name) {
      loadSimilarCompanies();
    }
  }, [activeTab]);

  const loadCompanyData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:8000/api/companies/${id}/`, {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setCompany(data);
      } else if (response.status === 404) {
        setError('Company not found');
      } else {
        throw new Error('Failed to load company data');
      }
    } catch (err) {
      setError('Failed to load company. Please try again.');
      console.error('Load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadSimilarCompanies = async () => {
    if (!company || similarCompanies.length > 0) return;
    setLoadingSimilar(true);
    try {
      const response = await fetch(`http://localhost:8000/api/company/${encodeURIComponent(company.name)}/similar/`);
      if (response.ok) {
        const data = await response.json();
        setSimilarCompanies(data.similar_companies || []);
      }
    } catch (err) {
      console.error('Failed to load similar companies', err);
    } finally {
      setLoadingSimilar(false);
    }
  };

  const handleUnlockClick = (contact) => {
    
    if (contact.is_unlocked || contact.is_public) {
      return;
    }

    setSelectedContact(contact);
    setShowConfirmModal(true);
  };

  
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const handleConfirmUnlock = async () => {
    setShowConfirmModal(false);
    setUnlocking(true);

    try {
      const csrftoken = getCookie('csrftoken');
      const response = await fetch(
        `http://localhost:8000/api/key-contacts/${selectedContact.id}/unlock/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
          },
          credentials: 'include',
        }
      );

      const data = await response.json();

      if (response.ok) {
        
        await refreshUser(); 
        setUnlockedContactData(data.contact);
        setShowSuccessModal(true);
        
        
        setTimeout(() => loadCompanyData(), 500);
      } else {
        
        if (data.status === 'insufficient_tokens' || response.status === 402) {
          setShowInsufficientTokensModal(true);
        } else {
          setErrorMessage(data.message || 'Failed to unlock contact');
          setShowErrorModal(true);
        }
      }
    } catch (err) {
      setErrorMessage('Network error. Please check your connection.');
      setShowErrorModal(true);
      console.error('Unlock error:', err);
    } finally {
      setUnlocking(false);
    }
  };

  const handleBuyTokens = () => {
    setShowInsufficientTokensModal(false);
    navigate('/subscription');
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading company profile...</p>
      </div>
    );
  }

  if (error || !company) {
    return (
      <div className="error-container">
        <h2>{error || 'Company Not Found'}</h2>
        <button onClick={() => navigate('/trade-directory/find-suppliers')} className="btn-primary">
          Back to Directory
        </button>
      </div>
    );
  }

  return (
    <>
      <Navbar />
      <div className="company-profile-container">
      {}
      <div className="profile-header">
        <div className="header-content">
          <div>
            <h1>{company.name.toUpperCase()}</h1>
            {company.legal_name && company.legal_name !== company.name && (
              <p className="legal-name">{company.legal_name}</p>
            )}
              <p className="location">
                {company.district && `${company.district}, `}{company.province}, {company.country}
              </p>
          </div>
          <div className="header-badges">
            <span className={`status-badge ${company.verification_status}`}>
              {company.verification_status === 'verified' ? 'Verified' : 'Pending'}
            </span>
            {company.market_sentiment && (
               <span className="status-badge" style={{ 
                   backgroundColor: company.market_sentiment === 'Positive' ? '#e6f4ea' : company.market_sentiment === 'Negative' ? '#fce8e6' : '#f1f3f4',
                   color: company.market_sentiment === 'Positive' ? '#137333' : company.market_sentiment === 'Negative' ? '#c5221f' : '#202124',
                   marginLeft: '0.5rem'
               }}>
                  {company.market_sentiment} Sentiment
               </span>
            )}
          </div>
        </div>
      </div>

      {}
      <div className="profile-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'products' ? 'active' : ''}`}
          onClick={() => setActiveTab('products')}
        >
          Products ({company.products?.length || 0})
        </button>
        <button
          className={`tab ${activeTab === 'contacts' ? 'active' : ''}`}
          onClick={() => setActiveTab('contacts')}
        >
          Key Contacts ({company.key_contacts?.length || 0})
        </button>
        <button
          className={`tab ${activeTab === 'similar' ? 'active' : ''}`}
          onClick={() => setActiveTab('similar')}
        >
          Similar Companies
        </button>
      </div>

      {}
      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            {company.description && (
              <div className="info-section">
                <h3>About</h3>
                <p>{company.description}</p>
              </div>
            )}

            <div className="info-grid">
              {company.sector && (
                <div className="info-card">
                  <span className="info-label">Sector</span>
                  <span className="info-value">{company.sector.name}</span>
                </div>
              )}
              {company.company_role && (
                <div className="info-card">
                  <span className="info-label">Role</span>
                  <span className="info-value">{company.company_role.name}</span>
                </div>
              )}
              {company.company_type && (
                <div className="info-card">
                  <span className="info-label">Type</span>
                  <span className="info-value">{company.company_type.name}</span>
                </div>
              )}
              {company.year_established && (
                <div className="info-card">
                  <span className="info-label">Established</span>
                  <span className="info-value">{company.year_established}</span>
                </div>
              )}
              {company.number_of_employees && (
                <div className="info-card">
                  <span className="info-label">Employees</span>
                  <span className="info-value">{company.number_of_employees}</span>
                </div>
              )}
              {company.website && (
                <div className="info-card">
                  <span className="info-label">Website</span>
                  <a href={company.website} target="_blank" rel="noopener noreferrer" className="info-link">
                    Visit Website →
                  </a>
                </div>
              )}
            </div>

            {company.contact_email && (
              <div className="info-section">
                <h3>General Contact</h3>
                <p>Email: {company.contact_email}</p>
                {company.phone && <p>Phone: {company.phone}</p>}
              </div>
            )}
          </div>
        )}

        {activeTab === 'products' && (
          <div className="products-tab">
            {company.products && company.products.length > 0 ? (
              <div className="products-grid">
                {company.products.map((product) => (
                  <div key={product.id} className="product-card">
                    <h4>{product.name}</h4>
                    {product.variety && <p className="product-variety">{product.variety}</p>}
                    {product.description && <p className="product-description">{product.description}</p>}
                    {product.value_added && (
                      <span className="value-added-badge">Value Added</span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-data">
                <p>No products listed for this company</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'contacts' && (
          <div className="contacts-tab">
            {company.key_contacts && company.key_contacts.length > 0 ? (
              <div className="contacts-grid">
                {company.key_contacts.map((contact) => (
                  <div key={contact.id} className="contact-card">
                    <div className="contact-header">
                      <div>
                        <h4>{contact.name}</h4>
                        {contact.designation && <p className="designation">{contact.designation}</p>}
                      </div>
                      {contact.is_public && (
                        <span className="public-badge">Public</span>
                      )}
                    </div>

                    <div className="contact-details">
                      <div className="detail-row">
                        <span className="detail-label">Phone:</span>
                        {contact.is_unlocked || contact.is_public ? (
                          <span className="detail-value unlocked">{contact.phone}</span>
                        ) : (
                          <span className="detail-value locked">Locked</span>
                        )}
                      </div>
                      <div className="detail-row">
                        <span className="detail-label">Email:</span>
                        {contact.is_unlocked || contact.is_public ? (
                          <span className="detail-value unlocked">{contact.email}</span>
                        ) : (
                          <span className="detail-value locked">Locked</span>
                        )}
                      </div>
                      {contact.whatsapp && (
                        <div className="detail-row">
                          <span className="detail-label">WhatsApp:</span>
                          {contact.is_unlocked || contact.is_public ? (
                            <span className="detail-value unlocked">{contact.whatsapp}</span>
                          ) : (
                            <span className="detail-value locked">Locked</span>
                          )}
                        </div>
                      )}
                    </div>

                    {!contact.is_unlocked && !contact.is_public && (
                      <button
                        onClick={() => handleUnlockClick(contact)}
                        disabled={unlocking}
                        className="btn-unlock"
                      >
                        {unlocking ? 'Unlocking...' : 'Unlock (1 token)'}
                      </button>
                    )}
                    {contact.is_unlocked && !contact.is_public && (
                      <div className="unlocked-badge">Unlocked</div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-data">
                <p>No key contacts listed for this company</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'similar' && (
          <div className="similar-tab">
            {loadingSimilar ? (
               <div className="loading-container" style={{ padding: '2rem' }}>
                <div className="spinner"></div>
                <p>Finding similar companies...</p>
              </div>
            ) : similarCompanies.length > 0 ? (
              <div className="products-grid">
                {similarCompanies.map((sim, idx) => (
                  <div key={idx} className="product-card" style={{ borderTop: '4px solid #1a73e8' }}>
                     <div style={{ padding: '1rem' }}>
                       <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>{sim.company_name}</h4>
                       
                       <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                         <span style={{ 
                           backgroundColor: '#e8f0fe', 
                           color: '#1967d2', 
                           padding: '2px 8px', 
                           borderRadius: '4px', 
                           fontSize: '0.875rem', 
                           fontWeight: '500' 
                         }}>
                           {(sim.similarity * 100).toFixed(1)}% Match
                         </span>
                         {sim.segment_tag && (
                           <span style={{ 
                             backgroundColor: '#e6f4ea', 
                             color: '#137333', 
                             padding: '2px 8px', 
                             borderRadius: '4px', 
                             fontSize: '0.8rem' 
                           }}>
                             {sim.segment_tag}
                           </span>
                         )}
                       </div>

                       <button 
                         onClick={() => window.location.href = `/trade-directory/find-suppliers?search=${encodeURIComponent(sim.company_name)}`}
                         className="btn-primary"
                         style={{ width: '100%', padding: '0.5rem', fontSize: '0.9rem' }}
                       >
                         View Profile
                       </button>
                     </div>
                  </div>
                ))}
              </div>
            ) : (
                <div className="no-data">
                <p>No similar companies found based on trade patterns.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {}
      <UnlockConfirmModal
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        onConfirm={handleConfirmUnlock}
        contactName={selectedContact?.name}
        tokenCost={1}
      />

      <SuccessModal
        isOpen={showSuccessModal}
        onClose={() => setShowSuccessModal(false)}
        contactInfo={unlockedContactData || {}}
        tokensRemaining={tokenBalance}
      />

      <InsufficientTokensModal
        isOpen={showInsufficientTokensModal}
        onClose={() => setShowInsufficientTokensModal(false)}
        currentBalance={tokenBalance}
        required={1}
        onBuyTokens={handleBuyTokens}
      />

      <ErrorModal
        isOpen={showErrorModal}
        onClose={() => setShowErrorModal(false)}
        errorMessage={errorMessage}
      />
    </div>
    </>
  );
};

export default CompanyProfile;
