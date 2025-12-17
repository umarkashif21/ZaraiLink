


const getNestedValue = (obj, path) => {
  if (!path) return '';
  const keys = path.split('.');
  let value = obj;
  for (const key of keys) {
    if (value === null || value === undefined) return '';
    value = value[key];
  }
  return value;
};


export const convertToCSV = (data, columns) => {
  if (!data || data.length === 0) return '';
  
  
  const headers = columns 
    ? columns.map(col => col.label || col.key)
    : Object.keys(data[0]);
  
  const keys = columns 
    ? columns.map(col => col.key)
    : Object.keys(data[0]);
  
  
  const csvRows = [
    headers.join(','),
    ...data.map(row => 
      keys.map(key => {
        
        const value = key.includes('.') ? getNestedValue(row, key) : row[key];
        
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


export const downloadCSV = (data, columns, filename = 'export') => {
  try {
    if (!data || data.length === 0) {
      console.warn('No data to export to CSV');
      return;
    }
    const csv = convertToCSV(data, columns);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (navigator.msSaveBlob) {
      
      navigator.msSaveBlob(blob, `${filename}.csv`);
    } else {
      link.href = URL.createObjectURL(blob);
      link.download = `${filename}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    }
  } catch (error) {
    console.error('CSV export failed:', error);
  }
};


export const downloadPDF = async (data, columns, options = {}) => {
  try {
    if (!data || data.length === 0) {
      console.warn('No data to export to PDF');
      return;
    }
    
    const { jsPDF } = await import('jspdf');
    const { default: autoTable } = await import('jspdf-autotable');
    
    const {
      title = 'Export',
      filename = 'export',
      orientation = 'landscape',
      pageSize = 'a4',
      subtitle = '',
    } = options;
    
    const doc = new jsPDF(orientation, 'mm', pageSize);
    
    
    doc.setFontSize(18);
    doc.setTextColor(16, 185, 129); 
    doc.text(title, 14, 20);
    
    
    let startY = 28;
    if (subtitle) {
      doc.setFontSize(12);
      doc.setTextColor(60, 60, 60);
      doc.text(subtitle, 14, startY);
      startY += 8;
    }
    
    
    doc.setFontSize(10);
    doc.setTextColor(100, 100, 100);
    doc.text(`Generated: ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}`, 14, startY);
    startY += 10;
    
    
    const headers = columns ? columns.map(col => col.label || col.key) : Object.keys(data[0] || {});
    const keys = columns ? columns.map(col => col.key) : Object.keys(data[0] || {});
    
    const tableData = data.map(row => 
      keys.map(key => {
        
        const value = key.includes('.') ? getNestedValue(row, key) : row[key];
        if (value === null || value === undefined) return '';
        return String(value);
      })
    );
    
    
    autoTable(doc, {
      head: [headers],
      body: tableData,
      startY: startY,
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
      didDrawPage: (data) => {
        
        const pageCount = doc.internal.getNumberOfPages();
        doc.setFontSize(8);
        doc.setTextColor(150);
        doc.text(
          `Page ${data.pageNumber} of ${pageCount}`,
          doc.internal.pageSize.width - 30,
          doc.internal.pageSize.height - 10
        );
      },
    });
    
    
    doc.save(`${filename}.pdf`);
  } catch (error) {
    console.error('PDF export failed:', error);
  }
};


export const formatDataForExport = (data, formatters = {}) => {
  if (!data || !Array.isArray(data)) return [];
  
  return data.map(item => {
    const formatted = {};
    Object.entries(item).forEach(([key, value]) => {
      if (formatters[key]) {
        formatted[key] = formatters[key](value, item);
      } else if (value instanceof Date) {
        formatted[key] = value.toLocaleDateString();
      } else if (typeof value === 'object' && value !== null) {
        
        if (value.name) {
          formatted[key] = value.name;
        } else {
          formatted[key] = JSON.stringify(value);
        }
      } else {
        formatted[key] = value;
      }
    });
    return formatted;
  });
};


export const flattenDataForExport = (data, keyMappings = {}) => {
  if (!data || !Array.isArray(data)) return [];
  
  return data.map(item => {
    const flat = { ...item };
    Object.entries(keyMappings).forEach(([flatKey, nestedPath]) => {
      flat[flatKey] = getNestedValue(item, nestedPath);
    });
    return flat;
  });
};
