
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';


const EmptyState = ({ 
  title = 'No results found',
  message = 'Try adjusting your search or filters.',
  icon = '📭',
  actionLabel,
  onAction,
  type = 'default'
}) => {
  return (
    <div className={`empty-state empty-state-${type}`} data-testid="empty-state">
      <div className="empty-state-icon">{icon}</div>
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-message">{message}</p>
      {actionLabel && onAction && (
        <button 
          className="empty-state-action" 
          onClick={onAction}
          data-testid="empty-state-action"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};

describe('EmptyState Component', () => {
  test('renders with default props', () => {
    render(<EmptyState />);
    
    expect(screen.getByText('No results found')).toBeInTheDocument();
    expect(screen.getByText('Try adjusting your search or filters.')).toBeInTheDocument();
    expect(screen.getByText('📭')).toBeInTheDocument();
  });

  test('renders with custom title and message', () => {
    render(
      <EmptyState 
        title="No companies available" 
        message="Check back later for updates."
      />
    );
    
    expect(screen.getByText('No companies available')).toBeInTheDocument();
    expect(screen.getByText('Check back later for updates.')).toBeInTheDocument();
  });

  test('renders with custom icon', () => {
    render(<EmptyState icon="🔍" />);
    
    expect(screen.getByText('🔍')).toBeInTheDocument();
  });

  test('renders action button when actionLabel and onAction provided', () => {
    const onAction = jest.fn();
    render(
      <EmptyState 
        actionLabel="Retry" 
        onAction={onAction}
      />
    );
    
    const button = screen.getByTestId('empty-state-action');
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('Retry');
  });

  test('calls onAction when action button clicked', () => {
    const onAction = jest.fn();
    render(
      <EmptyState 
        actionLabel="Try Again" 
        onAction={onAction}
      />
    );
    
    fireEvent.click(screen.getByTestId('empty-state-action'));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  test('does not render action button when actionLabel is missing', () => {
    render(<EmptyState onAction={() => {}} />);
    
    expect(screen.queryByTestId('empty-state-action')).not.toBeInTheDocument();
  });

  test('applies type class correctly', () => {
    render(<EmptyState type="search" />);
    
    expect(screen.getByTestId('empty-state')).toHaveClass('empty-state-search');
  });
});
