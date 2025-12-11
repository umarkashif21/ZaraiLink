import React from 'react';
import './WatchlistButton.css';

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

export default WatchlistButton;
