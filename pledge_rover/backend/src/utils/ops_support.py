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

async def analyze_error_async(error: Exception, context: str = "general") -> Optional[Dict[str, Any]]:
    """
    Analyzes an error using Gemini asynchronously and returns a JSON diagnostic.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        # Note: We use the synchronous genai call inside a thread if async client isn't configured,
        # but here we'll simulate the async flow for FastAPI readiness.
        model = genai.GenerativeModel('gemini-3-flash-preview')
        error_msg = str(error)
        error_type = type(error).__name__

        prompt = f"""You are the Pledge Rover Operational Support Agent (SRE).
A system error has occurred in the {context} phase of the Institutional Pledging Tracker.

ERROR DETAILS:
- Type: {error_type}
- Message: {error_msg}

TASK:
1. Identify likely root cause.
2. Recommend a GRACEFUL DEGRADATION strategy for the frontend.
3. Suggest a quick fix for the developer.

Respond ONLY with a JSON object."""

        # Use anyio or standard thread pool for the blocking call to keep event loop free
        import anyio
        response = await anyio.to_thread.run_sync(model.generate_content, prompt)

        raw_content = response.text if hasattr(response, 'text') else str(response)
        clean_content = raw_content.strip().replace('```json', '').replace('```', '').strip()

        try:
            return json.loads(clean_content)
        except:
            return {"rootCause": "Anomaly detected", "severity": "high"}

    except Exception as e:
        logger.error(f"SRE Ops Agent (Pledge Rover) failed: {e}")
        return None
