require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'investcraft',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'Invest123'
});

async function deepCheck() {
    try {
        console.log("--- Scheduled Puzzles ---");
        const today = new Date().toISOString().split('T')[0];
        const res = await pool.query("SELECT id, ticker, company_name, scheduled_date FROM puzzles ORDER BY scheduled_date DESC NULLS LAST LIMIT 20");
        console.table(res.rows);

        console.log(`--- Checking Today (${today}) ---`);
        const todayRes = await pool.query("SELECT * FROM puzzles WHERE scheduled_date = $1", [today]);
        console.table(todayRes.rows);

        console.log("--- Checking for JIOFIN or RELIANCE ---");
        const jioRes = await pool.query("SELECT * FROM puzzles WHERE ticker IN ('JIOFIN', 'RELIANCE')");
        console.table(jioRes.rows);

        console.log("--- Checking Recent Game Sessions ---");
        const sessRes = await pool.query("SELECT gs.*, p.ticker FROM game_sessions gs JOIN puzzles p ON gs.puzzle_id = p.id ORDER BY gs.played_at DESC LIMIT 10");
        console.table(sessRes.rows);

    } catch (err) {
        console.error(err);
    } finally {
        pool.end();
    }
}

deepCheck();
