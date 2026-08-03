const { ChatGoogleGenerativeAI } = require("@langchain/google-genai");
const logger = require("../utils/logger");

require("dotenv").config();

let llm = null;

function getLLMClient() {
  const apiKey = process.env.GOOGLE_API_KEY;
  if (!apiKey) {
    logger.warn("GOOGLE_API_KEY is missing. AI features will use fallbacks.");
    return null;
  }
  if (!llm) {
    llm = new ChatGoogleGenerativeAI({
      model: "gemini-1.5-flash",
      apiKey: apiKey,
      temperature: 0.8,
    });
  }
  return llm;
}

/**
 * Generates the initial puzzle metadata (Word Cloud string, and 3 hints based on fundamentals)
 */
async function generateInitialClues(companyName, ticker, sector) {
  try {
    const aiLlm = getLLMClient();
    if (!aiLlm) {
      throw new Error("LLM client not initialized (missing API key)");
    }
    const systemPrompt = `
      You are an expert game designer creating a "Guess the Stock" puzzle for: ${companyName} (${ticker}) in the ${sector} sector.

      1. DO NOT mention the company name, its ticker, or exact founder names.
      2. wordCloud MUST be 5-7 thematic words that define the company's legacy, products, or geography (e.g., 'Jamnagar, Refining, Polyester' for an energy giant).
      3. clue1 MUST describe the sector name and a generic stock price range.

      Your output MUST be a valid JSON object:
      {
        "wordCloud": "A comma separated string of 5-7 thematic words",
        "clue1": "Sector name and stock price range (e.g. 'Sector: IT. Range: Rs. 3000 - 3500')",
        "clue2": "Medium hint about products/market dominance",
        "clue3": "Easy hint about famous characteristics"
      }
    `;

    logger.info(`Generating clues for ${ticker}...`);
    const response = await aiLlm.invoke(systemPrompt);
    const cleanJsonStr = String(response?.content || "").replace(/```json/gi, '').replace(/```/g, '').trim();
    return JSON.parse(cleanJsonStr);
  } catch (err) {
    logger.error(`AI Clue Generation failed for ${ticker}: ${err.message}`);

    const sectorBase = sector || "General";
    // Dynamic Fallback Dictionary
    const sectorMap = {
      "IT": "Digital, Cloud, Outsourcing, Software, Mystery",
      "Energy": "Power, Grid, Renewables, Fuel, Infrastructure, Mystery",
      "Finance": "Capital, Banking, Credit, Nifty, Investment, Mystery",
      "Consumer Goods": "FMCG, Brand, Retail, Household, Distribution, Mystery",
      "Automobile": "Wheels, Engine, EV, Transport, Mobility, Mystery",
      "Pharma": "Healthcare, Labs, Medicine, Wellness, Biotech, Mystery"
    };

    return {
      wordCloud: sectorMap[sector] || sectorMap[sectorBase] || "Growth, Value, Industry, Market, Global",
      clue1: `This company is a key player in the ${sectorBase} sector.`,
      clue2: "It has a significant market presence and long-term history.",
      clue3: "Its products or services are part of many Indian households."
    };
  }
}

/**
 * Evaluates a user's guess and provides a dynamic hint
 */
async function evaluateGuess(userGuess, actualCompanyName, actualSector) {
  try {
    const aiLlm = getLLMClient();
    if (!aiLlm) {
      throw new Error("LLM client not initialized (missing API key)");
    }
    const systemPrompt = `
      You are the Game Master in a "Guess the Stock" game.
      The actual company is: ${actualCompanyName} (Sector: ${actualSector}).
      The user guessed: "${userGuess}".

      Your job is to provide a single, short, witty response (max 2 sentences).
      1. If the guess is correct (ignoring case/slight spelling errors), congratulate them enthusiastically and start your response with "CORRECT:".
      2. If the guess is wrong, briefly compare the user's guess to the actual company to give them a subtle hint.

      RULES:
      - NEVER reveal the actual company name.
      - NEVER reveal exact founder names or the exact establishment year of the actual company.
      - Do not use markdown like bolding or italics if possible.

      Example Wrong Guess: User guesses "TCS", Actual is "Infosys".
      Response: "Good try! You got the IT sector right, but our mystery company is headquartered down in Bangalore."

      Output ONLY the response text.
    `;

    logger.info(`Evaluating user guess: ${userGuess} against ${actualCompanyName}`);
    const response = await aiLlm.invoke(systemPrompt);
    return String(response?.content || "").trim();
  } catch (err) {
    logger.error(`Error evaluating guess: ${err.message}`);
    return "Not quite right. Try looking at their sector or products differently!";
  }
}

module.exports = {
  generateInitialClues,
  evaluateGuess
};
