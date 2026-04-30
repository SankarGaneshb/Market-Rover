import os
import asyncio
from src.state import AgentState
from rover_tools.advanced_skills import calculate_mtc_score_tool, detect_technical_patterns_tool
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def analyze_ticker_technicals(ticker: str):
    """Analyzes technicals for a single ticker in a thread."""
    try:
        # Wrap synchronous tool calls in to_thread
        mtc_res = await asyncio.to_thread(calculate_mtc_score_tool, ticker)
        patterns = await asyncio.to_thread(detect_technical_patterns_tool, ticker)

        concordance_status = "None"
        if "STRONG BUY CONCORDANCE" in mtc_res or "85/100" in mtc_res:
            concordance_status = "Strong"

        return {
            "ticker": ticker,
            "mtc_score": mtc_res,
            "patterns": patterns,
            "concordance": concordance_status
        }
    except Exception as e:
        logger.error(f"Technical analysis error for {ticker}: {e}")
        return {"ticker": ticker, "concordance": "Data Unavailable"}

async def technical_node(state: AgentState) -> dict:
    """
    Node: Technical Analysis (Parallel)
    Scans for Institutional Footprints and MTC (Multi-Timeframe Concordance).
    """
    logger.info("Executing Technical Node (Async/Parallel)...")
    tickers = state.get("tickers", [])

    if not tickers:
        return {"technical_data": [], "current_node": "technicals"}

    # Run all ticker technical analyses in parallel
    results = await asyncio.gather(*[analyze_ticker_technicals(t) for t in tickers])

    triple_concordance_tickers = [r["ticker"] for r in results if r.get("concordance") == "Strong"]
    celebrations = []
    feedback_prompts = []

    # Interactive UX Trigger: Triple Concordance Celebration
    if triple_concordance_tickers:
        celebrations.append({
            "type": "TRIPLE_PULSE_ACTION",
            "message": f"TRIPLE CONCORDANCE! {', '.join(triple_concordance_tickers)} are aligned across 15m, 1h, and Day charts. High conviction levels detected.",
            "context": "technical_triple_concordance"
        })

    # Interactive UX Trigger: Divergence Feedback
    if len(results) > 0 and not triple_concordance_tickers:
        feedback_prompts.append({
            "type": "DIVERGENCE_REVIEW",
            "message": "Technical signals are currently conflicting (No Concordance). Should I focus on the Daily trend or the 1-hour reversal?",
            "choices": ["Daily Trend", "Short-term Reversal"]
        })

    return {
        "technical_data": results,
        "celebrations": celebrations,
        "feedback_prompts": feedback_prompts,
        "current_node": "technicals"
    }
