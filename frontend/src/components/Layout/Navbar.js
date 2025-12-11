import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import './Navbar.css';

const Navbar = () => {
  const { user, tokenBalance, logout } = useAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path);
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo */}
        <Link to="/dashboard" className="navbar-logo">
          <span className="logo-icon">🌾</span>
          <span className="logo-text">ZaraiLink</span>
        </Link>

        {/* Navigation Links */}
        <div className="navbar-menu">
          <Link 
            to="/dashboard" 
            className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
          >
            Home
          </Link>
          
          <div className="nav-dropdown">
            <button className={`nav-link dropdown-toggle ${isActive('/trade-directory') ? 'active' : ''}`}>
              Trade Directory ▼
            </button>
            <div className="dropdown-content">
              <Link to="/trade-directory/find-suppliers">Find Suppliers</Link>
              <Link to="/trade-directory/find-buyers">Find Buyers</Link>
            </div>
          </div>

          <div className="nav-dropdown">
            <button className={`nav-link dropdown-toggle ${isActive('/trade-intelligence') ? 'active' : ''}`}>
              Trade Intelligence ▼
            </button>
            <div className="dropdown-content">
              <Link to="/trade-intelligence/ledger">Trade Ledger</Link>
              <Link to="/trade-intelligence/pulse">Trade Pulse</Link>
              <Link to="/trade-intelligence/lens">Trade Lens</Link>
            </div>
          </div>

          <Link 
            to="/subscription" 
            className={`nav-link ${isActive('/subscription') ? 'active' : ''}`}
          >
            Subscription
          </Link>
          
          <Link 
            to="/watchlist" 
            className={`nav-link ${isActive('/watchlist') ? 'active' : ''}`}
          >
            ⭐ Watchlist
          </Link>
        </div>

        {/* Right Section */}
        <div className="navbar-right">
          {/* Theme Toggle */}
          <button 
            className="theme-toggle" 
            onClick={toggleTheme}
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>

          {/* Token Balance */}
          <div className="token-display">
            <span className="token-icon">💎</span>
            <span className="token-count">{tokenBalance || 0}</span>
          </div>

          {/* User Menu */}
          <div className="user-menu">
            <button className="user-button">
              <div className="user-avatar">
                {user?.name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <span className="user-name">{user?.name || user?.email}</span>
              <span className="dropdown-arrow">▼</span>
            </button>
            <div className="user-dropdown">
              <div className="user-info">
                <strong>{user?.name || 'User'}</strong>
                <span>{user?.email}</span>
              </div>
              <hr />
              <button onClick={handleLogout} className="logout-button">
                <span>🚪</span> Sign Out
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

