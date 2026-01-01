
import os
import requests
from PIL import Image, ImageOps
from io import BytesIO
import time

# Target Directory
ASSETS_DIR = os.path.join(os.getcwd(), "assets", "logos")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Mapping of Tickers to Domains
TICKER_TO_DOMAIN = {
    "RELIANCE": "ril.com",
    "TCS": "tcs.com",
    "HDFCBANK": "hdfcbank.com",
    "ICICIBANK": "icicibank.com",
    "INFY": "infosys.com",
    "SBIN": "sbi.co.in",
    "BHARTIARTL": "airtel.in",
    "ITC": "itcportal.com",
    "KOTAKBANK": "kotak.com",
    "LT": "larsentoubro.com",
    "HINDUNILVR": "hul.co.in",
    "AXISBANK": "axisbank.com",
    "BAJFINANCE": "bajajfinserv.in",
    "MARUTI": "marutisuzuki.com",
    "ASIANPAINT": "asianpaints.com",
    "HCLTECH": "hcltech.com",
    "TITAN": "titan.co.in",
    "SUNPHARMA": "sunpharma.com",
    "ULTRACEMCO": "ultratechcement.com",
    "TATASTEEL": "tatasteel.com",
    "NTPC": "ntpc.co.in",
    "POWERGRID": "powergrid.in",
    "BAJAJFINSV": "bajajfinserv.in",
    "TATAMOTORS": "tatamotors.com",
    "M&M": "mahindra.com",
    "ADANIENT": "adanienterprises.com",
    "ADANIPORTS": "adaniports.com",
    "ONGC": "ongcindia.com",
    "JSWSTEEL": "jsw.in",
    "WIPRO": "wipro.com",
    "COALINDIA": "coalindia.in",
    "GRASIM": "grasim.com",
    "HINDALCO": "hindalco.com",
    "DRREDDY": "drreddys.com",
    "TECHM": "techmahindra.com",
    "DIVISLAB": "divislabs.com",
    "CIPLA": "cipla.com",
    "SBILIFE": "sbilife.co.in",
    "BPCL": "bharatpetroleum.in",
    "BRITANNIA": "britannia.co.in",
    "EICHERMOT": "eichermotors.com",
    "HDFCLIFE": "hdfclife.com",
    "TATACONSUM": "tataconsumer.com",
    "NESTLEIND": "nestle.in",
    "HEROMOTOCO": "heromotocorp.com",
    "APOLLOHOSP": "apollohospitals.com",
    "UPL": "uplonline.com",
    "INDUSINDBK": "indusind.com",
    "BAJAJ-AUTO": "bajajauto.com",
    "LTIM": "ltimindtree.com"
}

# Hardcoded High-Res Source URLs (Google/IconHorse Bypasses)
HARDCODED_URLS = {
    # Reliable Google Sources (Verified >128px)
    "SBIN": "https://www.google.com/s2/favicons?domain=sbicard.com&sz=192",
    "BHARTIARTL": "https://www.google.com/s2/favicons?domain=airtel.com&sz=192",
    "HINDUNILVR": "https://www.google.com/s2/favicons?domain=unilever.com&sz=192",
    "TATASTEEL": "https://www.google.com/s2/favicons?domain=tata.com&sz=192",
    "LTIM": "https://www.google.com/s2/favicons?domain=ltimindtree.com&sz=192",
    
    # Fallback Sources (IconHorse/Clearbit Alternates)
    "ITC": "https://icon.horse/icon/itcportal.com",
    "KOTAKBANK": "https://icon.horse/icon/kotak.com",
    
    # Bypassed Wikimedia (use valid Google/Official if possible, else keep old or remove if broken)
    # Reliance/TCS likely work via standard Google fallback if removed, or we use Group domains
    "RELIANCE": "https://www.google.com/s2/favicons?domain=jio.com&sz=192", 
    "TCS": "https://www.google.com/s2/favicons?domain=tcs.com&sz=192",
    
    # Rest can rely on standard logic (Google -> yfinance)
}

def download_and_process_logo(ticker, domain):
    # Use standard Chrome UA to satisfy Google/Clearbit checks
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    img = None
    source = "Unknown"

    # VALIDATION HELPER
    def is_valid_image(image_obj, content_len):
        if content_len < 800: # Reject anything < 800 bytes (tiny icons/empty)
            return False, f"Too small file ({content_len} bytes)"
        if image_obj.width < 50 or image_obj.height < 50:
            return False, f"Dimensions too small ({image_obj.size})"
        return True, "OK"

    # STRATEGY 1: Hardcoded High-Res (Top 16)
    if ticker in HARDCODED_URLS:
        url = HARDCODED_URLS[ticker]
        print(f"Fetching {ticker} from Hardcoded: {url} ...")
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                temp_img = Image.open(BytesIO(resp.content))
                valid, msg = is_valid_image(temp_img, len(resp.content))
                if valid:
                    img = temp_img
                    source = "Hardcoded"
                else:
                    print(f"❌ Hardcoded rejected: {msg}")
        except Exception as e:
            print(f"❌ Hardcoded fetch failed for {ticker}: {e}")

    # STRATEGY 2: Clearbit (Usually good quality)
    if img is None:
        try:
            # Clearbit often has 128-512px logos
            url = f"https://logo.clearbit.com/{domain}?size=500"
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                temp_img = Image.open(BytesIO(resp.content))
                valid, msg = is_valid_image(temp_img, len(resp.content))
                if valid:
                    img = temp_img
                    source = "Clearbit"
        except:
            pass
            
    # STRATEGY 3: Google Favicons (High Res Attempt)
    if img is None:
        try:
            url = f"https://www.google.com/s2/favicons?domain={domain}&sz=512"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                temp_img = Image.open(BytesIO(resp.content))
                # Google often returns a default 16x16 globe (approx 300-500 bytes) if domain not found
                # The size check (3KB limit) effectively filters these out.
                valid, msg = is_valid_image(temp_img, len(resp.content))
                if valid:
                    img = temp_img
                    source = "Google"
        except:
            pass

    # FALLBACK: yfinance (Last Resort)
    if img is None: 
        print(f"⚠️ No high-res found. Trying yfinance for {ticker}...")
        try:
            import yfinance as yf
            symbol = ticker if ticker.endswith(".NS") else f"{ticker}.NS"
            yf_ticker = yf.Ticker(symbol)
            logo_url = yf_ticker.info.get('logo_url')
            if logo_url:
                print(f"Found yfinance logo: {logo_url}")
                yf_response = requests.get(logo_url, headers=headers, timeout=10)
                if yf_response.status_code == 200:
                    temp_img = Image.open(BytesIO(yf_response.content))
                    # Accept smaller from yfinance if we have nothing else, but prefer >1KB
                    if len(yf_response.content) > 1000:
                        img = temp_img
                        source = "yfinance"
        except Exception as e:
            print(f"yfinance fallback failed: {e}")

    # Final Processing
    if img:
        try:
            img = img.convert("RGBA")
            
            img = img.convert("RGBA")
            
            # ADAPTIVE MODE: No square padding. Just resize if too massive, otherwise keep raw.
            # Max width 800 to ensure quality but not insane file sizes.
            if img.width > 800:
                ratio = 800 / img.width
                new_height = int(img.height * ratio)
                img = img.resize((800, new_height), Image.LANCZOS)
            
            # Save Raw (Transparent PNG preferred)
            save_path = os.path.join(ASSETS_DIR, f"{ticker}.png")
            img.save(save_path, "PNG")
            print(f"✅ Saved {save_path} (Raw Aspect Ratio: {img.size})")
            return True
        except Exception as e:
            print(f"❌ Error processing image for {ticker}: {e}")
            return False
    else:
        print(f"❌ ALL Strategies failed for {ticker}")
        return False

def main():
    print(f"Starting legacy-compatible download to {ASSETS_DIR}...")
    count = 0
    for ticker, domain in TICKER_TO_DOMAIN.items():
        if download_and_process_logo(ticker, domain):
            count += 1
        time.sleep(0.5) 
        
    print(f"\nDownload Complete. Successfully processed {count}/{len(TICKER_TO_DOMAIN)} logos.")

if __name__ == "__main__":
    main()
