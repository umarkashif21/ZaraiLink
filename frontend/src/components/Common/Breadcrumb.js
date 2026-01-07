import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Breadcrumb.css';


const routeLabels = {
  'dashboard': 'Home',
  'trade-directory': 'Trade Directory',
  'trade-intelligence': 'Trade Intelligence',
  'find-suppliers': 'Find Suppliers',
  'find-buyers': 'Find Buyers',
  'company': 'Company',
  'subscription': 'Subscription',
  'ledger': 'Trade Ledger',
  'pulse': 'Trade Pulse',
  'lens': 'Trade Lens',
  'link-prediction': 'Link Prediction',
  'overview': 'Overview',
  'products': 'Products',
  'partners': 'Partners',
  'trends': 'Trends',
  'watchlist': 'Watchlist',
  'analytics': 'Analytics',
  'statistics': 'Statistics',
};

const Breadcrumb = ({ customItems, className = '' }) => {
  const location = useLocation();
  
  
  const generateBreadcrumbs = () => {
    const pathnames = location.pathname.split('/').filter(x => x);
    
    return pathnames.map((value, index) => {
      const to = `/${pathnames.slice(0, index + 1).join('/')}`;
      const isLast = index === pathnames.length - 1;
      
      
      let label = routeLabels[value] || value
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      
      
      if (/^\d+$/.test(value) || value.length > 20) {
        label = 'Details';
      }
      
      return {
        label,
        path: to,
        isLast,
      };
    });
  };

  const items = customItems || generateBreadcrumbs();

  
  if (items.length <= 1) {
    return null;
  }

  return (
    <nav className={`breadcrumb ${className}`} aria-label="Breadcrumb">
      <ol className="breadcrumb-list">
        <li className="breadcrumb-item">
          <Link to="/dashboard" className="breadcrumb-link">
            {/* <span className="breadcrumb-icon">🏠</span> */}
            <span className="breadcrumb-home-text">Home</span>
          </Link>
        </li>
        {items.map((item, index) => (
          <li key={index} className="breadcrumb-item">
            <span className="breadcrumb-separator">›</span>
            {item.isLast ? (
              <span className="breadcrumb-current" aria-current="page">
                {item.label}
              </span>
            ) : (
              <Link to={item.path} className="breadcrumb-link">
                {item.label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
};


export const BreadcrumbWithContext = ({ 
  context, 
  currentPage,
  className = '' 
}) => {
  const items = [
    ...context.map(item => ({ ...item, isLast: false })),
    { label: currentPage, path: '', isLast: true }
  ];
  
  return <Breadcrumb customItems={items} className={className} />;
};

export default Breadcrumb;
