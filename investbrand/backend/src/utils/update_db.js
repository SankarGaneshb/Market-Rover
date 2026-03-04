require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: 5432,
    database: process.env.DB_NAME || 'investcraft',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'Postgresql12#',
});

const companies = [
    { t: 'RELIANCE', name: 'Reliance Industries', diff: 1, sec: 'Energy', hint: 'Largest conglomerate', dayOff: 0 },
    { t: 'TCS', name: 'Tata Consultancy Services', diff: 2, sec: 'IT', hint: 'Largest IT company', dayOff: 1 },
    { t: 'HDFCBANK', name: 'HDFC Bank', diff: 2, sec: 'Financials', hint: 'Largest private bank', dayOff: 2 },
    { t: 'SBIN', name: 'State Bank of India', diff: 1, sec: 'Financials', hint: 'Largest public sector bank', dayOff: 3 },
    { t: 'ITC', name: 'ITC Limited', diff: 1, sec: 'FMCG', hint: 'FMCG and Hotels giant', dayOff: 4 },
    { t: 'MARUTI', name: 'Maruti Suzuki', diff: 1, sec: 'Automobile', hint: 'Largest car manufacturer', dayOff: 5 },
    { t: 'ASIANPAINT', name: 'Asian Paints', diff: 1, sec: 'Consumer', hint: 'Leading paints company', dayOff: 6 }
];

async function run() {
    const client = await pool.connect();
    try {
        console.log('Connected to Investcraft DB. Truncating broken puzzles...');
        await client.query('TRUNCATE TABLE puzzles CASCADE');

        for (let c of companies) {
            const rawSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400"><rect width="400" height="400" fill="#1E3A8A"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="200" font-weight="bold">' + c.name.charAt(0) + '</text><text x="50%" y="80%" dominant-baseline="middle" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-family="Arial, sans-serif" font-size="30">' + c.name.substring(0, 20) + '</text></svg>';
            const base64Svg = Buffer.from(rawSvg).toString('base64');
            const dataUri = 'data:image/svg+xml;base64,' + base64Svg;

            await client.query(
                'INSERT INTO puzzles (company_name, ticker, logo_url, difficulty, sector, hint, scheduled_date) VALUES ($1, $2, $3, $4, $5, $6, CURRENT_DATE + ($7::int))',
                [c.name, c.t, dataUri, c.diff, c.sec, c.hint, c.dayOff]
            );
        }
        console.log('Success! Database seamlessly updated with offline data URIs.');
    } catch (e) {
        console.error('Error:', e);
    } finally {
        client.release();
        pool.end();
    }
}
run();
