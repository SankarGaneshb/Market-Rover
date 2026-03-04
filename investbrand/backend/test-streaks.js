require('dotenv').config();
const { Pool } = require('pg');

async function testStreaks() {
    const pool = new Pool({
        host: process.env.DB_HOST || 'localhost',
        port: parseInt(process.env.DB_PORT) || 5432,
        database: process.env.DB_NAME || 'investcraft', // DB is still named investcraft locally
        user: process.env.DB_USER || 'postgres',
        password: process.env.DB_PASSWORD || 'postgres',
    });

    try {
        const client = await pool.connect();

        console.log('--- Testing Streak Increment Logic ---');

        // 1. Get a test user
        const userRes = await client.query(`SELECT id FROM users LIMIT 1`);
        if (userRes.rowCount === 0) {
            console.log('No users found in the database. Creating one...');
            await client.query(`INSERT INTO users (google_id, email, name) VALUES ('test_google_id_2', 'test2@example.com', 'Test User 2') ON CONFLICT DO NOTHING`);
        }

        const testUser = await client.query(`SELECT id FROM users LIMIT 1`);
        const userId = testUser.rows[0].id;

        console.log(`Testing with User ID: ${userId}`);

        // Test Case 1: Played yesterday 
        const yesterday = new Date(Date.now() - 86_400_000).toISOString().split('T')[0];
        await client.query('UPDATE users SET last_played = $1, streak = 5 WHERE id = $2', [yesterday, userId]);
        let reqRes = await simulatePuzzleCompletion(pool, userId);
        console.log('Test 1 (Yesterday -> Today): Expected Streak: 6 | Actual:', reqRes.streak);

        // Test Case 2: Played today already
        const today = new Date().toISOString().split('T')[0];
        await client.query('UPDATE users SET last_played = $1, streak = 10 WHERE id = $2', [today, userId]);
        reqRes = await simulatePuzzleCompletion(pool, userId);
        console.log('Test 2 (Today -> Today): Expected Streak: 10 | Actual:', reqRes.streak);

        // Test Case 3: Played 2 days ago
        const twoDaysAgo = new Date(Date.now() - (86_400_000 * 2)).toISOString().split('T')[0];
        await client.query('UPDATE users SET last_played = $1, streak = 20 WHERE id = $2', [twoDaysAgo, userId]);
        reqRes = await simulatePuzzleCompletion(pool, userId);
        console.log('Test 3 (2 Days Ago -> Today): Expected Streak: 1 | Actual:', reqRes.streak);

        // Test Case 4: Never played before
        await client.query('UPDATE users SET last_played = NULL, streak = 0 WHERE id = $1', [userId]);
        reqRes = await simulatePuzzleCompletion(pool, userId);
        console.log('Test 4 (Never Played -> Today): Expected Streak: 1 | Actual:', reqRes.streak);

        client.release();
        await pool.end();
    } catch (err) {
        console.error('Test failed:', err);
    }
}

async function simulatePuzzleCompletion(pool, userId) {
    // Logic from routes/puzzles.js
    const score = 100;

    // Fake total check
    const realTotal = 100;

    const userRes = await pool.query(
        'SELECT last_played, streak FROM users WHERE id = $1',
        [userId]
    );
    let { last_played, streak } = userRes.rows[0];

    const today = new Date().toISOString().split('T')[0];
    let newStreak = 1;

    if (last_played) {
        const lastPlayedDate = new Date(last_played);
        const todayDate = new Date(today);
        const diffTime = Math.abs(todayDate - lastPlayedDate);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            newStreak = streak;
        } else if (diffDays === 1) {
            newStreak = streak + 1;
        } else {
            newStreak = 1;
        }
    }

    return { streak: newStreak };
}

testStreaks();
