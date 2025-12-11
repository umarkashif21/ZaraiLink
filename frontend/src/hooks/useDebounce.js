import { useState, useEffect } from 'react';

/**
 * Custom hook to debounce a value
 * Useful for search inputs to prevent excessive API calls
 * 
 * @param {any} value - The value to debounce
 * @param {number} delay - Debounce delay in milliseconds (default: 300ms)
 * @returns {any} - The debounced value
 */
const useDebounce = (value, delay = 300) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

/**
 * Custom hook to debounce a callback function
 * 
 * @param {Function} callback - The callback to debounce
 * @param {number} delay - Debounce delay in milliseconds
 * @returns {Function} - The debounced callback
 */
export const useDebouncedCallback = (callback, delay = 300) => {
  const [timeoutId, setTimeoutId] = useState(null);

  const debouncedCallback = (...args) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    
    const newTimeoutId = setTimeout(() => {
      callback(...args);
    }, delay);
    
    setTimeoutId(newTimeoutId);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [timeoutId]);

  return debouncedCallback;
};

export default useDebounce;
