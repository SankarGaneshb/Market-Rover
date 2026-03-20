const { Pool } = require('pg');

async function testCreds(user, password, database) {
  try {
    const pool = new Pool({ host: 'localhost', port: 5432, database, user, password });
    await pool.query('SELECT 1');
    await pool.end();
    console.log(`[SUCCESS] Connected! User: ${user}, Password: ${password}, DB: ${database}`);
    return true;
  } catch (err) {
    console.log(`[FAILED] User: ${user}, Password: ${password}, DB: ${database} - Error: ${err.message}`);
    return false;
  }
}

async function runTests() {
  const users = ['postgres', 'postgresql', 'admin', 'root'];
  const passwords = ['postgres', 'Postgresql12#', 'admin', 'root', 'password', ''];
  const databases = ['investcraft', 'investbrand', 'postgres'];

  for (const db of databases) {
    for (const u of users) {
      for (const p of passwords) {
        const success = await testCreds(u, p, db);
        if (success) {
            console.log("\nFound valid credentials!");
            process.exit(0);
        }
      }
    }
  }
  console.log("\nCould not find valid credentials.");
}

runTests();
