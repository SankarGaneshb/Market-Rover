const { getPool } = require('../config/database');
const logger = require('./logger');

const MISSIONS = {
  first_steps: { id: 'first_steps', target: 5 },
  sector_explorer: { id: 'sector_explorer', target: 3 }
};

async function updateMission(client, userId, missionId, progress, target) {
  const isCompleted = progress >= target;
  await client.query(
    `INSERT INTO user_missions (user_id, mission_id, progress, is_completed, completed_at)
     VALUES ($1, $2, $3, $4, CASE WHEN $4 THEN NOW() ELSE NULL END)
     ON CONFLICT (user_id, mission_id)
     DO UPDATE SET 
       progress = GREATEST(user_missions.progress, EXCLUDED.progress),
       is_completed = CASE WHEN EXCLUDED.progress >= $5 THEN true ELSE user_missions.is_completed END,
       completed_at = CASE WHEN EXCLUDED.progress >= $5 AND user_missions.is_completed = false THEN NOW() ELSE user_missions.completed_at END`,
    [userId, missionId, progress, isCompleted, target]
  );
}

async function checkMissions(userId) {
  const pool = getPool();
  try {
    const client = await pool.connect();
    try {
      // Fetch all votes for this user
      const votesResult = await client.query(
        `SELECT pv.vote_date, p.sector
         FROM puzzle_votes pv
         LEFT JOIN puzzles p ON pv.brand_id = p.brand_id
         WHERE pv.user_id = $1`,
        [userId]
      );
      
      const votes = votesResult.rows;
      if (votes.length === 0) return;

      // 1. First Steps: 5 votes total
      await updateMission(client, userId, MISSIONS.first_steps.id, votes.length, MISSIONS.first_steps.target);

      // 2. Sector Explorer: Votes across 3 different sectors
      const distinctSectors = new Set(votes.map(v => v.sector).filter(Boolean)).size;
      await updateMission(client, userId, MISSIONS.sector_explorer.id, distinctSectors, MISSIONS.sector_explorer.target);

    } finally {
      client.release();
    }
  } catch (err) {
    logger.error('Error evaluating missions', { error: err.message, userId });
  }
}

async function calculateStrategyTags(userId) {
  const pool = getPool();
  try {
    const client = await pool.connect();
    try {
      // Get rolling 7 day votes for the strategy profiling
      const votesResult = await client.query(
        `SELECT pv.vote_date, p.sector 
         FROM puzzle_votes pv
         LEFT JOIN puzzles p ON pv.brand_id = p.brand_id
         WHERE pv.user_id = $1 AND pv.vote_date >= CURRENT_DATE - INTERVAL '7 days'`,
        [userId]
      );
      
      const votes = votesResult.rows;
      if (votes.length === 0) return;

      const totalVotes = votes.length;
      let assignedTag = 'Explorer';

      const sectors = votes.map(v => v.sector).filter(Boolean);
      const uniqueSectors = new Set(sectors).size;
      const sectorCounts = sectors.reduce((acc, curr) => (acc[curr] = (acc[curr] || 0) + 1, acc), {});
      const maxSectorCount = Object.keys(sectorCounts).length > 0 ? Math.max(...Object.values(sectorCounts)) : 0;

      const growthCount = sectors.filter(s => s === 'Information Technology' || s === 'Healthcare').length;
      const valueCount = sectors.filter(s => s === 'FMCG' || s === 'Utilities').length;
      
      if (uniqueSectors >= 4) {
        assignedTag = 'Sector Diversifier';
      } else if (maxSectorCount / totalVotes > 0.7) {
        assignedTag = 'Brand Loyalist';
      } else if (growthCount / totalVotes > 0.5) {
        assignedTag = 'Growth Hunter';
      } else if (valueCount / totalVotes > 0.5) {
        assignedTag = 'Value Seeker';
      } else {
        assignedTag = 'Index Lover'; 
      }

      await client.query(
        `INSERT INTO user_strategy_tags (user_id, tag, calculation_date, voting_pattern)
         VALUES ($1, $2, CURRENT_DATE, $3)
         ON CONFLICT (user_id, calculation_date) 
         DO UPDATE SET tag = EXCLUDED.tag, voting_pattern = EXCLUDED.voting_pattern`,
        [userId, assignedTag, JSON.stringify(sectorCounts)]
      );
    } finally {
      client.release();
    }
  } catch (err) {
    logger.error('Error calculating strategy tags', { error: err.message, userId });
  }
}

module.exports = { checkMissions, calculateStrategyTags };
