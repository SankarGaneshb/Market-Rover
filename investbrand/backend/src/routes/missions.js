const express = require('express');
const router = express.Router();
const { getPool } = require('../config/database');
const { authenticate } = require('../middleware/auth');

const { generateDailyMission } = require('../agents/gamemasterAgent');
const { getIstDateString } = require('../utils/date');

// GET /api/missions
router.get('/', authenticate, async (req, res) => {
  const pool = getPool();
  const userId = req.user.id;
  
  // Use today's date formatted as YYYY-MM-DD for uniqueness
  const todayStr = getIstDateString();
  const dynamicMissionId = `daily_${todayStr}`;

  try {
    // 1. Fetch existing missions
    let result = await pool.query(
      'SELECT mission_id, progress, is_completed, completed_at, mission_def FROM user_missions WHERE user_id = $1',
      [userId]
    );
    
    // 2. See if today's Gamemaster mission exists
    const hasDaily = result.rows.some(r => r.mission_id === dynamicMissionId);
    
    if (!hasDaily) {
      // 3. Trigger the Gamemaster AI to create one
      console.log(`No daily mission found for user ${userId}. Generating via Gamemaster Agent...`);
      const dynamicDef = await generateDailyMission(userId);
      
      if (dynamicDef) {
        // Override its ID for database tracking
        dynamicDef.id = dynamicMissionId;

        // 4. Save to user_missions
        await pool.query(
          `INSERT INTO user_missions (user_id, mission_id, progress, is_completed, mission_def)
           VALUES ($1, $2, 0, false, $3)`,
          [userId, dynamicMissionId, JSON.stringify(dynamicDef)]
        );

        // Append it to our response array dynamically to avoid a secondary query
        result.rows.push({
          mission_id: dynamicMissionId,
          progress: 0,
          is_completed: false,
          completed_at: null,
          mission_def: dynamicDef
        });
      } else {
        console.warn('Gamemaster failed to produce a mission (likely missing GOOGLE_API_KEY). Skipping dynamic mission generation.');
      }
    }

    res.json(result.rows);
  } catch (err) {
    console.error('Error fetching missions:', err);
    res.status(500).json({ error: 'Failed to fetch missions' });
  }
});

module.exports = router;
