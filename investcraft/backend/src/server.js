const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const { initializePool } = require('./config/database');
const routes = require('./routes');
const errorHandler = require('./middleware/errorHandler');
const logger = require('./utils/logger');

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
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// Health check endpoint (can be checked by Cloud Run)
app.get('/api/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

const server = app.listen(PORT, async () => {
  logger.info(`InvestCraft API starting on port ${PORT}`, {
    node_env: process.env.NODE_ENV,
    port: PORT,
    has_db_conn: !!process.env.CLOUD_SQL_CONNECTION_NAME
  });

  try {
    await initializePool();
    logger.info('Database pool initialized and connected');
  } catch (error) {
    logger.error('Database initialization failed in background:', error);
    // We don't exit here, so we can see the logs in Cloud Run
  }
});

process.on('SIGTERM', () => {
  logger.info('SIGTERM received: closing server');
  server.close(() => {
    process.exit(0);
  });
});
