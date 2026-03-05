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
  try {
    console.log("Starting radical simplified migrations with corrected order...");

    // 1. Core Tables Initialization (Independent first)
    await pool.query("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, google_id VARCHAR(255) UNIQUE NOT NULL, email VARCHAR(255) UNIQUE NOT NULL)");
    await pool.query("CREATE TABLE IF NOT EXISTS puzzles (id SERIAL PRIMARY KEY, brand_id INTEGER, brand_name VARCHAR(255) NOT NULL, ticker VARCHAR(50) NOT NULL, logo_url TEXT NOT NULL, scheduled_date DATE UNIQUE)");
    await pool.query("CREATE TABLE IF NOT EXISTS puzzle_votes (id SERIAL PRIMARY KEY, user_id INTEGER, vote_date DATE NOT NULL)");

    // 2. Schema Evolution / Column Additions
    await pool.query('ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER DEFAULT 0');
    await pool.query('ALTER TABLE puzzle_votes ADD COLUMN IF NOT EXISTS brand_id INTEGER');
    await pool.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS brand_id INTEGER');

    // 3. Relax legacy constraints
    try {
      await pool.query('ALTER TABLE puzzle_votes ALTER COLUMN puzzle_id DROP NOT NULL');
    } catch (e) { /* ignore if column missing */ }

    // 4. Drop ALL old unique indexes/constraints to clear path
    await pool.query(`
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

    // 5. Add Triple Constraint
    await pool.query('ALTER TABLE puzzle_votes ADD CONSTRAINT puzzle_votes_user_date_brand_key UNIQUE(user_id, vote_date, brand_id)');

    // 6. Secondary tables and indices
    await pool.query("CREATE TABLE IF NOT EXISTS game_sessions (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id), puzzle_id INTEGER REFERENCES puzzles(id), UNIQUE(user_id, puzzle_id))");
    await pool.query("CREATE TABLE IF NOT EXISTS share_clicks (id SERIAL PRIMARY KEY, promoter_id INTEGER REFERENCES users(id) ON DELETE SET NULL, ref_page VARCHAR(50), clicked_at TIMESTAMPTZ DEFAULT NOW())");

    logger.info('Database migrations completed');
  } catch (err) {
    logger.error('Migration failed', { error: err.message });
    throw err;
  }
}

function getPool() {
  if (!pool) throw new Error('Database pool not initialized. Call initializePool() first.');
  return pool;
}

module.exports = { initializePool, getPool };
