import { useState, useEffect, useCallback } from 'react';

const CACHE_NAME = 'zarailink-offline-v1';
const OFFLINE_KEY = 'zarailink-offline-data';


const useOffline = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [cachedData, setCachedData] = useState(() => {
    try {
      const saved = localStorage.getItem(OFFLINE_KEY);
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const cacheData = useCallback((key, data) => {
    setCachedData(prev => {
      const updated = {
        ...prev,
        [key]: {
          data,
          timestamp: Date.now(),
        }
      };
      localStorage.setItem(OFFLINE_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  const getCachedData = useCallback((key, maxAgeMs = 24 * 60 * 60 * 1000) => {
    const cached = cachedData[key];
    if (!cached) return null;
    
    const age = Date.now() - cached.timestamp;
    if (age > maxAgeMs) return null;
    
    return cached.data;
  }, [cachedData]);

  const clearCache = useCallback(() => {
    setCachedData({});
    localStorage.removeItem(OFFLINE_KEY);
  }, []);

  
  const hasOfflineData = useCallback((key) => {
    return !!cachedData[key];
  }, [cachedData]);

  return {
    isOnline,
    isOffline: !isOnline,
    cacheData,
    getCachedData,
    clearCache,
    hasOfflineData,
  };
};

export default useOffline;
