const express = require('express');
const router = express.Router();
const { getPool } = require('../config/database');
const { authenticate } = require('../middleware/auth');
const logger = require('../utils/logger');
const { getIstDateString } = require('../utils/date');

// GET /api/puzzles/daily
router.get('/daily', async (req, res) => {
  const pool = getPool();
  const today = getIstDateString();

  try {
    let result = await pool.query(
      `SELECT id, brand_id, brand_name, company_name, ticker, logo_url, difficulty, sector, hint
       FROM puzzles WHERE scheduled_date = $1`,
      [today]
    );

    // If no puzzle is scheduled for TODAY, handle the logic to find one based on votes
    if (!result.rows[0]) {
      // Find the most voted brand_id for TODAY
      const voteResult = await pool.query(
        `SELECT brand_id, COUNT(*) as vote_count, MIN(created_at) as first_vote
         FROM puzzle_votes
         WHERE vote_date = $1
         GROUP BY brand_id
         ORDER BY vote_count DESC, first_vote ASC
         LIMIT 1`,
        [today]
      );

      let chosenBrandId = null;
      if (voteResult.rows[0]) {
        chosenBrandId = voteResult.rows[0].brand_id;
      }

      if (chosenBrandId) {
        // Try to find a puzzle with that brand_id that hasn't been played yet
        result = await pool.query(
          `SELECT id, brand_id, brand_name, company_name, ticker, logo_url, difficulty, sector, hint
           FROM puzzles WHERE brand_id = $1 AND scheduled_date IS NULL ORDER BY RANDOM() LIMIT 1`,
          [chosenBrandId]
        );
      }

      // Fall back to a random puzzle if no votes or no puzzle found for the voted brand_id
      if (!result.rows[0]) {
        result = await pool.query(
          `SELECT id, brand_id, brand_name, company_name, ticker, logo_url, difficulty, sector, hint
           FROM puzzles 
           WHERE scheduled_date IS NULL
           ORDER BY RANDOM() LIMIT 1`
        );
        // If all puzzles have been scheduled, just pick a random one
        if (!result.rows[0]) {
          result = await pool.query(
            `SELECT id, brand_id, brand_name, company_name, ticker, logo_url, difficulty, sector, hint
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

// POST /api/puzzles/vote - Vote for tomorrow's puzzle brand
router.post('/vote', authenticate, async (req, res) => {
  const pool = getPool();
  const userId = req.user.id;
  const { brandId } = req.body;

  if (!brandId) {
    return res.status(400).json({ error: 'brandId is required' });
  }

  // Calculate tomorrow's date using IST base
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = getIstDateString(tomorrow);

  try {
    await pool.query(
      `INSERT INTO puzzle_votes (user_id, brand_id, vote_date)
       VALUES ($1, $2, $3)
       ON CONFLICT (user_id, vote_date, brand_id)
       DO NOTHING`,
      [userId, brandId, tomorrowStr]
    );

    res.json({ success: true, message: 'Vote recorded for tomorrow!' });
  } catch (err) {
    logger.error('Error recording puzzle vote', { error: err.message });
    res.status(500).json({ error: 'Failed to record vote' });
  }
});

// GET /api/puzzles/vote-status - Get played and voted brandIds
router.get('/vote-status', authenticate, async (req, res) => {
  const pool = getPool();
  const userId = req.user.id;

  const todayStr = getIstDateString();

  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = getIstDateString(tomorrow);

  try {
    // Get brands user has voted for tomorrow
    const userVotes = await pool.query(
      `SELECT brand_id FROM puzzle_votes WHERE user_id = $1 AND vote_date = $2`,
      [userId, tomorrowStr]
    );
    const votedBrandIds = userVotes.rows.map(row => row.brand_id);

    // Get brands that have been played (in the past or today)
    const playedPuzzles = await pool.query(
      `SELECT brand_id FROM puzzles WHERE scheduled_date <= $1 AND scheduled_date IS NOT NULL`,
      [todayStr]
    );
    const playedBrandIds = playedPuzzles.rows.map(row => row.brand_id);

    res.json({ votedBrandIds, playedBrandIds });
  } catch (err) {
    logger.error('Error fetching vote status', { error: err.message });
    res.status(500).json({ error: 'Failed to fetch vote status' });
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
      `SELECT id, brand_id, brand_name, company_name, ticker, difficulty, sector, scheduled_date
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

    // Streak logic - calculate days difference
    const userRes = await pool.query(
      'SELECT last_played, streak FROM users WHERE id = $1',
      [userId]
    );
    let { last_played, streak } = userRes.rows[0];

    // Normalize to today's date string in IST
    const today = getIstDateString();
    let newStreak = 1;

    if (last_played) {
      // Convert both dates to pure Date objects at midnight UTC to safely compare the calendar days
      const lastPlayedDate = new Date(last_played + 'T00:00:00Z');
      const todayDate = new Date(today + 'T00:00:00Z');

      // Calculate difference in time then difference in days
      const diffTime = todayDate - lastPlayedDate;
      const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

      if (diffDays === 0) {
        // Played again on the exact same day, keep the streak
        newStreak = streak;
      } else if (diffDays === 1) {
        // Played exactly one day later, increment streak
        newStreak = streak + 1;
      } else {
        // Played 2+ days later, streak resets to 1 (which is the default)
        newStreak = 1;
      }
    }

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
