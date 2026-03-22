const { Pool } = require('pg');
const { Connector } = require('@google-cloud/cloud-sql-connector');
const logger = require('../utils/logger');

let pool;
const connector = new Connector();

async function initializePool() {
  const isProduction = process.env.NODE_ENV === 'production';
  let config;

  if (isProduction) {
    logger.info('Initializing production database connection via Cloud SQL Connector', {
      instance: process.env.CLOUD_SQL_CONNECTION_NAME,
      database: process.env.IC_DB_NAME || process.env.DB_NAME
    });

    try {
      const clientOpts = await connector.getOptions({
        instanceConnectionName: process.env.CLOUD_SQL_CONNECTION_NAME,
        ipType: 'PUBLIC',
      });

      config = {
        ...clientOpts,
        user: process.env.IC_DB_USER || process.env.DB_USER,
        password: process.env.IC_DB_PASSWORD || process.env.DB_PASSWORD,
        database: process.env.IC_DB_NAME || process.env.DB_NAME,
        max: 20,
      };
    } catch (err) {
      logger.error('Failed to get Cloud SQL Connector options', { error: err.message });
      throw err;
    }
  } else {
    config = {
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT) || 5432,
      database: process.env.DB_NAME || 'investcraft',
      user: process.env.DB_USER || 'postgresql',
      password: process.env.DB_PASSWORD || 'Postgresql12#',
      max: 5,
    };
  }

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
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS brand_name VARCHAR(255)');
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS company_name VARCHAR(255)');
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS difficulty INTEGER DEFAULT 1');
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS sector VARCHAR(100)');
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS description TEXT');
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS hint TEXT');
    await client.query("ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS selection_method VARCHAR(20) DEFAULT 'lucky_draw'");
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS scheduled_date DATE');
    await client.query('ALTER TABLE puzzles ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()');
    try { await client.query('ALTER TABLE puzzles ADD CONSTRAINT puzzles_scheduled_date_key UNIQUE(scheduled_date)'); } catch (e) { }

    await client.query('ALTER TABLE puzzle_votes ADD COLUMN IF NOT EXISTS brand_id INTEGER');
    await client.query('ALTER TABLE puzzle_votes ADD COLUMN IF NOT EXISTS puzzle_id INTEGER');
    await client.query('ALTER TABLE puzzle_votes ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()');

    // 3. Relaxation
    try { await client.query('ALTER TABLE puzzle_votes ALTER COLUMN puzzle_id DROP NOT NULL'); } catch (e) { }
    try { await client.query('ALTER TABLE puzzles ALTER COLUMN scheduled_date DROP NOT NULL'); } catch (e) { }

    // 4. Index/Constraint Cleanup - Aggressive Legacy Removal
    await client.query(`
      DO $$ 
      DECLARE r record; 
      BEGIN 
        -- Drop all unique constraints on puzzle_votes except the PK
        FOR r IN SELECT conname FROM pg_constraint WHERE conrelid = 'puzzle_votes'::regclass AND contype = 'u' LOOP 
          EXECUTE 'ALTER TABLE puzzle_votes DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname) || ' CASCADE'; 
        END LOOP;

        -- Drop all unique indices on puzzle_votes that are NOT backing a constraint
        FOR r IN SELECT i.relname AS index_name 
                 FROM pg_class t 
                 JOIN pg_index ix ON t.oid = ix.indrelid 
                 JOIN pg_class i ON i.oid = ix.indexrelid 
                 WHERE t.relname = 'puzzle_votes' 
                   AND ix.indisunique = true 
                   AND ix.indisprimary = false 
                   AND NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conindid = ix.indexrelid) 
        LOOP 
          EXECUTE 'DROP INDEX IF EXISTS ' || quote_ident(r.index_name) || ' CASCADE'; 
        END LOOP;

        -- Explicitly drop the rogue_idx if the loop missed it for some reason
        EXECUTE 'DROP INDEX IF EXISTS rogue_idx CASCADE';

        -- Drop rogue columns that might be NOT NULL and causing failures
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'puzzle_votes' AND column_name = 'ticker') THEN
           EXECUTE 'ALTER TABLE puzzle_votes DROP COLUMN ticker CASCADE';
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'puzzle_votes' AND column_name = 'brand_name') THEN
           EXECUTE 'ALTER TABLE puzzle_votes DROP COLUMN brand_name CASCADE';
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'puzzle_votes' AND column_name = 'brand') THEN
           EXECUTE 'ALTER TABLE puzzle_votes DROP COLUMN brand CASCADE';
        END IF;
      END $$;
    `);

    // Remove legacy puzzle_id if it exists, as we now use brand_id exclusively
    try {
      await client.query('ALTER TABLE puzzle_votes DROP COLUMN IF EXISTS puzzle_id CASCADE');
      logger.info('Legacy column puzzle_id removed from puzzle_votes');
    } catch (e) {
      logger.warn('Failed to drop puzzle_id (might not exist): ' + e.message);
    }

    // 5. Final Constraints - Apply the new standard alone
    await client.query(`
      DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'puzzle_votes_user_date_brand_key') THEN
          ALTER TABLE puzzle_votes ADD CONSTRAINT puzzle_votes_user_date_brand_key UNIQUE(user_id, vote_date, brand_id);
        END IF;
      END $$;
    `);

    // 6. Secondary Tables
    await client.query('CREATE TABLE IF NOT EXISTS game_sessions (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id), puzzle_id INTEGER REFERENCES puzzles(id), score INTEGER DEFAULT 0, completed BOOLEAN DEFAULT FALSE, played_at TIMESTAMPTZ DEFAULT NOW())');
    await client.query('CREATE TABLE IF NOT EXISTS share_clicks (id SERIAL PRIMARY KEY, promoter_id INTEGER REFERENCES users(id), clicked_at TIMESTAMPTZ DEFAULT NOW())');

    // 7. Financial Literacy & Agentic Framework Tables
    try { await client.query('CREATE EXTENSION IF NOT EXISTS vector'); } catch (e) { logger.warn('Failed to ensure pgvector extension: ' + e.message); }
    await client.query('CREATE TABLE IF NOT EXISTS user_missions (user_id INTEGER REFERENCES users(id), mission_id VARCHAR(50), progress INTEGER DEFAULT 0, is_completed BOOLEAN DEFAULT FALSE, completed_at TIMESTAMPTZ, PRIMARY KEY(user_id, mission_id))');
    await client.query('ALTER TABLE user_missions ADD COLUMN IF NOT EXISTS mission_def JSONB');
    await client.query('CREATE TABLE IF NOT EXISTS user_strategy_tags (user_id INTEGER REFERENCES users(id), tag VARCHAR(100), calculated_at TIMESTAMPTZ DEFAULT NOW())');
    await client.query('CREATE TABLE IF NOT EXISTS user_content_views (user_id INTEGER REFERENCES users(id), content_id VARCHAR(100), viewed_at TIMESTAMPTZ DEFAULT NOW())');
    await client.query('CREATE TABLE IF NOT EXISTS user_personas (user_id INTEGER PRIMARY KEY REFERENCES users(id), profile_summary TEXT, embedding JSONB, last_updated TIMESTAMPTZ DEFAULT NOW())');

    // Add Difficulty to game_sessions and adjust unique constraint
    await client.query('ALTER TABLE game_sessions ADD COLUMN IF NOT EXISTS difficulty VARCHAR(20) DEFAULT \'easy\'');
    try { await client.query('ALTER TABLE game_sessions DROP CONSTRAINT IF EXISTS game_sessions_user_id_puzzle_id_key'); } catch (e) { }
    try { await client.query('DROP INDEX IF EXISTS game_sessions_user_id_puzzle_id_key CASCADE'); } catch (e) { }

    await client.query(`
      DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_sessions_user_puzzle_diff_key') THEN
          ALTER TABLE game_sessions ADD CONSTRAINT game_sessions_user_puzzle_diff_key UNIQUE(user_id, puzzle_id, difficulty);
        END IF;
      END $$;
    `);

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
