"""
Batch Tools - Parallel processing for Market Rover agents.
Replaces single-stock tools with optimized batch operations.
"""
import concurrent.futures
import yfinance as yf
from crewai.tools import tool
from typing import List, Dict
import json
from rover_tools.shadow_tools import detect_silent_accumulation
from rover_tools.news_scraper_tool import scrape_stock_news
from utils.logger import get_logger

logger = get_logger(__name__)

# --- Helper for Parallel Execution ---
def run_in_parallel(func, items, max_workers=10):
    """Run a function for multiple items in parallel using threading."""
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {executor.submit(func, item): item for item in items}
        for future in concurrent.futures.as_completed(future_to_item):
            item = future_to_item[future]
            try:
                data = future.result()
                results[item] = data
            except Exception as e:
                logger.error(f"Error processing {item}: {e}")
                results[item] = f"Error: {str(e)}"
    return results

@tool("Batch Stock Data Fetcher")
def batch_get_stock_data(tickers: str) -> str:
    """
    Fetches real-time stock data for MULTIPLE stocks in parallel.
    
    Args:
        tickers: Comma-separated list of stock symbols (e.g., "RELIANCE.NS, TCS.NS, INFY.NS")
    
    Returns:
        A consolidated text report with data for all stocks.
    """
    try:
        # 1. Parse Tickers
        ticker_list = [t.strip().upper() for t in tickers.split(',') if t.strip()]
        
        # Ensure suffixes
        final_list = []
        for t in ticker_list:
            t = t.replace("$", "")
            if not t.endswith(('.NS', '.BO')) and '^' not in t:
                t += ".NS"
            final_list.append(t)
            
        logger.info(f"Batch fetching stock data for: {final_list}")

        # 2. Fetch all at once using yfinance (optimized)
        # yfinance can fetch multiple tickers in one call: yf.download(tickers)
        # But for 'info', we still need separate calls usually, or we use .Tickers
        
        # Strategy: Use ThreadPool for 'info' as it's often faster for detailed data vs bulk download which gives only OHLC
        
        def fetch_single(sym):
            t = yf.Ticker(sym)
            try:
                # Fast track: use fast_info if available or regular info
                price = t.fast_info.last_price
                prev = t.fast_info.previous_close
                if price is None: # Fallback
                    hist = t.history(period="2d")
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2] if len(hist)>1 else price
                    else:
                        return f"{sym}: No Data"
                
                change_pct = ((price - prev) / prev) * 100 if prev else 0.0
                return f"{sym}: ₹{price:.2f} ({change_pct:+.2f}%)"
            except Exception as e:
                return f"{sym}: Error ({str(e)})"

        results = run_in_parallel(fetch_single, final_list, max_workers=10)
        
        # Format Output
        output = "📊 **Batch Stock Market Data**:\n"
        for sym, res in results.items():
            output += f"- {res}\n"
            
        return output

    except Exception as e:
        return f"Batch Fetch Failed: {str(e)}"


@tool("Batch News Scraper")
def batch_scrape_news(tickers: str) -> str:
    """
    Scrapes news for MULTIPLE stocks in parallel.
    
    Args:
        tickers: Comma-separated stock symbols.
        
    Returns:
        Summarized news for all stocks.
    """
    try:
        ticker_list = [t.strip() for t in tickers.split(',') if t.strip()]
        logger.info(f"Batch scraping news for: {ticker_list}")

        # Re-use existing scrape_stock_news logic but parallelize it
        # We need to wrap it to return string result
        
        results = run_in_parallel(scrape_stock_news.run, ticker_list, max_workers=5) # Lower workers for scraping to be nice
        
        output = "📰 **Batch News Report**:\n\n"
        for sym, news in results.items():
            # Truncate to save context window
            summary = news[:500] + "..." if len(news) > 500 else news
            output += f"**{sym}**:\n{summary}\n\n"
            
        return output

    except Exception as e:
        return f"Batch Scrape Failed: {str(e)}"


@tool("Batch Shadow Scan")
def batch_detect_accumulation(tickers: str) -> str:
    """
    Runs Shadow Analysis (Accumulation/Trap Detection) for MULTIPLE stocks in parallel.
    
    Args:
        tickers: Comma-separated stock symbols.
    """
    try:
        ticker_list = [t.strip() for t in tickers.split(',') if t.strip()]
        logger.info(f"Batch shadow scan for: {ticker_list}")
        
        def scan_single(t):
            res = detect_silent_accumulation(t)
            # Short format
            sigs = ", ".join(res['signals']) if res['signals'] else "None"
            return f"Score: {res['score']}/100 | Signals: {sigs}"

        results = run_in_parallel(scan_single, ticker_list, max_workers=10)
        
        output = "🕵️ **Batch Institutional Shadow Scan**:\n"
        for sym, res in results.items():
            output += f"- **{sym}**: {res}\n"
            
        return output

    except Exception as e:
        return f"Batch Shadow Scan Failed: {str(e)}"
