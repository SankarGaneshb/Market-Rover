const { ChatGoogleGenerativeAI } = require("@langchain/google-genai");
const logger = require("../utils/logger");

require("dotenv").config();

let llm = null;

function getLLMClient() {
  if (!process.env.GOOGLE_API_KEY) {
    throw new Error("GOOGLE_API_KEY is missing from environment variables.");
  }
  if (!llm) {
    llm = new ChatGoogleGenerativeAI({
      model: "gemini-2.0-flash",
      apiKey: process.env.GOOGLE_API_KEY,
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
    const systemPrompt = `
      You are an expert game designer creating a "Guess the Stock" puzzle for: ${companyName} (${ticker}) in the ${sector} sector.

      1. DO NOT mention the company name, its ticker, exact founder names, or the exact year of establishment.
      2. Keep it completely anonymous.
      3. clue1 MUST describe the sector name and a generic stock price range (e.g. 'Sector: IT. Stock Price Range: ₹1000 - ₹2000').

      Your output MUST be a valid JSON object matching exactly this schema:
      {
        "wordCloud": "A comma separated string of 5-7 thematic words/concepts related to the company's geography, iconic products, or loosely to its founders (e.g. 'Electronic City, Outsourcing, Banyan, Hub')",
        "clue1": "Sector name and stock price range (e.g. 'Sector: Energy. Stock Price Range: ₹2500 - ₹3000').",
        "clue2": "A medium difficulty hint focusing on product lines or thematic dominance.",
        "clue3": "An easy difficulty hint focusing on its most famous characteristic or geographical origin."
      }
    `;


    logger.info(`Generating initial stock clues for ${ticker}...`);
    const response = await aiLlm.invoke(systemPrompt);
    const cleanJsonStr = String(response?.content || "").replace(/```json/gi, '').replace(/```/g, '').trim();
    return JSON.parse(cleanJsonStr);
  } catch (err) {
    logger.error(`Error generating initial clues: ${err.message}`);
    return {
      wordCloud: "Mystery, Finance, Giant, Benchmark, Value",
      clue1: "This company is a giant in its sector.",
      clue2: "It has a long history of dominating the market.",
      clue3: "You might interact with its products daily."
    };
  }
}

/**
 * Evaluates a user's guess and provides a dynamic hint
 */
async function evaluateGuess(userGuess, actualCompanyName, actualSector) {
  try {
    const aiLlm = getLLMClient();
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
