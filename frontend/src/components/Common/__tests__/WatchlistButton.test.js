

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';


const WatchlistButton = ({ 
  isWatched, 
  onToggle, 
  size = 'normal',
  showLabel = true,
  className = '' 
}) => {
  return (
    <button
      className={`watchlist-button ${isWatched ? 'watched' : ''} ${size} ${className}`}
      onClick={(e) => {
        e.stopPropagation();
        onToggle();
      }}
      aria-label={isWatched ? 'Remove from watchlist' : 'Add to watchlist'}
      title={isWatched ? 'Remove from watchlist' : 'Add to watchlist'}
      data-testid="watchlist-button"
    >
      <span className="watchlist-icon">
        {isWatched ? '★' : '☆'}
      </span>
      {showLabel && (
        <span className="watchlist-label">
          {isWatched ? 'Watching' : 'Watch'}
        </span>
      )}
    </button>
  );
};

describe('WatchlistButton Component', () => {
  test('renders with "Watch" label when not watched', () => {
    render(<WatchlistButton isWatched={false} onToggle={() => {}} />);
    
    expect(screen.getByText('Watch')).toBeInTheDocument();
    expect(screen.getByText('☆')).toBeInTheDocument();
  });

  test('renders with "Watching" label when watched', () => {
    render(<WatchlistButton isWatched={true} onToggle={() => {}} />);
    
    expect(screen.getByText('Watching')).toBeInTheDocument();
    expect(screen.getByText('★')).toBeInTheDocument();
  });

  test('calls onToggle when clicked', () => {
    const onToggle = jest.fn();
    render(<WatchlistButton isWatched={false} onToggle={onToggle} />);
    
    fireEvent.click(screen.getByTestId('watchlist-button'));
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  test('does not show label when showLabel is false', () => {
    render(<WatchlistButton isWatched={false} onToggle={() => {}} showLabel={false} />);
    
    expect(screen.queryByText('Watch')).not.toBeInTheDocument();
  });

  test('has correct aria-label for accessibility', () => {
    const { rerender } = render(<WatchlistButton isWatched={false} onToggle={() => {}} />);
    
    expect(screen.getByTestId('watchlist-button')).toHaveAttribute(
      'aria-label', 
      'Add to watchlist'
    );

    rerender(<WatchlistButton isWatched={true} onToggle={() => {}} />);
    expect(screen.getByTestId('watchlist-button')).toHaveAttribute(
      'aria-label', 
      'Remove from watchlist'
    );
  });

  test('applies custom className', () => {
    render(<WatchlistButton isWatched={false} onToggle={() => {}} className="custom-class" />);
    
    expect(screen.getByTestId('watchlist-button')).toHaveClass('custom-class');
  });
});
