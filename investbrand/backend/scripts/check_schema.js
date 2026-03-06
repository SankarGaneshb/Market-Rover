const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  host: process.env.IC_DB_HOST || process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.IC_DB_PORT || process.env.DB_PORT || '5432'),
  database: process.env.IC_DB_NAME || process.env.DB_NAME || 'investcraft',
  user: process.env.IC_DB_USER || process.env.DB_USER || 'postgres',
  password: process.env.IC_DB_PASS || process.env.DB_PASSWORD || 'Invest123',
});

async function checkSchema() {
  try {
    const res = await pool.query(`
      SELECT 
        conname AS constraint_name, 
        contype AS constraint_type,
        pg_get_constraintdef(c.oid) AS constraint_definition
      FROM pg_constraint c
      JOIN pg_namespace n ON n.oid = c.connamespace
      WHERE n.nspname = 'public' AND conrelid = 'puzzle_votes'::regclass;
    `);
    console.log('Constraints for puzzle_votes:');
    console.table(res.rows);

    const cols = await pool.query(`
      SELECT column_name, data_type 
      FROM information_schema.columns 
      WHERE table_name = 'puzzle_votes';
    `);
    console.log('Columns for puzzle_votes:');
    console.table(cols.rows);

  } catch (err) {
    console.error('Error checking schema:', err.message);
  } finally {
    await pool.end();
  }
}

checkSchema();
