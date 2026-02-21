const logger = require('../utils/logger');

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
  logger.error('Unhandled error', {
    message: err.message,
    stack: err.stack,
    method: req.method,
    path: req.path,
  });

  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({ error: 'Invalid JSON payload' });
  }

  const statusCode = err.statusCode || 500;
  const isProduction = process.env.NODE_ENV === 'production';
  const message = isProduction && statusCode === 500 ? 'Internal server error' : err.message;

  res.status(statusCode).json({ error: message });
}

module.exports = errorHandler;
