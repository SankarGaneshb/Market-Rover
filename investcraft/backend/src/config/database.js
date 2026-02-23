const { Pool } = require('pg');
const logger = require('../utils/logger');

let pool;

async function initializePool() {
  const isProduction = process.env.NODE_ENV === 'production';

  const config = isProduction
    ? {
      host: `/cloudsql/${process.env.CLOUD_SQL_CONNECTION_NAME}`,
      database: process.env.IC_DB_NAME || process.env.DB_NAME,
      user: process.env.IC_DB_USER || process.env.DB_USER,
      password: process.env.DB_PASSWORD,
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 5000,
    }
    : {
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT) || 5432,
      database: process.env.DB_NAME || 'investcraft',
      user: process.env.DB_USER || 'postgresql',
      password: process.env.DB_PASSWORD || 'Postgresql12#',
      max: 5,
    };

  pool = new Pool(config);

  const client = await pool.connect();
  await client.query('SELECT NOW()');
  client.release();
  logger.info('Database connected successfully');

  await runMigrations();
  return pool;
}

async function runMigrations() {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS users (
        id           SERIAL PRIMARY KEY,
        google_id    VARCHAR(255) UNIQUE NOT NULL,
        email        VARCHAR(255) UNIQUE NOT NULL,
        name         VARCHAR(255) NOT NULL,
        avatar_url   TEXT,
        streak       INTEGER DEFAULT 0,
        last_played  DATE,
        total_score  INTEGER DEFAULT 0,
        created_at   TIMESTAMPTZ DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS puzzles (
        id             SERIAL PRIMARY KEY,
        company_name   VARCHAR(255) NOT NULL,
        ticker         VARCHAR(50)  NOT NULL,
        logo_url       TEXT         NOT NULL,
        difficulty     INTEGER      DEFAULT 1,
        sector         VARCHAR(100),
        description    TEXT,
        hint           TEXT,
        scheduled_date DATE UNIQUE,
        created_at     TIMESTAMPTZ  DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS game_sessions (
        id          SERIAL PRIMARY KEY,
        user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
        puzzle_id   INTEGER REFERENCES puzzles(id) ON DELETE CASCADE,
        score       INTEGER  DEFAULT 0,
        moves_used  INTEGER  DEFAULT 0,
        completed   BOOLEAN  DEFAULT FALSE,
        time_taken  INTEGER,
        played_at   TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(user_id, puzzle_id)
      );

      CREATE TABLE IF NOT EXISTS puzzle_votes (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        ticker VARCHAR(50) NOT NULL,
        vote_date DATE NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(user_id, vote_date)
      );

      CREATE INDEX IF NOT EXISTS idx_game_sessions_user   ON game_sessions(user_id);
      CREATE INDEX IF NOT EXISTS idx_game_sessions_puzzle ON game_sessions(puzzle_id);
      CREATE INDEX IF NOT EXISTS idx_puzzles_date         ON puzzles(scheduled_date);
      CREATE INDEX IF NOT EXISTS idx_puzzle_votes_date    ON puzzle_votes(vote_date);
    `);
    logger.info('Database migrations completed');
  } catch (err) {
    logger.error('Migration failed', { error: err.message });
    throw err;
  } finally {
    client.release();
  }
}

function getPool() {
  if (!pool) throw new Error('Database pool not initialized. Call initializePool() first.');
  return pool;
}

module.exports = { initializePool, getPool };
