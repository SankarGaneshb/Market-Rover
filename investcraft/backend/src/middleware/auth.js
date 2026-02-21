const jwt = require('jsonwebtoken');
const { getPool } = require('../config/database');

async function authenticate(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Authentication required' });
  }

  try {
    const token = authHeader.split(' ')[1];
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    const pool = getPool();
    const result = await pool.query(
      'SELECT id, name, email FROM users WHERE id = $1',
      [decoded.userId]
    );

    if (!result.rows[0]) {
      return res.status(401).json({ error: 'User not found' });
    }

    req.user = result.rows[0];
    next();
  } catch (err) {
    res.status(401).json({ error: 'Invalid or expired token' });
  }
}

module.exports = { authenticate };
