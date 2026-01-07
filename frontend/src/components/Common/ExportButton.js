import React, { useState } from 'react';
import { downloadCSV, downloadPDF } from '../../utils/exportUtils';
import './ExportButton.css';

const ExportButton = ({
  data,
  columns,
  filename = 'export',
  title = 'Export Data',
  className = '',
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleExportCSV = () => {
    setIsExporting(true);
    try {
      downloadCSV(data, columns, filename);
    } finally {
      setIsExporting(false);
      setIsOpen(false);
    }
  };

  const handleExportPDF = async () => {
    setIsExporting(true);
    try {
      await downloadPDF(data, columns, { title, filename });
    } finally {
      setIsExporting(false);
      setIsOpen(false);
    }
  };

  if (!data || data.length === 0) {
    return null;
  }

  return (
    <div className={`export-button-container ${className}`}>
      <button
        className="export-button"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || isExporting}
      >
        {/* <span className="export-icon">📥</span> */}
        <span>Export</span>
        {/* <span className="export-arrow">▼</span> */}
      </button>
      
      {isOpen && (
        <div className="export-dropdown">
          <button 
            className="export-option" 
            onClick={handleExportCSV}
            disabled={isExporting}
          >
            {/* <span className="option-icon">📊</span> */}
            <div className="option-content">
              <span className="option-title">Export as CSV</span>
              <span className="option-desc">Spreadsheet format</span>
            </div>
          </button>
          <button 
            className="export-option" 
            onClick={handleExportPDF}
            disabled={isExporting}
          >
            {/* <span className="option-icon">📄</span> */}
            <div className="option-content">
              <span className="option-title">Export as PDF</span>
              <span className="option-desc">Document format</span>
            </div>
          </button>
        </div>
      )}
    </div>
  );
};

export default ExportButton;
