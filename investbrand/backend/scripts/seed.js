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

      // Use IST-aware "today" as the base
      const istOffsetMs = 5.5 * 60 * 60 * 1000;
      const nowIst = new Date(Date.now() + istOffsetMs);
      const todayStr = nowIst.toISOString().split('T')[0];

      // Start from day+2 (skip today's active puzzle and tomorrow's vote window)
      const startFromDay = 2;
      const daysToSeed = 45;

      console.log(`Today (IST): ${todayStr}. Seeding ${daysToSeed} days starting from day+${startFromDay}...`);

      let seeded = 0;
      let skipped = 0;

      for (let i = startFromDay; i < startFromDay + daysToSeed; i++) {
        // Calculate target date in IST
        const d = new Date(nowIst);
        d.setUTCDate(nowIst.getUTCDate() + i);
        const scheduledDate = d.toISOString().split('T')[0];

        // Calculate which brand this date SHOULD have based on its distance from the epoch
        const diffTime = Math.abs(new Date(scheduledDate) - PUZZLE_EPOCH);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        const brand = brands[diffDays % brands.length];

        // Only insert if no puzzle is already scheduled for this date (DO NOTHING on conflict)
        const result = await client.query(
          `INSERT INTO puzzles (brand_id, brand_name, company_name, ticker, logo_url, difficulty, sector, hint, scheduled_date)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
           ON CONFLICT (scheduled_date) DO NOTHING`,
          [
            brand.id,
            brand.brand,
            brand.company,
            brand.ticker,
            brand.logoUrl,
            (diffDays % 3) + 1,
            brand.sector,
            brand.insight,
            scheduledDate
          ]
        );

        if (result.rowCount > 0) {
          seeded++;
          if (seeded <= 5 || i % 10 === 0) console.log(`  ✓ Seeded: ${scheduledDate} → ${brand.brand}`);
        } else {
          skipped++;
          if (skipped <= 3) console.log(`  ~ Skipped: ${scheduledDate} (already scheduled)`);
        }
      }

      console.log(`\nDone. Seeded ${seeded} new dates, skipped ${skipped} already-scheduled dates.`);
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

