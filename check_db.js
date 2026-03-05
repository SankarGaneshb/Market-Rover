require('dotenv').config({ path: './investcraft/backend/.env' });
const { getPool, initializePool } = require('./investcraft/backend/src/config/database');

async function test() {
    await initializePool();
    const pool = getPool();
    // check how many puzzles per ticker
    const count = await pool.query('SELECT ticker, COUNT(*), max(scheduled_date) as last_play FROM puzzles GROUP BY ticker');
    console.table(count.rows);
    pool.end();
}
test();
