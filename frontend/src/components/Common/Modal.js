import React from 'react';
import './Modal.css';


export const Modal = ({ isOpen, onClose, children, title }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {title && (
          <div className="modal-header">
            <h2>{title}</h2>
            <button className="modal-close" onClick={onClose}>✕</button>
          </div>
        )}
        <div className="modal-body">
          {children}
        </div>
      </div>
    </div>
  );
};


export const UnlockConfirmModal = ({ isOpen, onClose, onConfirm, contactName, tokenCost }) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="unlock-confirm-modal">
        <div className="icon-container success-icon">
          <span>🔓</span>
        </div>
        <h3>Unlock Contact?</h3>
        <p>You are about to unlock contact information for:</p>
        <p className="contact-name">{contactName}</p>
        <p className="token-cost">
          <strong>{tokenCost} token</strong> will be deducted from your balance
        </p>
        <div className="modal-actions">
          <button onClick={onClose} className="btn-cancel">
            Cancel
          </button>
          <button onClick={onConfirm} className="btn-confirm">
            Unlock ({tokenCost} token)
          </button>
        </div>
      </div>
    </Modal>
  );
};


export const SuccessModal = ({ isOpen, onClose, contactInfo, tokensRemaining }) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="success-modal">
        <div className="icon-container success-icon">
          <span>✓</span>
        </div>
        <h3>Contact Unlocked Successfully!</h3>
        <p className="success-message">You now have access to the contact details</p>
        
        <div className="contact-details-box">
          <div className="detail-item">
            <span className="detail-label">Name:</span>
            <span className="detail-value">{contactInfo.name}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Designation:</span>
            <span className="detail-value">{contactInfo.designation}</span>
          </div>
          {contactInfo.phone && (
            <div className="detail-item">
              <span className="detail-label">Phone:</span>
              <span className="detail-value">{contactInfo.phone}</span>
            </div>
          )}
          {contactInfo.email && (
            <div className="detail-item">
              <span className="detail-label">Email:</span>
              <span className="detail-value">{contactInfo.email}</span>
            </div>
          )}
          {contactInfo.whatsapp && (
            <div className="detail-item">
              <span className="detail-label">WhatsApp:</span>
              <span className="detail-value">{contactInfo.whatsapp}</span>
            </div>
          )}
        </div>

        <div className="tokens-remaining">
          <span>Remaining Balance:</span>
          <strong>{tokensRemaining} tokens</strong>
        </div>

        <button onClick={onClose} className="btn-primary-modal">
          Continue
        </button>
      </div>
    </Modal>
  );
};


export const InsufficientTokensModal = ({ isOpen, onClose, currentBalance, required, onBuyTokens }) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="insufficient-tokens-modal">
        <div className="icon-container error-icon">
          <span>⚠️</span>
        </div>
        <h3>Insufficient Tokens</h3>
        <p className="error-message">You don't have enough tokens to unlock this contact</p>
        
        <div className="balance-info">
          <div className="balance-row">
            <span>Current Balance:</span>
            <strong className="balance-current">{currentBalance} tokens</strong>
          </div>
          <div className="balance-row">
            <span>Required:</span>
            <strong className="balance-required">{required} token</strong>
          </div>
        </div>

        <div className="modal-actions">
          <button onClick={onClose} className="btn-cancel">
            Cancel
          </button>
          <button onClick={onBuyTokens} className="btn-buy-tokens">
            Buy Tokens
          </button>
        </div>
      </div>
    </Modal>
  );
};

// Error Modal
export const ErrorModal = ({ isOpen, onClose, errorMessage }) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="error-modal">
        <div className="icon-container error-icon">
          <span>✕</span>
        </div>
        <h3>Operation Failed</h3>
        <p className="error-message">{errorMessage || 'An unexpected error occurred. Please try again.'}</p>
        <button onClick={onClose} className="btn-primary-modal">
          Close
        </button>
      </div>
    </Modal>
  );
};

export default Modal;
