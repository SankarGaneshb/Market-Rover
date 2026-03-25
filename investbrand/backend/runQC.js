require('dotenv').config();
const { initializePool, getPool } = require('./src/config/database');
const { runQualityCheck } = require('./src/agents/qcAgent');
const logger = require('./src/utils/logger');

async function main() {
  try {
    await initializePool();
    const result = await runQualityCheck();
    console.log('--- QC AUDIT COMPLETE ---');
    console.log('Actions Taken:', JSON.stringify(result.actions, null, 2));
    process.exit(0);
  } catch (err) {
    logger.error('CRITICAL: QC Script failed', err);
    process.exit(1);
  }
}

main();
