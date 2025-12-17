import { useState, useEffect, useCallback } from 'react';

const WATCHLIST_KEY = 'zarailink-watchlist';


const useWatchlist = () => {
  const [watchlist, setWatchlist] = useState(() => {
    try {
      const saved = localStorage.getItem(WATCHLIST_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  
  useEffect(() => {
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(watchlist));
  }, [watchlist]);

  const addToWatchlist = useCallback((company) => {
    setWatchlist(prev => {
      if (prev.find(c => c.id === company.id || c.name === company.name)) {
        return prev; 
      }
      return [...prev, { 
        ...company, 
        addedAt: new Date().toISOString() 
      }];
    });
  }, []);

  const removeFromWatchlist = useCallback((companyId) => {
    setWatchlist(prev => prev.filter(c => c.id !== companyId && c.name !== companyId));
  }, []);

  const isInWatchlist = useCallback((companyId) => {
    return watchlist.some(c => c.id === companyId || c.name === companyId);
  }, [watchlist]);

  const toggleWatchlist = useCallback((company) => {
    if (isInWatchlist(company.id || company.name)) {
      removeFromWatchlist(company.id || company.name);
      return false;
    } else {
      addToWatchlist(company);
      return true;
    }
  }, [isInWatchlist, addToWatchlist, removeFromWatchlist]);

  const clearWatchlist = useCallback(() => {
    setWatchlist([]);
  }, []);

  return {
    watchlist,
    addToWatchlist,
    removeFromWatchlist,
    isInWatchlist,
    toggleWatchlist,
    clearWatchlist,
    watchlistCount: watchlist.length,
  };
};

export default useWatchlist;
