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

async function startServer() {
  try {
    await initializePool();
    logger.info('Database pool initialized');
    app.listen(PORT, () => {
      logger.info(`InvestCraft API running on port ${PORT}`, {
        environment: process.env.NODE_ENV,
        port: PORT
      });
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

process.on('SIGTERM', () => {
  logger.info('SIGTERM received: closing server');
  process.exit(0);
});

startServer();
