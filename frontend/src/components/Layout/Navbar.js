import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { motion, AnimatePresence } from 'framer-motion';
import './Navbar.css';

const Navbar = () => {
  const { user, tokenBalance, logout } = useAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  
  const [activeDropdown, setActiveDropdown] = useState(null);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path);
  };

  const dropdownVariants = {
    hidden: { opacity: 0, y: -10, scale: 0.95 },
    visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.2, ease: "easeOut" } },
    exit: { opacity: 0, y: -10, scale: 0.95, transition: { duration: 0.15, ease: "easeIn" } }
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {}
        <Link to="/dashboard" className="navbar-logo">
          {/* <span className="logo-icon">🌾</span> */}
          <span className="logo-text">ZaraiLink</span>
        </Link>

        {}
        <div className="navbar-menu">
          <Link 
            to="/dashboard" 
            className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
          >
            Home
          </Link>
          
          {}
          <div 
            className="nav-dropdown"
            onMouseEnter={() => setActiveDropdown('directory')}
            onMouseLeave={() => setActiveDropdown(null)}
          >
            <button className={`nav-link dropdown-toggle ${isActive('/trade-directory') ? 'active' : ''}`}>
              Trade Directory ▼
            </button>
            <AnimatePresence>
              {activeDropdown === 'directory' && (
                <motion.div 
                  className="dropdown-content"
                  variants={dropdownVariants}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                >
                  <Link to="/trade-directory/find-suppliers">Find Suppliers</Link>
                  <Link to="/trade-directory/find-buyers">Find Buyers</Link>
                </motion.div>
              )}
            </AnimatePresence>
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

        {}
        <div className="navbar-right">
          {}
          <motion.button 
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="theme-toggle" 
            onClick={toggleTheme}
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </motion.button>

          {}
          <div className="token-display">
            {/* <span className="token-icon">💎</span> */}
            <span className="token-count">{tokenBalance || 0}</span>
          </div>

          {}
          <div 
            className="user-menu"
            onMouseEnter={() => setActiveDropdown('user')}
            onMouseLeave={() => setActiveDropdown(null)}
          >
            <button className="user-button">
              <div className="user-avatar">
                {user?.name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <span className="user-name">{user?.name || user?.email}</span>
              <span className="dropdown-arrow">▼</span>
            </button>
            <AnimatePresence>
              {activeDropdown === 'user' && (
                <motion.div 
                  className="user-dropdown"
                  variants={dropdownVariants}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                >
                  <div className="user-info">
                    <strong>{user?.name || 'User'}</strong>
                    <span>{user?.email}</span>
                  </div>
                  <hr />
                  <button onClick={handleLogout} className="logout-button">
                    {/* <span>🚪</span> */} Sign Out
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

