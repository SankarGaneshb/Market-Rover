"""
Outcome Validator - The Learning Feedback Loop.

This script audits the 'Agent Brain' (memory.json) to check if past predictions were correct.
It compares the 'Signal' (Buy/Sell) against actual price movement over the next 5-7 days using Yahoo Finance.

Usage:
    python scripts/validate_outcomes.py
"""
import sys
import os
import json
import yfinance as yf
from datetime import datetime, timedelta
from dateutil import parser
import pandas as pd

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.logger import get_logger
from rover_tools.memory_tool import read_memory, write_memory

logger = get_logger(__name__)

def get_price_change(ticker: str, start_date_str: str, days: int = 7):
    """Calculate percentage price change from start_date to start_date + days."""
    try:
        start_date = parser.parse(start_date_str).date()
        end_date = start_date + timedelta(days=days + 3) # Buffer for weekends
        
        # Download data
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if df.empty:
            return None
        
        # Get Entry Price (Close of Start Date)
        # Note: yfinance indices might be timezone aware
        # We need the closest available date on or after 'start_date'
        
        # Simple approach: First and Last available in range
        if len(df) < 2:
            return None
            
        entry_price = float(df['Close'].iloc[0])
        exit_price = float(df['Close'].iloc[-1]) # Or specifically after N days
        
        # Let's find the price exactly N days later (or closest)
        target_date = pd.Timestamp(start_date + timedelta(days=days))
        
        # Find index closest to target_date
        exit_row = df.iloc[(df.index - target_date).abs().argsort()[:1]]
        if exit_row.empty:
             exit_price = float(df['Close'].iloc[-1])
        else:
             exit_price = float(exit_row['Close'].iloc[0])

        pct_change = ((exit_price - entry_price) / entry_price) * 100
        return pct_change
        
    except Exception as e:
        logger.warning(f"Price fetch failed for {ticker}: {e}")
        return None

def validate_prediction(signal: str, pct_change: float):
    """Determine outcome based on signal and price movement."""
    signal = signal.lower()
    threshold = 1.0 # 1% move required to count as 'move'
    
    if "buy" in signal or "bull" in signal:
        if pct_change >= threshold:
            return "Success"
        elif pct_change <= -threshold:
            return "Fail"
        else:
            return "Neutral"
            
    elif "sell" in signal or "bear" in signal:
        if pct_change <= -threshold:
            return "Success"
        elif pct_change >= threshold:
            return "Fail"
        else:
            return "Neutral"
            
    return "Skipped" # Wait/Hold signals

def main():
    logger.info("🧠 Starting Outcome Validation (Learning Cycle)...")
    
    memory = read_memory()
    if not memory:
        logger.info("No memories to validate.")
        return

    updated_count = 0
    
    for entry in memory:
        # Only validate Pending items older than 3 days
        if entry.get('outcome') != 'Pending':
            continue
            
        pred_date_str = entry['date']
        pred_date = parser.parse(pred_date_str).date()
        days_passed = (datetime.now().date() - pred_date).days
        
        if days_passed < 3:
            continue # Too early to judge
            
        logger.info(f"Validating {entry['ticker']} from {pred_date_str} ({days_passed} days ago)...")
        
        pct = get_price_change(entry['ticker'], pred_date_str)
        
        if pct is not None:
            result = validate_prediction(entry['signal'], pct)
            if result != "Skipped":
                entry['outcome'] = f"{result} ({pct:+.2f}%)"
                updated_count += 1
                logger.info(f" -> Result: {entry['outcome']}")
            else:
                 entry['outcome'] = f"Neutral ({pct:+.2f}%)" # Mark as closed even if neutral
                 updated_count += 1
        else:
            logger.warning(" -> No price data available.")

    if updated_count > 0:
        write_memory(memory)
        logger.info(f"✅ Learning Complete. Updated {updated_count} memories.")
    else:
        logger.info("No memories required updates.")

if __name__ == "__main__":
    main()
