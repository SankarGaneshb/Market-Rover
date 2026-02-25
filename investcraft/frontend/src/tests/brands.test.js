import { NIFTY50_BRANDS } from '../data/brands';

describe('Authentic Brand Integrity Constraints', () => {
    it('should guarantee that all 151 Nifty brands are correctly loaded', () => {
        expect(NIFTY50_BRANDS).toBeDefined();
        expect(NIFTY50_BRANDS.length).toBeGreaterThanOrEqual(151);
    });

    it('must strictly enforce that every logo securely sources from the authentic high-res Wikipedia Special:FilePath', () => {
        NIFTY50_BRANDS.forEach(brandObj => {
            if (brandObj.logoUrl) {
                // 1. Must use the exact Wikipedia protocol
                expect(brandObj.logoUrl).toContain('https://en.wikipedia.org/wiki/Special:FilePath');

                // Secondary check to ensure no raw synthetic Clearbit APIs or tiny gstatic API fallbacks snuck through
                expect(brandObj.logoUrl).not.toContain('logo.clearbit.com');
                expect(brandObj.logoUrl).not.toContain('t2.gstatic.com');
            }
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
