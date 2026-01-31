
import requests
try:
    url = "https://icon.horse/icon/kotak.com"
    resp = requests.get(url, timeout=5)
    print(f"Status: {resp.status_code}, Size: {len(resp.content)}")
except Exception as e:
    print(f"Error: {e}")
