require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'investcraft',
    user: process.env.DB_USER || 'postgresql',
    password: process.env.DB_PASSWORD || 'Postgresql12#',
});

async function run() {
    const client = await pool.connect();
    try {
        console.log('Connected to Investcraft DB. Truncating broken puzzles...');
        await client.query('TRUNCATE TABLE puzzles CASCADE');

        console.log('Re-seeding with stable remote Clearbit logo APIs...');
        await client.query(`
            INSERT INTO puzzles (company_name, ticker, logo_url, difficulty, sector, hint, scheduled_date) VALUES 
            ('Reliance Industries', 'RELIANCE', 'https://logo.clearbit.com/ril.com', 1, 'Energy', 'Largest conglomerate', CURRENT_DATE),
            ('Tata Consultancy Services', 'TCS', 'https://logo.clearbit.com/tcs.com', 2, 'IT', 'Largest IT company', CURRENT_DATE + 1),
            ('HDFC Bank', 'HDFCBANK', 'https://logo.clearbit.com/hdfcbank.com', 2, 'Financials', 'Largest private bank', CURRENT_DATE + 2),
            ('State Bank of India', 'SBIN', 'https://logo.clearbit.com/sbi.co.in', 1, 'Financials', 'Largest public sector bank', CURRENT_DATE + 3),
            ('ITC Limited', 'ITC', 'https://logo.clearbit.com/itcportal.com', 1, 'FMCG', 'FMCG and Hotels giant', CURRENT_DATE + 4),
            ('Maruti Suzuki', 'MARUTI', 'https://logo.clearbit.com/marutisuzuki.com', 1, 'Automobile', 'Largest car manufacturer', CURRENT_DATE + 5),
            ('Asian Paints', 'ASIANPAINT', 'https://logo.clearbit.com/asianpaints.com', 1, 'Consumer', 'Leading paints company', CURRENT_DATE + 6)
        `);
        console.log('Success! The database will now serve the fast, Canvas-safe remote APIs APIs.');
    } catch (e) {
        console.error('Error:', e);
    } finally {
        client.release();
        pool.end();
    }
}
run();
