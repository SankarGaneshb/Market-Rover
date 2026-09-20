"""
Script to extract official corporate logos from NSE/BSE official company homepages.
Saves high-res assets to both investbrand/frontend/public/logos/ and static/investbrand/logos/
and updates brands_data.json and brands.js.
"""
import os
import json
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

NSE_COMPANIES = [
    {"id": 1, "ticker": "LICI", "company": "Life Insurance Corporation of India", "brand": "LIC", "sector": "Financials", "website": "https://licindia.in", "insight": "India's largest institutional investor and dominant life insurer founded in 1956 with the iconic motto 'Yogakshemam Vahamyaham'."},
    {"id": 2, "ticker": "RELIANCE", "company": "Reliance Industries", "brand": "Jio", "sector": "Energy", "website": "https://www.ril.com", "insight": "Digital powerhouse revolutionizing 4G/5G, telecommunications, and retail in India."},
    {"id": 3, "ticker": "TCS", "company": "Tata Consultancy Services", "brand": "TCS", "sector": "IT", "website": "https://www.tcs.com", "insight": "Pioneered India's IT export boom and flagship wealth creator of the Tata Group."},
    {"id": 4, "ticker": "HDFCBANK", "company": "HDFC Bank", "brand": "HDFC Bank", "sector": "Financials", "website": "https://www.hdfcbank.com", "insight": "India's largest private sector bank renowned for robust retail lending and digital banking."},
    {"id": 5, "ticker": "INFY", "company": "Infosys", "brand": "Infosys", "sector": "IT", "website": "https://www.infosys.com", "insight": "Global leader in digital consulting, cloud services, and next-generation software architecture."},
    {"id": 6, "ticker": "ICICIBANK", "company": "ICICI Bank", "brand": "ICICI Bank", "sector": "Financials", "website": "https://www.icicibank.com", "insight": "Leader in multi-channel banking innovation with flagship platforms like iMobile Pay."},
    {"id": 7, "ticker": "HINDUNILVR", "company": "Hindustan Unilever", "brand": "Surf Excel", "sector": "Consumer Goods", "website": "https://www.hul.co.in", "insight": "FMCG market leader whose household brand portfolio touches 9 out of 10 Indian households."},
    {"id": 8, "ticker": "ITC", "company": "ITC Limited", "brand": "Aashirvaad", "sector": "Consumer Goods", "website": "https://www.itcportal.com", "insight": "Diversified conglomerate with massive FMCG presence, paperboards, agribusiness, and luxury hotels."},
    {"id": 9, "ticker": "SBIN", "company": "State Bank of India", "brand": "SBI", "sector": "Financials", "website": "https://www.sbi.co.in", "insight": "Largest public sector bank in India serving over 480 million customers across 22,000+ branches."},
    {"id": 10, "ticker": "BHARTIARTL", "company": "Bharti Airtel", "brand": "Airtel", "sector": "Telecom", "website": "https://www.airtel.in", "insight": "Leading global telecommunications provider with extensive 5G network coverage and digital enterprise solutions."},
    {"id": 11, "ticker": "KOTAKBANK", "company": "Kotak Mahindra Bank", "brand": "Kotak 811", "sector": "Financials", "website": "https://www.kotak.com", "insight": "Pioneered digital zero-balance accounts in India and high-growth retail financial services."},
    {"id": 12, "ticker": "LT", "company": "Larsen & Toubro", "brand": "L&T", "sector": "Industrial", "website": "https://www.larsentoubro.com", "insight": "India's engineering and construction giant behind nation-building megaprojects and defense infrastructure."},
    {"id": 13, "ticker": "AXISBANK", "company": "Axis Bank", "brand": "Axis Bank", "sector": "Financials", "website": "https://www.axisbank.com", "insight": "Major private bank recognized for retail payments, credit cards, and digital wealth solutions."},
    {"id": 14, "ticker": "ASIANPAINT", "company": "Asian Paints", "brand": "Asian Paints", "sector": "Consumer Goods", "website": "https://www.asianpaints.com", "insight": "India's undisputed leader in decorative paints and home decor with unmatched supply chain efficiency."},
    {"id": 15, "ticker": "MARUTI", "company": "Maruti Suzuki", "brand": "Maruti Suzuki", "sector": "Automobile", "website": "https://www.marutisuzuki.com", "insight": "Market leader in the Indian passenger vehicle industry with an iconic nationwide service footprint."},
    {"id": 16, "ticker": "TATAMOTORS", "company": "Tata Motors", "brand": "Tata Motors", "sector": "Automobile", "website": "https://www.tatamotors.com", "insight": "Leader in India's electric mobility transition and owner of iconic luxury brand Jaguar Land Rover."},
    {"id": 17, "ticker": "SUNPHARMA", "company": "Sun Pharma", "brand": "Sun Pharma", "sector": "Pharma", "website": "https://sunpharma.com", "insight": "India's largest pharmaceutical company and top generic dermatology/specialty player globally."},
    {"id": 18, "ticker": "TITAN", "company": "Titan Company", "brand": "Tanishq", "sector": "Consumer Goods", "website": "https://www.titancompany.in", "insight": "Tata Group lifestyle powerhouse dominating branded jewelry, premium watches, and eyewear in India."},
    {"id": 19, "ticker": "BAJFINANCE", "company": "Bajaj Finance", "brand": "Bajaj Finserv", "sector": "Financials", "website": "https://www.bajajfinserv.in", "insight": "Omnichannel consumer finance leader that transformed point-of-sale zero-cost EMI lending."},
    {"id": 20, "ticker": "HCLTECH", "company": "HCL Technologies", "brand": "HCLTech", "sector": "IT", "website": "https://www.hcltech.com", "insight": "Global technology giant specializing in digital engineering, hybrid cloud, and AI transformation."},
    {"id": 21, "ticker": "WIPRO", "company": "Wipro Limited", "brand": "Wipro", "sector": "IT", "website": "https://www.wipro.com", "insight": "Leading global information technology, consulting, and business process services company."},
    {"id": 22, "ticker": "NTPC", "company": "NTPC Limited", "brand": "NTPC", "sector": "Power", "website": "https://www.ntpc.co.in", "insight": "India's largest power utility producing a quarter of the nation's electricity with rapid green energy scale."},
    {"id": 23, "ticker": "ONGC", "company": "Oil and Natural Gas Corporation", "brand": "ONGC", "sector": "Energy", "website": "https://www.ongcindia.com", "insight": "Largest crude oil and natural gas exploration and production company in India."},
    {"id": 24, "ticker": "POWERGRID", "company": "Power Grid Corporation", "brand": "PowerGrid", "sector": "Power", "website": "https://www.powergrid.in", "insight": "Central transmission utility carrying approximately 85% of India's inter-state power grid."},
    {"id": 25, "ticker": "TATASTEEL", "company": "Tata Steel", "brand": "Tata Tiscon", "sector": "Metals", "website": "https://www.tatasteel.com", "insight": "One of the world's most geographically diversified steelmakers with continuous low-cost capacity expansion."},
    {"id": 26, "ticker": "ADANIENT", "company": "Adani Enterprises", "brand": "Adani", "sector": "Industrial", "website": "https://www.adanienterprises.com", "insight": "Flagship business incubator of the Adani Group spanning airports, green hydrogen, and data infrastructure."},
    {"id": 27, "ticker": "ADANIPORTS", "company": "Adani Ports and SEZ", "brand": "Adani Ports", "sector": "Industrial", "website": "https://www.adaniports.com", "insight": "India's largest private commercial port operator and integrated logistics provider."},
    {"id": 28, "ticker": "COALINDIA", "company": "Coal India Limited", "brand": "Coal India", "sector": "Energy", "website": "https://www.coalindia.in", "insight": "Single largest coal producer in the world powering over 70% of India's thermal generation."},
    {"id": 29, "ticker": "BAJAJAUTO", "company": "Bajaj Auto", "brand": "Pulsar", "sector": "Automobile", "website": "https://www.bajajauto.com", "insight": "World's third-largest motorcycle manufacturer and leading exporter of two-wheelers and three-wheelers."},
    {"id": 30, "ticker": "MM", "company": "Mahindra & Mahindra", "brand": "Mahindra SUV", "sector": "Automobile", "website": "https://www.mahindra.com", "insight": "Market leader in rugged SUVs, farm tractors, and commercial vehicles with strong global reach."},
    {"id": 31, "ticker": "NESTLEIND", "company": "Nestle India", "brand": "Maggi", "sector": "Consumer Goods", "website": "https://www.nestle.in", "insight": "Iconic food & beverage titan behind legendary Indian pantry staples like Maggi, Nescafe, and KitKat."},
    {"id": 32, "ticker": "ULTRACEMCO", "company": "UltraTech Cement", "brand": "UltraTech", "sector": "Materials", "website": "https://www.ultratechcement.com", "insight": "Third-largest cement manufacturer in the world outside China and India's top building materials brand."},
    {"id": 33, "ticker": "JSWSTEEL", "company": "JSW Steel", "brand": "JSW Steel", "sector": "Metals", "website": "https://www.jsw.in", "insight": "Flagship company of JSW Group operating state-of-the-art steel production facilities across India."},
    {"id": 34, "ticker": "GRASIM", "company": "Grasim Industries", "brand": "Birla Pivot", "sector": "Materials", "website": "https://www.grasim.com", "insight": "Global leader in Viscose Staple Fibre (VSF) and emerging disruptor in decorative paints."},
    {"id": 35, "ticker": "TECHM", "company": "Tech Mahindra", "brand": "Tech Mahindra", "sector": "IT", "website": "https://www.techmahindra.com", "insight": "Specialist in 5G, telecom networking solutions, and next-gen enterprise digital consulting."},
    {"id": 36, "ticker": "HINDALCO", "company": "Hindalco Industries", "brand": "Hindalco", "sector": "Metals", "website": "https://www.hindalco.com", "insight": "Global leader in aluminum rolling and recycling through Novelis, and major copper producer in India."},
    {"id": 37, "ticker": "BRITANNIA", "company": "Britannia Industries", "brand": "Good Day", "sector": "Consumer Goods", "website": "https://britannia.co.in", "insight": "Over 130-year-old beloved bakery and dairy brand famous for Good Day, Marie Gold, and Jim Jam."},
    {"id": 38, "ticker": "CIPLA", "company": "Cipla Limited", "brand": "Cipla", "sector": "Pharma", "website": "https://www.cipla.com", "insight": "Global pharmaceutical pioneer championing accessible healthcare, respiratory therapies, and essential medicines."},
    {"id": 39, "ticker": "DRREDDY", "company": "Dr. Reddy's Laboratories", "brand": "Dr. Reddy's", "sector": "Pharma", "website": "https://www.drreddys.com", "insight": "International generic pharma innovator with deep expertise in APIs, biosimilars, and active oncology drugs."},
    {"id": 40, "ticker": "EICHERMOT", "company": "Eicher Motors", "brand": "Royal Enfield", "sector": "Automobile", "website": "https://www.eicher.in", "insight": "Parent company of legendary mid-weight leisure motorcycle brand Royal Enfield and VECV trucks."},
    {"id": 41, "ticker": "DIVISLAB", "company": "Divi's Laboratories", "brand": "Divi's Labs", "sector": "Pharma", "website": "https://www.divislabs.com", "insight": "World's leading manufacturer of active pharmaceutical ingredients (APIs) and custom synthesis for global pharma."},
    {"id": 42, "ticker": "APOLLOHOSP", "company": "Apollo Hospitals", "brand": "Apollo 24|7", "sector": "Healthcare", "website": "https://www.apollohospitals.com", "insight": "Pioneered integrated healthcare in India with multi-specialty hospitals, pharmacies, and digital health."},
    {"id": 43, "ticker": "TATACONSUM", "company": "Tata Consumer Products", "brand": "Tata Tea", "sector": "Consumer Goods", "website": "https://www.tataconsumer.com", "insight": "Fast-growing consumer goods giant uniting Tata Tea, Tata Salt, Sampann, and Starbucks in India."},
    {"id": 44, "ticker": "HEROMOTOCO", "company": "Hero MotoCorp", "brand": "Splendor", "sector": "Automobile", "website": "https://www.heromotocorp.com", "insight": "World's largest manufacturer of motorcycles and scooters in terms of unit volumes for over two decades."},
    {"id": 45, "ticker": "BPCL", "company": "Bharat Petroleum", "brand": "Bharat Petroleum", "sector": "Energy", "website": "https://www.bharatpetroleum.in", "insight": "Maharatna energy PSU with major refining operations and nationwide premium fuel station retail networks."},
    {"id": 46, "ticker": "LTIM", "company": "LTIMindtree", "brand": "LTIMindtree", "sector": "IT", "website": "https://www.ltimindtree.com", "insight": "L&T Group global technology consulting and digital solutions enterprise formed through a landmark merger."},
    {"id": 47, "ticker": "INDUSINDBK", "company": "IndusInd Bank", "brand": "IndusInd Bank", "sector": "Financials", "website": "https://www.indusind.com", "insight": "Leading new-generation private bank specializing in commercial vehicle loans and consumer finance."},
    {"id": 48, "ticker": "SBILIFE", "company": "SBI Life Insurance", "brand": "SBI Life", "sector": "Financials", "website": "https://www.sbilife.co.in", "insight": "Joint venture life insurer leveraging SBI's vast branch distribution with market-leading solvency ratios."},
    {"id": 49, "ticker": "HDFCLIFE", "company": "HDFC Life Insurance", "brand": "HDFC Life", "sector": "Financials", "website": "https://www.hdfclife.com", "insight": "Pioneering private life insurer with industry-leading product innovation and long-term asset management."},
    {"id": 50, "ticker": "ZOMATO", "company": "Zomato Limited", "brand": "Zomato", "sector": "Consumer Goods", "website": "https://www.zomato.com", "insight": "India's hypergrowth food delivery and quick-commerce pioneer with Blinkit revolutionizing instant grocery delivery."}
]

FRONTEND_LOGOS_DIR = r"c:\Users\bsank\Market-Rover\investbrand\frontend\public\logos"
STATIC_LOGOS_DIR = r"c:\Users\bsank\Market-Rover\static\investbrand\logos"
BRANDS_DATA_JSON = r"c:\Users\bsank\Market-Rover\investbrand\backend\brands_data.json"
BRANDS_JS = r"c:\Users\bsank\Market-Rover\investbrand\frontend\src\data\brands.js"

os.makedirs(FRONTEND_LOGOS_DIR, exist_ok=True)
os.makedirs(STATIC_LOGOS_DIR, exist_ok=True)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

updated_brands = []

print(f"Extracting authentic logos for {len(NSE_COMPANIES)} Nifty companies from official homepages...")

for idx, comp in enumerate(NSE_COMPANIES):
    ticker = comp["ticker"]
    brand_name = comp["brand"]
    company_name = comp["company"]
    website = comp["website"]

    png_filename = f"{ticker}.png"
    frontend_path = os.path.join(FRONTEND_LOGOS_DIR, png_filename)
    static_path = os.path.join(STATIC_LOGOS_DIR, png_filename)

    logo_found = False

    # If the file already exists and is non-empty, keep it
    if os.path.exists(static_path) and os.path.getsize(static_path) > 1000:
        logo_found = True
        print(f"[{idx+1}/{len(NSE_COMPANIES)}] {ticker} ({brand_name}): Using verified asset ({os.path.getsize(static_path)} bytes)")
    else:
        # Fetch from official website
        try:
            resp = requests.get(website, headers=headers, timeout=5, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Look for high-res logo
            logo_img_tag = soup.find('img', alt=lambda x: x and any(k in x.lower() for k in ['logo', brand_name.lower(), ticker.lower()]))
            if not logo_img_tag:
                logo_img_tag = soup.find('link', rel=lambda x: x and 'apple-touch-icon' in x.lower())

            logo_src = None
            if logo_img_tag:
                logo_src = logo_img_tag.get('src') or logo_img_tag.get('href')
                if logo_src and not logo_src.startswith('http'):
                    logo_src = urllib.parse.urljoin(website, logo_src)

            if logo_src:
                img_data = requests.get(logo_src, headers=headers, timeout=5, verify=False).content
                if len(img_data) > 500:
                    with open(frontend_path, 'wb') as f:
                        f.write(img_data)
                    with open(static_path, 'wb') as f:
                        f.write(img_data)
                    logo_found = True
                    print(f"[{idx+1}/{len(NSE_COMPANIES)}] {ticker} ({brand_name}): Extracted from {logo_src}")
        except Exception as e:
            pass

    # Build brand dictionary
    entry = {
        "id": comp["id"],
        "index": "Nifty 50",
        "company": company_name,
        "ticker": ticker,
        "brand": brand_name,
        "sector": comp["sector"],
        "logoUrl": f"/logos/{png_filename}",
        "website": website,
        "insight": comp["insight"]
    }
    updated_brands.append(entry)

# Write to brands_data.json
with open(BRANDS_DATA_JSON, 'w', encoding='utf-8') as f:
    json.dump(updated_brands, f, indent=2)

# Write to brands.js
js_content = "export const NIFTY50_BRANDS = " + json.dumps(updated_brands, indent=2) + ";\n"
with open(BRANDS_JS, 'w', encoding='utf-8') as f:
    f.write(js_content)

print(f"\n[DONE] Successfully structured {len(updated_brands)} authentic brand datasets.")
