const path = require('path');
require('dotenv').config({ path: path.join(__dirname, 'investbrand/backend/.env') });
const { initializePool } = require(path.join(__dirname, 'investbrand/backend/src/config/database'));

async function verifyMigration() {
    try {
        console.log('Starting migration verification...');
        console.log('DB_NAME:', process.env.DB_NAME);
        const pool = await initializePool();
        console.log('Migration finished successfully.');

        // Check constraints
        const res = await pool.query(`
      SELECT conname, pg_get_constraintdef(oid) 
      FROM pg_constraint 
      WHERE conrelid = 'puzzle_votes'::regclass;
    `);
        console.log('Current constraints for puzzle_votes:');
        console.table(res.rows);

        await pool.end();
    } catch (err) {
        console.error('Migration verification failed:', err.message);
        process.exit(1);
    }
}

verifyMigration();
