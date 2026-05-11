import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { motion, AnimatePresence } from 'framer-motion';

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
    <nav className="sticky top-0 z-50 bg-slate-900 border-b border-slate-800 shadow-lg">
      <div className="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/dashboard" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center font-bold text-slate-900">
            Z
          </div>
          <span className="text-xl font-bold text-white tracking-tight">ZaraiLink</span>
        </Link>

        <div className="hidden md:flex items-center gap-6 ml-12 flex-1">
          <Link 
            to="/dashboard" 
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive('/dashboard') ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Dashboard
          </Link>
          
          <div
            className="relative h-16 flex items-center"
            onMouseEnter={() => setActiveDropdown('directory')}
            onMouseLeave={() => setActiveDropdown(null)}
          >
            <button id="tour-nav-intelligence" className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 ${
              isActive('/trade-directory') ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}>
              Intelligence ▼
            </button>
            <AnimatePresence>
              {activeDropdown === 'directory' && (
                <motion.div 
                  className="absolute top-full left-0 mt-1 w-56 bg-white rounded-xl shadow-2xl border border-slate-200 py-2 overflow-hidden"
                  variants={dropdownVariants}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                >
                  <Link to="/trade-directory/find-suppliers" className="block px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 hover:text-emerald-600 transition-colors">
                    Find Suppliers
                  </Link>
                  <Link to="/trade-directory/find-buyers" className="block px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 hover:text-emerald-600 transition-colors">
                    Find Buyers
                  </Link>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <Link 
            id="tour-nav-subscription"
            to="/subscription" 
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive('/subscription') ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Subscription
          </Link>
          
          <Link 
            to="/watchlist" 
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive('/watchlist') ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Watchlist
          </Link>
        </div>

        <div className="flex items-center gap-4">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 hover:text-white transition-colors"
            onClick={toggleTheme}
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </motion.button>

          <div className="hidden sm:flex items-center px-3 py-1.5 bg-slate-800 border border-emerald-500/30 rounded-full">
            <span className="text-sm font-black text-emerald-400 font-mono tracking-wider">{tokenBalance || 0}</span>
          </div>

          <div
            className="relative h-16 flex items-center"
            onMouseEnter={() => setActiveDropdown('user')}
            onMouseLeave={() => setActiveDropdown(null)}
          >
            <button className="flex items-center gap-2 pl-2 pr-1 py-1 rounded-full hover:bg-slate-800 transition-colors">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-400 to-blue-500 flex items-center justify-center text-slate-900 font-bold text-sm">
                {user?.name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <span className="hidden sm:block text-sm font-medium text-slate-300 max-w-[120px] truncate">
                {user?.name || user?.email}
              </span>
              <span className="text-slate-500 text-xs">▼</span>
            </button>
            <AnimatePresence>
              {activeDropdown === 'user' && (
                <motion.div 
                  className="absolute top-full right-0 mt-1 w-64 bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden"
                  variants={dropdownVariants}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                >
                  <div className="px-4 py-4 bg-slate-50 border-b border-slate-100">
                    <div className="font-bold text-slate-900 text-sm truncate">{user?.name || 'User'}</div>
                    <div className="text-slate-500 text-xs truncate mt-0.5">{user?.email}</div>
                  </div>
                  <div className="py-2">
                    <Link 
                      to="/profile" 
                      onClick={() => setActiveDropdown(null)}
                      className="block px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 hover:text-emerald-600 transition-colors"
                    >
                      View Profile
                    </Link>
                    <button 
                      onClick={handleLogout} 
                      className="w-full px-4 py-2 text-left text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
                    >
                      Sign Out
                    </button>
                  </div>
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
