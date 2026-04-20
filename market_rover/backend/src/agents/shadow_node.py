import os
from src.state import AgentState
from rover_tools.shadow_tools import get_trap_indicator_tool, analyze_sector_flow_tool
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def shadow_node(state: AgentState) -> dict:
    """
    Node: Institutional Shadow Analysis (Forensic)
    Combines Sentiment and Technicals to detect Bull/Bear traps.
    This is the "Alpha Discovery" layer of the graph.
    """
    logger.info("Executing Shadow Node...")

    sentiment_data = state.get("sentiment_data", [])
    technical_data = state.get("technical_data", [])
    forensic_reports = state.get("forensic_reports", [])

    shadow_signals = []
    institutional_intent = "NEUTRAL"
    celebrations = []
    feedback_prompts = []

    # Logic: Cross-reference Sentiment with Technicals
    # Sentiment List: [{'ticker': 'INFY.NS', 'sentiment': 'positive', ...}]
    # Technical List: [{'ticker': 'INFY.NS', 'concordance': 'Strong', ...}]

    trap_ticker = None

    for s_item in sentiment_data:
        ticker = s_item['ticker']
        # Find matching technical data
        t_item = next((t for t in technical_data if t['ticker'] == ticker), None)

        if not t_item:
            continue

        # 1. Detect Institutional Absorption (Bull Trap for the shorts)
        if s_item['sentiment'] == "negative" and t_item['concordance'] == "Strong":
            signal = f"INSTITUTIONAL ABSORPTION detected in {ticker}. Retail is panicking, but institutional support (POC) is holding firm."
            shadow_signals.append(signal)
            trap_ticker = ticker
            institutional_intent = "ACCUMULATION"

        # 2. Detect Distribution Trap (Bear Trap for the longs)
        elif s_item['sentiment'] == "positive" and t_item['concordance'] == "None":
            signal = f"DISTRIBUTION TRAP detected in {ticker}. Euphoric retail news is being used by institutions to exit positions."
            shadow_signals.append(signal)
            institutional_intent = "DISTRIBUTION"

        # 3. Detect Forensic Ghost (Accounting Manipulation Trap)
        f_item = next((f for f in forensic_reports if f['ticker'] == ticker), None)
        if f_item and f_item['status'] == "CRITICAL":
            signal = f"FORENSIC GHOST detected in {ticker}. Despite technical signals, severe accounting red flags are present: {f_item['summary']}"
            shadow_signals.append(signal)
            institutional_intent = "WARNING"

    # Interactive UX Trigger: Forensic Discovery
    if trap_ticker:
        celebrations.append({
            "type": "FORENSIC_DISCOVERY_FLARE",
            "message": f"ALPHA SIGNAL: I have unmasked an Institutional Fingerprint in {trap_ticker}! This is a high-conviction divergence.",
            "context": "shadow_trap_discovered"
        })

        # Interactive UX Trigger: Investigate Deeper
        feedback_prompts.append({
            "type": "DEEP_DIVE_REQUEST",
            "message": f"Would you like me to run a block-deal forensic scan on {trap_ticker} to confirm the buyer quality?",
            "data": {"ticker": trap_ticker}
        })

    return {
        "shadow_signals": shadow_signals,
        "institutional_intent": institutional_intent,
        "celebrations": celebrations,
        "feedback_prompts": feedback_prompts,
        "current_node": "shadow"
    }
