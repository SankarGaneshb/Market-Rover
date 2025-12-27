
import sys
import os
import pandas as pd
# Add project root to path
sys.path.append(os.getcwd())

from tools.market_analytics import MarketAnalyzer

def test_analytics():
    print("Testing MarketAnalyzer Analytics Features...")
    analyzer = MarketAnalyzer()
    
    # 1. Test Correlation Matrix
    tickers = ["RELIANCE.NS", "TCS.NS"]
    print(f"\n1. Correlation Matrix for {tickers}...")
    try:
        corr = analyzer.calculate_correlation_matrix(tickers, period="1mo")
        print("Result Head:")
        print(corr.head())
        if not corr.empty and corr.shape == (2,2):
            print("✅ Correlation Matrix Success")
        else:
            print("❌ Correlation Matrix Failed (Empty or Wrong Shape)")
    except Exception as e:
        print(f"❌ Correlation Matrix Error: {e}")

    # 2. Test Portfolio Rebalance
    print("\n2. Portfolio Rebalance...")
    portfolio = [
        {'symbol': 'RELIANCE.NS', 'value': 50000},
        {'symbol': 'TCS.NS', 'value': 50000}
    ]
    try:
        res = analyzer.suggest_rebalance(portfolio)
        print("Result Head:")
        print(res.head())
        if not res.empty and 'action' in res.columns:
            print("✅ Rebalance Success")
        else:
            print("❌ Rebalance Failed (Empty or Missing Columns)")
    except Exception as e:
        print(f"❌ Rebalance Error: {e}")

if __name__ == "__main__":
    test_analytics()
