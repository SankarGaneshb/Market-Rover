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
  { company: 'Reliance Industries', ticker: 'RELIANCE', sector: 'Energy', diff: 2, hint: "India's largest conglomerate" },
  { company: 'TCS', ticker: 'TCS', sector: 'IT', diff: 1, hint: "Largest IT services" },
  { company: 'HDFC Bank', ticker: 'HDFCBANK', sector: 'Banking', diff: 1, hint: "Largest private bank" },
  { company: 'Infosys', ticker: 'INFY', sector: 'IT', diff: 1, hint: 'IT giant from Bengaluru' },
  { company: 'ICICI Bank', ticker: 'ICICIBANK', sector: 'Banking', diff: 2, hint: "Second-largest private bank" },
];
async function seed() {
  const client = await pool.connect();
  try {
    console.log('Seeding...');
    const base = new Date();
    for (let i = 0; i < NIFTY50.length; i++) {
      const c = NIFTY50[i];
      const d = new Date(base);
      d.setDate(base.getDate() + i);
      const dateStr = d.toISOString().split('T')[0];
      const logoSlug = c.company.toLowerCase().replace(/[^a-z0-9]+/g, '');
      await client.query(
        'INSERT INTO puzzles (company_name, ticker, logo_url, difficulty, sector, hint, scheduled_date) VALUES (,,,,,,) ON CONFLICT DO NOTHING',
        [c.company, c.ticker, https://logo.clearbit.com/.com, c.diff, c.sector, c.hint, dateStr]
      );
    }
    console.log('Done!');
  } finally { client.release(); await pool.end(); }
}
seed();
