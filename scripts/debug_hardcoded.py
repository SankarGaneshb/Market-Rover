
import requests
from PIL import Image
from io import BytesIO

DOMAINS = {
    "SBIN": ["yono.sbi", "onlinesbi.sbi", "sbi.co.in", "statebankofindia.com"],
    "ITC": ["itcstore.in", "itcportal.com", "itc.in"],
    "BHARTIARTL": ["airtel.com", "airtel.in", "airtelbank.com"],
    "KOTAKBANK": ["kotak811.com", "kotak.com"],
    "TATASTEEL": ["tatasteel.com", "tatasteelindia.com", "tatasteel.co.uk"],
    "HINDUNILVR": ["hul.co.in", "unilever.com", "hindul.in"],
    "RELIANCE": ["ril.com", "jio.com"],
    "TCS": ["tcs.com"],
    "INFY": ["infosys.com"]
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
}

print("Testing Google Favicons (sz=512)...")
for ticker, domain_list in DOMAINS.items():
    print(f"\n--- {ticker} ---")
    for d in domain_list:
        # Try t2.gstatic.com endpoint
        url = f"https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{d}&size=256"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=5)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content))
                print(f"{d}: {img.size} ({len(resp.content)} bytes)")
            else:
                print(f"{d}: Status {resp.status_code}")
        except Exception as e:
            print(f"{d}: Error {e}")
