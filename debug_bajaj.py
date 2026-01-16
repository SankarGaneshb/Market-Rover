
from rover_tools.market_data import MarketDataFetcher
import pandas as pd

def test_ticker():
    ticker = "BAJAJ-AUTO.NS"
    print(f"Testing {ticker}...")
    
    fetcher = MarketDataFetcher()
    
    # 1. Fetch History
    try:
        hist = fetcher.fetch_full_history(ticker)
        print(f"History: {len(hist)} rows")
        if hist.empty:
            print("❌ History is EMPTY")
        else:
            print("✅ History OK")
    except Exception as e:
        print(f"❌ History Failed: {e}")

    # 2. Fetch Option Chain (Just to see if it works, even though we removed dependency)
    try:
        oc = fetcher.fetch_option_chain(ticker)
        print(f"Option Chain: {oc is not None}")
    except Exception as e:
        print(f"❌ Option Chain Failed: {e}")

if __name__ == "__main__":
    test_ticker()
