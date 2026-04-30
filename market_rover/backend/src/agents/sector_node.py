import os
import asyncio
from src.state import AgentState
from rover_tools.shadow_tools import analyze_sector_flow_tool
from rover_tools.ticker_resources import NIFTY_50_SECTOR_MAP
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def sector_node(state: AgentState) -> dict:
    """
    Node: Sector Rotator (Parallel)
    Maps tickers to sectors and identifies 'Leading vs Lagging' flows.
    """
    logger.info("Executing Sector Rotator Node (Async)...")
    tickers = state.get("tickers", [])

    # 1. Analyze Sector Flows using existing tool (wrapped in thread)
    sector_flow_res = await asyncio.to_thread(analyze_sector_flow_tool)

    # 2. Map Tickers to Sectors
    ticker_map = {}
    aligned_tickers = []

    for ticker in tickers:
        # Clean ticker for lookup (TCS.NS -> TCS)
        short_ticker = ticker.split('.')[0].upper()
        sector = NIFTY_50_SECTOR_MAP.get(short_ticker, "Other / Diversified")
        ticker_map[ticker] = sector

        # Check alignment with top sectors
        if sector.upper() in sector_flow_res.upper():
            aligned_tickers.append(ticker)

    sector_data = {
        "report": sector_flow_res,
        "ticker_map": ticker_map
    }

    celebrations = []

    # Logic: If major portfolio holdings are in the leading sector
    if aligned_tickers:
        celebrations.append({
            "type": "SECTOR_LEADER_PULSE",
            "message": f"STRATEGIC MATCH: {', '.join(aligned_tickers)} are aligned with current Sector Outperformance!",
            "context": "sector_rotation_alignment"
        })

    return {
        "sector_data": [sector_data],
        "celebrations": celebrations,
        "current_node": "sector_rotator"
    }
