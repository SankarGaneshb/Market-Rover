const { getPool } = require('../config/database');
const { ChatGoogleGenerativeAI } = require('@langchain/google-genai');
const logger = require('../utils/logger');

let aiLlmClient = null;

function getLLMClient() {
  if (!process.env.GOOGLE_API_KEY) {
    throw new Error("GOOGLE_API_KEY is missing from environment variables.");
  }
  if (!aiLlmClient) {
    aiLlmClient = new ChatGoogleGenerativeAI({
      modelName: 'gemini-2.0-flash',
      maxOutputTokens: 500,
      temperature: 0.1, // Low temperature for consistent analysis
      apiKey: process.env.GOOGLE_API_KEY
    });
  }
  return aiLlmClient;
}

/**
 * Quality Control Agent: Scans puzzle feedback and takes corrective actions.
 * Actions include:
 * 1. Disabling puzzles with broken/wrong logos.
 * 2. Flagging difficulty imbalances.
 */
async function runQualityCheck() {
  const pool = getPool();
  logger.info("QC Agent: Starting quality check audit...");

  try {
    // 1. Fetch aggregate feedback for active puzzles
    const feedbackQuery = `
      SELECT 
        p.id as puzzle_id, 
        p.brand_name, 
        p.ticker, 
        f.category, 
        f.rating, 
        COUNT(*) as count
      FROM puzzle_feedback f
      JOIN puzzles p ON f.puzzle_id = p.id
      WHERE p.is_active = true
      GROUP BY p.id, p.brand_name, p.ticker, f.category, f.rating
    `;
    
    const feedbackRes = await pool.query(feedbackQuery);
    
    if (feedbackRes.rows.length === 0) {
      logger.info("QC Agent: No new feedback to process.");
      return { success: true, actions: [] };
    }

    // 2. Group feedback by puzzle
    const organized = {};
    feedbackRes.rows.forEach(row => {
      if (!organized[row.puzzle_id]) {
        organized[row.puzzle_id] = {
          ticker: row.ticker,
          brand: row.brand_name,
          feedback: []
        };
      }
      organized[row.puzzle_id].feedback.push({
        category: row.category,
        rating: row.rating,
        count: parseInt(row.count)
      });
    });

    const aiLlm = getLLMClient();
    const actionsTaken = [];

    // 3. Let the Agent analyze the grouped feedback
    for (const puzzleId in organized) {
      const data = organized[puzzleId];
      
      const analysisPrompt = `You are the InvestBrand Quality Control Agent.
Analyze the following user feedback for the puzzle "${data.brand}" (${data.ticker}).

FEEDBACK DATA:
${JSON.stringify(data.feedback, null, 2)}

TASK:
1. Determine if the logo for this puzzle is significantly broken (Category: logo, Ratings: "blurry" or "wrong").
2. Determine if the puzzle difficulty is imbalanced (Category: puzzle, Ratings: "too_hard" or "too_easy").
3. Decide if the puzzle should be DISABLED (is_active = false) because of a bad logo.

RULES:
- Only disable if "blurry" or "wrong" counts are high (e.g., > 30% of total logo feedback AND at least 3 samples).
- Provide a brief rationale for your decision.

Respond ONLY with a JSON object:
{
  "shouldDisable": boolean,
  "issueType": "logo_broken" | "difficulty_imbalanced" | "none",
  "rationale": "one sentence explanation"
}`;

      const response = await aiLlm.invoke(analysisPrompt);
      let content = response.content.trim().replace(/```json/gi, '').replace(/```/g, '').trim();
      
      try {
        const decision = JSON.parse(content);
        
        if (decision.shouldDisable) {
          logger.warn(`QC Agent: DISABLING puzzle ${data.ticker} due to: ${decision.rationale}`);
          await pool.query('UPDATE puzzles SET is_active = false WHERE id = $1', [puzzleId]);
          actionsTaken.push({ ticker: data.ticker, action: 'disabled', reason: decision.rationale });
        } else if (decision.issueType !== 'none') {
          logger.info(`QC Agent: Flagging ${data.ticker}: ${decision.rationale}`);
          actionsTaken.push({ ticker: data.ticker, action: 'flagged', reason: decision.rationale });
        }
      } catch (e) {
        logger.error(`QC Agent: Error parsing decision for ${data.ticker}`, { error: e.message });
      }
    }

    return { success: true, actions: actionsTaken };

  } catch (err) {
    logger.error("QC Agent: Audit failed", { error: err.message });
    throw err;
  }
}

module.exports = { runQualityCheck };
