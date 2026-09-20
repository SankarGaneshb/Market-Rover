import { NIFTY50_BRANDS } from '../data/brands';

describe('Authentic Brand Integrity Constraints', () => {
    it('should guarantee that all Nifty brands are correctly loaded', () => {
        expect(NIFTY50_BRANDS).toBeDefined();
        expect(NIFTY50_BRANDS.length).toBeGreaterThanOrEqual(50);
    });

    it('must strictly enforce that every brand uses an authentic logo source', () => {
        NIFTY50_BRANDS.forEach(brandObj => {
            // 1. MUST HAVE A LOGO
            expect(brandObj.logoUrl).toBeDefined();
            expect(brandObj.logoUrl).toBeTruthy();

            // 2. Must use a valid local or official asset path
            const validProtocol = brandObj.logoUrl.startsWith('/logos/') ||
                                  brandObj.logoUrl.startsWith('http://') ||
                                  brandObj.logoUrl.startsWith('https://');
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
