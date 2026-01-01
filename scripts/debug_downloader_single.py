
import requests
from PIL import Image
from io import BytesIO

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

ticker = "SBIN"
hardcoded_url = "https://www.google.com/s2/favicons?domain=sbicard.com&sz=192"


print(f"--- Debugging {ticker} ---")

# Test DuckDuckGo
ddg_url = f"https://icons.duckduckgo.com/ip3/sbicard.com.ico"
print(f"Trying DDG: {ddg_url}")
try:
    resp = requests.get(ddg_url, headers=HEADERS, timeout=10)
    print(f"DDG Status: {resp.status_code}, Length: {len(resp.content)}")
    if resp.status_code == 200:
        img = Image.open(BytesIO(resp.content))
        print(f"DDG Size: {img.size}")
except Exception as e:
    print(f"DDG Error: {e}")

# Test yfinance
print("Trying yfinance...")
try:
    import yfinance as yf
    t = yf.Ticker("SBIN.NS")
    info = t.info
    logo = info.get('logo_url')
    print(f"yfinance URL: {logo}")
    if logo:
        r2 = requests.get(logo, headers=HEADERS, timeout=10)
        print(f"yf Status: {r2.status_code}, Length: {len(r2.content)}")
except Exception as e:
    print(f"yfinance Error: {e}")
