jest.mock('../middleware/auth', () => ({
    authenticate: (req, res, next) => {
        req.user = { id: 1, email: 'integration_test@example.com' };
        next();
    }
}));

const request = require('supertest');
const express = require('express');
const { initializePool, getPool } = require('../config/database');
const puzzleRoutes = require('../routes/puzzles');

// We intercept auth logic by inserting our own middleware before the router
const app = express();
app.use(express.json());

app.use('/api/puzzles', puzzleRoutes);

describe('Database Integration: Puzzle Votes', () => {
    let pool;

    beforeAll(async () => {
        // This connects to process.env.DB_NAME which will be set to 'investcraft_test' by package.json scripts
        process.env.DB_HOST = process.env.DB_HOST || 'localhost';
        process.env.DB_USER = process.env.DB_USER || 'postgres';
        process.env.DB_PASSWORD = process.env.DB_PASSWORD || 'Invest123';
        process.env.DB_NAME = 'investcraft_test';

        // Explicitly do not mock the database - connect to real Postgres test database
        pool = await initializePool();

        // Ensure user 1 exists to satisfy foreign key constraints
        await pool.query(`
      INSERT INTO users (id, google_id, email, name)
      VALUES (1, 'mock-google-id', 'integration_test@example.com', 'Integration Test User')
      ON CONFLICT (id) DO NOTHING
    `);

        // Clear any previous votes from previous test runs
        await pool.query('DELETE FROM puzzle_votes');
    });

    afterAll(async () => {
        if (pool) {
            await pool.end();
        }
    });

    it('CRITICAL TEST: Should allow voting for TWO DIFFERENT brands on the SAME DAY', async () => {
        // 1. Vote for Brand 100
        const res1 = await request(app).post('/api/puzzles/vote').send({ brandId: 100 });
        expect(res1.statusCode).toBe(200);
        expect(res1.body.success).toBe(true);

        // 2. Vote for Brand 200 on the exact same day
        const res2 = await request(app).post('/api/puzzles/vote').send({ brandId: 200 });

        // If the database has an incorrect "UNIQUE(user_id, vote_date)" constraint,
        // this will throw a 500 error instead of passing, which correctly fails the test.
        expect(res2.statusCode).toBe(200);
        expect(res2.body.success).toBe(true);

        // Verify both votes are in the DB
        const dbCheck = await pool.query('SELECT brand_id FROM puzzle_votes WHERE user_id = 1');
        const votedBrands = dbCheck.rows.map(r => r.brand_id).sort();

        expect(votedBrands).toEqual([100, 200]);
    });

    it('Should gracefully do nothing when voting for the SAME brand TWICE on the SAME DAY', async () => {
        // 1. Initial vote
        const res1 = await request(app).post('/api/puzzles/vote').send({ brandId: 300 });
        expect(res1.statusCode).toBe(200);

        // 2. Duplicate vote immediately after
        const res2 = await request(app).post('/api/puzzles/vote').send({ brandId: 300 });

        // It should STILL return 200 due to ON CONFLICT DO NOTHING, not crash
        expect(res2.statusCode).toBe(200);
        expect(res2.body.success).toBe(true);

        // However, the database should only contain ONE row for brand 300
        const dbCheck = await pool.query('SELECT COUNT(*) FROM puzzle_votes WHERE user_id = 1 AND brand_id = 300');
        expect(parseInt(dbCheck.rows[0].count)).toBe(1);
    });
});
