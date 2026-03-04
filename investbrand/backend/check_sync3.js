const { Pool } = require('pg');

const pool = new Pool({
    host: 'localhost',
    port: 5432,
    database: 'investcraft',
    user: 'postgres',
    password: 'Invest123'
});

async function run() {
    try {
        const res = await pool.query(`
      SELECT 
        p.scheduled_date as date, 
        COUNT(DISTINCT s.puzzle_id) as puzzles_played,
        STRING_AGG(DISTINCT p.ticker, ', ') as tickers
      FROM game_sessions s
      JOIN puzzles p ON s.puzzle_id = p.id
      WHERE p.scheduled_date IS NOT NULL
      GROUP BY p.scheduled_date
      ORDER BY p.scheduled_date DESC
      LIMIT 10;
    `);
        console.table(res.rows);
    } catch (err) {
        console.error(err);
    } finally {
        process.exit(0);
    }
}
run();
