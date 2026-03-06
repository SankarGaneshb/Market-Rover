const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
    host: process.env.IC_DB_HOST || process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.IC_DB_PORT || process.env.DB_PORT || '5432'),
    database: process.env.IC_DB_NAME || process.env.DB_NAME || 'investcraft',
    user: process.env.IC_DB_USER || process.env.DB_USER || 'postgres',
    password: process.env.IC_DB_PASS || process.env.DB_PASSWORD || 'Invest123',
});

async function run() {
    try {
        const res = await pool.query(`
      SELECT
          t.relname as table_name,
          i.relname as index_name,
          a.attname as column_name,
          ix.indisunique,
          ix.indisprimary
      FROM
          pg_class t,
          pg_class i,
          pg_index ix,
          pg_attribute a
      WHERE
          t.oid = ix.indrelid
          AND i.oid = ix.indexrelid
          AND a.attrelid = t.oid
          AND a.attnum = ANY(ix.indkey)
          AND t.relname = 'puzzle_votes'
      ORDER BY
          t.relname,
          i.relname;
    `);
        console.table(res.rows);
    } catch (err) {
        console.error(err);
    } finally {
        await pool.end();
    }
}
run();
