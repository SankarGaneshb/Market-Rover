import requests
import pandas as pd
import json

def fetch_nse_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.nseindia.com/'
    }
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        # First visit homepage to get cookies
        session.get("https://www.nseindia.com", timeout=10)
        
        # Then hit the API
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Status Code {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

print("--- Probing FII/DII Data ---")
fii_data = fetch_nse_data("https://www.nseindia.com/api/fiidiiActivity")
print(str(fii_data)[:500])

print("\n--- Probing Block Deals Data ---")
# Note: Block deals URL often changes or requires specific params, trying a common one
block_data = fetch_nse_data("https://www.nseindia.com/api/snapshot-capital-market-largedeal") 
print(str(block_data)[:500])
