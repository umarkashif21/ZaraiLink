/**
 * Export utilities for CSV and PDF generation
 */

// Convert data array to CSV string
export const convertToCSV = (data, columns) => {
  if (!data || data.length === 0) return '';
  
  // Get column headers
  const headers = columns 
    ? columns.map(col => col.label || col.key)
    : Object.keys(data[0]);
  
  const keys = columns 
    ? columns.map(col => col.key)
    : Object.keys(data[0]);
  
  // Create CSV rows
  const csvRows = [
    headers.join(','),
    ...data.map(row => 
      keys.map(key => {
        const value = row[key];
        // Handle values with commas or quotes
        if (value === null || value === undefined) return '';
        const stringValue = String(value);
        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      }).join(',')
    )
  ];
  
  return csvRows.join('\n');
};

// Download CSV file
export const downloadCSV = (data, columns, filename = 'export') => {
  const csv = convertToCSV(data, columns);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  
  if (navigator.msSaveBlob) {
    // IE 10+
    navigator.msSaveBlob(blob, `${filename}.csv`);
  } else {
    link.href = URL.createObjectURL(blob);
    link.download = `${filename}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  }
};

// Generate and download PDF
export const downloadPDF = async (data, columns, options = {}) => {
  const { jsPDF } = await import('jspdf');
  await import('jspdf-autotable');
  
  const {
    title = 'Export',
    filename = 'export',
    orientation = 'landscape',
    pageSize = 'a4',
  } = options;
  
  const doc = new jsPDF(orientation, 'mm', pageSize);
  
  // Add title
  doc.setFontSize(18);
  doc.setTextColor(16, 185, 129); // Primary green color
  doc.text(title, 14, 20);
  
  // Add date
  doc.setFontSize(10);
  doc.setTextColor(100, 100, 100);
  doc.text(`Generated: ${new Date().toLocaleDateString()}`, 14, 28);
  
  // Prepare table data
  const headers = columns ? columns.map(col => col.label || col.key) : Object.keys(data[0] || {});
  const keys = columns ? columns.map(col => col.key) : Object.keys(data[0] || {});
  
  const tableData = data.map(row => 
    keys.map(key => {
      const value = row[key];
      if (value === null || value === undefined) return '';
      return String(value);
    })
  );
  
  // Generate table
  doc.autoTable({
    head: [headers],
    body: tableData,
    startY: 35,
    styles: {
      fontSize: 9,
      cellPadding: 3,
    },
    headStyles: {
      fillColor: [16, 185, 129],
      textColor: 255,
      fontStyle: 'bold',
    },
    alternateRowStyles: {
      fillColor: [245, 247, 250],
    },
    margin: { left: 14, right: 14 },
  });
  
  // Save PDF
  doc.save(`${filename}.pdf`);
};

// Format data for export (handles nested objects, dates, etc.)
export const formatDataForExport = (data, formatters = {}) => {
  return data.map(item => {
    const formatted = {};
    Object.entries(item).forEach(([key, value]) => {
      if (formatters[key]) {
        formatted[key] = formatters[key](value, item);
      } else if (value instanceof Date) {
        formatted[key] = value.toLocaleDateString();
      } else if (typeof value === 'object' && value !== null) {
        formatted[key] = JSON.stringify(value);
      } else {
        formatted[key] = value;
      }
    });
    return formatted;
  });
};
