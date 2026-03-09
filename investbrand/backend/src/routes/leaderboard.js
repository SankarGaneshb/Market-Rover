const express = require('express');
const router = express.Router();
const { getPool } = require('../config/database');
const logger = require('../utils/logger');
const { getIstDateString } = require('../utils/date');

// GET /api/leaderboard?type=all-time|weekly|daily
router.get('/', async (req, res) => {
  const pool = getPool();
  const type = req.query.type || 'all-time';

  try {
    let result;

    if (type === 'daily') {
      const today = getIstDateString();
      result = await pool.query(
        `SELECT u.id, u.name, u.avatar_url, u.streak,
                SUM(gs.score)::int AS score, 
                SUM(gs.moves_used)::int AS moves_used, 
                SUM(gs.time_taken)::int AS time_taken,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'easy'), 0)::int AS easy_score,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'medium'), 0)::int AS medium_score,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'hard'), 0)::int AS hard_score
         FROM users u
         JOIN game_sessions gs ON u.id = gs.user_id
         JOIN puzzles p        ON gs.puzzle_id = p.id
         WHERE p.scheduled_date = $1
         GROUP BY u.id, u.name, u.avatar_url, u.streak
         ORDER BY score DESC, time_taken ASC
         LIMIT 50`,
        [today]
      );
    } else if (type === 'weekly') {
      result = await pool.query(
        `SELECT u.id, u.name, u.avatar_url, u.streak,
                SUM(gs.score)::int AS score,
                COUNT(gs.id)::int  AS games_played,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'easy'), 0)::int AS easy_score,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'medium'), 0)::int AS medium_score,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'hard'), 0)::int AS hard_score
         FROM users u
         JOIN game_sessions gs ON u.id = gs.user_id
         WHERE gs.played_at >= NOW() - INTERVAL '7 days'
         GROUP BY u.id, u.name, u.avatar_url, u.streak
         ORDER BY score DESC
         LIMIT 50`
      );
    } else {
      const level = req.query.level;
      let streakFilter = '';
      const params = [];

      if (level) {
        const levels = {
          'Copper': { min: 28, max: 55 },
          'Bronze': { min: 56, max: 83 },
          'Silver': { min: 84, max: 167 },
          'Gold': { min: 168, max: 364 },
          'Platinum': { min: 365, max: 729 },
          'Diamond': { min: 730, max: 1094 },
          'Rhodium': { min: 1095, max: 1459 },
          'Obsidian': { min: 1460, max: 1824 },
          'Palladium': { min: 1825, max: 3649 },
          'Astral': { min: 3650, max: 9124 }, // 10 years
          'Galactic': { min: 3650, max: 9124 }, // Assuming 10+
          'Universal': { min: 9125, max: 18249 }, // 25+
          'Apex': { min: 18250, max: 27374 }, // 50+
          'Mythical': { min: 27375, max: 999999 } // 75+
        };

        const range = levels[level];
        if (range) {
          streakFilter = 'WHERE streak >= $1 AND streak <= $2';
          params.push(range.min, range.max);
        }
      }

      result = await pool.query(
        `WITH top_users AS (
           SELECT id, name, avatar_url, streak, total_score AS score
           FROM users
           ${streakFilter}
           ORDER BY total_score DESC
           LIMIT 50
         )
         SELECT tu.*,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'easy'), 0)::int AS easy_score,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'medium'), 0)::int AS medium_score,
                COALESCE(SUM(gs.score) FILTER (WHERE gs.difficulty = 'hard'), 0)::int AS hard_score
         FROM top_users tu
         LEFT JOIN game_sessions gs ON tu.id = gs.user_id
         GROUP BY tu.id, tu.name, tu.avatar_url, tu.streak, tu.score
         ORDER BY tu.score DESC`,
        params
      );
    }

    res.json({ leaderboard: result.rows, type });
  } catch (err) {
    logger.error('Error fetching leaderboard', { error: err.message });
    res.status(500).json({ error: 'Failed to fetch leaderboard' });
  }
});

module.exports = router;
