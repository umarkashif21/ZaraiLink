const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function generateComparisonPDF(companies, comparisonData, outputPath) {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();
    
    
    const htmlContent = generateHTMLTemplate(companies, comparisonData);
    
    
    await page.setContent(htmlContent, {
      waitUntil: 'networkidle0'
    });

    
    await page.pdf({
      path: outputPath,
      format: 'A4',
      printBackground: true,
      margin: {
        top: '20px',
        right: '20px',
        bottom: '20px',
        left: '20px'
      }
    });

    console.log(`PDF generated successfully: ${outputPath}`);
    return outputPath;
  } finally {
    await browser.close();
  }
}

function generateHTMLTemplate(companies, data) {
  const companiesData = data.companies || [];
  
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Company Comparison Report</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
      padding: 30px;
      color: #2d3748;
      background: white;
    }
    
    .header {
      text-align: center;
      margin-bottom: 40px;
      padding-bottom: 20px;
      border-bottom: 3px solid #10b981;
    }
    
    .header h1 {
      font-size: 28px;
      color: #10b981;
      margin-bottom: 10px;
    }
    
    .header .subtitle {
      font-size: 14px;
      color: #718096;
    }
    
    .section {
      margin-bottom: 30px;
    }
    
    .section-title {
      font-size: 20px;
      font-weight: 700;
      color: #2d3748;
      margin-bottom: 15px;
      padding-bottom: 8px;
      border-bottom: 2px solid #e2e8f0;
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 20px;
    }
    
    th, td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid #e2e8f0;
    }
    
    th {
      background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
      font-weight: 700;
      color: #2d3748;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.5px;
    }
    
    td {
      font-size: 13px;
      color: #4a5568;
    }
    
    tr:hover {
      background: #f7fafc;
    }
    
    .metric-row td:first-child {
      font-weight: 600;
      color: #2d3748;
    }
    
    .cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin-top: 15px;
    }
    
    .card {
      background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
      padding: 15px;
      border-radius: 8px;
      border-left: 4px solid #10b981;
    }
    
    .card h4 {
      font-size: 12px;
      color: #718096;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    .card-value {
      font-size: 18px;
      font-weight: 700;
      color: #2d3748;
    }
    
    .footer {
      margin-top: 40px;
      padding-top: 20px;
      border-top: 2px solid #e2e8f0;
      text-align: center;
      font-size: 11px;
      color: #a0aec0;
    }
    
    @media print {
      body {
        padding: 20px;
      }
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>Company Comparison Report</h1>
    <div class="subtitle">Trade Intelligence Analysis • Generated ${new Date().toLocaleDateString()}</div>
  </div>

  <div class="section">
    <h2 class="section-title">Overview Metrics</h2>
    <table>
      <thead>
        <tr>
          <th>Metric</th>
          ${companies.map(comp => `<th>${comp}</th>`).join('')}
        </tr>
      </thead>
      <tbody>
        <tr class="metric-row">
          <td>Trade Volume</td>
          ${companiesData.map(comp => `<td>$${comp.trade_volume?.toLocaleString() || 'N/A'}</td>`).join('')}
        </tr>
        <tr class="metric-row">
          <td>Estimated Revenue</td>
          ${companiesData.map(comp => `<td>$${comp.estimated_revenue?.toLocaleString() || 'N/A'}</td>`).join('')}
        </tr>
        <tr class="metric-row">
          <td>Total Products</td>
          ${companiesData.map(comp => `<td>${comp.total_products || 0}</td>`).join('')}
        </tr>
        <tr class="metric-row">
          <td>Total Partners</td>
          ${companiesData.map(comp => `<td>${comp.total_partners || 0}</td>`).join('')}
        </tr>
        <tr class="metric-row">
          <td>Partner Diversity Score</td>
          ${companiesData.map(comp => `<td>${comp.partner_diversity_score?.toFixed(2) || 'N/A'}</td>`).join('')}
        </tr>
        <tr class="metric-row">
          <td>Active Since</td>
          ${companiesData.map(comp => `<td>${comp.active_since ? new Date(comp.active_since).getFullYear() : 'N/A'}</td>`).join('')}
        </tr>
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2 class="section-title">Network Influence</h2>
    <div class="cards-grid">
      ${companiesData.map((comp, idx) => `
        <div class="card">
          <h4>${companies[idx]}</h4>
          <div style="margin-top: 10px;">
            <div style="margin-bottom: 5px;">
              <strong>PageRank:</strong> ${comp.pagerank?.toFixed(4) || 'N/A'}
            </div>
            <div>
              <strong>Network Degree:</strong> ${comp.network_degree || 'N/A'}
            </div>
          </div>
        </div>
      `).join('')}
    </div>
  </div>

  <div class="footer">
    <div>ZaraiLink Trade Intelligence Platform</div>
    <div>This report is confidential and intended for internal use only.</div>
  </div>
</body>
</html>
  `;
}

module.exports = { generateComparisonPDF };
