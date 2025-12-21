from tools.market_data import MarketDataFetcher
import pandas as pd

fetcher = MarketDataFetcher()
ticker = "SBIN"
print(f"Fetching Option Chain for {ticker}...")
chain = fetcher.fetch_option_chain(ticker)

if chain:
    # Find ATM IV
    ltp = fetcher.fetch_ltp(ticker)
    print(f"LTP: {ltp}")
    
    data = chain['records']['data']
    expiry_dates = chain['records']['expiryDates']
    current_expiry = expiry_dates[0]
    
    # Filter for current expiry
    expiry_data = [x for x in data if x['expiryDate'] == current_expiry]
    
    # Find ATM strike
    min_diff = float('inf')
    atm_row = None
    
    for row in expiry_data:
        diff = abs(row['strikePrice'] - ltp)
        if diff < min_diff:
            min_diff = diff
            atm_row = row
            
    if atm_row:
        print(f"ATM Strike: {atm_row['strikePrice']}")
        call_iv = atm_row.get('CE', {}).get('impliedVolatility', 0)
        put_iv = atm_row.get('PE', {}).get('impliedVolatility', 0)
        print(f"Call IV: {call_iv}")
        print(f"Put IV: {put_iv}")
        
        avg_iv = (call_iv + put_iv) / 2
        print(f"Average ATM IV: {avg_iv}")
    else:
        print("Could not find ATM row.")
else:
    print("Failed to fetch option chain.")
