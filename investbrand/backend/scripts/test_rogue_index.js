require('dotenv').config();
const { initializePool } = require('../src/config/database');
const { Client } = require('pg');

async function testLegacySchema() {
    process.env.DB_NAME = 'investcraft_test';

    const client = new Client({
        host: process.env.DB_HOST || 'localhost',
        port: parseInt(process.env.DB_PORT) || 5432,
        user: process.env.DB_USER || 'postgres',
        password: process.env.DB_PASSWORD || 'Invest123',
        database: 'postgres',
    });

    try {
        await client.connect();
        await client.query('DROP DATABASE IF EXISTS investcraft_test');
        await client.query('CREATE DATABASE investcraft_test');
        await client.end();

        const testClient = new Client({
            host: process.env.DB_HOST || 'localhost',
            port: parseInt(process.env.DB_PORT) || 5432,
            user: process.env.DB_USER || 'postgres',
            password: process.env.DB_PASSWORD || 'Invest123',
            database: 'investcraft_test',
        });

        await testClient.connect();
        console.log("Simulating legacy schema (puzzle_id NOT NULL)...");
        await testClient.query(`
      CREATE TABLE users (id SERIAL PRIMARY KEY, google_id VARCHAR UNIQUE, email VARCHAR UNIQUE);
      CREATE TABLE puzzles (id SERIAL PRIMARY KEY, brand_id INTEGER);
      CREATE TABLE puzzle_votes (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        puzzle_id INTEGER NOT NULL,
        vote_date DATE DEFAULT CURRENT_DATE
      );
      CREATE UNIQUE INDEX rogue_idx ON puzzle_votes(user_id, vote_date);
    `);
        await testClient.end();

        console.log("Running app migrations...");
        const pool = await initializePool();

        const colCheck = await pool.query(`
      SELECT column_name FROM information_schema.columns WHERE table_name = 'puzzle_votes'
    `);
        console.log("Current columns in puzzle_votes:", colCheck.rows.map(r => r.column_name).join(', '));

        console.log("Attempting to insert a vote for a brand...");
        try {
            await pool.query(
                `INSERT INTO puzzle_votes (user_id, brand_id, vote_date) VALUES ($1, $2, $3)`,
                [1, 101, '2026-03-07']
            );
            console.log("SUCCESS: Insert passed!");
        } catch (err) {
            console.error("FAIL: Insert failed! Error:", err.message);
            process.exit(1);
        }

        await pool.end();
    } catch (err) {
        console.error("Global Error:", err);
        process.exit(1);
    }
}

testLegacySchema();
