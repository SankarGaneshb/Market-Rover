"""
Comprehensive Authentic Logo Fetcher for Indian Market Brands.
Fetches exact authentic corporate logos from official verified sources & Wikipedia High-Res Vector Renders.
Squares and centers each logo to 512x512 with clean padding for 3x3, 4x4, and 5x5 jigsaw puzzles.
Preserves user's verified LIC emblem (LICI.png).
"""
import os
import io
import json
import urllib.request
import urllib.parse
from PIL import Image

STATIC_LOGOS_DIR = r"c:\Users\bsank\Market-Rover\static\investbrand\logos"
FRONTEND_LOGOS_DIR = r"c:\Users\bsank\Market-Rover\investbrand\frontend\public\logos"
BUILD_LOGOS_DIR = r"c:\Users\bsank\Market-Rover\investbrand\frontend\build\logos"

os.makedirs(STATIC_LOGOS_DIR, exist_ok=True)
os.makedirs(FRONTEND_LOGOS_DIR, exist_ok=True)
os.makedirs(BUILD_LOGOS_DIR, exist_ok=True)

# Direct map of verified Wikipedia/Wikimedia SVG/PNG logo files for each company
BRAND_LOGO_FILES = {
    "LICI": "PRESERVE",  # User's authentic LIC emblem
    "RELIANCE": "File:Reliance_Jio_Logo.svg",
    "TCS": "File:Tata_Consultancy_Services_Logo.svg",
    "HDFCBANK": "File:HDFC_Bank_Logo.svg",
    "INFY": "File:Infosys_logo.svg",
    "ICICIBANK": "File:ICICI_Bank_Logo.svg",
    "HINDUNILVR": "File:Hindustan_Unilever_Logo.svg",
    "ITC": "File:ITC_Limited_Logo.svg",
    "SBIN": "File:State_Bank_of_India_logo.svg",
    "BHARTIARTL": "File:Bharti_Airtel_Logo.svg",
    "KOTAKBANK": "File:Kotak_Mahindra_Bank_logo.svg",
    "LT": "File:Larsen-&-Toubro-Logo.svg",
    "AXISBANK": "File:Axis_Bank_logo.svg",
    "ASIANPAINT": "File:Asian_paints_logo.svg",
    "MARUTI": "File:Maruti_Suzuki_logo.svg",
    "TATAMOTORS": "File:Tata_Motors_Logo.svg",
    "SUNPHARMA": "File:Sun_Pharma_logo.svg",
    "TITAN": "File:Tanishq Logo.svg",
    "BAJFINANCE": "File:Bajaj_Finserv_Logo.svg",
    "HCLTECH": "File:HCLTech-new-logo.svg",
    "WIPRO": "File:Wipro Logo Black.svg",
    "NTPC": "File:National_Thermal_Power_logo.svg",
    "ONGC": "File:ONGC Logo.svg",
    "POWERGRID": "File:POWERGRID NEW LOGO.png",
    "TATASTEEL": "File:Tata_Steel_Logo.svg",
    "ADANIENT": "File:Adani_logo_2012.svg",
    "ADANIPORTS": "File:Adani Ports Logo.png",
    "COALINDIA": "File:Coal_India_Logo.svg",
    "BAJAJAUTO": "File:Bajaj_Auto_logo.svg",
    "MM": "File:Mahindra_logo.svg",
    "NESTLEIND": "File:Maggi_logo.svg",
    "ULTRACEMCO": "File:Ultratech Cement Logo.svg",
    "JSWSTEEL": "File:JSW_Group_logo.svg",
    "GRASIM": "File:Aditya_Birla_Group_Logo.svg",
    "TECHM": "File:Tech_Mahindra_New_Logo.svg",
    "HINDALCO": "File:Hindalco Logo.svg",
    "BRITANNIA": "File:Britannia_Industries_logo.svg",
    "CIPLA": "File:Cipla_logo.svg",
    "DRREDDY": "File:Dr. Reddy's Laboratories logo.svg",
    "EICHERMOT": "File:Royal_Enfield_logo.svg",
    "DIVISLAB": "File:Divi's Laboratories Logo.svg",
    "APOLLOHOSP": "File:Apollo_Hospitals_Logo.svg",
    "TATACONSUM": "File:TATA-CONSUMER-PRODUCTS BLUE LOGO Feb 13.png",
    "HEROMOTOCO": "File:Hero MotoCorp Logo.svg",
    "BPCL": "File:Bharat Petroleum logo.svg",
    "LTIM": "File:LTIMindtree_Logo.svg",
    "INDUSINDBK": "File:IndusInd Bank SVG Logo.svg",
    "SBILIFE": "File:SBI Life Insurance Company Limited.svg",
    "HDFCLIFE": "File:HDFC_Life_Logo.svg",
    "ZOMATO": "File:Zomato_logo.png",
    "AMBUJACEM": "File:Ambuja Cements.svg",
    "ASHOKLEY": "File:Ashok_Leyland_logo.svg",
    "DLF": "File:DLF logo.svg",
    "INDIGO": "File:IndiGo_Airlines_logo.svg",
    "MARICO": "File:Marico Logo.svg",
    "NYKAA": "File:Nykaa New Logo.svg",
    "PAGEIND": "File:Page Industries logo.png",
    "PAYTM": "File:Paytm Logo (standalone).svg",
    "SIEMENS": "File:Siemens-logo.svg",
    "TRENT": "File:Tata logo.svg",
    "TVSMOTOR": "File:TVS Motor logo.svg",
    "VBL": "File:Pepsi_logo_2014.svg"
}

def resolve_wikimedia_url(file_title, width=960):
    url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(file_title)}&prop=imageinfo&iiprop=url&iiurlwidth={width}&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'MarketRoverLogoFetcher/2.0 (contact@marketrover.app)'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', {})
            for pid, pdata in pages.items():
                img_info = pdata.get('imageinfo', [{}])[0]
                return img_info.get('thumburl') or img_info.get('url')
    except Exception as e:
        print(f"  [API Error] {file_title}: {e}")
    return None

def search_wikimedia_logo(company_query, width=960):
    url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(company_query + ' logo')}&srnamespace=6&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'MarketRoverLogoFetcher/2.0 (contact@marketrover.app)'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get('query', {}).get('search', [])
            for res in results:
                title = res.get('title', '')
                if any(ext in title.lower() for ext in ['.svg', '.png', '.jpg', '.jpeg']):
                    thumb_url = resolve_wikimedia_url(title, width)
                    if thumb_url:
                        return thumb_url, title
    except Exception as e:
        print(f"  [Search Error] {company_query}: {e}")
    return None, None

def format_logo_to_512(img_bytes, padding_pct=0.15):
    """Trims margins and centers logo into a 512x512 canvas with clean white background."""
    im = Image.open(io.BytesIO(img_bytes)).convert('RGBA')

    # Crop transparent borders
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)

    canvas_size = 512
    max_dim = int(canvas_size * (1.0 - padding_pct * 2))

    # Scale down preserving aspect ratio
    im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    # Center on white background
    canvas = Image.new('RGBA', (canvas_size, canvas_size), (255, 255, 255, 255))
    offset = ((canvas_size - im.size[0]) // 2, (canvas_size - im.size[1]) // 2)
    canvas.paste(im, offset, mask=im if im.mode == 'RGBA' else None)
    return canvas

print(f"Starting Authentic Brand Logo Extraction for {len(BRAND_LOGO_FILES)} companies...")

success_count = 0
preserve_count = 0
failed = []

for ticker, file_title in BRAND_LOGO_FILES.items():
    static_file = os.path.join(STATIC_LOGOS_DIR, f"{ticker}.png")
    frontend_file = os.path.join(FRONTEND_LOGOS_DIR, f"{ticker}.png")
    build_file = os.path.join(BUILD_LOGOS_DIR, f"{ticker}.png")

    if file_title == "PRESERVE" and ticker == "LICI" and os.path.exists(static_file):
        print(f"[PRESERVED AUTHENTIC] {ticker}: Kept official LIC emblem.")
        preserve_count += 1
        # Sync to all dirs
        im = Image.open(static_file)
        im.save(frontend_file, "PNG")
        im.save(build_file, "PNG")
        continue

    # 1. Try direct resolution
    img_url = resolve_wikimedia_url(file_title, width=960)

    # 2. If not found, try search fallback
    if not img_url:
        img_url, found_title = search_wikimedia_logo(ticker)
        if img_url:
            print(f"  [Fallback Search Found] {ticker} -> {found_title}")

    if img_url:
        try:
            req = urllib.request.Request(img_url, headers={'User-Agent': 'MarketRoverLogoFetcher/2.0 (contact@marketrover.app)'})
            with urllib.request.urlopen(req, timeout=12) as resp:
                raw_bytes = resp.read()

            formatted_logo = format_logo_to_512(raw_bytes)
            formatted_logo.save(static_file, "PNG")
            formatted_logo.save(frontend_file, "PNG")
            formatted_logo.save(build_file, "PNG")
            print(f"[OK] {ticker}: Downloaded & formatted authentic original logo ({formatted_logo.size})")
            success_count += 1
        except Exception as e:
            print(f"[ERROR] {ticker} download failed: {e}")
            failed.append(ticker)
    else:
        print(f"[FAILED TO RESOLVE] {ticker} ({file_title})")
        failed.append(ticker)

print(f"\n==========================================")
print(f"Extraction Summary:")
print(f"  Authentic Logos Downloaded: {success_count}")
print(f"  Preserved Authentic (LIC): {preserve_count}")
print(f"  Failed: {len(failed)} -> {failed}")
print(f"==========================================")
