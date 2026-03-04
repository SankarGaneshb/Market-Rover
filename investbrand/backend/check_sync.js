const { getPool } = require('./src/config/database');

async function checkSync() {
  const pool = getPool();
  try {
    const res = await pool.query(`
      SELECT 
        p.scheduled_date as date, 
        COUNT(DISTINCT s.puzzle_id) as num_different_puzzles,
        STRING_AGG(DISTINCT p.ticker, ', ') as tickers
      FROM game_sessions s
      JOIN puzzles p ON s.puzzle_id = p.id
      WHERE p.scheduled_date IS NOT NULL
      GROUP BY p.scheduled_date
      ORDER BY p.scheduled_date DESC
      LIMIT 10;
    `);
    console.table(res.rows);
  } catch (error) {
    console.error("Database query failed:", error);
  } finally {
    process.exit();
  }
}

checkSync();
