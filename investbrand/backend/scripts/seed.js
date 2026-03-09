require('dotenv').config();
const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');

function getPool() {
  const isProduction = process.env.NODE_ENV === 'production';

  if (isProduction) {
    const socketPath = process.env.DB_HOST || `/cloudsql/${process.env.CLOUD_SQL_CONNECTION_NAME}`;
    console.log(`Connecting via socket: ${socketPath}`);
    return new Pool({
      host: socketPath,
      database: process.env.DB_NAME || 'postgres',
      user: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD,
    });
  }

  return new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'investcraft',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'postgres',
  });
}

// Helper to load brands from frontend data
function loadBrands() {
  const localPath = path.join(__dirname, '../src/data/brands.js');
  const fallbackPath = path.join(__dirname, '../../frontend/src/data/brands.js');

  const brandsFilePath = fs.existsSync(localPath) ? localPath : fallbackPath;
  console.log(`Loading brands from: ${brandsFilePath}`);

  const content = fs.readFileSync(brandsFilePath, 'utf8');
  const jsonMatch = content.match(/export const NIFTY50_BRANDS = (\[[\s\S]*\]);/);
  if (!jsonMatch) throw new Error('Could not parse brands.js');
  return JSON.parse(jsonMatch[1]);
}

async function seed() {
  let pool;
  try {
    pool = getPool();
    const client = await pool.connect();
    try {
      const brands = loadBrands();
      const PUZZLE_EPOCH = new Date('2026-02-01'); // Fixed starting point for brand rotation
      const base = new Date();

      console.log(`Found ${brands.length} brands. Seeding puzzles...`);

      // Seed puzzles for the next 30 days starting from today
      for (let i = 0; i < 45; i++) {
        const d = new Date(base);
        d.setDate(base.getDate() + i);
        const scheduledDate = d.toISOString().split('T')[0];

        // Calculate which brand this date SHOULD have based on its distance from the epoch
        const diffTime = Math.abs(d - PUZZLE_EPOCH);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        const brand = brands[diffDays % brands.length];

        await client.query(
          `INSERT INTO puzzles (brand_id, brand_name, company_name, ticker, logo_url, difficulty, sector, hint, scheduled_date) 
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) 
           ON CONFLICT (scheduled_date) 
           DO UPDATE SET 
              brand_id = EXCLUDED.brand_id,
              brand_name = EXCLUDED.brand_name,
              company_name = EXCLUDED.company_name,
              ticker = EXCLUDED.ticker,
              logo_url = EXCLUDED.logo_url,
              sector = EXCLUDED.sector,
              hint = EXCLUDED.hint`,
          [
            brand.id,
            brand.brand,
            brand.company,
            brand.ticker,
            brand.logoUrl,
            (diffDays % 3) + 1, // Consistent difficulty
            brand.sector,
            brand.insight,
            scheduledDate
          ]
        );

        if (i % 5 === 0) console.log(`Seeded date: ${scheduledDate} -> ${brand.brand}`);
      }

      console.log('Database seeding completed successfully.');
    } catch (err) {
      console.error('Seeding query failed:', err);
      process.exit(1);
    } finally {
      client.release();
    }
  } catch (err) {
    console.error('Pool initialization or connection failed:', err);
    process.exit(1);
  } finally {
    if (pool) await pool.end();
  }
}

seed();

