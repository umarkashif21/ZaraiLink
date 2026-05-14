import React, { useState, useEffect, useRef } from 'react';
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
  const [mobileOpen, setMobileOpen] = useState(false);
  const [mobileDropdown, setMobileDropdown] = useState(null);
  const userMenuRef = useRef(null);
  const dirMenuRef = useRef(null);

  useEffect(() => {
    setMobileOpen(false);
    setMobileDropdown(null);
    setActiveDropdown(null);
  }, [location.pathname]);

  useEffect(() => {
    const onClick = (e) => {
      if (
        userMenuRef.current && !userMenuRef.current.contains(e.target) &&
        dirMenuRef.current && !dirMenuRef.current.contains(e.target)
      ) {
        setActiveDropdown(null);
      }
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

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

  const linkClass = (path) =>
    `px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive(path) ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
    }`;

  const toggleDir = () => setActiveDropdown(activeDropdown === 'directory' ? null : 'directory');
  const toggleUser = () => setActiveDropdown(activeDropdown === 'user' ? null : 'user');

  return (
    <nav className="sticky top-0 z-50 bg-slate-900 border-b border-slate-800 shadow-lg">
      <div className="max-w-[1400px] mx-auto px-3 sm:px-4 lg:px-6 h-14 sm:h-16 flex items-center justify-between gap-2">
        <Link to="/dashboard" className="flex items-center gap-2 hover:opacity-80 transition-opacity shrink-0">
          <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center font-bold text-slate-900">
            Z
          </div>
          <span className="text-lg sm:text-xl font-bold text-white tracking-tight">ZaraiLink</span>
        </Link>

        <div className="hidden md:flex items-center gap-3 lg:gap-6 ml-6 lg:ml-12 flex-1">
          <Link to="/dashboard" className={linkClass('/dashboard')}>Dashboard</Link>

          <div
            ref={dirMenuRef}
            className="relative h-16 flex items-center"
            onMouseEnter={() => setActiveDropdown('directory')}
            onMouseLeave={() => setActiveDropdown(null)}
          >
            <button
              id="tour-nav-intelligence"
              onClick={toggleDir}
              aria-haspopup="menu"
              aria-expanded={activeDropdown === 'directory'}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 ${
                isActive('/trade-directory') ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
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

          <Link id="tour-nav-subscription" to="/subscription" className={linkClass('/subscription')}>Subscription</Link>
          <Link to="/watchlist" className={linkClass('/watchlist')}>Watchlist</Link>
        </div>

        <div className="flex items-center gap-2 sm:gap-3 lg:gap-4">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="zl-icon-btn w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 hover:text-white transition-colors"
            onClick={toggleTheme}
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </motion.button>

          <div className="flex items-center px-2.5 sm:px-3 py-1 sm:py-1.5 bg-slate-800 border border-emerald-500/30 rounded-full">
            <span className="text-xs sm:text-sm font-black text-emerald-400 font-mono tracking-wider">{tokenBalance || 0}</span>
          </div>

          <div
            ref={userMenuRef}
            className="hidden md:flex relative h-16 items-center"
            onMouseEnter={() => setActiveDropdown('user')}
            onMouseLeave={() => setActiveDropdown(null)}
          >
            <button
              onClick={toggleUser}
              aria-haspopup="menu"
              aria-expanded={activeDropdown === 'user'}
              className="flex items-center gap-2 pl-2 pr-1 py-1 rounded-full hover:bg-slate-800 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-400 to-blue-500 flex items-center justify-center text-slate-900 font-bold text-sm">
                {user?.name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <span className="hidden lg:block text-sm font-medium text-slate-300 max-w-[120px] truncate">
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

          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
            aria-expanded={mobileOpen}
            className="zl-icon-btn md:hidden w-9 h-9 rounded-md bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-200 hover:text-white"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18" /></svg>
          </button>
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              className="md:hidden fixed inset-0 bg-black/60 z-40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
              aria-hidden="true"
            />
            <motion.aside
              role="dialog"
              aria-modal="true"
              aria-label="Main menu"
              className="md:hidden fixed top-0 right-0 bottom-0 z-50 w-[85%] max-w-[320px] bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col"
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'tween', duration: 0.25 }}
            >
              <div className="flex items-center justify-between px-4 h-14 border-b border-slate-800">
                <span className="text-white font-bold">Menu</span>
                <button
                  onClick={() => setMobileOpen(false)}
                  aria-label="Close menu"
                  className="zl-icon-btn w-9 h-9 rounded-md bg-slate-800 text-slate-200 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div className="px-4 py-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-400 to-blue-500 flex items-center justify-center text-slate-900 font-bold">
                    {user?.name?.charAt(0)?.toUpperCase() || 'U'}
                  </div>
                  <div className="min-w-0">
                    <div className="text-white font-semibold text-sm truncate">{user?.name || 'Guest'}</div>
                    <div className="text-slate-400 text-xs truncate">{user?.email || ''}</div>
                  </div>
                </div>
                <div className="mt-3 inline-flex items-center px-3 py-1 bg-slate-800 border border-emerald-500/30 rounded-full">
                  <span className="text-xs font-black text-emerald-400 font-mono tracking-wider">{tokenBalance || 0} tokens</span>
                </div>
              </div>

              <nav className="flex-1 overflow-y-auto px-2 py-3">
                <Link to="/dashboard" className="block px-3 py-3 rounded-lg text-sm text-slate-200 hover:bg-slate-800">Dashboard</Link>
                <button
                  className="w-full text-left px-3 py-3 rounded-lg text-sm text-slate-200 hover:bg-slate-800 flex items-center justify-between"
                  onClick={() => setMobileDropdown(mobileDropdown === 'dir' ? null : 'dir')}
                  aria-expanded={mobileDropdown === 'dir'}
                >
                  <span>Intelligence</span>
                  <span className="text-slate-500 text-xs">{mobileDropdown === 'dir' ? '▲' : '▼'}</span>
                </button>
                {mobileDropdown === 'dir' && (
                  <div className="ml-3 border-l border-slate-800 pl-3 py-1">
                    <Link to="/trade-directory/find-suppliers" className="block px-3 py-2.5 rounded text-sm text-slate-300 hover:bg-slate-800">Find Suppliers</Link>
                    <Link to="/trade-directory/find-buyers" className="block px-3 py-2.5 rounded text-sm text-slate-300 hover:bg-slate-800">Find Buyers</Link>
                  </div>
                )}
                <Link to="/subscription" className="block px-3 py-3 rounded-lg text-sm text-slate-200 hover:bg-slate-800">Subscription</Link>
                <Link to="/watchlist" className="block px-3 py-3 rounded-lg text-sm text-slate-200 hover:bg-slate-800">Watchlist</Link>
                <Link to="/profile" className="block px-3 py-3 rounded-lg text-sm text-slate-200 hover:bg-slate-800">View Profile</Link>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-3 py-3 rounded-lg text-sm text-red-400 hover:bg-red-500/10"
                >
                  Sign Out
                </button>
              </nav>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default Navbar;
