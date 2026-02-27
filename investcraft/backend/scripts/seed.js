require('dotenv').config();
const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT) || 5432,
  database: process.env.DB_NAME || 'investcraft',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
});

// Helper to load brands from frontend data
function loadBrands() {
  const brandsFilePath = path.join(__dirname, '../../frontend/src/data/brands.js');
  const content = fs.readFileSync(brandsFilePath, 'utf8');
  const jsonMatch = content.match(/export const NIFTY50_BRANDS = (\[[\s\S]*\]);/);
  if (!jsonMatch) throw new Error('Could not parse brands.js');
  return JSON.parse(jsonMatch[1]);
}

async function seed() {
  const client = await pool.connect();
  try {
    const brands = loadBrands();
    const base = new Date();

    console.log(`Found ${brands.length} brands. Seeding puzzles...`);

    // Seed puzzles for the next 30 days starting from today
    for (let i = 0; i < 30; i++) {
      const brand = brands[i % brands.length];
      const d = new Date(base);
      d.setDate(base.getDate() + i);
      const scheduledDate = d.toISOString().split('T')[0];

      await client.query(
        `INSERT INTO puzzles (company_name, ticker, logo_url, difficulty, sector, hint, scheduled_date) 
         VALUES ($1, $2, $3, $4, $5, $6, $7) 
         ON CONFLICT (scheduled_date) 
         DO UPDATE SET 
            company_name = EXCLUDED.company_name,
            ticker = EXCLUDED.ticker,
            logo_url = EXCLUDED.logo_url,
            difficulty = EXCLUDED.difficulty,
            sector = EXCLUDED.sector,
            hint = EXCLUDED.hint`,
        [
          brand.company,
          brand.ticker,
          brand.logoUrl,
          (i % 3) + 1, // Cycle difficulty 1, 2, 3
          brand.sector,
          brand.insight,
          scheduledDate
        ]
      );

      if (i % 5 === 0) console.log(`Seeded date: ${scheduledDate}`);
    }

    console.log('Database seeding completed successfully.');
  } catch (err) {
    console.error('Seeding failed:', err);
  } finally {
    client.release();
    await pool.end();
  }
}

seed();

