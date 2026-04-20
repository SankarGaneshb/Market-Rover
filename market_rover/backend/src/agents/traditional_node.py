import os
import yfinance as yf
from src.state import AgentState
from rover_tools.advanced_skills import fetch_subha_muhurtham_tool
from src.utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

async def traditional_node(state: AgentState) -> dict:
    """
    Node: Traditional & Fundamental Analysis (Parallel)
    Maps the 'Auspicious When' and 'Fundamental Why' using P/E and PEG ratios.
    """
    logger.info("Executing Traditional & Fundamental Node...")
    tickers = state.get("tickers", [])
    current_year = datetime.now().year

    # 1. Fetch Muhurtham Data
    muhurtham_res = fetch_subha_muhurtham_tool(current_year)

    # 2. Fundamental Scrub
    fundamental_results = []
    undervalued_tickers = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            pe = info.get('trailingPE', 0)
            peg = info.get('pegRatio', 0)
            pb = info.get('priceToBook', 0)

            # Logic: Identify "Deep Value" or "Growth at Reasonable Price"
            is_undervalued = False
            if pe and pe > 0 and pe < 20 and (peg and peg > 0 and peg < 1.0):
                is_undervalued = True
                undervalued_tickers.append(ticker)

            fundamental_results.append({
                "ticker": ticker,
                "pe": f"{pe:.2f}" if pe else "N/A",
                "peg": f"{peg:.2f}" if peg else "N/A",
                "pb": f"{pb:.2f}" if pb else "N/A",
                "is_undervalued": is_undervalued
            })
        except Exception as e:
            logger.debug(f"Fundamental fetch for {ticker} failed: {e}")
            fundamental_results.append({"ticker": ticker, "status": "Fundamental Data Unavailable"})

    traditional_insights = [muhurtham_res]
    celebrations = []

    # 3. Traditional Celebration
    if "Akshaya Tritiya" in muhurtham_res or "Diwali" in muhurtham_res:
        celebrations.append({
            "type": "TRADITIONAL_DIYA",
            "message": "AUSPICIOUS MATCH: A major Subha Muhurtham window is approaching for your entry!",
            "context": "traditional_festive_match"
        })

    # 4. Fundamental Celebration
    if undervalued_tickers:
        celebrations.append({
            "type": "VALUE_GEM_GLOW",
            "message": f"VALUE DISCOVERY: {', '.join(undervalued_tickers)} are trading at a significant fundamental discount (PEG < 1.0)!",
            "context": "fundamental_undervalued"
        })

    return {
        "traditional_insights": traditional_insights,
        "fundamental_data": fundamental_results,
        "celebrations": celebrations,
        "current_node": "traditional_fundamental"
    }
