"""
Shadow Tools - Unconventional Institutional Analytics
"""
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from nselib import capital_market, derivatives
from rover_tools.ticker_resources import NIFTY_50_SECTOR_MAP
from utils.logger import get_logger
try:
    from crewai.tools import tool
except ImportError:
    # Fallback if crewai is not installed (e.g. in lightweight CI scripts)
    def tool(name_or_func):
        def decorator(func):
            return func
        return decorator

logger = get_logger(__name__)

# --- 1. THE SPIDER WEB (Sector Rotation) ---
def analyze_sector_flow():
    """
    Analyzes relative strength of major sectors to detect rotation.
    Returns a DataFrame with 1W, 1M performance and Relative Strength Ranking.
    """
    sectors = {
        "Nifty Bank": "^NSEBANK",
        "Nifty Auto": "^CNXAUTO",
        "Nifty IT": "^CNXIT",
        "Nifty Metal": "^CNXMETAL",
        "Nifty Pharma": "^CNXPHARMA",
        "Nifty FMCG": "^CNXFMCG",
        "Nifty Energy": "^CNXENERGY",
        "Nifty Infra": "^CNXINFRA",
        "Nifty Realty": "^CNXREALTY",
        "Nifty PSU Bank": "^CNXPSUBANK"
    }
    
    results = []
    
    try:
        # Fetch last 30 days of data for all sectors
        tickers = list(sectors.values())
        data = yf.download(tickers, period="1mo", progress=False)['Close']
        
        if data.empty:
            logger.error("No sector data fetched")
            return pd.DataFrame()

        for name, ticker in sectors.items():
            if ticker not in data.columns:
                continue
                
            series = data[ticker].dropna()
            if series.empty:
                continue
                
            current_price = series.iloc[-1]
            week_ago = series.iloc[-5] if len(series) >= 5 else series.iloc[0]
            month_ago = series.iloc[0]
            
            pct_1w = ((current_price - week_ago) / week_ago) * 100
            pct_1m = ((current_price - month_ago) / month_ago) * 100
            
            # Simple Momentum Score
            momentum = (pct_1w * 0.4) + (pct_1m * 0.6)
            
            results.append({
                "Sector": name,
                "Ticker": ticker,
                "1W %": round(pct_1w, 2),
                "1M %": round(pct_1m, 2),
                "Momentum Score": round(momentum, 2)
            })
            
        df = pd.DataFrame(results).sort_values(by="Momentum Score", ascending=False)
        df = df.reset_index(drop=True)
        df['Rank'] = df.index + 1
        return df
        
    except Exception as e:
        logger.error(f"Sector Analysis Failed: {e}")
        return pd.DataFrame()


# --- 2. WHALE ALERT (Block Deals) ---
def fetch_block_deals(symbol=None):
    """
    Fetches recent Block/Bulk deals using nselib.
    If symbol is provided, filters for that specific stock.
    """
    try:
        # Fetch data for the last 1M to ensure we get something
        raw_data = capital_market.block_deals_data(period='1M')
        
        if raw_data.empty:
            return []

        # Normalize columns
        raw_data.columns = [c.strip() for c in raw_data.columns]
        
        # Filter by symbol if provided
        if symbol:
            # Handle symbol formatting (NSE:RELIANCE or RELIANCE.NS -> RELIANCE)
            clean_symbol = symbol.split('.')[0].split(':')[-1].upper()
            raw_data = raw_data[raw_data['Symbol'].str.upper() == clean_symbol]

        deals = []
        for idx, row in raw_data.iterrows():
            try:
                qty_str = str(row.get('Quantity', '0')).replace(',', '')
                price_str = str(row.get('Trade Price/Wght. Avg. Price', '0')).replace(',', '')
                qty = float(qty_str)
                price = float(price_str)
                value_lac = (qty * price) / 100000
                
                if value_lac > 100: # Show only deals > 1 Cr for relevance
                    deals.append({
                        "Date": row.get('Date', ''),
                        "Symbol": row.get('Symbol', ''),
                        "Client": row.get('Client Name', 'Unknown'),
                        "Type": row.get('Buy/Sell', 'Unknown'),
                        "Qty": f"{qty/100000:.2f}L",
                        "Price": price
                    })
            except Exception:
                continue
                
        # Return top 5 most recent
        return deals[:5]
        
    except Exception as e:
        logger.error(f"Failed to fetch block deals: {e}")
        return []


# --- 3. SILENT ACCUMULATION (Delivery + IV) ---
def detect_silent_accumulation(ticker):
    """
    Calculates a 'Shadow Score' (0-100) indicating likely institutional accumulation.
    Based on:
    1. Low Volatility (Consolidation)
    2. Rising Volume/Delivery (Simulated via Volume trend if Delivery unavailable)
    3. Put Call Ratio (PCR) > 1 (Bullish)
    """
    score = 0
    signals = []
    
    try:
        ticker = ticker.replace("$", "").strip().upper()
        if not ticker.endswith(('.NS', '.BO')) and '^' not in ticker:
             ticker += ".NS"
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return {"score": 0, "signals": ["No Data"]}
            
        # 1. Price Consolidation Check (Low ADR)
        # Calculate Average Daily Range %
        last_10 = hist.tail(10)
        daily_range_pct = ((last_10['High'] - last_10['Low']) / last_10['Low']).mean() * 100
        
        if daily_range_pct < 2.0: # Very tight consolidation
            score += 30
            signals.append("Price Squeeze (Tight Consolidation)")
            
        # 2. Volume Anomaly (Rising Volume during flat price)
        avg_vol_30 = hist['Volume'].mean()
        avg_vol_5 = last_10['Volume'].mean()
        
        if avg_vol_5 > (avg_vol_30 * 1.2): # 20% higher volume recently
            score += 30
            signals.append("Volume Spike (Possible Accumulation)")
            
        # 3. Option Chain (PCR) - via yfinance directly is hard, we use a heuristic
        # We'll check if close > 20DMA (Trend) as a proxy for "smart money support"
        ma_20 = hist['Close'].rolling(20).mean().iloc[-1]
        current = hist['Close'].iloc[-1]
        
        if current > ma_20:
            score += 20
            signals.append("Above 20-DMA (Institutional Support)")
        
        # 4. Delivery Proxy (close near high usually means delivery buying)
        # If today's close is in the top 25% of the daily range
        todays = hist.iloc[-1]
        range_len = todays['High'] - todays['Low']
        if range_len > 0:
            pos = (todays['Close'] - todays['Low']) / range_len
            if pos > 0.75:
                score += 20
                signals.append("Strong Close (High Buying Pressure)")
                
        return {"score": score, "signals": signals}

    except Exception as e:
        logger.error(f"Silent Accumulation Check Failed for {ticker}: {e}")
        return {"score": 0, "signals": ["Error analyzing data"]}


# --- 3.5 SECTOR ACCUMULATION STATS ---
def get_sector_stocks_accumulation(sector_name):
    """
    Aggregates accumulation scores for all stocks in a sector.
    """
    try:
        # Get stocks for sector
        sector_stocks = [t for t, s in NIFTY_50_SECTOR_MAP.items() if s == sector_name]
        
        if not sector_stocks:
            return pd.DataFrame()
            
        results = []
        for ticker in sector_stocks:
            res = detect_silent_accumulation(ticker)
            results.append({
                "Symbol": ticker.replace(".NS", ""),
                "Shadow Score": res.get('score', 0),
                "Signals": ", ".join(res.get('signals', []))
            })
            
        df = pd.DataFrame(results).sort_values(by="Shadow Score", ascending=False)
        return df
    except Exception as e:
        logger.error(f"Sector Accumulation Stats Failed for {sector_name}: {e}")
        return pd.DataFrame()


# --- 4. TRAP DETECTOR (FII Sentiment) ---
def get_trap_indicator():
    """
    Returns FII Sentiment Status based on Index Futures using nselib.
    """
    try:
        # Fetch FII derivatives stats (nselib requires explicit date sometimes)
        today_str = datetime.now().strftime("%d-%m-%Y")
        # If it fails for today (holiday/market closed), nselib might error or return empty
        # Ideally we loop back a few days, but let's try today first
        try:
             df = derivatives.fii_derivatives_statistics(trade_date=today_str)
        except:
             # Fallback to yesterday if today fails (rudimentary retry)
             yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
             df = derivatives.fii_derivatives_statistics(trade_date=yesterday)
        if df.empty:
             return {"status": "Unknown", "fii_long_pct": 50, "message": "Data Unavailable"}
             
        # Normalize columns (Date, Instrument Type, ... Number of Contracts Buy, Number of Contracts Sell)
        df = df.reset_index() # Ensure Date is available as column if it became index
        # We need 'Index Futures' row for the latest date
        if 'Date' not in df.columns:
             # Try finding a column that looks like date or lowercase
             for c in df.columns:
                 if 'date' in c.lower():
                     df.rename(columns={c: 'Date'}, inplace=True)
                     break
        
        if 'Date' not in df.columns:
             return {"status": "Unknown", "fii_long_pct": 50, "message": "Date column missing in FII data"}

        latest_date = df['Date'].iloc[-1]
        day_data = df[df['Date'] == latest_date]
        
        idx_fut = day_data[day_data['Instrument Type'].str.contains('Index Futures', case=False, na=False)]
        
        if idx_fut.empty:
             return {"status": "Neutral", "fii_long_pct": 50, "message": "No Index Futures Data"}
             
        idx_fut = idx_fut.iloc[0]
        
        # Extract values
        longs = float(str(idx_fut.get('Buy High', 0) if 'Buy High' in idx_fut else idx_fut.iloc[2]).replace(',', '')) # Fallback logic dependent on dataframe structure
        # Actually nselib returns specific columns. Let's rely on inspection logic or broad try/catch
        # Usually: "Buy Contract" vs "Sell Contract"
        # Since column names vary, we'll try standard keys
        
        # RE-FETCH with specific known method if possible or parse current df carefully
        # The dataframe usually has: ['Date', 'Instrument Type', 'Number of Contracts (Buy)', 'Number of Contracts (Sell)', ...]
        
        # Let's trust pandas structure from typical nselib output
        # Col 3 is Buy Contracts, Col 5 is Sell Contracts (0-indexed: 2, 4) if verifying locally
        # Better: use header matching
        buy_col = [c for c in df.columns if 'Buy' in c and 'Contract' in c][0]
        sell_col = [c for c in df.columns if 'Sell' in c and 'Contract' in c][0]
        
        long_contracts = float(str(idx_fut[buy_col]).replace(',', ''))
        sell_contracts = float(str(idx_fut[sell_col]).replace(',', ''))
        
        total = long_contracts + sell_contracts
        long_pct = round((long_contracts / total) * 100, 1)
        
        status = "Neutral"
        msg = f"FIIs have {long_pct}% Long Exposure."
        
        if long_pct > 70:
            status = "Euphoria"
            msg += " **Risk of Bull Trap!**"
        elif long_pct < 30:
            status = "Panic"
            msg += " **Risk of Bear Trap!** (Reversal Possible)"
        else:
            status = "Neutral"
            msg += " Balanced positioning."
            
        return {
            "status": status,
            "fii_long_pct": long_pct, 
            "message": msg
        }

    except Exception as e:
        import traceback
        logger.error(f"Trap Detector Failed: {traceback.format_exc()}")
        return {
            "status": "Error",
            "fii_long_pct": 50, 
            "message": f"Could not fetch FII Data: {str(e)[:100]}"
        }

# ==============================================================================
# WRAPPER TOOLS FOR AGENTS (Decorated for CrewAI)
# ==============================================================================

@tool("Analyze Sector Flow")
def analyze_sector_flow_tool() -> str:
    """
    Analyzes relative strength of major sectors (Bank, Auto, IT, etc.) to detect rotation.
    Returns a text summary of top performing sectors and their momentum.
    """
    df = analyze_sector_flow()
    if df.empty:
        return "Sector analysis unavailable."
    
    # Format as string
    output = "📊 **Sector Rotation Analysis**:\n"
    # Take top 3 and bottom 3
    top = df.head(3)
    output += "Top Sectors (Inflow):\n"
    for _, row in top.iterrows():
        output += f"- {row['Sector']}: Momentum {row['Momentum Score']}, 1W: {row['1W %']}%\n"
        
    return output

@tool("Fetch Block Deals")
def fetch_block_deals_tool(symbol: str = None) -> str:
    """
    Fetches recent large 'Block Deals' or 'Bulk Deals' from the market.
    Useful for identifying what Smart Money (Institutions) are buying or selling.
    
    Args:
        symbol: Optional stock symbol to filter (e.g., RELIANCE.NS)
    """
    deals = fetch_block_deals(symbol=symbol)
    if not deals:
        return "No recent block deals found."
        
    output = f"🐋 **Whale Alerts (Block Deals)**{f' for {symbol}' if symbol else ''}:\n"
    for deal in deals:
        output += f"- {deal['Symbol']}: {deal['Type']} {deal['Qty']} @ {deal['Price']} ({deal['Client']})\n"
    return output

@tool("Detect Silent Accumulation")
def detect_silent_accumulation_tool(ticker: str) -> str:
    """
    Analyzes a specific stock for signs of 'Silent Accumulation' by institutions.
    Checks for Price Squeezes, Volume Spikes, and Strong Closes.
    
    Args:
        ticker: The stock symbol (e.g., HDFCBANK.NS)
    """
    res = detect_silent_accumulation(ticker)
    output = f"🕵️ **Shadow Scan for {ticker}**:\n"
    output += f"Shadow Score: {res['score']}/100\n"
    output += "Signals detected:\n"
    for sig in res['signals']:
        output += f"- {sig}\n"
    return output

@tool("Get Trap Indicator")
def get_trap_indicator_tool() -> str:
    """
    Checks the overall FII (Foreign Institutional Investor) positioning in Index Futures.
    Useful for detecting 'Bull Traps' (if FIIs are short) or 'Bear Traps'.
    """
    res = get_trap_indicator()
    return f"🕸️ **Trap Detector**: Status is {res['status']}. {res['message']} (FII Longs: {res['fii_long_pct']}%)"
