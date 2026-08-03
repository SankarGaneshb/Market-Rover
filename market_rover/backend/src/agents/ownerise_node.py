from src.state import AgentState
from ownerise.backend.calculations import calculate_fractional_entitlement
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def ownerise_node(state: AgentState):
    """
    OwneRise Node: Identifies active rights issues for the portfolio.
    Alerts the user if any ticker has an upcoming record date or installment.
    """
    tickers = state.get("tickers", [])
    findings = []

    # In a real app, this would query a DB or NSE API
    # Mocking a hit for RELIANCE.NS for demonstration
    for ticker in tickers:
        if "RELIANCE" in ticker.upper():
            logger.info(f"OwneRise hit for {ticker}")
            findings.append({
                "ticker": ticker,
                "type": "RIGHTS_ISSUE",
                "message": "🚨 Active Rights Issue detected. Record Date: 2024-05-20. Entitlement: 1:15.",
                "action_url": "/ownerise"
            })

            # Add a celebration/alert to the state
            if "celebrations" not in state:
                state["celebrations"] = []
            state["celebrations"].append({
                "type": "OWNERISE_ALERT",
                "message": f"Rights Entitlement detected for {ticker}!"
            })

    # Update state
    if "traditional_insights" not in state:
        state["traditional_insights"] = []

    for f in findings:
        state["traditional_insights"].append(f["message"])

    return state
