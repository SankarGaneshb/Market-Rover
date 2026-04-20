"""
Global Market Tool - Fetches key global indices and commodities to assess market sentiment.
Uses yfinance to track Crude Oil, Gold, NASDAQ, and USDINR.
"""
import yfinance as yf
from crewai.tools import tool
from utils.logger import get_logger
from utils.metrics import track_error_detail

logger = get_logger(__name__)

@tool("Get Global Market Cues")
def get_global_cues() -> str:
    """
    Fetches real-time data for key global indicators to assess market sentiment.
    Checks:
    1. Brent Crude Oil (CL=F) - Impact on Paints, Tyres, Aviation.
    2. Gold (GC=F) - Impact on Jewelry, Gold Loans.
    3. NASDAQ 100 (^NDX) - Impact on Indian IT Sector.
    4. S&P 500 (^GSPC) - General Global Sentiment.
    5. USD/INR (INR=X) - Impact on Exporters.

    Returns:
        A formatted string summarizing the global cues (Price and % Change).
    """
    try:
        tickers = {
            "Brent Crude ($)": "CL=F",
            "Gold ($)": "GC=F",
            "NASDAQ": "^NDX",
            "S&P 500": "^GSPC",
            "USD/INR": "INR=X",
            "VIX": "^VIX",
            "US 10Y Yield": "^TNX"
        }

        output = "🌍 **Global Market Cues**:\n"

        # Download data for all tickers
        # Using auto_adjust=False to get close price
        data = yf.download(list(tickers.values()), period="5d", progress=False)

        # yfinance return structure changed in recent versions
        # Ideally we want 'Close' or 'Adj Close'
        if 'Close' in data:
            close_data = data['Close']
        else:
            close_data = data

        latest_data = close_data.iloc[-1]
        prev_data = close_data.iloc[-2]

        for name, ticker in tickers.items():
            try:
                # Handle potential MultiIndex columns in newer yfinance
                val_current = 0
                val_prev = 0

                if ticker in latest_data:
                    val_current = latest_data[ticker]
                    val_prev = prev_data[ticker]
                else:
                    # Fallback or loop to find
                     pass

                # If values are found
                if val_current and val_prev:
                    change = ((val_current - val_prev) / val_prev) * 100
                    emoji = "🟢" if change >= 0 else "🔴"
                    output += f"- {name}: {val_current:.2f} ({emoji} {change:+.2f}%)\n"
                else:
                     output += f"- {name}: Data Unavailable\n"

            except Exception as inner_e:
                 logger.debug(f"Failed to parse {name}: {inner_e}")
                 output += f"- {name}: Data Unavailable\n"

        return output

    except Exception as e:
        logger.error(f"Global Cues fetch failed: {e}")
        try:
            track_error_detail(type(e).__name__, str(e), context={"function": "get_global_cues"})
        except Exception:
            pass
        return "Error fetching Global Market Cues. Assume Neutral."

def get_global_cues_data() -> dict:
    """
    Returns raw numeric data for global metrics to be used by agents.
    """
    try:
        tickers = {"vix": "^VIX", "yield_10y": "^TNX", "dxy": "DX-Y.NYB", "sp500": "^GSPC"}
        data = yf.download(list(tickers.values()), period="2d", progress=False)
        latest = data['Close'].iloc[-1]

        return {
            "vix": float(latest.get("^VIX", 20)),
            "yield_10y": float(latest.get("^TNX", 3.5)),
            "dxy": float(latest.get("DX-Y.NYB", 100)),
            "sp500": float(latest.get("^GSPC", 5000))
        }
    except Exception:
        return {"vix": 20, "yield_10y": 3.5, "dxy": 100}
