import yfinance as yf
import pandas as pd
import traceback
from rover_tools.analytics.investor_profiler import InvestorProfiler, InvestorPersona

def run_simulation_check(holdings, name):
    print(f"\n--- Testing Persona: {name} ---")
    if not holdings:
        print("Empty holdings!")
        return
        
    sim_df = pd.DataFrame(holdings)
    print("Holdings:", sim_df['Symbol'].tolist())
    
    tickers = [t if t.endswith('.NS') or t.endswith('.BO') else f"{t}.NS" for t in sim_df['Symbol'].tolist()]
    # Remove duplicates
    tickers = list(set(tickers))
    
    print(f"Fetch Tickers: {tickers}")
    
    try:
        # 1. Fetch Data
        data = yf.download(tickers + ['^NSEI'], period="1y", progress=False)['Close']
        
        if data.empty:
            print("ERROR: Download returned EMPTY dataframe.", flush=True)
            return

        # 2. Check Missing Columns
        missing = [t for t in tickers if t not in data.columns]
        if missing:
            print(f"WARNING: These tickers returned no data: {missing}", flush=True)
        
        # 3. Check Benchmark
        if '^NSEI' not in data.columns:
            print("ERROR: Benchmark ^NSEI missing from data.", flush=True)
        else:
            bench = data['^NSEI'].pct_change().fillna(0)
            if bench.empty or bench.isna().all():
                 print("ERROR: Benchmark data is all NaN/Empty.", flush=True)
            else:
                 print("Benchmark OK.", flush=True)

        # 4. Check Stock Data Quality
        stock_data = data[[t for t in tickers if t in data.columns]]
        if stock_data.empty:
             print("ERROR: No valid stock data found.", flush=True)
             return
             
        # Check for flat lines (Liquid funds often cause issues if price is const or nan)
        for col in stock_data.columns:
            s_ret = stock_data[col].pct_change().fillna(0)
            if s_ret.sum() == 0 and s_ret.std() == 0:
                 print(f"WARNING: {col} has zero volatility (Flat line). Might be Liquid Fund or Error.", flush=True)
            
            if stock_data[col].isna().all():
                 print(f"ERROR: {col} is all NaN.", flush=True)

        print("Simulation Data Fetch Phase Complete.", flush=True)

    except Exception as e:
        print(f"Exception: {e}", flush=True)
        traceback.print_exc()

# Setup Profiler
profiler = InvestorProfiler()
personas = [
    InvestorPersona.PRESERVER, 
    InvestorPersona.DEFENDER, 
    InvestorPersona.COMPOUNDER, 
    InvestorPersona.HUNTER
]

# Pick generic brands for safety
user_brands = ["RELIANCE.NS", "TCS.NS"] 

for p in personas:
    holdings = profiler.generate_smart_portfolio(p, user_brands)
    run_simulation_check(holdings, p.name)
