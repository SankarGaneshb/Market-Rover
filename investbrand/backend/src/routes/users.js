const express = require('express');
const router = express.Router();
const { getPool } = require('../config/database');
const { authenticate } = require('../middleware/auth');

// GET /api/users/me
router.get('/me', authenticate, async (req, res) => {
  const pool = getPool();
  try {
    const result = await pool.query(
      `SELECT u.*,
              COUNT(gs.id) FILTER (WHERE gs.completed = true) AS puzzles_completed,
              COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'easy'), 0)::int AS easy_score,
              COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'medium'), 0)::int AS medium_score,
              COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'hard'), 0)::int AS hard_score,
              (SELECT tag FROM user_strategy_tags WHERE user_id = u.id ORDER BY calculation_date DESC LIMIT 1) as strategy_tag,
              ARRAY(SELECT mission_def->>'reward' FROM user_missions WHERE user_id = u.id AND is_completed = true) as unlocked_rewards
       FROM users u
       LEFT JOIN game_sessions gs ON u.id = gs.user_id
       WHERE u.id = $1
       GROUP BY u.id`,
      [req.user.id]
    );

    const u = result.rows[0];
    res.json({
      id: u.id,
      name: u.name,
      email: u.email,
      avatar: u.avatar_url,
      streak: u.streak,
      score: u.total_score,
      easyScore: u.easy_score,
      mediumScore: u.medium_score,
      hardScore: u.hard_score,
      bestScore: u.best_score,
      puzzlesCompleted: parseInt(u.puzzles_completed) || 0,
      joinedAt: u.created_at,
      strategyTag: u.strategy_tag || 'Market Explorer',
      badges: u.unlocked_rewards || []
    });

  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch profile' });
  }
});

// GET /api/users/me/sessions
router.get('/me/sessions', authenticate, async (req, res) => {
  const pool = getPool();
  try {
    const result = await pool.query(
      'SELECT puzzle_id, completed, score, played_at FROM game_sessions WHERE user_id = $1',
      [req.user.id]
    );
    res.json(result.rows);
  } catch (err) {
    console.error('Error fetching sessions:', err);
    res.status(500).json({ error: 'Failed to fetch sessions', details: err.message });
  }
});

module.exports = router;
