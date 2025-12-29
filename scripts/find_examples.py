
import sys
import os
sys.path.append(os.getcwd())

from rover_tools.shadow_tools import analyze_sector_flow, detect_silent_accumulation

def find_examples():
    print("--- 1. Scanning Sectors (LIVE) ---")
    sectors = analyze_sector_flow()
    if not sectors.empty:
        print("Top 3 Sectors:")
        print(sectors.head(3)[['Sector', 'Momentum Score']])
    else:
        print("No sector data found.")

    print("\n--- 2. Scanning for Accumulation (LIVE) ---")
    # List of liquid stocks to check
    watchlist = [
        "ITC.NS", "SBIN.NS", "RELIANCE.NS", "TATAMOTORS.NS", 
        "HDFCBANK.NS", "INFY.NS", "ONGC.NS", "NTPC.NS", 
        "COALINDIA.NS", "SUNPHARMA.NS", "M&M.NS", "LT.NS"
    ]
    
    found = False
    for ticker in watchlist:
        try:
            res = detect_silent_accumulation(ticker)
            score = res.get('score', 0)
            if score >= 50: # Show anything decent
                print(f"✅ {ticker}: Score {score}/100")
                print(f"   Signals: {res['signals']}")
                found = True
        except Exception as e:
            pass
            
    if not found:
        print("No high accumulation scores found in this small sample.")

if __name__ == "__main__":
    find_examples()
