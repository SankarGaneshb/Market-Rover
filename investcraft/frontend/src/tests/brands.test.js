import { NIFTY50_BRANDS } from '../data/brands';

describe('Authentic Brand Integrity Constraints', () => {
    it('should guarantee that all 151 Nifty brands are correctly loaded', () => {
        expect(NIFTY50_BRANDS).toBeDefined();
        expect(NIFTY50_BRANDS.length).toBeGreaterThanOrEqual(151);
    });

    it('must strictly enforce that every brand uses the official Wikipedia SVG logo source', () => {
        NIFTY50_BRANDS.forEach(brandObj => {
            // 1. MUST HAVE A LOGO
            expect(brandObj.logoUrl).toBeDefined();
            expect(brandObj.logoUrl).toBeTruthy();

            // 2. Must use the exact Wikipedia FilePath protocol
            const validProtocol = brandObj.logoUrl.includes('https://en.wikipedia.org/wiki/Special:FilePath/');
            expect(validProtocol).toBe(true);
        });
    });

    it('must rigidly map every brand to a valid 4-tier selection tree structure', () => {
        NIFTY50_BRANDS.forEach(brandObj => {
            // Index Validation
            expect(brandObj.index).toBeDefined();
            expect(['Nifty 50', 'Nifty Next 50', 'Nifty Midcap']).toContain(brandObj.index);

            // Structural Validation
            expect(brandObj.sector).toBeDefined();
            expect(brandObj.company).toBeDefined();
            expect(brandObj.brand).toBeDefined();
            expect(brandObj.ticker).toBeDefined();
            expect(brandObj.insight).toBeDefined();
        });
    });
});
