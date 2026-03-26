const { ChatGoogleGenerativeAI } = require('@langchain/google-genai');
const logger = require('../utils/logger');

let aiLlmClient = null;

function getLLMClient() {
  if (!process.env.GOOGLE_API_KEY) {
    throw new Error("GOOGLE_API_KEY is missing from environment variables.");
  }
  if (!aiLlmClient) {
    aiLlmClient = new ChatGoogleGenerativeAI({
      model: 'gemini-2.0-flash',
      maxOutputTokens: 500,
      temperature: 0.1,
      apiKey: process.env.GOOGLE_API_KEY
    });
  }
  return aiLlmClient;
}

/**
 * Operational Support Agent: Analyzes a system error and returns mitigation advice.
 */
async function analyzeError(err, req) {
  try {
    const aiLlm = getLLMClient();

    const errStack = err.stack ? String(err.stack).split('\n').slice(0, 5).join('\n') : "No stack trace";
    const errBody = req.body ? JSON.stringify(req.body) : "No body";

    const analysisPrompt = `You are the InvestBrand Operational Support Agent (SRE).
A system error has occurred in the backend. 

ERROR DETAILS:
- Message: ${err.message || "Unknown error"}
- Stack: ${errStack}
- Route: ${req.method} ${req.path}
- Body: ${errBody}

TASK:
1. Identify the likely root cause (e.g. Database connectivity, API rate limit, Code bug, Missing asset).
2. Recommend a GRACEFUL DEGRADATION strategy for the frontend.
3. Suggest a quick fix for the developer.

Respond ONLY with a JSON object:
{
  "rootCause": "brief explanation",
  "mitigation": "how to respond to user",
  "developerFix": "code or infrastructure fix suggestion",
  "severity": "low" | "medium" | "high" | "critical"
}`;

    const response = await aiLlm.invoke(analysisPrompt);
    
    // Check for response.content and ensure it is treated as a string
    let rawContent = "";
    if (response && response.content) {
      if (typeof response.content === 'string') {
        rawContent = response.content;
      } else {
        rawContent = JSON.stringify(response.content);
      }
    }

    const cleanContent = rawContent
      .trim()
      .replace(/```json/gi, '')
      .replace(/```/g, '')
      .trim();

    try {
      return JSON.parse(cleanContent);
    } catch (e) {
      logger.warn('Ops Agent: Falling back to string analysis');
      return { 
        rootCause: "Parsing error", 
        mitigation: "Check server logs for detailed trace", 
        severity: "high" 
      };
    }
  } catch (agentErr) {
    logger.error('Ops Support Agent failed to analyze error', { 
      errorMessage: agentErr.message 
    });
    return null;
  }
}

module.exports = { analyzeError };
