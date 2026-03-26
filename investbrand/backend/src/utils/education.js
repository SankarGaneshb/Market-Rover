const { getPool } = require('../config/database');
const { getIstDateString } = require('./date');

/**
 * Orchestrates a personalized growth tip based on the user's current progress.
 * Focuses on narrowing the gap to the next milestone.
 */
async function getTeacherInsight(userId) {
  const pool = getPool();
  try {
    // 1. Fetch user state
    const userResult = await pool.query('SELECT streak, total_score FROM users WHERE id = $1', [userId]);
    const missionResult = await pool.query('SELECT mission_id, progress, is_completed FROM user_missions WHERE user_id = $1', [userId]);
    const voteResult = await pool.query('SELECT COUNT(DISTINCT sector) as sector_count FROM puzzle_votes pv JOIN puzzles p ON p.brand_id = pv.brand_id WHERE pv.user_id = $1', [userId]);

    const user = userResult.rows[0];
    const missions = missionResult.rows;
    const sectorCount = parseInt(voteResult.rows[0].sector_count) || 0;

    // 2. Logic chain for tip prioritization
    
    // Priority: Streaks (Consistency)
    if (user.streak > 0 && user.streak < 3) {
      return `Mastery Path: You're on a ${user.streak}-day streak! Reach 3 days to unlock the first Virtuoso level.`;
    }

    // Priority: Sector Diversity (Missions)
    const sectorExplorer = missions.find(m => m.mission_id === 'sector_explorer');
    if (sectorExplorer && !sectorExplorer.is_completed && sectorCount >= 2) {
      return `Mission Insight: You've explored ${sectorCount} sectors. Find a brand in a new sector to become a "Sector Samurai"!`;
    }

    // Priority: New User (First Steps)
    const firstSteps = missions.find(m => m.mission_id === 'first_steps');
    if (!firstSteps || (!firstSteps.is_completed && firstSteps.progress < 5)) {
      const remaining = 5 - (firstSteps ? firstSteps.progress : 0);
      return `Welcome! Vote on ${remaining} more brands to unlock your first Financial Literacy guide.`;
    }

    // Default: Encouragement / Diversification
    if (sectorCount < 5) {
      return "Pro Tip: Diversifying your 'votes' across more sectors improves your Market Awareness rating!";
    }

    return "Teacher's Tip: Great work today! Check the leaderboard to see how your analysis compares to other Virtuosos.";

  } catch (err) {
    console.error('Error generating teacher insight:', err);
    return "Keep exploring the market to build your financial wisdom!";
  }
}

module.exports = { getTeacherInsight };
