import sys
from rover_tools.market_data import MarketDataFetcher
from rover_tools.market_analytics import MarketAnalyzer

fetcher = MarketDataFetcher()
analyzer = MarketAnalyzer()

ticker = "ABB.NS"
print(f"Fetching {ticker}...")
history = fetcher.fetch_full_history(ticker)
print(f"History shape: {history.shape}")

print("Running backtest...")
try:
    res = analyzer.backtest_strategies(history)
    print("Result:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
