require('dotenv').config();
const { Pool } = require('pg');
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT) || 5432,
  database: process.env.DB_NAME || 'investcraft',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
});
const NIFTY50 = [
  { company: 'Reliance', ticker: 'RELIANCE', sector: 'Energy', diff: 2, hint: 'Largest conglomerate' },
  { company: 'TCS', ticker: 'TCS', sector: 'IT', diff: 1, hint: 'Largest IT company' },
];
async function seed() {
  const client = await pool.connect();
  try {
    const base = new Date();
    for (let i = 0; i < NIFTY50.length; i++) {
      const c = NIFTY50[i], d = new Date(base);
      d.setDate(base.getDate() + i);
      await client.query('INSERT INTO puzzles (company_name,ticker,logo_url,difficulty,sector,hint,scheduled_date) VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING',
        [c.company, c.ticker, 'https://logo.clearbit.com/'+c.company.toLowerCase()+'.com', c.diff, c.sector, c.hint, d.toISOString().split('T')[0]]);
    }
  } finally { client.release(); await pool.end(); }
}
seed();
