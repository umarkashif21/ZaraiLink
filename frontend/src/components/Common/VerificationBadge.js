import React from 'react';
import './VerificationBadge.css';

const VerificationBadge = ({ 
  status = 'unverified',
  size = 'normal',
  showLabel = true,
  className = '' 
}) => {
  const badges = {
    verified: {
      icon: '',
      label: 'Verified',
      className: 'verified',
    },
    premium: {
      icon: '',
      label: 'Premium Partner',
      className: 'premium',
    },
    top_trader: {
      icon: '',
      label: 'Top Trader',
      className: 'top-trader',
    },
    pending: {
      icon: '',
      label: 'Pending',
      className: 'pending',
    },
    unverified: {
      icon: '',
      label: 'Unverified',
      className: 'unverified',
    },
  };

  const badge = badges[status] || badges.unverified;

  return (
    <span 
      className={`verification-badge ${badge.className} ${size} ${className}`}
      title={badge.label}
    >
      <span className="badge-icon">{badge.icon}</span>
      {showLabel && <span className="badge-label">{badge.label}</span>}
    </span>
  );
};


export const VerificationBadges = ({ 
  verificationStatus, 
  isTopTrader = false,
  size = 'small',
  className = '' 
}) => {
  const badges = [];
  
  if (verificationStatus === 'premium') {
    badges.push(<VerificationBadge key="premium" status="premium" size={size} showLabel={false} />);
  } else if (verificationStatus === 'verified') {
    badges.push(<VerificationBadge key="verified" status="verified" size={size} showLabel={false} />);
  }
  
  if (isTopTrader) {
    badges.push(<VerificationBadge key="top" status="top_trader" size={size} showLabel={false} />);
  }
  
  if (badges.length === 0) return null;
  
  return (
    <div className={`verification-badges-container ${className}`}>
      {badges}
    </div>
  );
};

export default VerificationBadge;
