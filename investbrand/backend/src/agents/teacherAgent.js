const { getPool } = require('../config/database');
const { ChatGoogleGenerativeAI } = require('@langchain/google-genai');
const logger = require('../utils/logger');

// Lazy initialization pattern to prevent startup crashes if key is missing
let aiLlmClient = null;

function getLLMClient() {
  if (!process.env.GOOGLE_API_KEY) {
    throw new Error("GOOGLE_API_KEY is missing from environment variables.");
  }
  if (!aiLlmClient) {
    aiLlmClient = new ChatGoogleGenerativeAI({
      modelName: 'gemini-1.5-flash',

      maxOutputTokens: 200,
      temperature: 0.7,
      apiKey: process.env.GOOGLE_API_KEY
    });
  }
  return aiLlmClient;
}

/**
 * Generates a targeted micro-learning tip about a specific company dynamically adjusted to the user's financial persona.
 */
async function generateTeacherInsight(userId, ticker, companyName) {
  try {
    const aiLlm = getLLMClient();
    const pool = getPool();

    // 1. Fetch user persona to understand their level
    const personaRes = await pool.query(
      `SELECT primary_tag, reading_level FROM user_personas WHERE user_id = $1`,
      [userId]
    );

    let primaryTag = "Beginner Investor";
    let readingLevel = "beginner";
    if (personaRes.rows[0]) {
      primaryTag = personaRes.rows[0].primary_tag;
      readingLevel = personaRes.rows[0].reading_level;
    }

    // 2. Build the LangChain system prompt
    const systemPrompt = `You are the Market-Rover Adaptive Teacher Agent.
Your job is to provide EXACTLY ONE punchy, fascinating micro-learning insight about the Indian stock "${companyName}" (${ticker}).
The user has just solved a puzzle guessing this brand.

USER PERSONA CONTEXT:
- Persona Tag: ${primaryTag}
- Financial Reading Level: ${readingLevel}

INSTRUCTIONS:
1. If the user is a "beginner", use a simple everyday analogy. Explain what makes this company's business model strong or weak.
2. If the user is "advanced", provide a compelling metric, macro-economic headwind, or competitive corporate moat analysis.
3. Keep it to exactly 2 sentences maximum. Do not exceed 40 words.
4. Make it extremely conversational and engaging. Start directly with the insight.

You must reply with ONLY a pure JSON object in the exact following structure with no markdown ticks:
{
  "title": "A catchy 2-4 word title",
  "insight": "Your 2 sentence explanation."
}`;

    logger.info(`Teacher Agent: Generating contextual insight for user ${userId} on ${ticker}...`);

    const llmResponse = await aiLlm.invoke(systemPrompt);
    const rawContent = llmResponse.content || "";
    const insightText = (typeof rawContent === 'string' ? rawContent : JSON.stringify(rawContent))
      .trim()
      .replace(/```json/g, '')
      .replace(/```/g, '')
      .trim();
    
    logger.info(`Teacher Agent: Success for ${ticker}`);

    try {
      const parsed = JSON.parse(insightText);
      return parsed;
    } catch (parseError) {
      logger.error('Teacher Agent returned invalid JSON:', { raw: rawContent });
      return {
        title: "Market Fact",
        insight: `${companyName} is one of the top publicly traded companies in India. Tracking its sector momentum can reveal broader economic trends!`
      };
    }
  } catch (err) {
    logger.error('Failed to generate teacher insight:', { error: err.message });
    return {
      title: "Market Fact",
      insight: `${companyName} is a prominent stock on the Indian exchanges.`
    };
  }
}

module.exports = {
  generateTeacherInsight
};
