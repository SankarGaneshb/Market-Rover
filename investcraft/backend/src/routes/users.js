const express = require('express');
const router  = express.Router();
const { getPool } = require('../config/database');
const { authenticate } = require('../middleware/auth');

// GET /api/users/me
router.get('/me', authenticate, async (req, res) => {
  const pool = getPool();
  try {
    const result = await pool.query(
      `SELECT u.*,
              COUNT(gs.id) FILTER (WHERE gs.completed = true) AS puzzles_completed
       FROM users u
       LEFT JOIN game_sessions gs ON u.id = gs.user_id
       WHERE u.id = $1
       GROUP BY u.id`,
      [req.user.id]
    );
    const u = result.rows[0];
    res.json({
      id:               u.id,
      name:             u.name,
      email:            u.email,
      avatar:           u.avatar_url,
      streak:           u.streak,
      score:            u.total_score,
      puzzlesCompleted: parseInt(u.puzzles_completed) || 0,
      joinedAt:         u.created_at,
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch profile' });
  }
});

module.exports = router;
