const fs = require('fs');

const frontendFile = './src/data/brands.js';
let content = fs.readFileSync(frontendFile, 'utf8');

const match = content.match(/export const NIFTY50_BRANDS = (\[[\s\S]*\]);/);
let brands = eval(match[1]);

const sectorColors = {
    'IT': ['#0ea5e9', '#0369a1'],
    'Financials': ['#a855f7', '#6b21a8'],
    'Energy': ['#f59e0b', '#92400e'],
    'FMCG': ['#10b981', '#064e3b'],
    'Telecom': ['#f43f5e', '#881337'],
    'Automobile': ['#6366f1', '#312e81'],
    'Healthcare': ['#14b8a6', '#0f766e'],
    'Consumer': ['#8b5cf6', '#4c1d95'],
    'Infrastructure': ['#f97316', '#9a3412'],
    'Metals': ['#94a3b8', '#334155'],
    'Materials': ['#64748b', '#0f172a'],
    'default': ['#3b82f6', '#1d4ed8']
};

function escapeXml(unsafe) {
    return unsafe.replace(/[<>&'"]/g, function (c) {
        switch (c) {
            case '<': return '&lt;';
            case '>': return '&gt;';
            case '&': return '&amp;';
            case '\'': return '&apos;';
            case '"': return '&quot;';
        }
    });
}

brands = brands.map(b => {
    // Check if the logoSvg is OUR auto-generated one so we can overwrite it with escaped text
    // Or if it's missing
    if (!b.logoSvg || b.logoSvg.includes('grad_')) {
        const colors = sectorColors[b.sector] || sectorColors.default;

        let shortText = b.brand;
        if (shortText.length > 12) {
            shortText = b.brand.substring(0, 10) + '..';
        }

        const safeText = escapeXml(shortText);

        b.logoSvg = `<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad_${b.id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:${colors[0]};stop-opacity:1" />
      <stop offset="100%" style="stop-color:${colors[1]};stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect fill="url(#grad_${b.id})" width="400" height="400" rx="40" />
  <text x="200" y="220" font-size="50" font-weight="900" fill="white" text-anchor="middle" font-family="Arial, sans-serif">${safeText}</text>
</svg>`;
    }
    return b;
});

const newExport = JSON.stringify(brands, null, 2);
const newContent = content.replace(match[1], newExport);
fs.writeFileSync(frontendFile, newContent);
console.log('Successfully injected properly escaped fallback SVGs');
