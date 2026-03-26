const { ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings } = require("@langchain/google-genai");
const { getPool } = require("../config/database");
const logger = require("../utils/logger");

require("dotenv").config();

let llm = null;
let embeddings = null;

function getAIClient() {
  if (!process.env.GOOGLE_API_KEY) {
    throw new Error("GOOGLE_API_KEY is missing from environment variables.");
  }
  if (!llm || !embeddings) {
    llm = new ChatGoogleGenerativeAI({
      model: "gemini-1.5-flash", 

      apiKey: process.env.GOOGLE_API_KEY,
      temperature: 0.7,
    });
    embeddings = new GoogleGenerativeAIEmbeddings({
      model: "text-embedding-004", // Standard 768-D text embedding model layout
      apiKey: process.env.GOOGLE_API_KEY,
    });
  }
  return { llm, embeddings };
}

/**
 * Autonomously analyzes a user's entire vote history, generates a qualitative
 * psychological "investing persona" summary via LLM, embeds it, and saves it
 * to pgvector memory.
 *
 * @param {integer} userId - The numeric user_id from the database
 */
async function generateUserPersona(userId) {
  const pool = getPool();

  try {
    const { llm, embeddings } = getAIClient();
    
    // 1. Fetch User's Raw Voting History Data
    const historyQuery = `
      SELECT pv.vote_date, p.company_name, p.sector, p.difficulty 
      FROM puzzle_votes pv
      JOIN puzzles p ON p.brand_id = pv.brand_id
      WHERE pv.user_id = $1
      ORDER BY pv.vote_date DESC
      LIMIT 20;
    `;
    const res = await pool.query(historyQuery, [userId]);
    
    if (res.rows.length === 0) {
      logger.info(`Profiler Agent: Skipped user ${userId} because no vote history exists.`);
      return;
    }

    // Prepare history payload for prompt
    const historyText = res.rows.map((r, i) => 
      `${i + 1}. Voted for ${r.company_name} (Sector: ${r.sector}) on ${r.vote_date.toISOString().split('T')[0]}`
    ).join('\n');

    // 2. Instruct The Teacher Agent (Gemini) to Analyze
    const systemPrompt = `
      You are an expert psychological financial profiler. Based on the user's recent stock picking history provided below,
      generate a succinct 2-3 sentence qualitative "Investing Persona" that describes their habits and risk-awareness.
      
      User Vote History:
      ${historyText}

      TASK:
      1. Create a 2-3 sentence "profileSummary".
      2. Categorize the user into a "primaryTag" (e.g., Growth Seeker, Value Hunter, Sector Diversifier).
      3. Determine their "readingLevel" (either: beginner, intermediate, or advanced).
      
      You must reply with ONLY a pure JSON object:
      {
        "profileSummary": "...",
        "primaryTag": "...",
        "readingLevel": "..."
      }
    `;

    logger.info(`Profiler Agent: Requesting generative profile mapping for user ${userId}...`);
    const llmResponse = await llm.invoke(systemPrompt);
    const rawContent = llmResponse.content || "";
    const cleanContent = (typeof rawContent === 'string' ? rawContent : JSON.stringify(rawContent))
      .trim()
      .replace(/```json/gi, '')
      .replace(/```/g, '')
      .trim();

    let parsed;
    try {
      parsed = JSON.parse(cleanContent);
    } catch (e) {
      logger.error('Profiler Agent: Invalid JSON response', { raw: rawContent });
      parsed = { 
        profileSummary: rawContent.substring(0, 500), 
        primaryTag: 'Explorer', 
        readingLevel: 'beginner' 
      };
    }

    const { profileSummary, primaryTag, readingLevel } = parsed;
    logger.info(`Profiler Agent generated summary for User ${userId}: ${profileSummary}`);

    // 3. Generate Semantic Embedding of the Summary
    const vectorEmbedding = await embeddings.embedQuery(profileSummary);

    // Format array for pgvector literal
    const embeddingString = `[${vectorEmbedding.join(',')}]`;

    // 4. Upsert Knowledge Graph into Postgres
    const upsertQuery = `
      INSERT INTO user_personas (user_id, profile_summary, embedding, primary_tag, reading_level, last_updated)
      VALUES ($1, $2, $3::jsonb, $4, $5, CURRENT_TIMESTAMP)
      ON CONFLICT (user_id) 
      DO UPDATE SET 
        profile_summary = EXCLUDED.profile_summary,
        embedding = EXCLUDED.embedding,
        primary_tag = EXCLUDED.primary_tag,
        reading_level = EXCLUDED.reading_level,
        last_updated = CURRENT_TIMESTAMP;
    `;
    
    await pool.query(upsertQuery, [userId, profileSummary, embeddingString, primaryTag, readingLevel]);
    logger.info(`Profiler Agent: Successfully saved contextual persona for user ${userId}.`);

  } catch (err) {
    logger.error(`Profiler Agent Error generating persona for user ${userId}: ${err.message}`);
  }
}

module.exports = {
  generateUserPersona
};
