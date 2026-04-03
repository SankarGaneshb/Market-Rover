require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT) || 5432,
  database: process.env.DB_NAME || 'investcraft',
  user: process.env.DB_USER || 'postgresql',
  password: process.env.DB_PASSWORD || 'Postgresql12#',
});

async function testQueries() {
  console.log('--- Testing Daily Leaderboard ---');
  try {
    const today = '2026-03-26';
    const result = await pool.query(
      `SELECT u.id, u.name, u.avatar_url, u.streak,
                SUM(gs.score)::int AS score, 
                SUM(gs.moves_used)::int AS moves_used, 
                SUM(gs.time_taken)::int AS time_taken,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'easy'), 0)::int AS easy_score,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'medium'), 0)::int AS medium_score,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'hard'), 0)::int AS hard_score
         FROM users u
         JOIN game_sessions gs ON u.id = gs.user_id
         JOIN puzzles p        ON gs.puzzle_id = p.id
         WHERE p.scheduled_date = $1
         GROUP BY u.id, u.name, u.avatar_url, u.streak
         ORDER BY score DESC, time_taken ASC
         LIMIT 50`,
      [today]
    );
    console.log('Daily Success:', result.rows.length, 'rows found');
  } catch (err) {
    console.error('Daily Failed:', err.message);
  }

  console.log('\n--- Testing All-Time Leaderboard ---');
  try {
    const result = await pool.query(
        `WITH top_users AS (
           SELECT id, name, avatar_url, streak, total_score AS score
           FROM users
           ORDER BY total_score DESC
           LIMIT 50
         )
         SELECT tu.*,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'easy'), 0)::int AS easy_score,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'medium'), 0)::int AS medium_score,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'hard'), 0)::int AS hard_score
         FROM top_users tu
         LEFT JOIN game_sessions gs ON tu.id = gs.user_id
         GROUP BY tu.id, tu.name, tu.avatar_url, tu.streak, tu.score
         ORDER BY tu.score DESC`
      );
    console.log('All-Time Success:', result.rows.length, 'rows found');
  } catch (err) {
    console.error('All-Time Failed:', err.message);
  }

  process.exit();
}

testQueries();
