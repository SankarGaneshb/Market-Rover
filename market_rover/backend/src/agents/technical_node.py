import os
from src.state import AgentState
from rover_tools.advanced_skills import calculate_mtc_score_tool, detect_technical_patterns_tool
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def technical_node(state: AgentState) -> dict:
    """
    Node: Technical Analysis (Parallel)
    Scans for Institutional Footprints and MTC (Multi-Timeframe Concordance).
    """
    logger.info("Executing Technical Node...")
    tickers = state.get("tickers", [])

    results = []
    celebrations = []
    feedback_prompts = []

    triple_concordance_tickers = []

    for ticker in tickers:
        # 1. Multi-Timeframe Concordance Check
        mtc_res = calculate_mtc_score_tool(ticker)

        # 2. Pattern Detection
        patterns = detect_technical_patterns_tool(ticker)

        concordance_status = "None"
        if "STRONG BUY CONCORDANCE" in mtc_res or "85/100" in mtc_res:
            concordance_status = "Strong"
            triple_concordance_tickers.append(ticker)

        results.append({
            "ticker": ticker,
            "mtc_score": mtc_res,
            "patterns": patterns,
            "concordance": concordance_status
        })

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
