import React from 'react';
import './EmptyState.css';


const NoDataIllustration = () => (
  <svg width="200" height="160" viewBox="0 0 200 160" fill="none" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx="100" cy="145" rx="80" ry="10" fill="var(--bg-tertiary)" />
    <rect x="50" y="30" width="100" height="100" rx="8" fill="var(--bg-tertiary)" stroke="var(--border-primary)" strokeWidth="2" />
    <rect x="65" y="50" width="70" height="8" rx="4" fill="var(--border-secondary)" />
    <rect x="65" y="68" width="50" height="8" rx="4" fill="var(--border-secondary)" />
    <rect x="65" y="86" width="60" height="8" rx="4" fill="var(--border-secondary)" />
    <circle cx="100" cy="110" r="15" fill="var(--color-primary-light)" stroke="var(--color-primary)" strokeWidth="2" />
    <path d="M95 110L98 113L105 106" stroke="var(--color-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const SearchIllustration = () => (
  <svg width="200" height="160" viewBox="0 0 200 160" fill="none" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx="100" cy="145" rx="80" ry="10" fill="var(--bg-tertiary)" />
    <circle cx="90" cy="70" r="40" fill="var(--bg-tertiary)" stroke="var(--border-primary)" strokeWidth="2" />
    <circle cx="90" cy="70" r="25" fill="var(--bg-secondary)" stroke="var(--border-secondary)" strokeWidth="2" />
    <line x1="115" y1="95" x2="140" y2="120" stroke="var(--color-primary)" strokeWidth="8" strokeLinecap="round" />
    <path d="M80 65C80 65 85 60 95 60C105 60 110 70 110 70" stroke="var(--border-secondary)" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const ErrorIllustration = () => (
  <svg width="200" height="160" viewBox="0 0 200 160" fill="none" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx="100" cy="145" rx="80" ry="10" fill="var(--bg-tertiary)" />
    <circle cx="100" cy="70" r="50" fill="var(--bg-tertiary)" stroke="var(--color-error)" strokeWidth="2" />
    <path d="M100 45V85" stroke="var(--color-error)" strokeWidth="6" strokeLinecap="round" />
    <circle cx="100" cy="100" r="4" fill="var(--color-error)" />
  </svg>
);

const CompanyIllustration = () => (
  <svg width="200" height="160" viewBox="0 0 200 160" fill="none" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx="100" cy="145" rx="80" ry="10" fill="var(--bg-tertiary)" />
    <rect x="60" y="50" width="80" height="80" rx="4" fill="var(--bg-tertiary)" stroke="var(--border-primary)" strokeWidth="2" />
    <rect x="75" y="65" width="20" height="20" rx="2" fill="var(--color-primary-light)" stroke="var(--color-primary)" strokeWidth="2" />
    <rect x="105" y="65" width="20" height="20" rx="2" fill="var(--color-primary-light)" stroke="var(--color-primary)" strokeWidth="2" />
    <rect x="75" y="95" width="20" height="20" rx="2" fill="var(--color-primary-light)" stroke="var(--color-primary)" strokeWidth="2" />
    <rect x="105" y="95" width="20" height="20" rx="2" fill="var(--color-primary-light)" stroke="var(--color-primary)" strokeWidth="2" />
    <path d="M100 30L130 50H70L100 30Z" fill="var(--color-primary)" />
  </svg>
);

const WatchlistIllustration = () => (
  <svg width="200" height="160" viewBox="0 0 200 160" fill="none" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx="100" cy="145" rx="80" ry="10" fill="var(--bg-tertiary)" />
    <path d="M100 35L115 65H145L120 85L130 115L100 95L70 115L80 85L55 65H85L100 35Z" fill="var(--color-warning)" stroke="var(--color-warning)" strokeWidth="2" />
  </svg>
);


const illustrations = {
  'no-data': NoDataIllustration,
  'search': SearchIllustration,
  'error': ErrorIllustration,
  'company': CompanyIllustration,
  'watchlist': WatchlistIllustration,
};

const EmptyState = ({
  type = 'no-data',
  title = 'No data found',
  description = 'There is no data to display at the moment.',
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  className = '',
}) => {
  const Illustration = illustrations[type] || illustrations['no-data'];

  return (
    <div className={`empty-state ${className}`}>
      <div className="empty-state-illustration">
        <Illustration />
      </div>
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-description">{description}</p>
      {(actionLabel || secondaryActionLabel) && (
        <div className="empty-state-actions">
          {actionLabel && (
            <button 
              className="empty-state-button primary" 
              onClick={onAction}
            >
              {actionLabel}
            </button>
          )}
          {secondaryActionLabel && (
            <button 
              className="empty-state-button secondary" 
              onClick={onSecondaryAction}
            >
              {secondaryActionLabel}
            </button>
          )}
        </div>
      )}
    </div>
  );
};


export const NoCompaniesFound = ({ onReset }) => (
  <EmptyState
    type="company"
    title="No companies found"
    description="We couldn't find any companies matching your search criteria. Try adjusting your filters or search terms."
    actionLabel="Clear Filters"
    onAction={onReset}
  />
);

export const NoSearchResults = ({ query, onReset }) => (
  <EmptyState
    type="search"
    title="No results found"
    description={`No results found for "${query}". Try a different search term or check your spelling.`}
    actionLabel="Clear Search"
    onAction={onReset}
  />
);

export const ErrorState = ({ message, onRetry }) => (
  <EmptyState
    type="error"
    title="Something went wrong"
    description={message || "An unexpected error occurred. Please try again later."}
    actionLabel="Try Again"
    onAction={onRetry}
  />
);

export const EmptyWatchlist = ({ onExplore }) => (
  <EmptyState
    type="watchlist"
    title="Your watchlist is empty"
    description="Save companies to your watchlist for quick access. Start exploring to find companies you're interested in."
    actionLabel="Explore Companies"
    onAction={onExplore}
  />
);

export const NoTradeData = ({ onExplore }) => (
  <EmptyState
    type="no-data"
    title="No trade data available"
    description="There is no trade data for the selected criteria. Try adjusting your date range or filters."
    actionLabel="Adjust Filters"
    onAction={onExplore}
  />
);

export default EmptyState;
