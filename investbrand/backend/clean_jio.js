require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'investcraft',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'postgres'
});

async function cleanUp() {
    try {
        const res = await pool.query("SELECT * FROM puzzles WHERE ticker = 'JIOFIN'");
        console.table(res.rows);

        console.log("Deleting unscheduled JIOFIN puzzles to clean up duplicates...");
        const delRes = await pool.query("DELETE FROM puzzles WHERE ticker = 'JIOFIN' AND scheduled_date IS NULL RETURNING *");
        console.log(`Deleted ${delRes.rowCount} unscheduled JIOFIN puzzles.`);

        const countRes = await pool.query("SELECT COUNT(*) FROM puzzles WHERE scheduled_date IS NULL");
        console.log("Total unscheduled puzzles remaining:", countRes.rows[0].count);
    } catch (err) {
        console.error(err);
    } finally {
        pool.end();
    }
}

cleanUp();
