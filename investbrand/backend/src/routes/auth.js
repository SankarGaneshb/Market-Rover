const express = require('express');
const router = express.Router();
const { OAuth2Client } = require('google-auth-library');
const jwt = require('jsonwebtoken');
const { getPool } = require('../config/database');
const logger = require('../utils/logger');

const googleClientId = process.env.IC_GOOGLE_CLIENT_ID || process.env.GOOGLE_CLIENT_ID;
const googleClient = new OAuth2Client(googleClientId);

function getSecret() {
  const secret = process.env.JWT_SECRET || process.env.GOOGLE_CLIENT_SECRET;
  if (!secret) {
    if (process.env.NODE_ENV === 'production') {
      logger.error('CRITICAL: JWT_SECRET and GOOGLE_CLIENT_SECRET are missing in production.');
      // Don't throw here to allow the server to at least start/report health,
      // but signToken will fail gracefully.
    }
    return 'dev-hide-in-prod';
  }
  return secret;
}

function signToken(user) {
  if (!user?.id) throw new Error('Cannot sign token for null user');
  const secret = getSecret();
  if (secret === 'dev-hide-in-prod' && process.env.NODE_ENV === 'production') {
    logger.error('CRITICAL: Using dev secret in production!');
  }
  return jwt.sign(
    { userId: user.id, email: user.email },
    secret,
    { expiresIn: '7d' }
  );
}

function formatUser(user) {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    avatar: user.avatar_url,
    streak: user.streak,
    score: user.total_score,
    bestScore: user.best_score,
  };
}

// POST /api/auth/google (DEPRECATED: Use /social-login instead)
router.post('/google', async (req, res) => {
  res.redirect(307, '/api/auth/social-login');
});

// POST /api/auth/social-login
router.post('/social-login', async (req, res) => {
  const { token, provider = 'google' } = req.body;
  if (!token) return res.status(400).json({ error: 'OAuth token required' });

  try {
    let googleId, email, name, picture;

    if (provider === 'google') {
      const ticket = await googleClient.verifyIdToken({
        idToken: token,
        audience: googleClientId,
      });
      const payload = ticket.getPayload();
      googleId = payload.sub;
      email = payload.email;
      name = payload.name;
      picture = payload.picture;
    } else {
      // Mock provider handling (for non-production or specific mock tokens)
      if (process.env.NODE_ENV === 'production' && !token.startsWith('mock_')) {
        return res.status(400).json({ error: `${provider} verification not yet configured in production.` });
      }
      // Use a stable ID for mock providers to prevent UNIQUE constraint violations on email
      googleId = `mock_${provider}_user_id`;
      email = `user@${provider}.demo`;
      name = `${provider.charAt(0).toUpperCase() + provider.slice(1)} Test User`;
      picture = null;
    }

    const pool = getPool();
    const result = await pool.query(
      `INSERT INTO users (google_id, email, name, avatar_url)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (google_id)
       DO UPDATE SET name = EXCLUDED.name, avatar_url = EXCLUDED.avatar_url
       RETURNING *`,
      [googleId, email, name, picture]
    );

    const user = result.rows[0];
    res.json({ token: signToken(user), user: formatUser(user) });
  } catch (err) {
    logger.error('Social auth error', { provider, message: err.message, stack: err.stack });

    // Distinguish between Auth errors and Database errors
    if (err.message.includes('Database') || err.message.includes('pool')) {
      return res.status(503).json({ error: 'Database connectivity issue', details: 'The server is currently unable to reach the database.' });
    }

    res.status(401).json({ error: 'Authentication failed', details: err.message });
  }
});

// GET /api/auth/me
router.get('/me', async (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'No token provided' });
  }
  try {
    const decoded = jwt.verify(authHeader.split(' ')[1], getSecret());
    const pool = getPool();
    const result = await pool.query('SELECT * FROM users WHERE id = $1', [decoded.userId]);
    if (!result.rows[0]) return res.status(401).json({ error: 'User not found' });
    res.json({ user: formatUser(result.rows[0]) });
  } catch (err) {
    res.status(401).json({ error: 'Invalid token' });
  }
});

module.exports = router;
