require('dotenv').config();
const { getPool, initializePool } = require('../src/config/database');
const { Client } = require('pg');

async function testRogueIndex() {
    process.env.DB_NAME = 'investcraft_test';

    const client = new Client({
        host: process.env.DB_HOST || 'localhost',
        port: parseInt(process.env.DB_PORT) || 5432,
        user: process.env.DB_USER || 'postgres',
        password: process.env.DB_PASSWORD || 'Invest123',
        database: 'investcraft_test',
    });

    try {
        await client.connect();

        // Create the table minimally if it doesn't exist
        await client.query(`
      CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, google_id VARCHAR UNIQUE, email VARCHAR UNIQUE);
      CREATE TABLE IF NOT EXISTS puzzle_votes (id SERIAL PRIMARY KEY, user_id INTEGER, brand_id INTEGER, vote_date DATE);
    `);

        // Simulate legacy rogue unique INDEX (NOT a constraint)
        await client.query(`
      TRUNCATE puzzle_votes CASCADE;
      DROP INDEX IF EXISTS legacy_rogue_idx;
      CREATE UNIQUE INDEX legacy_rogue_idx ON puzzle_votes(user_id, vote_date);
    `);

        console.log("Created rogue unique index on (user_id, vote_date)");
        await client.end();

        // Now run the application migration
        console.log("Running app migrations...");
        const pool = await initializePool();

        // Now verify the index is gone
        const check = await pool.query(`
      SELECT indexname 
      FROM pg_indexes 
      WHERE tablename = 'puzzle_votes' AND indexname = 'legacy_rogue_idx';
    `);

        if (check.rows.length > 0) {
            console.error("FAIL: Rogue index survived the migration!");
            process.exit(1);
        } else {
            console.log("SUCCESS: Rogue index was successfully destroyed by the migration.");
        }

        await pool.end();
    } catch (err) {
        console.error("Error:", err);
        process.exit(1);
    }
}

testRogueIndex();
