require('dotenv').config();
const { Pool } = require('pg');
const brandsData = require('./src/data/brands.js');

const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'investcraft',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'Invest123'
});

async function checkLogic() {
    try {
        const today = new Date().toISOString().split('T')[0];
        const result = await pool.query(
            `SELECT id, company_name, ticker, logo_url, difficulty, sector, hint
       FROM puzzles WHERE scheduled_date = $1`,
            [today]
        );

        const data = result.rows[0];
        console.log("DB Data for Today:", data);

        if (data) {
            let matchedBrand = brandsData.NIFTY50_BRANDS.find(b => b.ticker === data.ticker && b.insight === data.hint);
            console.log("Strict match (ticker + hint):", matchedBrand ? matchedBrand.brand : "Failed");

            if (!matchedBrand) {
                matchedBrand = brandsData.NIFTY50_BRANDS.find(b => b.ticker === data.ticker);
                console.log("Fallback match (ticker only):", matchedBrand ? matchedBrand.brand : "Failed");
            }

            if (!matchedBrand) {
                console.log("WARNING: Ticker not found in brands.js!");
            }

        } else {
            console.log("No puzzle scheduled for today in DB.");
        }
    } catch (e) {
        console.error(e);
    } finally {
        pool.end();
    }
}

checkLogic();
