import os
from src.state import AgentState
from src.utils.db_manager import db
from rover_tools.portfolio_tool import read_portfolio
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def retrieval_node(state: AgentState) -> dict:
    """
    Node: Portfolio Retrieval
    Ingests and validates tickers, looks up history from PostgreSQL LTM.
    """
    logger.info("Executing Retrieval Node...")

    # 1. Fetch Tickers (Simulated or via uploaded CSV context)
    # in an actual FastAPI request, this might come from the 'state' input
    raw_tickers = state.get("tickers", [])

    if not raw_tickers:
        # Check if there is a CSV to read via rover_tools
        try:
             # This uses the existing portfolio_tool.py logic
             portfolio_data = read_portfolio("Portfolio.csv")
             raw_tickers = [row['ticker'] for row in portfolio_data]
        except Exception as e:
            return {"errors": [f"Portfolio Retrieval Failed: {str(e)}"]}

    # 2. Cleanup & Standardize
    clean_tickers = []
    rejected_tickers = []

    for t in raw_tickers:
        t_clean = t.strip().upper()
        if not t_clean.endswith(".NS"):
            t_clean += ".NS"

        # Simple validation: length and alphanumeric
        if 2 <= len(t_clean.split('.')[0]) <= 10:
            clean_tickers.append(t_clean)
        else:
            rejected_tickers.append(t)

    # 3. Interactive UX Trigger: Celebration
    celebrations = []
    if len(clean_tickers) >= 5:
        celebrations.append({
            "type": "CONFETTI_LOW",
            "message": f"Successfully ingested {len(clean_tickers)} stocks for analysis!",
            "context": "retrieval_success"
        })

    # 4. Interactive UX Trigger: Feedback Loop
    feedback_prompts = []
    if rejected_tickers:
        feedback_prompts.append({
            "type": "TICKER_FIX",
            "message": f"I couldn't identify {len(rejected_tickers)} tickers. Would you like to correct them?",
            "data": rejected_tickers
        })

    # 5. Long-Term Memory (LTM) Lookup
    historical_stances = {}
    user_handle = state.get("discoverable_handle", "anonymous_user")

    # Ensure DB is connected (in a production lifecycle this happens at startup)
    await db.connect()

    for ticker in clean_tickers:
        past_call = await db.get_memory(user_handle, ticker)
        if past_call:
            historical_stances[ticker] = {
                "last_stance": past_call['stance'],
                "last_logic": past_call['logic_summary'],
                "date": past_call['analysis_date'].isoformat()
            }

    return {
        "tickers": clean_tickers,
        "celebrations": celebrations,
        "feedback_prompts": feedback_prompts,
        "historical_stances": historical_stances,
        "current_node": "retrieval"
    }
