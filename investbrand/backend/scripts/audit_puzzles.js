const { Pool } = require('pg');
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT) || 5432,
  database: process.env.DB_NAME || 'InvestBrand',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'Postgresql12#',
});

async function runAudit() {
  try {
    console.log('--- InvestBrand Community Success Audit ---');
    console.log('Days when user votes were SUCCESSFULLY honored:');

    // Identified specific dates where community vote WON
    const successHistory = await pool.query(`
      SELECT p.scheduled_date, p.company_name, p.selection_method,
             (SELECT COUNT(*) FROM puzzle_votes v WHERE v.vote_date = p.scheduled_date AND v.brand_id = p.brand_id) as confirmed_votes
      FROM puzzles p
      WHERE p.selection_method = 'voted'
      ORDER BY p.scheduled_date DESC
      LIMIT 100
    `);

    if (successHistory.rows.length === 0) {
      console.log('No "voted" daily puzzles found in history.');
    } else {
      console.log('Date       | Company             | Vote Count');
      console.log('-------------------------------------------');
      successHistory.rows.forEach(r => {
        const date = r.scheduled_date.toISOString().split('T')[0];
        console.log(`${date} | ${r.company_name.padEnd(19)} | ${r.confirmed_votes}`);
      });
    }

  } catch (err) {
    console.error('Audit Failed:', err.message);
  } finally {
    await pool.end();
  }
}

runAudit();
