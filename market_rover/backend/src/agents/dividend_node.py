import os
import asyncio
import yfinance as yf
from src.state import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def get_ticker_dividend(ticker: str):
    """Fetches dividend data for a single ticker in a thread."""
    try:
        # Wrap synchronous yfinance call in to_thread
        stock = yf.Ticker(ticker)
        info = await asyncio.to_thread(lambda: stock.info)

        dividend_yield = info.get('dividendYield', 0)
        # dividendYield is usually 0.05 for 5%
        yield_pct = float(dividend_yield) * 100 if dividend_yield else 0

        return {
            "ticker": ticker,
            "yield": f"{yield_pct:.2f}%",
            "yield_val": yield_pct,
            "payout_ratio": info.get('payoutRatio', 'N/A')
        }
    except Exception as e:
        logger.error(f"Dividend data error for {ticker}: {e}")
        return {"ticker": ticker, "yield": "Data Unavailable", "yield_val": 0}

async def dividend_node(state: AgentState) -> dict:
    """
    Node: Dividend Hunter (Parallel)
    Scans for high-yield passive income opportunities within the portfolio.
    """
    logger.info("Executing Dividend Hunter Node (Async/Parallel)...")
    tickers = state.get("tickers", [])

    if not tickers:
        return {"dividend_data": [], "current_node": "dividend_hunter"}

    # Run all ticker dividend checks in parallel
    results = await asyncio.gather(*[get_ticker_dividend(t) for t in tickers])

    high_yield_found = any(r.get("yield_val", 0) > 3.0 for r in results)
    celebrations = []

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
