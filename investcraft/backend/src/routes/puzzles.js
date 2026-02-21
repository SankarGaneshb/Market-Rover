const express = require('express');
const router  = express.Router();
const { getPool } = require('../config/database');
const { authenticate } = require('../middleware/auth');
const logger = require('../utils/logger');

// GET /api/puzzles/daily
router.get('/daily', async (req, res) => {
  const pool  = getPool();
  const today = new Date().toISOString().split('T')[0];

  try {
    let result = await pool.query(
      `SELECT id, company_name, ticker, logo_url, difficulty, sector, hint
       FROM puzzles WHERE scheduled_date = $1`,
      [today]
    );

    // Fall back to a random puzzle if none scheduled today
    if (!result.rows[0]) {
      result = await pool.query(
        `SELECT id, company_name, ticker, logo_url, difficulty, sector, hint
         FROM puzzles ORDER BY RANDOM() LIMIT 1`
      );
    }

    res.json(result.rows[0] || null);
  } catch (err) {
    logger.error('Error fetching daily puzzle', { error: err.message });
    res.status(500).json({ error: 'Failed to fetch puzzle' });
  }
});

// GET /api/puzzles — paginated list
router.get('/', async (req, res) => {
  const pool   = getPool();
  const page   = Math.max(1, parseInt(req.query.page) || 1);
  const limit  = 10;
  const offset = (page - 1) * limit;

  try {
    const result = await pool.query(
      `SELECT id, company_name, ticker, difficulty, sector, scheduled_date
       FROM puzzles
       ORDER BY scheduled_date DESC
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );
    res.json({ puzzles: result.rows, page });
  } catch (err) {
    logger.error('Error fetching puzzles', { error: err.message });
    res.status(500).json({ error: 'Failed to fetch puzzles' });
  }
});

// POST /api/puzzles/:id/complete — save game result (authenticated)
router.post('/:id/complete', authenticate, async (req, res) => {
  const pool     = getPool();
  const puzzleId = parseInt(req.params.id);
  const userId   = req.user.id;
  const { score = 0, movesUsed = 0, timeTaken = 0 } = req.body;

  try {
    await pool.query(
      `INSERT INTO game_sessions (user_id, puzzle_id, score, moves_used, completed, time_taken)
       VALUES ($1, $2, $3, $4, true, $5)
       ON CONFLICT (user_id, puzzle_id) DO NOTHING`,
      [userId, puzzleId, score, movesUsed, timeTaken]
    );

    // Streak logic
    const userRes = await pool.query(
      'SELECT last_played, streak FROM users WHERE id = $1',
      [userId]
    );
    const { last_played, streak } = userRes.rows[0];
    const today     = new Date().toISOString().split('T')[0];
    const yesterday = new Date(Date.now() - 86_400_000).toISOString().split('T')[0];

    let newStreak = 1;
    if (last_played === yesterday) newStreak = streak + 1;
    else if (last_played === today)  newStreak = streak;

    await pool.query(
      'UPDATE users SET total_score = total_score + $1, streak = $2, last_played = $3 WHERE id = $4',
      [score, newStreak, today, userId]
    );

    res.json({ success: true, score, streak: newStreak });
  } catch (err) {
    logger.error('Error completing puzzle', { error: err.message });
    res.status(500).json({ error: 'Failed to save result' });
  }
});

module.exports = router;
