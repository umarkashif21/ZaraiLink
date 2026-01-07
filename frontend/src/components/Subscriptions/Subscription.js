import React, { useState, useEffect } from 'react';


import { useAuth } from '../../context/AuthContext';
import { Modal } from '../Common/Modal';
import Navbar from '../Layout/Navbar';
import './Subscription.css';

const Subscription = () => {
  const { tokenBalance, refreshUser } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  
  
  const [showRedeemModal, setShowRedeemModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [redeemCode, setRedeemCode] = useState('');
  const [redeeming, setRedeeming] = useState(false);
  const [redeemMessage, setRedeemMessage] = useState({ type: '', text: '' });

  const [billingCycle, setBillingCycle] = useState('monthly');

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/subscriptions/plans/');
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

  const handleRedeemClick = (plan) => {
    setSelectedPlan(plan);
    setShowRedeemModal(true);
    setRedeemCode('');
    setRedeemMessage({ type: '', text: '' });
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

  const handleRedeem = async () => {
    if (!redeemCode.trim()) {
      setRedeemMessage({ type: 'error', text: 'Please enter a redeem code' });
      return;
    }

    setRedeeming(true);
    setRedeemMessage({ type: '', text: '' });

    try {
      const csrftoken = getCookie('csrftoken');
      const response = await fetch('http://localhost:8000/api/subscriptions/redeem/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
        },
        credentials: 'include',
        body: JSON.stringify({ 
          code: redeemCode.trim(),
          plan_id: selectedPlan?.id  
        }),
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        setRedeemMessage({
          type: 'success',
          text: `${data.tokens_added} tokens added! New balance: ${data.new_balance}`
        });
        await refreshUser(); 
        
        
        setTimeout(() => {
          setShowRedeemModal(false);
        }, 2000);
      } else {
        setRedeemMessage({
          type: 'error',
          text: data.message || 'Failed to redeem code'
        });
      }
    } catch (error) {
      setRedeemMessage({
        type: 'error',
        text: 'Network error. Please try again.'
      });
    } finally {
      setRedeeming(false);
    }
  };

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
            >
              Redeem Code
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
      <Modal
        isOpen={showRedeemModal}
        onClose={() => setShowRedeemModal(false)}
        title={`Redeem ${selectedPlan?.plan_name || 'Code'}`}
      >
        <div className="redeem-modal-content">
          <p className="redeem-instructions">
            Enter your redemption code to activate your subscription
          </p>

          <input
            type="text"
            value={redeemCode}
            onChange={(e) => setRedeemCode(e.target.value.toUpperCase())}
            placeholder="ENTER-CODE-HERE"
            className="redeem-input"
            maxLength={16}
            disabled={redeeming}
            onKeyPress={(e) => e.key === 'Enter' && handleRedeem()}
          />

          {redeemMessage.text && (
            <div className={`redeem-message ${redeemMessage.type}`}>
              {redeemMessage.text}
            </div>
          )}

          <div className="modal-actions">
            <button
              onClick={() => setShowRedeemModal(false)}
              className="btn-cancel"
              disabled={redeeming}
            >
              Cancel
            </button>
            <button
              onClick={handleRedeem}
              className="btn-confirm"
              disabled={redeeming || !redeemCode.trim()}
            >
              {redeeming ? 'Redeeming...' : 'Redeem'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
    </>
  );
};

export default Subscription;
