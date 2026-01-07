import yfinance as yf
import pandas as pd
import sys
import logging

# Suppress yfinance logging
logger = logging.getLogger('yfinance')
logger.setLevel(logging.CRITICAL)

from rover_tools.analytics.investor_profiler import InvestorProfiler, InvestorPersona

def run_test():
    profiler = InvestorProfiler()
    personas = [
        InvestorPersona.PRESERVER, 
        InvestorPersona.DEFENDER, 
        InvestorPersona.COMPOUNDER, 
        InvestorPersona.HUNTER
    ]
    
    # Generic picks
    user_brands = ["RELIANCE.NS", "TCS.NS"]
    
    for p in personas:
        print(f"\nTesting {p.name}...", flush=True)
        try:
            holdings = profiler.generate_smart_portfolio(p, user_brands)
            if not holdings:
                 print("  -> ERROR: No holdings generated.", flush=True)
                 continue
                 
            tickers = list(set([h['Symbol'] for h in holdings]))
            tickers = [t if t.endswith('.NS') or t.endswith('.BO') else f"{t}.NS" for t in tickers]
            
            print(f"  -> Tickers: {tickers}", flush=True)
            
            # Fetch
            data = yf.download(tickers + ['^NSEI'], period="1y", progress=False)['Close']
            
            if data.empty:
                 print("  -> ERROR: Empty Dataframe.", flush=True)
                 continue
                 
            # Check Tickers
            failed = []
            flat_line = []
            
            stock_data = data[[t for t in tickers if t in data.columns]]
            
            for t in tickers:
                if t not in data.columns:
                    failed.append(t)
                else:
                    # Check quality
                    series = data[t].dropna()
                    if series.empty:
                        failed.append(f"{t}(NoData)")
                    elif series.nunique() <= 1:
                        flat_line.append(t)
                        
            if failed:
                print(f"  -> FAIL: Missing Data for: {failed}", flush=True)
            if flat_line:
                print(f"  -> WARN: Flat line data for: {flat_line}", flush=True)
                
            if not failed and not flat_line:
                print("  -> SUCCESS", flush=True)
                
        except Exception as e:
            print(f"  -> EXCEPTION: {e}", flush=True)

if __name__ == "__main__":
    run_test()
