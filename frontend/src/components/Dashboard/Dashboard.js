
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Navbar from '../Layout/Navbar';
import './Dashboard.css';

const Dashboard = () => {
  const { user, tokenBalance } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="dashboard-wrapper">
      <Navbar />

      <div className="dashboard-container">
        { }
        <div className="hero-section">
          <h1>Welcome back, {user?.name || user?.email?.split('@')[0]}!</h1>
          <p className="hero-subtitle">
            Your gateway to Pakistan's agricultural trade intelligence
          </p>
        </div>

        {/* Stats Cards */}
        <div className="stats-grid">
          <div className="stat-card token-card">
            {/* <div className="stat-icon">💎</div> */}
            <div className="stat-content">
              <h3>{tokenBalance || 0}</h3>
              <p>Available Tokens</p>
            </div>
            <button
              onClick={() => navigate('/subscription')}
              className="stat-action"
            >
              Get More →
            </button>
          </div>

          <div className="stat-card">
            {/* <div className="stat-icon">🏭</div> */}
            <div className="stat-content">
              <h3>Discover</h3>
              <p>Verified Suppliers</p>
            </div>
            <button
              onClick={() => navigate('/trade-directory/find-suppliers')}
              className="stat-action"
            >
              Browse →
            </button>
          </div>

          <div className="stat-card">
            {/* <div className="stat-icon">🤝</div> */}
            <div className="stat-content">
              <h3>Connect</h3>
              <p>AI Partner Match</p>
            </div>
            <button
              onClick={() => navigate('/trade-intelligence/link-prediction')}
              className="stat-action"
            >
              Explore →
            </button>
          </div>
          <div className="stat-card" style={{ background: 'linear-gradient(135deg, #4f46e5, #4338ca)', color: 'white' }}>
            <div className="stat-content">
              <h3 style={{ color: 'white' }}>Search</h3>
              <p style={{ color: 'rgba(255,255,255,0.8)' }}>Unified Interface</p>
            </div>
            <button
              onClick={() => navigate('/search')}
              className="stat-action"
              style={{ color: 'white', borderColor: 'rgba(255,255,255,0.3)' }}
            >
              Try Now →
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="quick-actions-section">
          <h2>Quick Actions</h2>
          <div className="actions-grid">
            <div
              className="action-card"
              onClick={() => navigate('/trade-directory/find-suppliers')}
            >
              {/* <div className="action-icon supplier">🏭</div> */}
              <h3>Find Suppliers</h3>
              <p>Search verified agricultural suppliers across Pakistan</p>
              <span className="action-arrow">→</span>
            </div>

            <div
              className="action-card"
              onClick={() => navigate('/trade-directory/find-buyers')}
            >
              {/* <div className="action-icon buyer">🛒</div> */}
              <h3>Find Buyers</h3>
              <p>Connect with verified buyers and distributors for your produce.</p>
              <span className="action-arrow">→</span>
            </div>

            <div
              className="action-card"
              onClick={() => navigate('/trade-intelligence/ledger')}
            >
              {/* <div className="action-icon intelligence">📊</div> */}
              <h3>Trade Intelligence</h3>
              <p>Access comprehensive trade data and company analytics</p>
              <span className="action-arrow">→</span>
            </div>

            <div
              className="action-card"
              onClick={() => navigate('/subscription')}
            >
              {/* <div className="action-icon subscription">💳</div> */}
              <h3>Manage Subscription</h3>
              <p>View plans and redeem codes for more tokens</p>
              <span className="action-arrow">→</span>
            </div>

            <div
              className="action-card"
              onClick={() => navigate('/trade-intelligence/link-prediction')}
            >
              {/* <div className="action-icon" style={{background: 'linear-gradient(135deg, #8b5cf6, #6366f1)'}}>🔮</div> */}
              <h3>AI Partner Prediction</h3>
              <p>Discover potential trading partners using machine learning</p>
              <span className="action-arrow">→</span>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="features-section">
          <h2>Platform Features</h2>
          <div className="features-grid">
            <div className="feature-item">
              <span className="feature-icon">✓</span>
              <div>
                <h4>Verified Directory</h4>
                <p>Access to PAR-verified agricultural businesses</p>
              </div>
            </div>
            <div className="feature-item">
              <span className="feature-icon">✓</span>
              <div>
                <h4>Direct Contacts</h4>
                <p>Unlock key decision-maker contact information</p>
              </div>
            </div>
            <div className="feature-item">
              <span className="feature-icon">✓</span>
              <div>
                <h4>Company Profiles</h4>
                <p>Detailed profiles with products and trade data</p>
              </div>
            </div>
            <div className="feature-item">
              <span className="feature-icon">✓</span>
              <div>
                <h4>Token System</h4>
                <p>Flexible credit-based access to premium features</p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="cta-section">
          <div className="cta-content">
            <h2>Ready to grow your business?</h2>
            <p>Start exploring verified suppliers and unlock valuable contacts</p>
            <div className="cta-buttons">
              <button
                onClick={() => navigate('/trade-directory/find-suppliers')}
                className="btn-primary-cta"
              >
                Browse Directory
              </button>
              <button
                onClick={() => navigate('/subscription')}
                className="btn-secondary-cta"
              >
                View Plans
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
