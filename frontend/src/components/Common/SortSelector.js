import React from 'react';
import './SortSelector.css';

const SortSelector = ({
  value,
  onChange,
  options = [],
  label = 'Sort by',
  className = '',
}) => {
  const defaultOptions = [
    { value: 'name_asc', label: 'Name (A-Z)' },
    { value: 'name_desc', label: 'Name (Z-A)' },
    { value: 'revenue_desc', label: 'Revenue (High to Low)' },
    { value: 'revenue_asc', label: 'Revenue (Low to High)' },
    { value: 'volume_desc', label: 'Volume (High to Low)' },
    { value: 'volume_asc', label: 'Volume (Low to High)' },
    { value: 'date_desc', label: 'Newest First' },
    { value: 'date_asc', label: 'Oldest First' },
  ];

  const sortOptions = options.length > 0 ? options : defaultOptions;

  return (
    <div className={`sort-selector ${className}`}>
      <label htmlFor="sort-select" className="sort-label">
        {label}
      </label>
      <select
        id="sort-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="sort-select"
      >
        {sortOptions.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
};

export default SortSelector;
