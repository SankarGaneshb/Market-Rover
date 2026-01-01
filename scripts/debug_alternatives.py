
import requests
import yfinance as yf
from PIL import Image
from io import BytesIO

def test_google():
    url = "https://www.google.com/s2/favicons?domain=tcs.com&sz=128"
    try:
        print(f"Testing Google Favicon: {url}")
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ Google Success. Size: {len(response.content)} bytes")
        else:
            print(f"❌ Google Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Google Error: {e}")

def test_yfinance():
    try:
        print("Testing yfinance for TCS.NS...")
        ticker = yf.Ticker("TCS.NS")
        info = ticker.info
        logo_url = info.get('logo_url', 'Not Found')
        print(f"yfinance logo: {logo_url}")
    except Exception as e:
        print(f"❌ yfinance Error: {e}")

if __name__ == "__main__":
    test_google()
    test_yfinance()
