const express = require('express');
const router  = express.Router();
const { getPool } = require('../config/database');
const logger = require('../utils/logger');

// GET /api/leaderboard?type=all-time|weekly|daily
router.get('/', async (req, res) => {
  const pool = getPool();
  const type = req.query.type || 'all-time';

  try {
    let result;

    if (type === 'daily') {
      const today = new Date().toISOString().split('T')[0];
      result = await pool.query(
        `SELECT u.id, u.name, u.avatar_url, u.streak,
                gs.score, gs.moves_used, gs.time_taken
         FROM users u
         JOIN game_sessions gs ON u.id = gs.user_id
         JOIN puzzles p        ON gs.puzzle_id = p.id
         WHERE p.scheduled_date = $1
         ORDER BY gs.score DESC, gs.time_taken ASC
         LIMIT 50`,
        [today]
      );
    } else if (type === 'weekly') {
      result = await pool.query(
        `SELECT u.id, u.name, u.avatar_url, u.streak,
                SUM(gs.score)::int AS score,
                COUNT(gs.id)::int  AS games_played
         FROM users u
         JOIN game_sessions gs ON u.id = gs.user_id
         WHERE gs.played_at >= NOW() - INTERVAL '7 days'
         GROUP BY u.id, u.name, u.avatar_url, u.streak
         ORDER BY score DESC
         LIMIT 50`
      );
    } else {
      result = await pool.query(
        `SELECT id, name, avatar_url, streak, total_score AS score
         FROM users
         ORDER BY total_score DESC
         LIMIT 50`
      );
    }

    res.json({ leaderboard: result.rows, type });
  } catch (err) {
    logger.error('Error fetching leaderboard', { error: err.message });
    res.status(500).json({ error: 'Failed to fetch leaderboard' });
  }
});

module.exports = router;
