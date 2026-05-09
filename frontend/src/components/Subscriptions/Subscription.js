import React, { useState, useEffect } from 'react';


import { useAuth } from '../../context/AuthContext';
import Navbar from '../Layout/Navbar';
import './Subscription.css';

const Subscription = () => {
  const { tokenBalance, refreshUser, isAuthenticated } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [redeeming, setRedeeming] = useState(false);

  const [billingCycle, setBillingCycle] = useState('monthly');

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/api/subscriptions/plans/`);
      if (response.ok) {
        const data = await response.json();
        setPlans(data);
      }
    } catch (error) {
      console.error('Failed to load plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRedeemClick = async (plan) => {
    if (!isAuthenticated) {
      alert('Please log in to redeem a subscription plan.');
      return;
    }
    setRedeeming(true);
    try {
      const csrftoken = getCookie('csrftoken');
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/api/subscriptions/redeem/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
        },
        credentials: 'include',
        body: JSON.stringify({ 
          plan_id: plan.id  
        }),
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        alert(`Success! ${data.tokens_added} tokens added. New balance: ${data.new_balance}`);
        await refreshUser(); 
      } else {
        alert(data.message || data.detail || 'Failed to redeem plan');
      }
    } catch (error) {
      alert('Network error. Please try again.');
    } finally {
      setRedeeming(false);
    }
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

  const filteredPlans = plans.filter(plan => {
    const name = plan.plan_name.toLowerCase();
    const description = plan.description ? plan.description.toLowerCase() : '';
    const isAnnual = name.includes('annually') || name.includes('yearly') || description.includes('annual');
    
    if (billingCycle === 'monthly') {
      return !isAnnual;
    } else {
      return isAnnual;
    }
  });

  if (loading) {
    return (
      <div className="subscription-container">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading subscription plans...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Navbar />
      <div className="subscription-container">
      <div className="header">
        <h1>Subscription Plans</h1>
        <div className="token-badge">
          {/* <span className="token-icon">💎</span> */}
          <span className="token-count">{tokenBalance}</span>
          <span className="token-label">tokens</span>
        </div>
      </div>

      <div className="subscription-controls">
        <p className="subtitle">Choose a plan and redeem your code to get started</p>
        
        <div className="billing-toggle">
          <button 
            className={`toggle-btn ${billingCycle === 'monthly' ? 'active' : ''}`}
            onClick={() => setBillingCycle('monthly')}
          >
            Monthly
          </button>
          <button 
            className={`toggle-btn ${billingCycle === 'annual' ? 'active' : ''}`}
            onClick={() => setBillingCycle('annual')}
          >
            Annually
          </button>
        </div>
      </div>

      <div className="plans-grid">
        {filteredPlans.map((plan) => (
          <div key={plan.id} className="plan-card">
            <div className="plan-header">
              <h3>{plan.plan_name}</h3>
              {plan.plan_name.toLowerCase().includes('popular') && (
                <span className="popular-badge">Popular</span>
              )}
            </div>

            <div className="plan-tokens">
              <span className="tokens-value">{plan.tokens_included.toLocaleString()}</span>
              <span className="tokens-label">credits</span>
              <span className="billing-cycle">per {billingCycle === 'monthly' ? 'month' : 'year'}</span>
            </div>

            {plan.description && (
              <p className="plan-description">{plan.description}</p>
            )}

            {plan.features && Object.keys(plan.features).length > 0 && (
              <ul className="features-list">
                {Object.entries(plan.features).map(([key, value]) => (
                  <li key={key}>
                    {/* ✓ */} {typeof value === 'boolean' && value ? key.replace(/_/g, ' ') : value}
                  </li>
                ))}
              </ul>
            )}

            <button
              onClick={() => handleRedeemClick(plan)}
              className="btn-redeem"
              disabled={redeeming}
            >
              Get Plan
            </button>
          </div>
        ))}
      </div>

      {plans.length === 0 && (
        <div className="no-plans">
          <p>No subscription plans available at the moment.</p>
        </div>
      )}

      {}

    </div>
    </>
  );
};

export default Subscription;
