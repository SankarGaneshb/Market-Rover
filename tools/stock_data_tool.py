"""
Stock Data Tool - Fetches stock data using yfinance.
"""
import yfinance as yf
from typing import Dict
from crewai.tools import tool
from config import convert_to_crores, CONVERT_TO_CRORES
from datetime import datetime, timedelta
from utils.logger import get_logger
from utils.metrics import track_error_detail

logger = get_logger(__name__)


@tool("Stock Data Fetcher")
def get_stock_data(symbol: str) -> str:
    """
    Fetches real-time stock data using yfinance for NSE stocks.
    Returns current price, change %, market cap, sector, and 52-week high/low.
    Converts financial figures to Crores for consistency.
    
    Args:
        symbol: Stock symbol with .NS suffix (e.g., RELIANCE.NS)
        
    Returns:
        Formatted string with stock data
    """
    try:
        # Fetch stock data
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Get historical data for 52-week range
        hist = stock.history(period="1y")
        
        if hist.empty:
            return f"No data available for {symbol}"
        
        # Extract key information
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or hist['Close'].iloc[-1]
        previous_close = info.get('previousClose') or hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        
        # Calculate change
        change = current_price - previous_close
        change_pct = (change / previous_close) * 100 if previous_close else 0
        
        # Get additional info
        market_cap = info.get('marketCap', 0)
        sector = info.get('sector', 'N/A')
        industry = info.get('industry', 'N/A')
        
        # 52-week high/low
        week_52_high = hist['High'].max()
        week_52_low = hist['Low'].min()
        
        # Format output
        output = f"Stock Data for {symbol}:\n"
        output += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        output += f"Current Price: ₹{current_price:.2f}\n"
        output += f"Change: ₹{change:.2f} ({change_pct:+.2f}%)\n"
        output += f"Previous Close: ₹{previous_close:.2f}\n"
        output += f"\n"
        
        if market_cap and CONVERT_TO_CRORES:
            output += f"Market Cap: {convert_to_crores(market_cap)}\n"
        elif market_cap:
            output += f"Market Cap: ₹{market_cap:,.0f}\n"
        
        output += f"Sector: {sector}\n"
        output += f"Industry: {industry}\n"
        output += f"\n"
        output += f"52-Week High: ₹{week_52_high:.2f}\n"
        output += f"52-Week Low: ₹{week_52_low:.2f}\n"
        
        return output
        
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}")
        try:
            track_error_detail(type(e).__name__, str(e), context={"function": "get_stock_data", "symbol": symbol})
        except Exception:
            pass
        return f"Error fetching data for {symbol}: {str(e)}"
