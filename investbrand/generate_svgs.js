const fs = require('fs');

const file = 'c:/Users/bsank/Market-Rover/investcraft/frontend/src/data/brands.js';
let content = fs.readFileSync(file, 'utf8');

const match = content.match(/export const NIFTY50_BRANDS = (\[[\s\S]*\]);/);
let brands = eval(match[1]);

brands = brands.map(b => {
    const initial = b.brand.charAt(0);
    const colors = ['1E3A8A', '7C3AED', 'DB2777', '059669', 'D97706'];
    const color = colors[b.brand.length % colors.length];

    // Direct raw SVG string, safe to btoa/Buffer.from
    const rawSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400"><rect width="400" height="400" fill="#${color}"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="200" font-weight="bold">${initial}</text><text x="50%" y="80%" dominant-baseline="middle" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-family="Arial, sans-serif" font-size="30">${b.brand.substring(0, 20)}</text></svg>`;

    // Convert directly to base64
    const base64Svg = Buffer.from(rawSvg).toString('base64');
    b.logoUrl = 'data:image/svg+xml;base64,' + base64Svg;

    return b;
});

let newExport = JSON.stringify(brands, null, 2);
let newContent = content.replace(match[1], newExport);
fs.writeFileSync(file, newContent);
console.log('Restored all frontend source links to guaranteed offline Base64 SVGs successfully!');
