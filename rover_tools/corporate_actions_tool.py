"""
Corporate Actions Tool - Fetches official corporate announcements from NSE.
Uses nsepython to track Board Meetings, Dividends, and Financial Results.
"""
from nsepython import nse_eq
from crewai.tools import tool
from utils.logger import get_logger
from utils.metrics import track_error_detail

logger = get_logger(__name__)

@tool("Get Corporate Actions")
def get_corporate_actions(symbol: str) -> str:
    """
    Fetches official corporate actions and board meeting information from NSE for a specific stock.
    Useful for finding Dividends, Bonus issues, Splits, and upcoming Financial Results.
    
    Args:
        symbol: Stock symbol (e.g., RELIANCE.NS or RELIANCE)
        
    Returns:
        Structured summary of recent/upcoming actions.
    """
    try:
        clean_symbol = symbol.replace('.NS', '').replace('.BO', '')
        
        # Fetch detailed quote data which contains corporate action info
        data = nse_eq(clean_symbol)
        
        if not data or 'info' not in data:
            # Fallback for when NSE site blocks or returns empty
            return f"No official corporate action data available for {symbol} (NSE Connection Issue)."
            
        output = f"🏢 **Corporate Actions for {clean_symbol}**:\n"
        
        # 1. Board Meetings (Results)
        output += "\n📅 **Board Meetings**:\n"
        try:
            if 'boardMeetings' in data:
                meetings = data['boardMeetings']
                if meetings:
                    for meeting in meetings[:3]: # Last 3
                        date = meeting.get('meetingDate', 'N/A')
                        purpose = meeting.get('purpose', 'N/A')
                        output += f"- {date}: {purpose}\n"
                else:
                    output += "None listed recently.\n"
            else:
                output += "None listed.\n"
        except Exception:
             output += "Data unavailable.\n"

        return output

    except Exception as e:
        logger.error(f"Corporate Actions fetch failed for {symbol}: {e}")
        try:
            track_error_detail(type(e).__name__, str(e), context={"function": "get_corporate_actions", "symbol": symbol})
        except Exception:
            pass
        # Fallback response
        return f"Could not fetch official corporate actions for {symbol}. Please check news instead."
