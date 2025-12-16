// Utility functions for formatting and N/A filtering

/**
 * Check if a value should be considered "N/A" (missing/invalid)
 * @param {*} value - The value to check
 * @returns {boolean} - True if the value is N/A
 */
export const isNA = (value) => {
  if (value === null || value === undefined) return true;
  if (value === 'N/A' || value === 'n/a') return true;
  if (typeof value === 'string' && value.trim() === '') return true;
  if (typeof value === 'number' && isNaN(value)) return true;
  return false;
};

/**
 * Format a value, returning null/undefined if it's N/A
 * @param {*} value - The value to format
 * @param {function} formatter - Formatting function to apply if value is valid
 * @returns {*} - Formatted value or null
 */
export const formatOrNull = (value, formatter = (v) => v) => {
  if (isNA(value)) return null;
  return formatter(value);
};

/**
 * Display a value, showing '-' or custom fallback if N/A
 * @param {*} value - The value to display
 * @param {string} fallback - Fallback string to show instead of N/A (default: '-')
 * @returns {string} - The display string
 */
export const displayValue = (value, fallback = '-') => {
  if (isNA(value)) return fallback;
  return String(value);
};

/**
 * Filter rows that have all N/A values for specified keys
 * @param {Array} rows - Array of row objects
 * @param {Array} requiredKeys - Keys that must have non-N/A values
 * @returns {Array} - Filtered array
 */
export const filterNARows = (rows, requiredKeys = []) => {
  if (!Array.isArray(rows)) return [];
  if (requiredKeys.length === 0) return rows;
  
  return rows.filter(row => {
    // Keep row if at least one required key has a non-N/A value
    return requiredKeys.some(key => !isNA(row[key]));
  });
};

/**
 * Format currency, returning null if N/A
 * @param {number} value - The value to format
 * @returns {string|null} - Formatted currency or null
 */
export const formatCurrency = (value) => {
  if (isNA(value)) return null;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

/**
 * Format percentage, returning null if N/A
 * @param {number} value - The percentage value
 * @returns {string|null} - Formatted percentage or null
 */
export const formatPercent = (value) => {
  if (isNA(value)) return null;
  const num = typeof value === 'number' ? value : parseFloat(value);
  if (isNaN(num)) return null;
  return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`;
};

/**
 * Format volume (MT), returning null if N/A
 * @param {number} value - The volume value
 * @returns {string|null} - Formatted volume or null
 */
export const formatVolume = (value) => {
  if (isNA(value)) return null;
  return `${new Intl.NumberFormat('en-US').format(value)} MT`;
};
