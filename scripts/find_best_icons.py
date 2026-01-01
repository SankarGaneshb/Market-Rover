
import requests
from PIL import Image
from io import BytesIO

CANDIDATES = {
    "SBIN": ["sbicard.com", "onlinesbi.sbi", "sbi.co.in", "statebankofindia.com", "yonosbi.com"],
    "ITC": ["itcstore.in", "itcportal.com", "itc.in", "itcfoods.com"],
    "BHARTIARTL": ["airtel.com", "airtel.in", "airtelbank.com", "wynk.in"],
    "KOTAKBANK": ["kotak811.com", "kotak.com", "kotaksecurities.com"],
    "TATASTEEL": ["tata.com", "tatasteel.com", "tatasteelindia.com"],
    "HINDUNILVR": ["unilever.com", "hul.co.in"],
    "LTIM": ["ltimindtree.com", "lntinfotech.com"],
    "TITAN": ["titan.co.in", "tanishq.co.in"],
    "HDFCLIFE": ["hdfclife.com"],
    "ASIANPAINT": ["asianpaints.com", "beautifulhomes.asianpaints.com"]
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
}

print("Searching for High-Res Icons (>64px)...")
for ticker, domains in CANDIDATES.items():
    found = False
    for d in domains:
        # Try sz=192 first (more common than 512, but big enough)
        # Or sz=512
        for sz in [512, 192, 128]:
            try:
                url = f"https://www.google.com/s2/favicons?domain={d}&sz={sz}"
                resp = requests.get(url, headers=HEADERS, timeout=3)
                if resp.status_code == 200:
                    img = Image.open(BytesIO(resp.content))
                    if img.width > 64:
                        print(f"✅ {ticker}: {d} ({img.size}) -> {url}")
                        found = True
                        break # Found a good one, verify next ticker
            except:
                pass
        if found:
            break
    if not found:
        print(f"❌ {ticker}: No good icon found.")
