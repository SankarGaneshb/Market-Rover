const { Client } = require('pg');
async function check() {
    const client = new Client({
        host: 'localhost',
        port: 5432,
        user: 'postgres',
        password: 'Invest123',
        database: 'investcraft_test'
    });
    try {
        await client.connect();
        const res = await client.query("SELECT attname FROM pg_attribute WHERE attrelid = 'puzzle_votes'::regclass AND attnum > 0");
        console.log("EXACT_COLUMNS:", JSON.stringify(res.rows.map(r => r.attname)));
    } catch (e) {
        console.error(e);
    } finally {
        await client.end();
    }
}
check();
