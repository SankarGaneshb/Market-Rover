"""
Unified Operational Support Agent (SRE) for Pledge Rover (Python/FastAPI).
Analyzes system errors and provides mitigation strategies.
"""
import os
import json
import logging
import google.generativeai as genai
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def analyze_error(error: Exception, context: str = "general") -> Optional[Dict[str, Any]]:
    """
    Analyzes an error using Gemini and returns a JSON diagnostic.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("SRE Ops Agent (Pledge Rover): GOOGLE_API_KEY not found.")
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        error_msg = str(error)
        error_type = type(error).__name__
        
        prompt = f"""You are the Pledge Rover Operational Support Agent (SRE).
A system error has occurred in the {context} phase of the Institutional Pledging Tracker.

ERROR DETAILS:
- Type: {error_type}
- Message: {error_msg}

TASK:
1. Identify likely root cause (e.g. Database, LLM Timeout, CrewAI threading error).
2. Recommend a GRACEFUL DEGRADATION strategy for the frontend.
3. Suggest a quick fix for the developer.

Respond ONLY with a JSON object:
{{
  "rootCause": "brief explanation",
  "mitigation": "how to respond to user",
  "developerFix": "code or infrastructure fix suggestion",
  "severity": "high"
}}"""

        response = model.generate_content(prompt)
        raw_content = response.text if hasattr(response, 'text') else str(response)
        clean_content = raw_content.strip().replace('```json', '').replace('```', '').strip()
        
        try:
            return json.loads(clean_content)
        except json.JSONDecodeError:
            return {
                "rootCause": "Complex system failure",
                "mitigation": "Please try again later.",
                "severity": "high"
            }

    except Exception as e:
        logger.error(f"SRE Ops Agent (Pledge Rover) failed: {e}")
        return None
