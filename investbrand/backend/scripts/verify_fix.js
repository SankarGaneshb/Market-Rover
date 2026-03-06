const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });
const { initializePool } = require('../src/config/database');
const { Client } = require('pg');

async function verifyFix() {
    process.env.DB_NAME = 'investcraft_verify';

    const client = new Client({
        host: process.env.DB_HOST || 'localhost',
        port: parseInt(process.env.DB_PORT) || 5432,
        user: process.env.DB_USER || 'postgres',
        password: process.env.DB_PASSWORD || 'Invest123',
        database: 'postgres',
    });

    try {
        await client.connect();
        await client.query('DROP DATABASE IF EXISTS investcraft_verify');
        await client.query('CREATE DATABASE investcraft_verify');
        await client.end();

        const testClient = new Client({
            host: process.env.DB_HOST || 'localhost',
            port: parseInt(process.env.DB_PORT) || 5432,
            user: process.env.DB_USER || 'postgres',
            password: process.env.DB_PASSWORD || 'Invest123',
            database: 'investcraft_verify',
        });

        await testClient.connect();
        console.log("Setting up legacy state (2-column unique index)...");
        await testClient.query(`
            CREATE TABLE users (id SERIAL PRIMARY KEY, google_id VARCHAR(255) UNIQUE NOT NULL, email VARCHAR(255) UNIQUE NOT NULL);
            CREATE TABLE puzzle_votes (
                id SERIAL PRIMARY KEY, 
                user_id INTEGER, 
                vote_date DATE NOT NULL,
                brand_id INTEGER
            );
            -- This is the rogue index causing the error in production
            CREATE UNIQUE INDEX rogue_idx ON puzzle_votes(user_id, vote_date);
            INSERT INTO users (google_id, email) VALUES ('google_123', 'test@example.com');
        `);
        await testClient.end();

        console.log("Running updated migrations...");
        const pool = await initializePool();

        console.log("Checking if rogue_idx still exists...");
        const indexCheck = await pool.query(`
            SELECT count(*) FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            WHERE t.relname = 'puzzle_votes' AND i.relname = 'rogue_idx';
        `);

        if (parseInt(indexCheck.rows[0].count) === 0) {
            console.log("SUCCESS: rogue_idx was removed!");
        } else {
            console.error("FAIL: rogue_idx still exists!");
            process.exit(1);
        }

        console.log("Attempting multi-voting (different brands, same day)...");
        try {
            const userId = 1;
            const tomorrow = '2026-03-07';

            console.log("Submitting Vote 1 (Brand 101)...");
            await pool.query(
                `INSERT INTO puzzle_votes (user_id, brand_id, vote_date) VALUES ($1, $2, $3)
                 ON CONFLICT (user_id, vote_date, brand_id) DO NOTHING`,
                [userId, 101, tomorrow]
            );

            console.log("Submitting Vote 2 (Brand 102) - This would fail on prod...");
            await pool.query(
                `INSERT INTO puzzle_votes (user_id, brand_id, vote_date) VALUES ($1, $2, $3)
                 ON CONFLICT (user_id, vote_date, brand_id) DO NOTHING`,
                [userId, 102, tomorrow]
            );

            const voteCount = await pool.query(`SELECT count(*) FROM puzzle_votes WHERE user_id = $1 AND vote_date = $2`, [userId, tomorrow]);
            if (parseInt(voteCount.rows[0].count) === 2) {
                console.log("SUCCESS: Multi-voting works!");
            } else {
                console.error("FAIL: Expected 2 votes, found " + voteCount.rows[0].count);
                process.exit(1);
            }
        } catch (err) {
            console.error("FAIL: Error during multi-voting test:", err.message);
            process.exit(1);
        }

        await pool.end();
        console.log("\nVERIFICATION COMPLETE: ALL SYSTEMS NOMINAL");
    } catch (err) {
        console.error("Global Error:", err);
        process.exit(1);
    }
}

verifyFix();
