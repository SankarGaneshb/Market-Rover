require('dotenv').config();
const { Client } = require('pg');

async function setupTestDb() {
    const host = process.env.DB_HOST || 'localhost';
    const port = parseInt(process.env.DB_PORT) || 5432;
    const user = process.env.DB_USER || 'postgres';
    const password = process.env.DB_PASSWORD || 'postgres';

    // Connect to default 'postgres' database to create test database
    const client = new Client({
        host,
        port,
        user,
        password,
        database: 'postgres',
    });

    try {
        let connected = false;
        let attempts = 0;
        while (!connected && attempts < 10) {
            attempts++;
            try {
                await client.connect();
                connected = true;
                console.log(`Connected to Postgres on ${host}:${port} (attempt ${attempts})`);
            } catch (connErr) {
                console.log(`Postgres not ready yet (attempt ${attempts}/10): ${connErr.message}. Retrying in 2s...`);
                await new Promise(r => setTimeout(r, 2000));
            }
        }

        if (!connected) {
            throw new Error(`Could not connect to Postgres on ${host}:${port} after 10 attempts.`);
        }

        // Check if test db exists
        const res = await client.query("SELECT 1 FROM pg_database WHERE datname='investbrand_test'");

        if (res.rowCount > 0) {
            console.log('Dropping existing investbrand_test database...');
            // Force disconnect other clients
            await client.query(`
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'investbrand_test'
                  AND pid <> pg_backend_pid();
            `);
            await client.query('DROP DATABASE "investbrand_test"');
        }

        console.log('Creating investbrand_test database...');
        await client.query('CREATE DATABASE "investbrand_test"');
        console.log('Test database created successfully.');
    } catch (err) {
        console.error('Error setting up test database:', err.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

if (require.main === module) {
    setupTestDb();
}

module.exports = { setupTestDb };
