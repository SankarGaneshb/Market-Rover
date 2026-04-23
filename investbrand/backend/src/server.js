const VERSION = '1.2.0-socket-fix';
console.log(`--- BACKEND STARTING UP (v${VERSION}) ---`);
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

console.log('--- ENV CHECK ---');
console.log('PORT:', process.env.PORT);
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('DB_NAME:', process.env.IC_DB_NAME || process.env.DB_NAME);
console.log('JWT_SECRET_DEBUG:', !!process.env.JWT_SECRET);

const { initializePool } = require('./config/database');
const routes = require('./routes');
const errorHandler = require('./middleware/errorHandler');
const logger = require('./utils/logger');

console.log('--- MODULES LOADED ---');

const app = express();
// Trust proxy is required for express-rate-limit when running behind a reverse proxy (like Cloud Run or a local dev proxy)
app.set('trust proxy', 1);

const PORT = process.env.PORT || 8080;

let isDbReady = false;
let dbError = null;

app.use(helmet());
app.use(compression());
app.use(cors({
  origin: (origin, callback) => {
    const allowed = process.env.FRONTEND_URL?.split(',') || [];
    // In production, if FRONTEND_URL is set, restrict to it.
    // Otherwise, allow same-origin/internal requests or any during debug.
    if (!origin || allowed.indexOf(origin) !== -1 || allowed.length === 0 || process.env.NODE_ENV !== 'production') {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  optionsSuccessStatus: 200
}));

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: 'Too many requests, please try again later.'
});
app.use('/api/', limiter);
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

app.use((req, res, next) => {
  if (!isDbReady && req.path.startsWith('/api') && req.path !== '/api/health') {
    if (dbError) {
      return res.status(503).json({ error: `Database Startup/Migration Failed: ${dbError}` });
    }
    return res.status(503).json({ error: 'Server starting up, database migrating. Please try again in 5 seconds.' });
  }
  next();
});

app.use((req, res, next) => {
  logger.info('Incoming Request', {
    method: req.method,
    path: req.path,
    ip: req.ip,
    hasAuth: !!req.headers.authorization,
    origin: req.headers.origin
  });
  next();
});

app.use('/api', routes);
app.use(errorHandler);
// Global error handlers to catch startup crashes
process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at:', { promise, reason });
});

process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception:', { error: error.message, stack: error.stack });
  process.exit(1);
});

// Health check endpoint (can be checked by Cloud Run)
app.get('/api/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

const startServer = async () => {
  try {
    // 1. Initialize Database (Awaited to prevent race conditions)
    await initializePool();
    logger.info('Database pool and migrations initialized successfully');
    isDbReady = true;

    // 2. Start Listening
    const server = app.listen(PORT, '0.0.0.0', () => {
      console.log(`InvestBrand API explicitly listening on 0.0.0.0:${PORT}`);
      logger.info(`InvestBrand API live on port ${PORT}`, {
        node_env: process.env.NODE_ENV,
        port: PORT
      });
    });

    // 3. Graceful Shutdown
    process.on('SIGTERM', () => {
      logger.info('SIGTERM received: closing server');
      server.close(() => {
        logger.info('Server closed. Exiting.');
        process.exit(0);
      });
    });

  } catch (err) {
    logger.error('FATAL STARTUP ERROR:', {
      error: err.message,
      stack: err.stack,
      code: err.code
    });
    dbError = err.message;
    // We exit in production to force Cloud Run to restart the container
    if (process.env.NODE_ENV === 'production') {
      process.exit(1);
    }
  }
};

if (require.main === module) {
  startServer();
}

module.exports = app; // Export for testing and integrity checks
