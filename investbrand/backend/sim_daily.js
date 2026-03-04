require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'investcraft',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'Invest123'
});

async function simulateDaily() {
    try {
        const today = new Date().toISOString().split('T')[0];
        console.log("Calculated Today String (UTC):", today);

        const result = await pool.query(
            `SELECT id, company_name, ticker, scheduled_date
       FROM puzzles WHERE scheduled_date = $1`,
            [today]
        );

        console.log("Found in DB:", result.rows);

        if (result.rows.length === 0) {
            console.log("WARNING: No puzzle scheduled for this specific string!");

            const allScheduled = await pool.query("SELECT id, ticker, scheduled_date FROM puzzles WHERE scheduled_date IS NOT NULL ORDER BY scheduled_date DESC LIMIT 5");
            console.log("Recent Scheduled Puzzles in DB:");
            allScheduled.rows.forEach(r => {
                console.log(`${r.scheduled_date.toISOString()} (Matches '${r.scheduled_date.toISOString().split('T')[0]}'): ${r.ticker}`);
            });
        }

    } catch (err) {
        console.error(err);
    } finally {
        pool.end();
    }
}

simulateDaily();
