const { ChatGoogleGenerativeAI } = require("@langchain/google-genai");
const { getPool } = require("../config/database");
const logger = require("../utils/logger");

require("dotenv").config();

let llm = null;

function getLLMClient() {
  if (!process.env.GOOGLE_API_KEY) {
    throw new Error("GOOGLE_API_KEY is missing from environment variables.");
  }
  if (!llm) {
    llm = new ChatGoogleGenerativeAI({
      model: "gemini-1.5-flash",

      apiKey: process.env.GOOGLE_API_KEY,
      temperature: 0.8,
    });
  }
  return llm;
}

/**
 * Generates a dynamic, personalized mission for a user based on their recent
 * voting history. Returns a JSON object describing the mission.
 *
 * @param {integer} userId - The numeric user_id
 * @returns {Object} The generated mission definition
 */
async function generateDailyMission(userId) {
  const pool = getPool();

  try {
    const aiLlm = getLLMClient();
    
    // 1. Fetch recent sectors to contextualize the mission
    const historyQuery = `
      SELECT p.sector 
      FROM puzzle_votes pv
      JOIN puzzles p ON p.brand_id = pv.brand_id
      WHERE pv.user_id = $1
      ORDER BY pv.vote_date DESC
      LIMIT 10;
    `;
    const res = await pool.query(historyQuery, [userId]);
    
    // Fallback if no history yet
    let contextStr = "The user is completely new with no voting history. Give them an introductory mission.";
    if (res.rows.length > 0) {
      const sectors = res.rows.map(r => r.sector).filter(Boolean);
      const uniqueSectors = [...new Set(sectors)];
      contextStr = `The user has recently voted in these sectors: ${uniqueSectors.join(', ')}. Create a mission that either encourages them to vote in a NEW sector, or dive deeper into one of their favorites.`;
    }

    // 2. Prompt Gemini for to act as a Gamemaster
    const systemPrompt = `
      You are an expert game designer constructing a personalized stock market educational mission for a player.
      Context: ${contextStr}

      Generate a single daily mission for the player. 
      CRITICAL: Ensure the title is unique and creative (e.g. "Sector Samurai", "Mid-Cap Maverick", "Dividend Detective"). 
      Avoid generic titles like "Market Explorer" unless the user is completely new.
      
      You must respond ONLY with a valid Raw JSON object (no markdown block formatting) matching exactly this schema:
      {
        "id": "dynamic_daily",
        "title": "A unique, catchy title relating to the mission type",
        "description": "1-2 sentences explaining what to do and why it helps their financial knowledge",
        "target": <an integer between 2 and 5 representing how many votes/actions they need>,
        "reward": "Name of an exclusive badge or title"
      }
    `;


    logger.info(`Gamemaster Agent: Orchestrating daily mission for user ${userId}...`);
    
    // We append the JSON instruction strongly
    const llmResponse = await aiLlm.invoke(systemPrompt);
    const rawContent = llmResponse.content || "";
    const cleanJsonStr = (typeof rawContent === 'string' ? rawContent : JSON.stringify(rawContent))
      .trim()
      .replace(/```json/g, '')
      .replace(/```/g, '')
      .trim();
    
    const missionData = JSON.parse(cleanJsonStr);

    logger.info(`Gamemaster Agent successfully orchestrated mission: ${missionData.title}`);
    
    return missionData;

  } catch (err) {
    logger.error(`Gamemaster Agent Error for user ${userId}: ${err.message}`);
    // Fallback static mission if generative pipeline fails
    return {
      id: "dynamic_daily_fallback",
      title: "Market Explorer",
      description: "Vote across 3 different sectors to learn about market diversification.",
      target: 3,
      reward: "Explorer Badge"
    };
  }
}

module.exports = {
  generateDailyMission
};
