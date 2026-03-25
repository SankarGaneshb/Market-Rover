const logger = require('../utils/logger');
const { analyzeError } = require('../agents/opsSupportAgent');

// eslint-disable-next-line no-unused-vars
async function errorHandler(err, req, res, next) {
  logger.error('Unhandled error', {
    message: err.message,
    stack: err.stack,
    method: req.method,
    path: req.path,
  });

  // Trigger AI analysis in the background (log it later)
  if (process.env.GOOGLE_API_KEY) {
    analyzeError(err, req).then(analysis => {
      if (analysis) {
        logger.info('Ops Support Agent Analysis:', analysis);
      }
    });
  }

  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({ error: 'Invalid JSON payload' });
  }

  const statusCode = err.statusCode || 500;
  const isProduction = process.env.NODE_ENV === 'production';
  const message = isProduction && statusCode === 500 ? 'Internal server error' : err.message;

  res.status(statusCode).json({ error: message });
}

module.exports = errorHandler;
