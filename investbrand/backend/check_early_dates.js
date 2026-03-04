require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'investcraft',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'Invest123'
});

async function checkEarlyDates() {
    try {
        const res = await pool.query(`
      SELECT id, ticker, company_name, scheduled_date 
      FROM puzzles 
      WHERE scheduled_date >= '2026-03-01' AND scheduled_date <= '2026-03-15'
      ORDER BY scheduled_date ASC
    `);
        console.log("--- Early March Schedule ---");
        res.rows.forEach(row => {
            const d = row.scheduled_date instanceof Date ? row.scheduled_date.toISOString().split('T')[0] : row.scheduled_date;
            console.log(`${d}: ${row.ticker} (${row.company_name}) [ID: ${row.id}]`);
        });

    } catch (err) {
        console.error(err);
    } finally {
        pool.end();
    }
}

checkEarlyDates();
