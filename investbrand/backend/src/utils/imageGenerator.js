const logger = require('./logger');

/**
 * Generates an SVG string containing a Dark Mode Google Finance style stock dashboard
 * with an integrated word cloud.
 *
 * @param {string} ticker - Stock ticker
 * @param {string} companyName - Company name
 * @param {string} wordCloudStr - Comma separated word cloud
 * @returns {string} - Base64 encoded Data URL of the SVG
 */
function generateMergedPuzzleSvg(ticker, companyName, wordCloudStr) {
  try {
    const width = 800;
    const height = 600;
    const bgColor = "#0f172a"; // Deep navy dark theme
    const cardColor = "#1e293b";
    const accentColor = "#22d3ee"; // Cyan
    const successColor = "#4ade80"; // Green

    // 1. Generate realistic-looking mock data
    const points = [];
    let price = 500 + Math.random() * 2000;
    const startPrice = price * (0.5 + Math.random() * 0.3);
    const diff = price - startPrice;
    const percentChange = ((diff / startPrice) * 100).toFixed(2);

    for (let i = 0; i < 50; i++) {
        const volatility = 0.02;
        const change = price * volatility * (Math.random() - 0.4);
        price += change;
        points.push(price);
    }

    const minPrice = Math.min(...points) * 0.95;
    const maxPrice = Math.max(...points) * 1.05;
    const range = maxPrice - minPrice;
    const currentPrice = points[points.length - 1].toFixed(2);

    const chartX = 60;
    const chartY = 150;
    const chartWidth = 680;
    const chartHeight = 280;

    const scaledPoints = points.map((p, i) => {
        const x = chartX + (i / 49) * chartWidth;
        const y = chartY + chartHeight - ((p - minPrice) / range) * chartHeight;
        return `${x},${y}`;
    }).join(' ');

    const words = wordCloudStr.split(',').map(w => w.trim()).filter(Boolean);

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`;
    svg += `<rect width="${width}" height="${height}" fill="${bgColor}" />`;

    // Dashboard Header
    svg += `<text x="40" y="70" fill="#f8fafc" font-family="Arial, sans-serif" font-size="52" font-weight="900">${currentPrice} <tspan font-size="20" fill="#94a3b8" font-weight="400">INR</tspan></text>`;
    svg += `<text x="40" y="105" fill="${successColor}" font-family="Arial, sans-serif" font-size="20" font-weight="bold">+${diff.toFixed(2)} (${percentChange}%) <tspan fill="#64748b" font-weight="400">^ ALL TIME</tspan></text>`;

    // Time selectors
    const selectors = ['1D', '5D', '1M', '6M', 'YTD', '1Y', '5Y', 'MAX'];
    selectors.forEach((s, i) => {
        const x = 40 + i * 55;
        const isSelected = s === 'MAX';
        svg += `<text x="${x}" y="145" fill="${isSelected ? accentColor : '#64748b'}" font-family="Arial, sans-serif" font-size="14" font-weight="${isSelected ? '900' : '400'}">${s}</text>`;
        if(isSelected) svg += `<line x1="${x - 5}" y1="152" x2="${x + 35}" y2="152" stroke="${accentColor}" stroke-width="3" />`;
    });

    // Chart Area
    svg += `<rect x="${chartX-10}" y="${chartY-10}" width="${chartWidth+20}" height="${chartHeight+20}" rx="15" fill="${cardColor}" fill-opacity="0.5" />`;

    for(let i=0; i<=4; i++) {
        const y = chartY + i * (chartHeight / 4);
        svg += `<line x1="${chartX}" y1="${y}" x2="${chartX + chartWidth}" y2="${y}" stroke="#334155" stroke-width="1" stroke-dasharray="8" />`;
    }

    // Chart Line
    svg += `<polyline points="${scaledPoints}" fill="none" stroke="${successColor}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" filter="drop-shadow(0 0 8px ${successColor}66)" />`;

    // Word Cloud
    const wordPositions = [
        { x: 450, y: 220, size: 42, color: '#fca5a5' }, // rose/pink
        { x: 250, y: 260, size: 34, color: '#93c5fd' }, // blue
        { x: 550, y: 310, size: 36, color: '#fdba74' }, // orange
        { x: 300, y: 340, size: 30, color: '#d8b4fe' }, // purple
        { x: 500, y: 380, size: 40, color: '#f1f5f9' }, // white
        { x: 650, y: 250, size: 32, color: '#5eead4' }, // teal
        { x: 150, y: 320, size: 28, color: '#fde047' }, // yellow
        { x: 600, y: 360, size: 34, color: '#fca5a5' }
    ];

    words.forEach((word, i) => {
        const pos = wordPositions[i] || { x: chartX + Math.random() * chartWidth, y: chartY + Math.random() * chartHeight, size: 22, color: '#94a3b8' };
        svg += `<text x="${pos.x}" y="${pos.y}" text-anchor="middle" fill="${pos.color}" font-family="Arial, sans-serif" font-size="${pos.size}" font-weight="900" style="opacity: 0.9">${word.toUpperCase()}</text>`;
    });

    // Fundamentals Table
    const tableY = chartY + chartHeight + 60;
    const colWidth = 240;

    const stats = [
        { label: 'OPEN', val: (currentPrice * 0.98).toFixed(2), col: 40, row: 0 },
        { label: 'HIGH', val: (currentPrice * 1.02).toFixed(2), col: 40, row: 1 },
        { label: 'LOW', val: (currentPrice * 0.97).toFixed(2), col: 40, row: 2 },

        { label: 'MKT CAP', val: '1.29L Cr', col: 40 + colWidth, row: 0 },
        { label: 'P/E RATIO', val: (12.5 + Math.random() * 8).toFixed(2), col: 40 + colWidth, row: 1 },
        { label: '52-WK HIGH', val: (currentPrice * 1.15).toFixed(2), col: 40 + colWidth, row: 2 },

        { label: 'DIVIDEND', val: '1.70%', col: 40 + colWidth * 2, row: 0 },
        { label: 'QTR DIV', val: '4.07', col: 40 + colWidth * 2, row: 1 },
        { label: '52-WK LOW', val: (currentPrice * 0.65).toFixed(2), col: 40 + colWidth * 2, row: 2 }
    ];

    stats.forEach(s => {
        const y = tableY + s.row * 35;
        svg += `<text x="${s.col}" y="${y}" fill="#64748b" font-family="Arial, sans-serif" font-size="14" font-weight="bold">${s.label}</text>`;
        svg += `<text x="${s.col + colWidth - 20}" y="${y}" text-anchor="end" fill="#f8fafc" font-family="Arial, sans-serif" font-size="14" font-weight="900">${s.val}</text>`;
        svg += `<line x1="${s.col}" y1="${y + 10}" x2="${s.col + colWidth - 20}" y2="${y + 10}" stroke="#1e293b" stroke-width="1" />`;
    });

    svg += `<text x="760" y="580" text-anchor="end" fill="#334155" font-family="Arial, sans-serif" font-size="10" font-weight="900" letter-spacing="2">INVESTBRAND ENGINE v4.2</text>`;
    svg += `</svg>`;

    const base64 = Buffer.from(svg).toString('base64');
    return `data:image/svg+xml;base64,${base64}`;
  } catch (err) {
    logger.error('Error generating merged puzzle SVG:', err);
    return null;
  }
}

module.exports = {
  generateMergedPuzzleSvg
};
