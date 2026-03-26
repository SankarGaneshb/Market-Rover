const express = require('express');
const router = express.Router();
const { authenticate } = require('../middleware/auth');
const { getPool } = require('../config/database');

const { getTeacherInsight } = require('../utils/education');
const { PREMIUM_GUIDES } = require('../data/premium_guides');


// GET /api/education/locker
router.get('/locker', authenticate, async (req, res) => {
  try {
    const pool = getPool();
    // Fetch all completed missions with rewards for this user
    const result = await pool.query(
      'SELECT unlocked_reward FROM user_missions WHERE user_id = $1 AND is_completed = true AND unlocked_reward IS NOT NULL',
      [req.user.id]
    );

    const unlockedIds = result.rows.map(r => r.unlocked_reward);
    const locker = unlockedIds
      .map(id => PREMIUM_GUIDES[id])
      .filter(Boolean);

    res.json({ locker });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch locker' });
  }
});

// GET /api/education/tip
router.get('/tip', authenticate, async (req, res) => {
  try {
    const tip = await getTeacherInsight(req.user.id);
    res.json({ tip });
  } catch (err) {
    res.status(500).json({ error: 'Failed' });
  }
});

// POST /api/education/views
// Record a content view for a user
router.post('/views', authenticate, async (req, res) => {
  const { contentId } = req.body;
  if (!contentId) return res.status(400).json({ error: 'contentId is required' });

  const pool = getPool();
  try {
    await pool.query(
      `INSERT INTO user_content_views (user_id, content_id) 
       VALUES ($1, $2)
       ON CONFLICT (user_id, content_id) 
       DO UPDATE SET view_count = user_content_views.view_count + 1, last_viewed_at = NOW()`,
      [req.user.id, contentId]
    );
    res.json({ success: true });
  } catch (err) {
    console.error('Error tracking view:', err);
    res.status(500).json({ error: 'Failed to track content view' });
  }
});

// GET /api/education/strategy
// Get user strategy tag
router.get('/strategy', authenticate, async (req, res) => {
  const pool = getPool();
  try {
    const result = await pool.query(
      'SELECT tag, calculation_date, voting_pattern FROM user_strategy_tags WHERE user_id = $1 ORDER BY calculation_date DESC LIMIT 1',
      [req.user.id]
    );
    res.json({ strategy: result.rows[0] || null });
  } catch (err) {
    console.error('Error fetching strategy:', err);
    res.status(500).json({ error: 'Failed to fetch strategy tag' });
  }
});

module.exports = router;
