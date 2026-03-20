const { Client } = require('pg');

const passwords = ['postgres', 'password', 'admin', 'root', '123456', '', 'Invest12#', 'Investcraft12#'];

async function test() {
    for (const p of passwords) {
        const client = new Client({
            host: 'localhost',
            port: 5432,
            user: 'postgres',
            password: p,
            database: 'postgres' // connect to default database
        });
        try {
            await client.connect();
            console.log(`SUCCESS: ${p === '' ? '<empty>' : p}`);
            await client.end();
            return;
        } catch (e) {
            console.log(`FAILED: ${p === '' ? '<empty>' : p}`);
        }
    }
    console.log("All common passwords failed.");
}

test();
