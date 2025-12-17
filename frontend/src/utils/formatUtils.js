


export const isNA = (value) => {
  if (value === null || value === undefined) return true;
  if (value === 'N/A' || value === 'n/a') return true;
  if (typeof value === 'string' && value.trim() === '') return true;
  if (typeof value === 'number' && isNaN(value)) return true;
  return false;
};


export const formatOrNull = (value, formatter = (v) => v) => {
  if (isNA(value)) return null;
  return formatter(value);
};


export const displayValue = (value, fallback = '-') => {
  if (isNA(value)) return fallback;
  return String(value);
};


export const filterNARows = (rows, requiredKeys = []) => {
  if (!Array.isArray(rows)) return [];
  if (requiredKeys.length === 0) return rows;
  
  return rows.filter(row => {
    
    return requiredKeys.some(key => !isNA(row[key]));
  });
};


export const formatCurrency = (value) => {
  if (isNA(value)) return null;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};


export const formatPercent = (value) => {
  if (isNA(value)) return null;
  const num = typeof value === 'number' ? value : parseFloat(value);
  if (isNaN(num)) return null;
  return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`;
};


export const formatVolume = (value) => {
  if (isNA(value)) return null;
  return `${new Intl.NumberFormat('en-US').format(value)} MT`;
};
