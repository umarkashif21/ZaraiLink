import React from 'react';
import './Skeleton.css';


export const Skeleton = ({ 
  width, 
  height, 
  borderRadius,
  className = '',
  style = {} 
}) => {
  return (
    <div 
      className={`skeleton ${className}`}
      style={{
        width: width || '100%',
        height: height || '1rem',
        borderRadius: borderRadius || '4px',
        ...style
      }}
    />
  );
};


export const SkeletonText = ({ 
  lines = 3, 
  size = 'normal',
  className = '' 
}) => {
  return (
    <div className={className}>
      {Array.from({ length: lines }).map((_, i) => (
        <div 
          key={i}
          className={`skeleton skeleton-text ${size}`}
          style={{ width: i === lines - 1 ? '70%' : '100%' }}
        />
      ))}
    </div>
  );
};


export const SkeletonAvatar = ({ size = 'normal' }) => {
  return <div className={`skeleton skeleton-avatar ${size}`} />;
};


export const SkeletonButton = ({ width }) => {
  return (
    <div 
      className="skeleton skeleton-button"
      style={{ width: width || '120px' }}
    />
  );
};


export const SkeletonImage = ({ height, variant = 'default' }) => {
  return (
    <div 
      className={`skeleton skeleton-image ${variant}`}
      style={{ height: height || '200px' }}
    />
  );
};


export const SkeletonCard = ({ showImage = false, lines = 3 }) => {
  return (
    <div className="skeleton-card">
      {showImage && <SkeletonImage height="150px" />}
      <div className="skeleton-card-header" style={{ marginTop: showImage ? '1rem' : 0 }}>
        <SkeletonAvatar />
        <div style={{ flex: 1 }}>
          <Skeleton height="1.25rem" width="60%" style={{ marginBottom: '0.5rem' }} />
          <Skeleton height="0.875rem" width="40%" />
        </div>
      </div>
      <div className="skeleton-card-body">
        <SkeletonText lines={lines} />
      </div>
    </div>
  );
};


export const SkeletonTableRow = ({ columns = 4 }) => {
  return (
    <div className="skeleton-table-row">
      {Array.from({ length: columns }).map((_, i) => (
        <div 
          key={i}
          className={`skeleton skeleton-table-cell ${i === 0 ? 'large' : ''}`}
        />
      ))}
    </div>
  );
};


export const SkeletonTable = ({ rows = 5, columns = 4 }) => {
  return (
    <div className="skeleton-table">
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonTableRow key={i} columns={columns} />
      ))}
    </div>
  );
};


export const SkeletonStat = () => {
  return (
    <div className="skeleton-stat">
      <div className="skeleton skeleton-stat-value" />
      <div className="skeleton skeleton-stat-label" />
    </div>
  );
};


export const SkeletonStats = ({ count = 4 }) => {
  return (
    <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonStat key={i} />
      ))}
    </div>
  );
};


export const SkeletonCardGrid = ({ count = 6, showImage = false }) => {
  return (
    <div className="skeleton-grid">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} showImage={showImage} />
      ))}
    </div>
  );
};


export const SkeletonCompanyCard = () => {
  return (
    <div className="skeleton-card">
      <div className="skeleton-card-header">
        <SkeletonAvatar size="large" />
        <div style={{ flex: 1 }}>
          <Skeleton height="1.25rem" width="70%" style={{ marginBottom: '0.5rem' }} />
          <Skeleton height="0.875rem" width="50%" />
        </div>
      </div>
      <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
        <SkeletonStat />
        <SkeletonStat />
      </div>
      <div style={{ marginTop: '1rem' }}>
        <SkeletonText lines={2} />
      </div>
      <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
        <SkeletonButton width="100px" />
        <SkeletonButton width="100px" />
      </div>
    </div>
  );
};


export const SkeletonPage = () => {
  return (
    <div style={{ padding: '2rem' }}>
      <Skeleton height="2rem" width="300px" style={{ marginBottom: '2rem' }} />
      <SkeletonStats count={4} />
      <div style={{ marginTop: '2rem' }}>
        <Skeleton height="1.5rem" width="200px" style={{ marginBottom: '1rem' }} />
        <SkeletonCardGrid count={6} />
      </div>
    </div>
  );
};

export default Skeleton;
