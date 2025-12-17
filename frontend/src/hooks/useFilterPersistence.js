import { useState, useEffect, useCallback } from 'react';


const useFilterPersistence = (key, defaultFilters = {}) => {
  
  const [filters, setFiltersState] = useState(() => {
    try {
      const saved = localStorage.getItem(key);
      if (saved) {
        const parsed = JSON.parse(saved);
        
        return { ...defaultFilters, ...parsed };
      }
    } catch (error) {
      console.error('Error loading filters from localStorage:', error);
    }
    return defaultFilters;
  });

  
  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(filters));
    } catch (error) {
      console.error('Error saving filters to localStorage:', error);
    }
  }, [key, filters]);

  
  const setFilter = useCallback((filterKey, value) => {
    setFiltersState(prev => ({
      ...prev,
      [filterKey]: value,
    }));
  }, []);

  
  const setFilters = useCallback((newFilters) => {
    setFiltersState(prev => ({
      ...prev,
      ...newFilters,
    }));
  }, []);

  
  const resetFilters = useCallback(() => {
    setFiltersState(defaultFilters);
  }, [defaultFilters]);

  
  const clearFilters = useCallback(() => {
    setFiltersState({});
    localStorage.removeItem(key);
  }, [key]);

  
  const hasActiveFilters = useCallback(() => {
    return Object.entries(filters).some(([filterKey, value]) => {
      const defaultValue = defaultFilters[filterKey];
      return value !== defaultValue && value !== '' && value !== null && value !== undefined;
    });
  }, [filters, defaultFilters]);

  return {
    filters,
    setFilter,
    setFilters,
    resetFilters,
    clearFilters,
    hasActiveFilters,
  };
};

export default useFilterPersistence;
