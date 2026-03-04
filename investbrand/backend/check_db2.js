const { Client } = require('pg');
require('dotenv').config({ path: './.env' });

async function test() {
    const client = new Client({
        connectionString: process.env.DATABASE_URL
    });
    await client.connect();
    const res = await client.query('SELECT ticker, COUNT(*), count(scheduled_date) as played FROM puzzles GROUP BY ticker HAVING COUNT(*) > 1');
    console.log('Duplicates in puzzles:', res.rows);
    const jio = await client.query('SELECT id, scheduled_date FROM puzzles WHERE ticker = \'JIOFIN\'');
    console.log('Jio schedules:', jio.rows);
    await client.end();
}
test();
