const express = require('express');
const router = express.Router();
const { getPool } = require('../config/database');
const { authenticate } = require('../middleware/auth');
const logger = require('../utils/logger');

// GET /api/puzzles/daily
router.get('/daily', async (req, res) => {
  const pool = getPool();
  const today = new Date().toISOString().split('T')[0];

  try {
    let result = await pool.query(
      `SELECT id, company_name, ticker, logo_url, difficulty, sector, hint
       FROM puzzles WHERE scheduled_date = $1`,
      [today]
    );

    // If no puzzle is scheduled for TODAY, handle the logic to find one based on votes
    if (!result.rows[0]) {
      // Find the most voted ticker for TODAY
      const voteResult = await pool.query(
        `SELECT ticker, COUNT(*) as vote_count, MIN(created_at) as first_vote
         FROM puzzle_votes
         WHERE vote_date = $1
         GROUP BY ticker
         ORDER BY vote_count DESC, first_vote ASC
         LIMIT 1`,
        [today]
      );

      let chosenTicker = null;
      if (voteResult.rows[0]) {
        chosenTicker = voteResult.rows[0].ticker;
      }

      if (chosenTicker) {
        // Try to find a puzzle with that ticker that hasn't been played today (or ever, normally shouldn't reuse, but we'll accept any)
        result = await pool.query(
          `SELECT id, company_name, ticker, logo_url, difficulty, sector, hint
           FROM puzzles WHERE ticker = $1 ORDER BY RANDOM() LIMIT 1`,
          [chosenTicker]
        );
      }

      // Fall back to a random puzzle if no votes or no puzzle found for the voted ticker
      if (!result.rows[0]) {
        result = await pool.query(
          `SELECT id, company_name, ticker, logo_url, difficulty, sector, hint
           FROM puzzles 
           WHERE scheduled_date IS NULL
           ORDER BY RANDOM() LIMIT 1`
        );
        // If all puzzles have been scheduled, just pick a random one
        if (!result.rows[0]) {
          result = await pool.query(
            `SELECT id, company_name, ticker, logo_url, difficulty, sector, hint
               FROM puzzles ORDER BY RANDOM() LIMIT 1`
          );
        }
      }

      // Schedule the chosen puzzle for today
      if (result.rows[0]) {
        await pool.query(
          `UPDATE puzzles SET scheduled_date = $1 WHERE id = $2`,
          [today, result.rows[0].id]
        );
      }
    }

    res.json(result.rows[0] || null);
  } catch (err) {
    logger.error('Error fetching daily puzzle', { error: err.message });
    res.status(500).json({ error: 'Failed to fetch puzzle' });
  }
});

// POST /api/puzzles/vote - Vote for tomorrow's puzzle ticker
router.post('/vote', authenticate, async (req, res) => {
  const pool = getPool();
  const userId = req.user.id;
  const { ticker } = req.body;

  if (!ticker) {
    return res.status(400).json({ error: 'Ticker is required' });
  }

  // Calculate tomorrow's date
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().split('T')[0];

  try {
    await pool.query(
      `INSERT INTO puzzle_votes (user_id, ticker, vote_date)
       VALUES ($1, $2, $3)
       ON CONFLICT (user_id, vote_date)
       DO UPDATE SET ticker = EXCLUDED.ticker, created_at = NOW()`,
      [userId, ticker, tomorrowStr]
    );

    res.json({ success: true, message: 'Vote recorded for tomorrow!' });
  } catch (err) {
    logger.error('Error recording puzzle vote', { error: err.message });
    res.status(500).json({ error: 'Failed to record vote' });
  }
});

// POST /api/puzzles/track-click - Track shared links
router.post('/track-click', async (req, res) => {
  const pool = getPool();
  const { promoterId, ref } = req.body;

  try {
    await pool.query(
      `INSERT INTO share_clicks (promoter_id, ref_page)
       VALUES ($1, $2)`,
      [promoterId || null, ref || 'direct']
    );
    res.json({ success: true });
  } catch (err) {
    logger.error('Error tracking share click', { error: err.message });
    res.status(500).json({ error: 'Failed to track click' });
  }
});

// GET /api/puzzles — paginated list
router.get('/', async (req, res) => {
  const pool = getPool();
  const page = Math.max(1, parseInt(req.query.page) || 1);
  const limit = 10;
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
  const pool = getPool();
  const puzzleId = parseInt(req.params.id);
  const userId = req.user.id;
  const { score = 0, movesUsed = 0, timeTaken = 0 } = req.body;

  try {
    await pool.query(
      `INSERT INTO game_sessions (user_id, puzzle_id, score, moves_used, completed, time_taken)
       VALUES ($1, $2, $3, $4, true, $5)
       ON CONFLICT (user_id, puzzle_id) 
       DO UPDATE SET 
         score = GREATEST(game_sessions.score, EXCLUDED.score),
         moves_used = LEAST(game_sessions.moves_used, EXCLUDED.moves_used),
         time_taken = LEAST(game_sessions.time_taken, EXCLUDED.time_taken)`,
      [userId, puzzleId, score, movesUsed, timeTaken]
    );

    // Compute absolute total score from high-scores to prevent infinite farming
    const aggResult = await pool.query(
      `SELECT SUM(score) as real_total FROM game_sessions WHERE user_id = $1`,
      [userId]
    );
    const realTotal = parseInt(aggResult.rows[0].real_total) || 0;

    // Streak logic
    const userRes = await pool.query(
      'SELECT last_played, streak FROM users WHERE id = $1',
      [userId]
    );
    const { last_played, streak } = userRes.rows[0];
    const today = new Date().toISOString().split('T')[0];
    const yesterday = new Date(Date.now() - 86_400_000).toISOString().split('T')[0];

    let newStreak = 1;
    if (last_played === yesterday) newStreak = streak + 1;
    else if (last_played === today) newStreak = streak;

    await pool.query(
      'UPDATE users SET total_score = $1, best_score = GREATEST(best_score, $2), streak = $3, last_played = $4 WHERE id = $5',
      [realTotal, score, newStreak, today, userId]
    );

    res.json({ success: true, score, streak: newStreak, realTotal });
  } catch (err) {
    logger.error('Error completing puzzle', { error: err.message });
    res.status(500).json({ error: 'Failed to save result' });
  }
});

module.exports = router;
