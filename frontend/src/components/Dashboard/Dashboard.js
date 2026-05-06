import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, X, ChevronRight, Hash, Package, Zap, Info, Layers, ArrowRight, TrendingUp, Globe, Users, BarChart2, Building2, Phone } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Navbar from '../Layout/Navbar';
import { motion, AnimatePresence, useInView } from 'framer-motion';
import Shepherd from 'shepherd.js';
import 'shepherd.js/dist/css/shepherd.css';

const API_BASE = process.env.REACT_APP_API_BASE_URL;

// ── Animated counter ──────────────────────────────────────────────────────────
const AnimatedCounter = ({ end, suffix = '', duration = 2 }) => {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (!inView) return;
    let startTime = null;
    const step = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / (duration * 1000), 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setCount(Math.floor(eased * end));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [inView, end, duration]);

  return <span ref={ref}>{count.toLocaleString()}{suffix}</span>;
};

// ── Floating orb background ────────────────────────────────────────────────────
const FloatingOrb = ({ className }) => (
  <motion.div
    className={`absolute rounded-full blur-3xl opacity-20 pointer-events-none ${className}`}
    animate={{ y: [0, -20, 0], scale: [1, 1.05, 1] }}
    transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
  />
);

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [query, setQuery] = useState('');
  const [scope, setScope] = useState(null);

  // Shepherd.js Tour Logic
  useEffect(() => {
    // Check if tour has already been shown
    if (localStorage.getItem('zarailink_tour_done')) return;

    // Delay to ensure the DOM elements are fully mounted
    const tourTimer = setTimeout(() => {
      const tour = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
          classes: 'custom-shepherd-theme',
          scrollTo: { behavior: 'smooth', block: 'center' },
          cancelIcon: { enabled: true }
        }
      });

      const getElement = (selector) => document.querySelector(selector);

      if (getElement('#tour-search-bar')) {
        tour.addStep({
          id: 'step-search',
          text: 'Start here. Search by product name, HS code, or plain English.',
          attachTo: { element: '#tour-search-bar', on: 'bottom' },
          buttons: [
            { text: 'Skip', action: tour.cancel, classes: 'shepherd-button-secondary' },
            { text: 'Next', action: tour.next }
          ]
        });
      }

      if (getElement('#tour-search-methods')) {
        tour.addStep({
          id: 'step-search-methods',
          text: 'You can directly search by HS Code, Category, or Product Name without clicking the Import/Export scope button.',
          attachTo: { element: '#tour-search-methods', on: 'bottom' },
          buttons: [
            { text: 'Next', action: tour.next }
          ]
        });
      }

      if (getElement('#tour-scope-toggle')) {
        tour.addStep({
          id: 'step-scope',
          text: 'Or switch between finding buyers or suppliers if using an AI Query.',
          attachTo: { element: '#tour-scope-toggle', on: 'bottom' },
          buttons: [
            { text: 'Next', action: tour.next }
          ]
        });
      }

      if (getElement('#tour-ai-query')) {
        tour.addStep({
          id: 'step-ai',
          text: "Try natural language like 'buy sugar from Brazil'.",
          attachTo: { element: '#tour-ai-query', on: 'bottom' },
          buttons: [
            { text: 'Next', action: tour.next }
          ]
        });
      }

      if (getElement('#tour-example-queries')) {
        tour.addStep({
          id: 'step-examples',
          text: 'Not sure where to start? Try one of these example queries.',
          attachTo: { element: '#tour-example-queries', on: 'top' },
          buttons: [
            { text: 'Next', action: tour.next }
          ]
        });
      }

      if (getElement('#tour-nav-intelligence')) {
        tour.addStep({
          id: 'step-nav-intelligence',
          text: 'Click Intelligence on the nav bar to see the supplier directory by clicking "Find Suppliers", or find buyers by clicking "Find Buyers".',
          attachTo: { element: '#tour-nav-intelligence', on: 'bottom' },
          buttons: [
            { text: 'Next', action: tour.next }
          ]
        });
      }

      if (getElement('#tour-nav-subscription')) {
        tour.addStep({
          id: 'step-nav-subscription',
          text: 'Need more searches? Click Subscription to buy tokens.',
          attachTo: { element: '#tour-nav-subscription', on: 'bottom' },
          buttons: [
            { text: 'Done', action: tour.complete }
          ]
        });
      }

      const finishTour = () => {
        localStorage.setItem('zarailink_tour_done', 'true');
      };

      tour.on('complete', finishTour);
      tour.on('cancel', finishTour);

      if (tour.steps.length > 0) {
        tour.start();
      }
    }, 1000); // 1s delay to let animations settle

    return () => {
      clearTimeout(tourTimer);
      // Ensure we don't leave lingering Shepherd modals
      if (Shepherd.activeTour) {
        Shepherd.activeTour.cancel();
      }
    };
  }, []);

  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedHsCode, setSelectedHsCode] = useState(null);
  const [selectedProductName, setSelectedProductName] = useState(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);



  const searchMode = (() => {
    if (!query.trim()) return null;
    if (/^[\d.]+$/.test(query.trim())) return 'hscode';
    if (scope) return 'ai';
    return 'product';
  })();

  const debounceRef = useRef(null);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  const fetchSuggestions = useCallback(async (q) => {
    if (q.length < 2) { setSuggestions([]); setShowSuggestions(false); return; }
    setLoadingSuggestions(true);
    try {
      const isNumeric = /^[\d.]+$/.test(q);
      const endpoint = isNumeric
        ? `${API_BASE}/api/search/hs-code-tree/?q=${encodeURIComponent(q)}`
        : `${API_BASE}/api/search/autocomplete/?q=${encodeURIComponent(q)}`;
      const res = await fetch(endpoint);
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data);
        setShowSuggestions(data.length > 0);
      }
    } catch (err) {
      console.error('Autocomplete fetch error:', err);
    } finally {
      setLoadingSuggestions(false);
    }
  }, []);

  useEffect(() => {
    setSelectedHsCode(null);
    setSelectedProductName(null);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(query), 250);
    return () => clearTimeout(debounceRef.current);
  }, [query, fetchSuggestions]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(e.target) &&
        !inputRef.current.contains(e.target)
      ) setShowSuggestions(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectSuggestion = (suggestion) => {
    if (suggestion.is_final !== undefined && !suggestion.is_final) {
      setQuery(suggestion.hs_code);
      inputRef.current?.focus();
      return;
    }
    if (suggestion.is_final !== undefined && suggestion.is_final) {
      setQuery(suggestion.name);
      setSelectedHsCode(suggestion.hs_code);
      setSelectedProductName(suggestion.name);
      setShowSuggestions(false);
      // Always route to DataDashboard — the 4-pill UI handles import/export direction.
      // mode=dashboard is the key that tells the router to render DataDashboard, not SearchResults.
      const params = new URLSearchParams({
        q:            suggestion.name,
        hs_code:      suggestion.hs_code,
        variant_name: suggestion.name,
        mode:         'dashboard',
      });
      navigate(`/search/results?${params.toString()}`);
      return;
    }
    setQuery(suggestion.name);
    setSelectedHsCode(suggestion.hs_code);
    setSelectedProductName(suggestion.name);
    setShowSuggestions(false);
    // Always route to DataDashboard — the 4-pill UI handles import/export direction.
    // mode=dashboard is the key that tells the router to render DataDashboard, not SearchResults.
    const params = new URLSearchParams({
      q:            suggestion.name,
      hs_code:      suggestion.hs_code,
      variant_name: suggestion.name,
      mode:         'dashboard',
    });
    navigate(`/search/results?${params.toString()}`);
  };

  const clearQuery = () => {
    setQuery('');
    setSelectedHsCode(null);
    setSelectedProductName(null);
    setSuggestions([]);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    const isHsCode = /^[\d.]+$/.test(query.trim());
    const params = new URLSearchParams({ q: query });
    if (isHsCode) {
      params.set('hs_code', selectedHsCode || query.trim());
    } else {
      if (scope) params.set('scope', scope);
      if (selectedHsCode) params.set('hs_code', selectedHsCode);
    }
    navigate(`/search/results?${params.toString()}`);
  };

  const handlePillClick = (text) => {
    setQuery(text);
    setSelectedHsCode(null);
    setSelectedProductName(null);
  };

  // ── Animation variants ────────────────────────────────────────────────────
  const fadeUp = {
    hidden: { opacity: 0, y: 24 },
    visible: { opacity: 1, y: 0 },
  };

  const stagger = {
    visible: { transition: { staggerChildren: 0.1 } },
    hidden: {},
  };

  const FEATURES = [
    {
      Icon: Search,
      color: 'from-emerald-400 to-teal-500',
      title: 'Discover Buyers & Suppliers',
      desc: 'Search by product name, HS code, category, or plain language — instantly surface active importers and exporters.',
    },
    {
      Icon: BarChart2,
      color: 'from-blue-400 to-indigo-500',
      title: 'Understand the Market',
      desc: 'See real pricing, trade volumes, shipment trends, and top origin/destination countries for any product.',
    },
    {
      Icon: Building2,
      color: 'from-violet-400 to-purple-500',
      title: 'Deep-Dive Company Profiles',
      desc: "Review a company's full transaction history, product portfolio, and trading partners before you reach out.",
    },
    {
      Icon: Phone,
      color: 'from-amber-400 to-orange-500',
      title: 'Contact Decision Makers',
      desc: 'Unlock verified phone numbers, emails, and WhatsApp contacts for the right person at any company.',
    },
  ];

  const STATS = [
    { icon: <Globe size={20} />, value: 50000, suffix: '+', label: 'Trade Records' },
    { icon: <Users size={20} />, value: 2000, suffix: '+', label: 'Companies Listed' },
    { icon: <TrendingUp size={20} />, value: 500, suffix: '+', label: 'Products Tracked' },
  ];

  return (
    <div className="min-h-screen bg-slate-50 font-sans overflow-x-hidden">
      <Navbar />

      {/* ── HERO ────────────────────────────────────────────────────────── */}
      <div className="relative bg-white border-b border-slate-100">
        {/* Background orbs — clipped independently so they don't bleed out */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <FloatingOrb className="w-96 h-96 bg-emerald-400 -top-20 -left-32" />
          <FloatingOrb className="w-80 h-80 bg-teal-300 top-10 right-0" />
          <FloatingOrb className="w-64 h-64 bg-blue-300 bottom-0 left-1/2" />
        </div>

        <main className="max-w-4xl mx-auto px-6 py-20 md:py-28 relative z-10">

          {/* ── How to Search Card ─────────────────────────────────────── */}
              <motion.div
                initial={{ opacity: 0, y: -12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="mb-10 bg-white/80 backdrop-blur border border-slate-200 rounded-2xl shadow-lg shadow-slate-200/50 p-5 text-left relative"
              >
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-7 h-7 rounded-lg bg-emerald-100 flex items-center justify-center">
                    <Info size={15} className="text-emerald-600" />
                  </div>
                  <span className="font-bold text-slate-700 text-sm">4 Ways to Search ZaraiLink</span>
                </div>
                <div id="tour-search-methods" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {[
                    { color: 'blue', Icon: Hash, title: 'HS Code', sub: 'Type a numeric code', example: '1702.3000' },
                    { color: 'orange', Icon: Layers, title: 'Category', sub: 'Broad product class', example: 'glucose syrup' },
                    { color: 'emerald', Icon: Package, title: 'Product Name', sub: 'Specific variant', example: 'dextrose ball' },
                    { color: 'violet', Icon: Zap, title: 'AI Query', sub: 'Select Import/Export first', example: 'buy urea from india', id: 'tour-ai-query' },
                  ].map(({ color, Icon, title, sub, example, id }) => (
                    <div key={title} id={id} className={`flex items-start gap-3 p-3 bg-${color}-50 border border-${color}-100 rounded-xl`}>
                      <div className={`w-8 h-8 rounded-lg bg-${color}-500 flex items-center justify-center flex-shrink-0 mt-0.5`}>
                        <Icon size={15} className="text-white" />
                      </div>
                      <div>
                        <p className="font-bold text-slate-800 text-sm">{title}</p>
                        <p className="text-xs text-slate-500 mt-0.5">{sub}</p>
                        <p className={`text-xs text-${color}-700 font-mono mt-1 bg-${color}-100 rounded px-1.5 py-0.5 inline-block`}>{example}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>

          {/* ── Headline ──────────────────────────────────────────────── */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={stagger}
            className="text-center mb-10"
          >
            <motion.h1
              variants={fadeUp}
              className="text-4xl md:text-6xl font-extrabold text-slate-900 tracking-tight mb-4 leading-tight"
            >
              What are you<br />
              looking for,{' '}
              <span className="relative inline-block">
                <span className="text-emerald-600">{user?.name || user?.email?.split('@')[0]}</span>
                <motion.div
                  className="absolute -bottom-1 left-0 h-1 bg-emerald-400 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: '100%' }}
                  transition={{ delay: 0.6, duration: 0.5 }}
                />
              </span>?
            </motion.h1>

            <motion.p variants={fadeUp} className="text-slate-400 text-lg font-medium mb-8">
              Search across thousands of importers, exporters, and their transaction histories.
            </motion.p>
          </motion.div>

          {/* ── Search Bar ────────────────────────────────────────────── */}
          <motion.div
            initial={{ opacity: 0, y: 32, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            <form id="tour-search-bar" onSubmit={handleSearch} className="relative w-full mx-auto mb-6">
              <div className="relative group shadow-2xl shadow-emerald-500/10 rounded-2xl">
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                  placeholder="Try 'Import Dextrose from China under $700'..."
                  className="w-full h-16 pl-16 pr-36 rounded-2xl border-2 border-slate-200 bg-white focus:outline-none focus:ring-0 focus:border-emerald-400 text-base transition-all shadow-inner"
                  autoComplete="off"
                />
                <div className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-emerald-500 transition-colors">
                  <Search size={22} />
                </div>

                {query && (
                  <button
                    type="button"
                    onClick={clearQuery}
                    className="absolute right-[8.5rem] top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    <X size={18} />
                  </button>
                )}

                <button
                  type="submit"
                  className="absolute right-2 top-2 bottom-2 px-7 bg-emerald-500 hover:bg-emerald-400 text-slate-900 rounded-xl font-bold transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2 group/btn"
                >
                  Search
                  <ArrowRight size={16} className="group-hover/btn:translate-x-1 transition-transform" />
                </button>
              </div>

              {/* Search Mode Badge */}
              <AnimatePresence>
                {searchMode && (
                  <motion.div
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    className="mt-3 flex justify-center"
                  >
                    {searchMode === 'hscode' && (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-700 border border-blue-200">
                        <Hash size={11} /> HS Code Mode — browsing by trade code
                      </span>
                    )}
                    {searchMode === 'product' && (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700 border border-emerald-200">
                        <Package size={11} /> Product Search — browse matching variants
                      </span>
                    )}
                    {searchMode === 'ai' && (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-violet-100 text-violet-700 border border-violet-200">
                        <Zap size={11} /> AI Query Mode — powered by natural language
                      </span>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Product pin banner */}
              <AnimatePresence>
                {selectedProductName && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="mt-4 flex items-center justify-center gap-2 text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-full py-2 px-5 mx-auto w-fit shadow-sm"
                  >
                    <span className="font-bold">Searching exactly for:</span>
                    <span>{selectedProductName}</span>
                    <button type="button" onClick={clearQuery} className="text-emerald-500 hover:text-emerald-700 ml-1">
                      <X size={14} />
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Autocomplete Dropdown */}
              <AnimatePresence>
                {showSuggestions && (
                  <motion.div
                    ref={suggestionsRef}
                    initial={{ opacity: 0, y: 8, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 8, scale: 0.98 }}
                    transition={{ duration: 0.15 }}
                    className="absolute z-50 top-full mt-3 w-full bg-white rounded-2xl shadow-2xl border border-slate-100 max-h-96 overflow-y-auto overflow-x-hidden text-left"
                  >
                    <div className="px-6 py-3 text-xs font-bold text-slate-400 uppercase tracking-widest border-b border-slate-50 bg-slate-50/50">
                      Product Matches
                    </div>
                    {suggestions.map((s, i) => (
                      <button
                        key={s.hs_code + i}
                        type="button"
                        onClick={() => handleSelectSuggestion(s)}
                        className="w-full flex items-center justify-between px-6 py-4 hover:bg-emerald-50/50 transition-colors border-b border-slate-50 last:border-0 group"
                      >
                        <div className="flex flex-col items-start gap-1">
                          <span className="font-bold text-slate-800 group-hover:text-emerald-700 transition-colors">{s.name}</span>
                          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{s.category} • HS {s.hs_code}</span>
                        </div>
                        <div className="flex items-center gap-4">
                          {s.is_final === false && (
                            <span className="text-xs font-bold text-emerald-700 bg-emerald-100 rounded-lg px-3 py-1">Drill Down</span>
                          )}
                          <ChevronRight size={18} className="text-slate-300 group-hover:text-emerald-500 transition-colors" />
                        </div>
                      </button>
                    ))}
                    {loadingSuggestions && (
                      <div className="px-6 py-4 text-sm font-medium text-slate-400 text-center animate-pulse">Searching global database...</div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </form>
          </motion.div>

          {/* ── Scope Toggle ───────────────────────────────────────────── */}
          <motion.div
            id="tour-scope-toggle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="flex justify-center gap-3 mb-8"
          >
            {[
              { label: 'Imports', value: 'IMPORT' },
              { label: 'Exports', value: 'EXPORT' },
            ].map(({ label, value }) => (
              <button
                key={value}
                type="button"
                onClick={() => setScope(scope === value ? null : value)}
                className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all ${scope === value
                  ? 'bg-emerald-500 text-slate-900 shadow-lg shadow-emerald-500/20 scale-105'
                  : 'bg-white text-slate-600 border border-slate-200 hover:border-emerald-400 hover:text-emerald-600'
                  }`}
              >
                {label}
              </button>
            ))}
          </motion.div>

          {/* ── Intent Pills ───────────────────────────────────────────── */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="flex flex-wrap justify-center gap-3 mb-10"
          >
            {['I want to buy', 'I want to sell', 'Find suppliers', 'Find buyers'].map((pill) => (
              <button
                key={pill}
                onClick={() => handlePillClick(pill)}
                className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:border-emerald-500 hover:text-emerald-600 hover:shadow-md transition-all hover:-translate-y-0.5"
              >
                {pill}
              </button>
            ))}
          </motion.div>

          {/* ── Example Queries ────────────────────────────────────────── */}
          <motion.div
            id="tour-example-queries"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            className="text-center"
          >
            <p className="mb-3 font-bold uppercase tracking-widest text-xs text-slate-400">Example Queries</p>
            <div className="flex flex-wrap justify-center gap-6 text-slate-400 font-medium text-sm">
              {[
                'Dextrose suppliers in Pakistan',
                'Buy Urea 46%',
                'Who sells PVC Resin?',
              ].map((q) => (
                <span
                  key={q}
                  className="cursor-pointer hover:text-emerald-600 transition-colors underline-offset-2 hover:underline"
                  onClick={() => setQuery(q)}
                >
                  "{q}"
                </span>
              ))}
            </div>
          </motion.div>
        </main>
      </div>

      {/* ── STATS BAR ─────────────────────────────────────────────────────────── */}
      <div className="bg-slate-900 py-10">
        <div className="max-w-4xl mx-auto px-6">
          <div className="grid grid-cols-3 gap-8 text-center">
            {STATS.map(({ icon, value, suffix, label }) => (
              <div key={label} className="flex flex-col items-center gap-1">
                <div className="text-emerald-400 mb-2">{icon}</div>
                <div className="text-3xl font-black text-white font-mono">
                  <AnimatedCounter end={value} suffix={suffix} />
                </div>
                <div className="text-slate-400 text-sm font-medium">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── FEATURES ──────────────────────────────────────────────────────────── */}
      <div className="max-w-7xl mx-auto px-6 py-24">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-80px' }}
          variants={stagger}
          className="text-center mb-14"
        >
          <motion.h2 variants={fadeUp} className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-3">
            Everything you need to close better deals
          </motion.h2>
          <motion.p variants={fadeUp} className="text-slate-400 text-base">
            From first search to the right contact — all in one place.
          </motion.p>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-60px' }}
          variants={stagger}
          className="grid md:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {FEATURES.map((f, i) => (
            <motion.div
              key={i}
              variants={fadeUp}
              whileHover={{ y: -6, boxShadow: '0 20px 40px rgba(0,0,0,0.08)' }}
              className="bg-white p-7 rounded-3xl border border-slate-100 shadow-lg shadow-slate-200/40 cursor-default"
            >
              <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-5 shadow-lg`}>
                <f.Icon size={22} className="text-white" strokeWidth={2} />
              </div>
              <h4 className="font-bold text-slate-900 mb-2 text-base">{f.title}</h4>
              <p className="text-sm text-slate-500 leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* ── CTA ───────────────────────────────────────────────────────────────── */}
      <div className="max-w-7xl mx-auto px-6 pb-24">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="relative bg-slate-900 rounded-[2.5rem] p-12 text-center overflow-hidden shadow-2xl"
        >
          {/* Animated gradient background */}
          <motion.div
            className="absolute inset-0 opacity-30"
            style={{ background: 'radial-gradient(ellipse at 20% 50%, #10b981 0%, transparent 60%), radial-gradient(ellipse at 80% 50%, #3b82f6 0%, transparent 60%)' }}
            animate={{ opacity: [0.2, 0.35, 0.2] }}
            transition={{ duration: 4, repeat: Infinity }}
          />

          {/* Grid overlay */}
          <div className="absolute inset-0 opacity-5" style={{ backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

          <div className="relative z-10">
            <h2 className="text-3xl md:text-5xl font-extrabold text-white mb-4 leading-tight">
              Find your next<br />trading partner
            </h2>
            <p className="text-slate-400 text-lg mb-10 max-w-2xl mx-auto leading-relaxed">
              Browse the directory, explore real transaction data, and connect with the right buyers or suppliers — without the cold calls.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <motion.button
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => navigate('/trade-directory/find-suppliers')}
                className="px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-bold rounded-2xl transition-colors shadow-lg shadow-emerald-500/30 flex items-center justify-center gap-2 group"
              >
                Browse Suppliers <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => navigate('/trade-directory/find-buyers')}
                className="px-8 py-4 bg-white/10 hover:bg-white/20 text-white font-bold rounded-2xl border border-white/20 transition-colors flex items-center justify-center gap-2 group"
              >
                Browse Buyers <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </motion.button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
