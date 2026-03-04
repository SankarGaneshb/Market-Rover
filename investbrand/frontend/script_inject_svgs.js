const fs = require('fs');

const frontendFile = 'c:/Users/bsank/Market-Rover/investcraft/frontend/src/data/brands.js';
let content = fs.readFileSync(frontendFile, 'utf8');

// Safely extract the current exports array
const match = content.match(/export const NIFTY50_BRANDS = (\[[\s\S]*\]);/);
let brands = eval(match[1]);

// Read the original backup
const backupContent = fs.readFileSync('c:/Users/bsank/Downloads/brand-puzzle-game.tsx', 'utf8');
const backupMatch = backupContent.match(/const NIFTY50_BRANDS = (\[[\s\S]*?\]);\n\nconst PuzzleGame/);
let backupBrands = [];
if (backupMatch) {
    backupBrands = eval(backupMatch[1]);
}

// Merge
brands = brands.map(b => {
    const backupBrand = backupBrands.find(backup => backup.ticker === b.ticker && backup.brand === b.brand);
    if (backupBrand && backupBrand.logoSvg) {
        b.logoSvg = backupBrand.logoSvg;
    } else if (b.brand === 'Jio' || b.ticker === 'RELIANCE') {
        b.logoSvg = `<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="jioGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#0057FF;stop-opacity:1" /><stop offset="100%" style="stop-color:#00D4FF;stop-opacity:1" /></linearGradient></defs><rect fill="url(#jioGrad)" width="400" height="400"/><circle cx="200" cy="150" r="40" fill="white"/><text x="200" y="280" font-size="120" font-weight="900" fill="white" text-anchor="middle" font-family="Arial, sans-serif">Jio</text></svg>`;
    }
    return b;
});

const newExport = JSON.stringify(brands, null, 2);
const newContent = content.replace(match[1], newExport);
fs.writeFileSync(frontendFile, newContent);
console.log('Successfully injected pristine logoSvg fields into brands.js');
