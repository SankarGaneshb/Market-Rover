console.log('--- BACKEND STARTING UP ---');
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

console.log('--- ENV CHECK ---');
console.log('PORT:', process.env.PORT);
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('DB_NAME:', process.env.IC_DB_NAME || process.env.DB_NAME);

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

const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`InvestCraft API explicitly listening on 0.0.0.0:${PORT}`);
  logger.info(`InvestCraft API starting on port ${PORT}`, {
    node_env: process.env.NODE_ENV,
    port: PORT,
    host: '0.0.0.0'
  });

  // Database initialization happens in the background
  initializePool()
    .then(() => {
      logger.info('Database pool and migrations initialized successfully');
      isDbReady = true;
    })
    .catch(err => {
      logger.error('LATE DATABASE FAILURE:', { error: err.message, stack: err.stack });
      dbError = err.message;
    });
});

process.on('SIGTERM', () => {
  logger.info('SIGTERM received: closing server');
  server.close(() => {
    process.exit(0);
  });
});
