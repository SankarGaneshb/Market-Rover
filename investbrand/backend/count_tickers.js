require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'investcraft',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'Invest123'
});

async function countTickers() {
    try {
        const res = await pool.query("SELECT ticker, COUNT(*) FROM puzzles GROUP BY ticker ORDER BY count DESC");
        console.table(res.rows);

        const nullDates = await pool.query("SELECT ticker, COUNT(*) FROM puzzles WHERE scheduled_date IS NULL GROUP BY ticker");
        console.log("--- Puzzles with NULL scheduled_date ---");
        console.table(nullDates.rows);

    } catch (err) {
        console.error(err);
    } finally {
        pool.end();
    }
}

countTickers();
