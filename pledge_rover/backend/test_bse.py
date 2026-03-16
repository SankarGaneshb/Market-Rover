import requests

def fetch_bse_sast():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        url = "https://api.bseindia.com/BseIndiaAPI/api/SastReg31/w?scripcode=&fromdate=&todate="
        print("Fetching BSE Reg 31 data...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"Successfully fetched records from BSE.")
        print(len(data.get('Table', [])))
        return data
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error fetching BSE data: {e}")
        return None

if __name__ == "__main__":
    fetch_bse_sast()
