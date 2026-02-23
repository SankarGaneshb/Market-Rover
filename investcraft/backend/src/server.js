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
const PORT = process.env.PORT || 8080;

app.use(helmet());
app.use(compression());
app.use(cors({
  origin: process.env.FRONTEND_URL?.split(',') || '*',
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
  logger.info('Request', { method: req.method, path: req.path, ip: req.ip });
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
    .then(() => logger.info('Database pool and migrations initialized successfully'))
    .catch(err => logger.error('LATE DATABASE FAILURE:', { error: err.message, stack: err.stack }));
});

process.on('SIGTERM', () => {
  logger.info('SIGTERM received: closing server');
  server.close(() => {
    process.exit(0);
  });
});
