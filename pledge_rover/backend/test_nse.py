import requests
import json
from datetime import datetime, timedelta

def fetch_nse_sast():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        print("Fetching NSE base page for cookies...")
        session.get("https://www.nseindia.com", timeout=10)
        
        # We want the last 7 days of Regulation 31. NSE endpoint for SAST is:
        print("Fetching NSE Reg 31 data...")
        url = "https://www.nseindia.com/api/corporates-sast-reg31?index=equities"
        
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"Successfully fetched {len(data.get('data', []))} records from NSE.")
        return data
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error fetching NSE data: {e}")
        return None

if __name__ == "__main__":
    fetch_nse_sast()
