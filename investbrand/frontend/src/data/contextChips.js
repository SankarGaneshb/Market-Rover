// Mock dictionary for contextual chips. Extensible in Phase 3.
export const INDEX_CHIPS = {
  "Nifty 50": [
    { type: 'info', text: 'Large-cap: Top 50 companies by market value' },
    { type: 'positive', text: 'Generally more stable, lower volatility' },
    { type: 'positive', text: 'Good starting point for beginners' }
  ],
  "Nifty Next 50": [
    { type: 'info', text: 'Future megacaps: Companies ranked 51-100' },
    { type: 'risk', text: 'Higher potential growth but more volatility' }
  ],
  "Nifty Midcap": [
    { type: 'info', text: 'Mid-sized growth companies' },
    { type: 'risk', text: 'Considerably higher volatility than large-caps' }
  ]
};

export const SECTOR_CHIPS = {
  "Automobile": [
    { type: 'info', text: 'Cyclical sector: performance tied to economic growth' },
    { type: 'risk', text: 'Affected by fuel prices, interest rates, consumer sentiment' }
  ],
  "FMCG": [
    { type: 'positive', text: 'Defensive sector: stable demand regardless of economy' },
    { type: 'info', text: 'Fast-Moving Consumer Goods (everyday products)' }
  ],
  "Information Technology": [
    { type: 'positive', text: 'High growth potential, export-oriented' },
    { type: 'risk', text: 'Sensitive to global trends and currency fluctuations' }
  ]
};

export const COMPANY_CHIPS = {
  "Bajaj Auto": [
    { type: 'info', text: 'Part of Nifty 50 Index' },
    { type: 'info', text: 'Ticker: BAJAJ-AUTO on NSE/BSE' }
  ],
  "Tata Motors": [
    { type: 'info', text: 'Ticker: TATAMOTORS on NSE/BSE' }
  ]
};

export function getChipsForSelection(type, value) {
  if (!value) return [];
  if (type === 'index') return INDEX_CHIPS[value] || [];
  if (type === 'sector') return SECTOR_CHIPS[value] || [];
  if (type === 'company') return COMPANY_CHIPS[value] || [{ type: 'info', text: `Detailed info on ${value} coming soon` }];
  return [];
}
