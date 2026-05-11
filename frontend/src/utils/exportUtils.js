export const downloadCSV = (data, columns, filename) => {
  console.log(`Exported ${data?.length} rows to CSV:`, filename);
  alert("Export functionality has been removed.");
};

export const downloadPDF = async (data, columns, options) => {
  console.log(`Exported ${data?.length} rows to PDF:`, options?.filename);
  alert("Export functionality has been removed.");
};
