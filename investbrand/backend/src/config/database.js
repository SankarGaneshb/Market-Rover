const { Pool } = require('pg');
const logger = require('../utils/logger');

let pool;

async function initializePool() {
  const isProduction = process.env.NODE_ENV === 'production';
  const config = isProduction ? {
    host: `/cloudsql/${process.env.CLOUD_SQL_CONNECTION_NAME}`,
    database: process.env.IC_DB_NAME || process.env.DB_NAME,
    user: process.env.IC_DB_USER || process.env.DB_USER,
    password: process.env.IC_DB_PASSWORD || process.env.DB_PASSWORD,
    max: 20,
  } : {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'investcraft',
    user: process.env.DB_USER || 'postgresql',
    password: process.env.DB_PASSWORD || 'Postgresql12#',
    max: 5,
  };

  pool = new Pool(config);
  await pool.query('SELECT NOW()');
  logger.info('Database connected successfully');
  await runMigrations();
  return pool;
}

async function runMigrations() {
  const client = await pool.connect();
  try {
    console.log("Starting hyper-sequential migrations...");

    // 1. Core Table Skeletons
    await client.query('CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, google_id VARCHAR(255) UNIQUE NOT NULL, email VARCHAR(255) UNIQUE NOT NULL)');
    await client.query('CREATE TABLE IF NOT EXISTS puzzles (id SERIAL PRIMARY KEY, brand_name VARCHAR(255), ticker VARCHAR(50), logo_url TEXT)');
    await client.query('CREATE TABLE IF NOT EXISTS puzzle_votes (id SERIAL PRIMARY KEY, user_id INTEGER, vote_date DATE NOT NULL)');

    // 2. Comprehensive Column Enforcement
    await client.query('ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(255) DEFAULT \'Player\'');
    await client.query('ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT');
    await client.query('ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER DEFAULT 0');
    await client.query('ALTER TABLE users ADD COLUMN IF NOT EXISTS last_played DATE');
    await client.query('ALTER TABLE users ADD COLUMN IF NOT EXISTS total_score INTEGER DEFAULT 0');
    await client.query('ALTER TABLE users ADD COLUMN IF NOT EXISTS best_score INTEGER DEFAULT 0');
    await client.query('ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()');

    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS brand_id INTEGER');
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS company_name VARCHAR(255)');
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS difficulty INTEGER DEFAULT 1');
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS sector VARCHAR(100)');
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS description TEXT');
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS hint TEXT');
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS scheduled_date DATE');
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()');
    try { await client.query('ALTER TABLE puzzles ADD CONSTRAINT puzzles_scheduled_date_key UNIQUE(scheduled_date)'); } catch (e) { }

    await client.query('ALTER TABLE puzzle_votes ADD COLUMN IF NOT EXISTS brand_id INTEGER');
    await client.query('ALTER TABLE puzzle_votes ADD COLUMN IF NOT EXISTS puzzle_id INTEGER');
    await client.query('ALTER TABLE puzzle_votes ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()');

    // 3. Relaxation
    try { await client.query('ALTER TABLE puzzle_votes ALTER COLUMN puzzle_id DROP NOT NULL'); } catch (e) { }
    try { await client.query('ALTER TABLE puzzles ALTER COLUMN scheduled_date DROP NOT NULL'); } catch (e) { }

    // 4. Index/Constraint Cleanup
    await client.query(`
      DO $$ 
      DECLARE r record; 
      BEGIN 
        FOR r IN SELECT conname FROM pg_constraint WHERE conrelid = 'puzzle_votes'::regclass AND contype = 'u' LOOP 
          EXECUTE 'ALTER TABLE puzzle_votes DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname) || ' CASCADE'; 
        END LOOP;
        FOR r IN SELECT i.relname AS index_name FROM pg_class t JOIN pg_index ix ON t.oid = ix.indrelid JOIN pg_class i ON i.oid = ix.indexrelid WHERE t.relname = 'puzzle_votes' AND ix.indisunique = true AND ix.indisprimary = false AND NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conindid = ix.indexrelid) LOOP 
          EXECUTE 'DROP INDEX IF EXISTS ' || quote_ident(r.index_name) || ' CASCADE'; 
        END LOOP;
      END $$;
    `);

    // 5. Final Constraints
    await client.query('ALTER TABLE puzzle_votes ADD CONSTRAINT puzzle_votes_user_date_brand_key UNIQUE(user_id, vote_date, brand_id)');

    // 6. Secondary Tables
    await client.query('CREATE TABLE IF NOT EXISTS game_sessions (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id), puzzle_id INTEGER REFERENCES puzzles(id), score INTEGER DEFAULT 0, completed BOOLEAN DEFAULT FALSE, played_at TIMESTAMPTZ DEFAULT NOW())');
    await client.query('CREATE TABLE IF NOT EXISTS share_clicks (id SERIAL PRIMARY KEY, promoter_id INTEGER REFERENCES users(id), clicked_at TIMESTAMPTZ DEFAULT NOW())');

    await client.query('CREATE INDEX IF NOT EXISTS idx_game_sessions_user ON game_sessions(user_id)');
    await client.query('CREATE INDEX IF NOT EXISTS idx_puzzles_date ON puzzles(scheduled_date)');
    await client.query('CREATE INDEX IF NOT EXISTS idx_puzzle_votes_date ON puzzle_votes(vote_date)');

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
