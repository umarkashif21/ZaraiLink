
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';


const VerificationBadge = ({ status = 'unverified', size = 'normal' }) => {
  const statusConfig = {
    verified: {
      icon: '✓',
      label: 'Verified',
      className: 'verified'
    },
    pending: {
      icon: '⏳',
      label: 'Pending',
      className: 'pending'
    },
    unverified: {
      icon: '○',
      label: 'Unverified',
      className: 'unverified'
    }
  };

  const config = statusConfig[status] || statusConfig.unverified;

  return (
    <span 
      className={`verification-badge ${config.className} ${size}`}
      data-testid="verification-badge"
      title={config.label}
    >
      <span className="badge-icon">{config.icon}</span>
      <span className="badge-label">{config.label}</span>
    </span>
  );
};

describe('VerificationBadge Component', () => {
  test('renders with default unverified status', () => {
    render(<VerificationBadge />);
    
    expect(screen.getByText('Unverified')).toBeInTheDocument();
    expect(screen.getByText('○')).toBeInTheDocument();
  });

  test('renders verified status correctly', () => {
    render(<VerificationBadge status="verified" />);
    
    expect(screen.getByText('Verified')).toBeInTheDocument();
    expect(screen.getByText('✓')).toBeInTheDocument();
    expect(screen.getByTestId('verification-badge')).toHaveClass('verified');
  });

  test('renders pending status correctly', () => {
    render(<VerificationBadge status="pending" />);
    
    expect(screen.getByText('Pending')).toBeInTheDocument();
    expect(screen.getByText('⏳')).toBeInTheDocument();
    expect(screen.getByTestId('verification-badge')).toHaveClass('pending');
  });

  test('renders unverified status correctly', () => {
    render(<VerificationBadge status="unverified" />);
    
    expect(screen.getByText('Unverified')).toBeInTheDocument();
    expect(screen.getByTestId('verification-badge')).toHaveClass('unverified');
  });

  test('applies size class', () => {
    render(<VerificationBadge size="small" />);
    
    expect(screen.getByTestId('verification-badge')).toHaveClass('small');
  });

  test('has correct title attribute', () => {
    render(<VerificationBadge status="verified" />);
    
    expect(screen.getByTestId('verification-badge')).toHaveAttribute('title', 'Verified');
  });

  test('handles unknown status gracefully', () => {
    render(<VerificationBadge status="unknown" />);
    
    expect(screen.getByText('Unverified')).toBeInTheDocument();
  });
});
