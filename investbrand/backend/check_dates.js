require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'investcraft',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'Invest123'
});

async function checkDates() {
    try {
        const res = await pool.query(`
      SELECT id, ticker, company_name, scheduled_date 
      FROM puzzles 
      WHERE scheduled_date >= '2026-03-01' 
      ORDER BY scheduled_date ASC
    `);
        console.log("--- Puzzle Schedule ---");
        res.rows.forEach(row => {
            console.log(`${row.scheduled_date}: ${row.ticker} (${row.company_name}) [ID: ${row.id}]`);
        });

    } catch (err) {
        console.error(err);
    } finally {
        pool.end();
    }
}

checkDates();
