require('dotenv').config();
const { Pool } = require('pg');
const fs = require('fs');

const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'investcraft',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'Invest123'
});

async function jsonDump() {
    try {
        const today = new Date().toISOString().split('T')[0];

        const puzzles = await pool.query("SELECT id, ticker, company_name, scheduled_date FROM puzzles ORDER BY id ASC");
        const todayPuzzles = await pool.query("SELECT * FROM puzzles WHERE scheduled_date = $1", [today]);
        const jioPuzzles = await pool.query("SELECT * FROM puzzles WHERE ticker IN ('JIOFIN', 'RELIANCE')");
        const adminUser = await pool.query("SELECT * FROM users WHERE email = 'b.sankarganesh@gmail.com'");

        const dump = {
            today,
            scheduled_puzzles: puzzles.rows,
            today_puzzles: todayPuzzles.rows,
            jio_puzzles: jioPuzzles.rows,
            user: adminUser.rows[0]
        };

        fs.writeFileSync('db_dump.json', JSON.stringify(dump, null, 2));
        console.log("Dump successful: db_dump.json");
    } catch (err) {
        console.error(err);
    } finally {
        pool.end();
    }
}

jsonDump();
