import os
from src.state import AgentState
import yfinance as yf
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def dividend_node(state: AgentState) -> dict:
    """
    Node: Dividend Hunter (Parallel)
    Scans for high-yield passive income opportunities within the portfolio.
    """
    logger.info("Executing Dividend Hunter Node...")
    tickers = state.get("tickers", [])

    results = []
    celebrations = []

    high_yield_found = False

    for ticker in tickers:
        try:
            # Using yfinance to fetch yield quickly
            stock = yf.Ticker(ticker)
            dividend_yield = stock.info.get('dividendYield', 0)

            # dividendYield is usually 0.05 for 5%
            yield_pct = float(dividend_yield) * 100 if dividend_yield else 0

            results.append({
                "ticker": ticker,
                "yield": f"{yield_pct:.2f}%",
                "payout_ratio": stock.info.get('payoutRatio', 'N/A')
            })

            if yield_pct > 3.0: # 3% yield is high for Indian large caps
                high_yield_found = True
        except:
            results.append({"ticker": ticker, "yield": "Data Unavailable"})

    if high_yield_found:
        celebrations.append({
            "type": "YIELD_WINNER_BANNER",
            "message": "PASSIVE INCOME ALERT: High-yield dividend opportunities identified in your portfolio!",
            "context": "dividend_yield_success"
        })

    return {
        "dividend_data": results,
        "celebrations": celebrations,
        "current_node": "dividend_hunter"
    }
