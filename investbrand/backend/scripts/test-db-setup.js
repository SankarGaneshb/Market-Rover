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
        await client.connect();
        console.log(`Connected to Postgres on ${host}:${port}`);

        // Check if test db exists
        const res = await client.query("SELECT 1 FROM pg_database WHERE datname='investcraft_test'");

        if (res.rowCount > 0) {
            console.log('Dropping existing investcraft_test database...');
            // Force disconnect other clients
            await client.query(`
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = 'investcraft_test'
          AND pid <> pg_backend_pid();
      `);
            await client.query('DROP DATABASE investcraft_test');
        }

        console.log('Creating investcraft_test database...');
        await client.query('CREATE DATABASE investcraft_test');
        console.log('Test database created successfully.');
    } catch (err) {
        console.error('Error setting up test database:', err.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

setupTestDb();
