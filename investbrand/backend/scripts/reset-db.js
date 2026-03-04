require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT) || 5432,
  database: process.env.DB_NAME || 'investcraft',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
});

async function resetDb() {
  const client = await pool.connect();
  try {
    console.log('Dropping tables...');
    await client.query(`DROP TABLE IF EXISTS puzzle_votes CASCADE`);
    await client.query(`DROP TABLE IF EXISTS game_sessions CASCADE`);
    await client.query(`DROP TABLE IF EXISTS puzzles CASCADE`);
    console.log('Tables dropped successfully.');
  } catch (err) {
    console.error('Failed to drop tables:', err);
  } finally {
    client.release();
    await pool.end();
  }
}

resetDb();
