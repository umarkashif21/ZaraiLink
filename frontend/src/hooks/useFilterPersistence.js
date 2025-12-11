import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook for persisting filter state in localStorage
 * 
 * @param {string} key - The localStorage key to store filters
 * @param {object} defaultFilters - Default filter values
 * @returns {object} - { filters, setFilter, setFilters, resetFilters, clearFilters }
 */
const useFilterPersistence = (key, defaultFilters = {}) => {
  // Initialize state from localStorage or defaults
  const [filters, setFiltersState] = useState(() => {
    try {
      const saved = localStorage.getItem(key);
      if (saved) {
        const parsed = JSON.parse(saved);
        // Merge with defaults to handle new filter keys
        return { ...defaultFilters, ...parsed };
      }
    } catch (error) {
      console.error('Error loading filters from localStorage:', error);
    }
    return defaultFilters;
  });

  // Persist to localStorage whenever filters change
  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(filters));
    } catch (error) {
      console.error('Error saving filters to localStorage:', error);
    }
  }, [key, filters]);

  // Update a single filter
  const setFilter = useCallback((filterKey, value) => {
    setFiltersState(prev => ({
      ...prev,
      [filterKey]: value,
    }));
  }, []);

  // Update multiple filters at once
  const setFilters = useCallback((newFilters) => {
    setFiltersState(prev => ({
      ...prev,
      ...newFilters,
    }));
  }, []);

  // Reset to default values
  const resetFilters = useCallback(() => {
    setFiltersState(defaultFilters);
  }, [defaultFilters]);

  // Clear all filters (empty object)
  const clearFilters = useCallback(() => {
    setFiltersState({});
    localStorage.removeItem(key);
  }, [key]);

  // Check if any filters are active
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
