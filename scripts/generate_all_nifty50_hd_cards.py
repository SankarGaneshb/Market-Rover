"""
Generate 512x512 High-Definition Authentic Brand Cards for all 50 Nifty 50 Companies.
Ensures every brand asset is crisp, colorful, recognizable, and optimized for 3x3, 4x4, and 5x5 jigsaw puzzles.
Preserves user-uploaded authentic emblem for LICI.
"""
import os
import json
from PIL import Image, ImageDraw, ImageFont

STATIC_LOGOS_DIR = r"c:\Users\bsank\Market-Rover\static\investbrand\logos"
FRONTEND_LOGOS_DIR = r"c:\Users\bsank\Market-Rover\investbrand\frontend\public\logos"

os.makedirs(STATIC_LOGOS_DIR, exist_ok=True)
os.makedirs(FRONTEND_LOGOS_DIR, exist_ok=True)

# Select best available system TrueType fonts on Windows
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"
FONT_SEGOE = "C:/Windows/Fonts/segoeuib.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.truetype(FONT_BOLD, size)
        except Exception:
            return ImageFont.load_default()

# Complete definitions for all 50 Nifty 50 companies with official brand colors, logos, and taglines
NIFTY50_DEFINITIONS = [
    {
        "ticker": "LICI",
        "company": "Life Insurance Corporation of India",
        "brand": "LIC",
        "sector": "Financials",
        "bg_color": "#005BA6",
        "accent_color": "#FFD200",
        "primary_text": "LIC",
        "sub_text": "योगक्षेमं वहाम्यहम्",
        "motto": "Life Insurance Corporation of India",
        "tagline": "A Government of India Enterprise",
        "shape": "circle"
    },
    {
        "ticker": "RELIANCE",
        "company": "Reliance Industries",
        "brand": "Jio",
        "sector": "Energy",
        "bg_color": "#0A2540",
        "accent_color": "#00D4FF",
        "primary_text": "Jio",
        "sub_text": "DIGITAL LIFE",
        "motto": "Reliance Industries Limited",
        "tagline": "Growth is Life",
        "shape": "circle"
    },
    {
        "ticker": "TCS",
        "company": "Tata Consultancy Services",
        "brand": "TCS",
        "sector": "IT",
        "bg_color": "#002D72",
        "accent_color": "#00A1DE",
        "primary_text": "TATA",
        "sub_text": "TCS • CONSULTANCY SERVICES",
        "motto": "Building on Belief",
        "tagline": "Global IT & Digital Solutions",
        "shape": "card"
    },
    {
        "ticker": "HDFCBANK",
        "company": "HDFC Bank",
        "brand": "HDFC Bank",
        "sector": "Financials",
        "bg_color": "#004C8F",
        "accent_color": "#ED1C24",
        "primary_text": "HDFC BANK",
        "sub_text": "We Understand Your World",
        "motto": "India's Premier Banking Leader",
        "tagline": "SmartBuy • PayZapp • NetBanking",
        "shape": "card"
    },
    {
        "ticker": "INFY",
        "company": "Infosys",
        "brand": "Infosys",
        "sector": "IT",
        "bg_color": "#007CC3",
        "accent_color": "#FFCC00",
        "primary_text": "Infosys",
        "sub_text": "NAVIGATE YOUR NEXT",
        "motto": "Digital Services & Consulting",
        "tagline": "Powered by Cloud & AI",
        "shape": "card"
    },
    {
        "ticker": "ICICIBANK",
        "company": "ICICI Bank",
        "brand": "ICICI Bank",
        "sector": "Financials",
        "bg_color": "#8B181B",
        "accent_color": "#F37021",
        "primary_text": "ICICI Bank",
        "sub_text": "Hum Hai Na, Khayal Apka",
        "motto": "India's Leading Financial Group",
        "tagline": "iMobile Pay • InstaBIZ",
        "shape": "card"
    },
    {
        "ticker": "HINDUNILVR",
        "company": "Hindustan Unilever",
        "brand": "Surf Excel",
        "sector": "Consumer Goods",
        "bg_color": "#1F36C7",
        "accent_color": "#00D4FF",
        "primary_text": "Surf excel",
        "sub_text": "DAAG ACCHE HAIN",
        "motto": "Hindustan Unilever Limited",
        "tagline": "India's #1 Household Brand",
        "shape": "card"
    },
    {
        "ticker": "ITC",
        "company": "ITC Limited",
        "brand": "Aashirvaad",
        "sector": "Consumer Goods",
        "bg_color": "#0B3C5D",
        "accent_color": "#D9B310",
        "primary_text": "AASHIRVAAD",
        "sub_text": "SHUDDH CHAKKI ATTA",
        "motto": "ITC Limited • Enduring Value",
        "tagline": "100% Pure Sampanna",
        "shape": "card"
    },
    {
        "ticker": "SBIN",
        "company": "State Bank of India",
        "brand": "SBI",
        "sector": "Financials",
        "bg_color": "#1F4788",
        "accent_color": "#00A8E1",
        "primary_text": "SBI",
        "sub_text": "THE BANKER TO EVERY INDIAN",
        "motto": "State Bank of India",
        "tagline": "YONO • Pure Banking Nothing Else",
        "shape": "circle"
    },
    {
        "ticker": "BHARTIARTL",
        "company": "Bharti Airtel",
        "brand": "Airtel",
        "sector": "Telecom",
        "bg_color": "#C40000",
        "accent_color": "#FFFFFF",
        "primary_text": "airtel",
        "sub_text": "5G PLUS",
        "motto": "Bharti Airtel Limited",
        "tagline": "India's Leading Telecom Network",
        "shape": "circle"
    },
    {
        "ticker": "KOTAKBANK",
        "company": "Kotak Mahindra Bank",
        "brand": "Kotak 811",
        "sector": "Financials",
        "bg_color": "#ED1C24",
        "accent_color": "#003366",
        "primary_text": "kotak 811",
        "sub_text": "KOTAK MAHINDRA BANK",
        "motto": "Let's Make Money Simple",
        "tagline": "Zero Balance Digital Banking",
        "shape": "card"
    },
    {
        "ticker": "LT",
        "company": "Larsen & Toubro",
        "brand": "L&T",
        "sector": "Industrial",
        "bg_color": "#003A70",
        "accent_color": "#FFCC00",
        "primary_text": "L&T",
        "sub_text": "LARSEN & TOUBRO",
        "motto": "It's All About Imagineering",
        "tagline": "Nation Building Infrastructure",
        "shape": "card"
    },
    {
        "ticker": "AXISBANK",
        "company": "Axis Bank",
        "brand": "Axis Bank",
        "sector": "Financials",
        "bg_color": "#97144D",
        "accent_color": "#FFFFFF",
        "primary_text": "AXIS BANK",
        "sub_text": "BADHTI KA NAAM ZINDAGI",
        "motto": "Axis Bank Limited",
        "tagline": "Open Banking & Smart Credit",
        "shape": "card"
    },
    {
        "ticker": "ASIANPAINT",
        "company": "Asian Paints",
        "brand": "Asian Paints",
        "sector": "Consumer Goods",
        "bg_color": "#D9272E",
        "accent_color": "#F7A800",
        "primary_text": "asianpaints",
        "sub_text": "HAR GHAR KUCH KEHTA HAI",
        "motto": "Asian Paints Limited",
        "tagline": "Royale • Apex • Beautiful Homes",
        "shape": "card"
    },
    {
        "ticker": "MARUTI",
        "company": "Maruti Suzuki",
        "brand": "Maruti Suzuki",
        "sector": "Automobile",
        "bg_color": "#002B49",
        "accent_color": "#EE1C25",
        "primary_text": "MARUTI SUZUKI",
        "sub_text": "WAY OF LIFE!",
        "motto": "India's #1 Passenger Automobile",
        "tagline": "Arena • NEXA • Smart Hybrid",
        "shape": "card"
    },
    {
        "ticker": "TATAMOTORS",
        "company": "Tata Motors",
        "brand": "Tata Motors",
        "sector": "Automobile",
        "bg_color": "#0F2847",
        "accent_color": "#00A1DE",
        "primary_text": "TATA MOTORS",
        "sub_text": "CONNECTING ASPIRATIONS",
        "motto": "Tata Motors • JLR",
        "tagline": "Nexon EV • Safari • Harrier",
        "shape": "card"
    },
    {
        "ticker": "SUNPHARMA",
        "company": "Sun Pharma",
        "brand": "Sun Pharma",
        "sector": "Pharma",
        "bg_color": "#EA5B0C",
        "accent_color": "#FFFFFF",
        "primary_text": "SUN PHARMA",
        "sub_text": "REACHING PEOPLE. TOUCHING LIVES.",
        "motto": "India's No. 1 Pharma Giant",
        "tagline": "Specialty & Global Generics",
        "shape": "circle"
    },
    {
        "ticker": "TITAN",
        "company": "Titan Company",
        "brand": "Tanishq",
        "sector": "Consumer Goods",
        "bg_color": "#1A1A1A",
        "accent_color": "#D4AF37",
        "primary_text": "TANISHQ",
        "sub_text": "A TATA PRODUCT",
        "motto": "Titan Company Limited",
        "tagline": "Pure Gold • Diamond Jewelry",
        "shape": "card"
    },
    {
        "ticker": "BAJFINANCE",
        "company": "Bajaj Finance",
        "brand": "Bajaj Finserv",
        "sector": "Financials",
        "bg_color": "#003865",
        "accent_color": "#00B4D8",
        "primary_text": "BAJAJ FINSERV",
        "sub_text": "FINANCE • EMI • LENDING",
        "motto": "Bajaj Finance Limited",
        "tagline": "Instant Credit & Retail Moat",
        "shape": "card"
    },
    {
        "ticker": "HCLTECH",
        "company": "HCL Technologies",
        "brand": "HCLTech",
        "sector": "IT",
        "bg_color": "#00529B",
        "accent_color": "#00D4FF",
        "primary_text": "HCLTech",
        "sub_text": "SUPERCHARGING PROGRESS",
        "motto": "HCL Technologies Limited",
        "tagline": "Digital, Engineering & Cloud",
        "shape": "card"
    },
    {
        "ticker": "WIPRO",
        "company": "Wipro Limited",
        "brand": "Wipro",
        "sector": "IT",
        "bg_color": "#1B365D",
        "accent_color": "#6366F1",
        "primary_text": "wipro)",
        "sub_text": "AMBITIONS REALIZED",
        "motto": "Wipro Limited",
        "tagline": "Global AI & Technology Consulting",
        "shape": "circle"
    },
    {
        "ticker": "NTPC",
        "company": "NTPC Limited",
        "brand": "NTPC",
        "sector": "Power",
        "bg_color": "#0B4F6C",
        "accent_color": "#01BAEF",
        "primary_text": "NTPC",
        "sub_text": "POWERING INDIA'S GROWTH",
        "motto": "A Maharatna Company",
        "tagline": "Thermal • Solar • Green Hydrogen",
        "shape": "card"
    },
    {
        "ticker": "ONGC",
        "company": "Oil and Natural Gas Corporation",
        "brand": "ONGC",
        "sector": "Energy",
        "bg_color": "#8B0000",
        "accent_color": "#FFD700",
        "primary_text": "ONGC",
        "sub_text": "OIL AND NATURAL GAS CORP",
        "motto": "Maharatna Energy Pioneer",
        "tagline": "Exploration & Production Giant",
        "shape": "card"
    },
    {
        "ticker": "POWERGRID",
        "company": "Power Grid Corporation",
        "brand": "PowerGrid",
        "sector": "Power",
        "bg_color": "#005A9C",
        "accent_color": "#A0E040",
        "primary_text": "POWERGRID",
        "sub_text": "ONE NATION • ONE GRID",
        "motto": "Power Grid Corporation of India",
        "tagline": "National Electricity Transmission",
        "shape": "card"
    },
    {
        "ticker": "TATASTEEL",
        "company": "Tata Steel",
        "brand": "Tata Tiscon",
        "sector": "Metals",
        "bg_color": "#003B70",
        "accent_color": "#FFB81C",
        "primary_text": "TATA TISCON",
        "sub_text": "JOY OF BUILDING",
        "motto": "Tata Steel Limited",
        "tagline": "India's #1 Rebar Steel Brand",
        "shape": "card"
    },
    {
        "ticker": "ADANIENT",
        "company": "Adani Enterprises",
        "brand": "Adani",
        "sector": "Industrial",
        "bg_color": "#1C3F60",
        "accent_color": "#00A86B",
        "primary_text": "adani",
        "sub_text": "GROWTH WITH GOODNESS",
        "motto": "Adani Enterprises Limited",
        "tagline": "Airports • Solar • Infrastructure",
        "shape": "card"
    },
    {
        "ticker": "ADANIPORTS",
        "company": "Adani Ports and SEZ",
        "brand": "Adani Ports",
        "sector": "Industrial",
        "bg_color": "#133E5E",
        "accent_color": "#20B2AA",
        "primary_text": "adani ports",
        "sub_text": "LOGISTICS & PORTS",
        "motto": "Adani Ports and Special Economic Zone",
        "tagline": "India's Largest Commercial Port",
        "shape": "card"
    },
    {
        "ticker": "COALINDIA",
        "company": "Coal India Limited",
        "brand": "Coal India",
        "sector": "Energy",
        "bg_color": "#2D3748",
        "accent_color": "#ECC94B",
        "primary_text": "COAL INDIA",
        "sub_text": "FUELING THE NATION",
        "motto": "Coal India Limited",
        "tagline": "World's Largest Coal Producer",
        "shape": "card"
    },
    {
        "ticker": "BAJAJAUTO",
        "company": "Bajaj Auto",
        "brand": "Pulsar",
        "sector": "Automobile",
        "bg_color": "#111827",
        "accent_color": "#EF4444",
        "primary_text": "BAJAJ Pulsar",
        "sub_text": "DEFINITELY MALE",
        "motto": "Bajaj Auto Limited",
        "tagline": "World's Favourite Indian Two-Wheeler",
        "shape": "card"
    },
    {
        "ticker": "MM",
        "company": "Mahindra & Mahindra",
        "brand": "Mahindra SUV",
        "sector": "Automobile",
        "bg_color": "#8B0000",
        "accent_color": "#FFFFFF",
        "primary_text": "Mahindra",
        "sub_text": "RISE • EXPLORE THE IMPOSSIBLE",
        "motto": "Mahindra & Mahindra Limited",
        "tagline": "Thar • Scorpio-N • XUV700",
        "shape": "card"
    },
    {
        "ticker": "NESTLEIND",
        "company": "Nestle India",
        "brand": "Maggi",
        "sector": "Consumer Goods",
        "bg_color": "#C5221F",
        "accent_color": "#FBE806",
        "primary_text": "Maggi",
        "sub_text": "2-MINUTE NOODLES",
        "motto": "Nestle India Limited",
        "tagline": "Taste Bhi, Health Bhi",
        "shape": "card"
    },
    {
        "ticker": "ULTRACEMCO",
        "company": "UltraTech Cement",
        "brand": "UltraTech",
        "sector": "Materials",
        "bg_color": "#F59E0B",
        "accent_color": "#1E3A8A",
        "primary_text": "UltraTech",
        "sub_text": "THE ENGINEER'S CHOICE",
        "motto": "UltraTech Cement Limited",
        "tagline": "Aditya Birla Group • Building India",
        "shape": "card"
    },
    {
        "ticker": "JSWSTEEL",
        "company": "JSW Steel",
        "brand": "JSW Steel",
        "sector": "Metals",
        "bg_color": "#004B87",
        "accent_color": "#E31B23",
        "primary_text": "JSW Steel",
        "sub_text": "BETTER EVERYDAY",
        "motto": "JSW Group Flagship",
        "tagline": "World Class Indian Steel",
        "shape": "card"
    },
    {
        "ticker": "GRASIM",
        "company": "Grasim Industries",
        "brand": "Birla Pivot",
        "sector": "Materials",
        "bg_color": "#7C2D12",
        "accent_color": "#FBBF24",
        "primary_text": "GRASIM",
        "sub_text": "ADITYA BIRLA GROUP",
        "motto": "Grasim Industries Limited",
        "tagline": "Viscose Staple Fibre & Paints",
        "shape": "card"
    },
    {
        "ticker": "TECHM",
        "company": "Tech Mahindra",
        "brand": "Tech Mahindra",
        "sector": "IT",
        "bg_color": "#B91C1C",
        "accent_color": "#FFFFFF",
        "primary_text": "Tech Mahindra",
        "sub_text": "CONNECTED WORLD.",
        "motto": "Tech Mahindra Limited",
        "tagline": "Next-Gen 5G & Enterprise IT",
        "shape": "card"
    },
    {
        "ticker": "HINDALCO",
        "company": "Hindalco Industries",
        "brand": "Hindalco",
        "sector": "Metals",
        "bg_color": "#1E3A8A",
        "accent_color": "#F59E0B",
        "primary_text": "HINDALCO",
        "sub_text": "ALUMINIUM & COPPER",
        "motto": "Aditya Birla Group • Novelis",
        "tagline": "Greener, Stronger, Smarter",
        "shape": "card"
    },
    {
        "ticker": "BRITANNIA",
        "company": "Britannia Industries",
        "brand": "Good Day",
        "sector": "Consumer Goods",
        "bg_color": "#DC2626",
        "accent_color": "#FEF08A",
        "primary_text": "BRITANNIA",
        "sub_text": "GOOD DAY • MARIE GOLD",
        "motto": "Eat Healthy, Think Better",
        "tagline": "India's Favourite Biscuits Since 1892",
        "shape": "card"
    },
    {
        "ticker": "CIPLA",
        "company": "Cipla Limited",
        "brand": "Cipla",
        "sector": "Pharma",
        "bg_color": "#004B87",
        "accent_color": "#F97316",
        "primary_text": "Cipla",
        "sub_text": "CARING FOR LIFE",
        "motto": "Cipla Limited",
        "tagline": "Respiratory & Essential Medicine",
        "shape": "card"
    },
    {
        "ticker": "DRREDDY",
        "company": "Dr. Reddy's Laboratories",
        "brand": "Dr. Reddy's",
        "sector": "Pharma",
        "bg_color": "#581C87",
        "accent_color": "#F97316",
        "primary_text": "Dr.Reddy's",
        "sub_text": "GOOD HEALTH CAN'T WAIT",
        "motto": "Dr. Reddy's Laboratories",
        "tagline": "Global Generic Pharmaceutical Leader",
        "shape": "card"
    },
    {
        "ticker": "EICHERMOT",
        "company": "Eicher Motors",
        "brand": "Royal Enfield",
        "sector": "Automobile",
        "bg_color": "#171717",
        "accent_color": "#D4AF37",
        "primary_text": "ROYAL ENFIELD",
        "sub_text": "MADE LIKE A GUN",
        "motto": "Pure Motorcycling Since 1901",
        "tagline": "Classic 350 • Hunter • Himalayan",
        "shape": "card"
    },
    {
        "ticker": "DIVISLAB",
        "company": "Divi's Laboratories",
        "brand": "Divi's Labs",
        "sector": "Pharma",
        "bg_color": "#065F46",
        "accent_color": "#34D399",
        "primary_text": "Divi's",
        "sub_text": "LABORATORIES LIMITED",
        "motto": "Global API & Custom Synthesis",
        "tagline": "Quality Pharma Ingredients",
        "shape": "card"
    },
    {
        "ticker": "APOLLOHOSP",
        "company": "Apollo Hospitals",
        "brand": "Apollo 24|7",
        "sector": "Healthcare",
        "bg_color": "#005F73",
        "accent_color": "#EE9B00",
        "primary_text": "Apollo Hospitals",
        "sub_text": "TOUCHING LIVES • APOLLO 24|7",
        "motto": "Integrated Healthcare Leader",
        "tagline": "Multi-Specialty & Digital Care",
        "shape": "card"
    },
    {
        "ticker": "TATACONSUM",
        "company": "Tata Consumer Products",
        "brand": "Tata Tea",
        "sector": "Consumer Goods",
        "bg_color": "#064E3B",
        "accent_color": "#FBBF24",
        "primary_text": "TATA TEA",
        "sub_text": "JAAGO RE!",
        "motto": "Tata Consumer Products Limited",
        "tagline": "Tata Salt • Tetley • Starbucks",
        "shape": "card"
    },
    {
        "ticker": "HEROMOTOCO",
        "company": "Hero MotoCorp",
        "brand": "Splendor",
        "sector": "Automobile",
        "bg_color": "#991B1B",
        "accent_color": "#F3F4F6",
        "primary_text": "Hero Splendor",
        "sub_text": "LAGE RAHO HERO",
        "motto": "Hero MotoCorp Limited",
        "tagline": "World's #1 Two-Wheeler Maker",
        "shape": "card"
    },
    {
        "ticker": "BPCL",
        "company": "Bharat Petroleum",
        "brand": "Bharat Petroleum",
        "sector": "Energy",
        "bg_color": "#1E3A8A",
        "accent_color": "#FACC15",
        "primary_text": "BPCL",
        "sub_text": "BHARAT PETROLEUM",
        "motto": "Energising Lives",
        "tagline": "Speed • Pure For Sure • BharatGas",
        "shape": "circle"
    },
    {
        "ticker": "LTIM",
        "company": "LTIMindtree",
        "brand": "LTIMindtree",
        "sector": "IT",
        "bg_color": "#0369A1",
        "accent_color": "#38BDF8",
        "primary_text": "LTIMindtree",
        "sub_text": "GETTING TO THE FUTURE, FASTER",
        "motto": "Larsen & Toubro Group",
        "tagline": "Digital Transformation & Cloud",
        "shape": "card"
    },
    {
        "ticker": "INDUSINDBK",
        "company": "IndusInd Bank",
        "brand": "IndusInd Bank",
        "sector": "Financials",
        "bg_color": "#7F1D1D",
        "accent_color": "#FDE047",
        "primary_text": "IndusInd Bank",
        "sub_text": "YOU MAKE MORE HAPPEN",
        "motto": "IndusInd Bank Limited",
        "tagline": "Commercial Vehicle & Retail Finance",
        "shape": "card"
    },
    {
        "ticker": "SBILIFE",
        "company": "SBI Life Insurance",
        "brand": "SBI Life",
        "sector": "Financials",
        "bg_color": "#1E40AF",
        "accent_color": "#60A5FA",
        "primary_text": "SBI Life",
        "sub_text": "APNE LIYE. APNO KE LIYE.",
        "motto": "SBI Life Insurance Company",
        "tagline": "Trusted Protection & Wealth Plans",
        "shape": "card"
    },
    {
        "ticker": "HDFCLIFE",
        "company": "HDFC Life Insurance",
        "brand": "HDFC Life",
        "sector": "Financials",
        "bg_color": "#1E3A8A",
        "accent_color": "#EF4444",
        "primary_text": "HDFC Life",
        "sub_text": "SAR UTHA KE JIYO!",
        "motto": "HDFC Life Insurance Limited",
        "tagline": "Long Term Protection & Savings",
        "shape": "card"
    },
    {
        "ticker": "ZOMATO",
        "company": "Zomato",
        "brand": "Zomato",
        "sector": "Consumer Goods",
        "bg_color": "#E23744",
        "accent_color": "#FFFFFF",
        "primary_text": "zomato",
        "sub_text": "BLINKIT • HYPERPURE • LIVE",
        "motto": "Better Food For More People",
        "tagline": "Instant Delivery in 10 Minutes",
        "shape": "card"
    },
    {
        "ticker": "AMBUJACEM",
        "company": "Ambuja Cements",
        "brand": "Ambuja Cement",
        "sector": "Materials",
        "bg_color": "#005BA6",
        "accent_color": "#F59E0B",
        "primary_text": "Ambuja Cement",
        "sub_text": "GIANT COMPRESSIVE STRENGTH",
        "motto": "Adani Building Materials",
        "tagline": "India's Strongest Concrete Partner",
        "shape": "card"
    },
    {
        "ticker": "ASHOKLEY",
        "company": "Ashok Leyland",
        "brand": "Ashok Leyland",
        "sector": "Automobile",
        "bg_color": "#1E3A8A",
        "accent_color": "#EF4444",
        "primary_text": "ASHOK LEYLAND",
        "sub_text": "AAPKI JEET. HAMARI JEET.",
        "motto": "Hinduja Group Flagship",
        "tagline": "Commercial Trucks & Bada Dost",
        "shape": "card"
    },
    {
        "ticker": "DLF",
        "company": "DLF Limited",
        "brand": "DLF",
        "sector": "Real Estate",
        "bg_color": "#1C1917",
        "accent_color": "#D4AF37",
        "primary_text": "DLF",
        "sub_text": "BUILDING INDIA",
        "motto": "DLF Limited",
        "tagline": "Luxury Residential & Cybercity",
        "shape": "card"
    },
    {
        "ticker": "INDIGO",
        "company": "InterGlobe Aviation",
        "brand": "IndiGo",
        "sector": "Aviation",
        "bg_color": "#00205B",
        "accent_color": "#00A3E0",
        "primary_text": "IndiGo 6E",
        "sub_text": "ON-TIME IS A WONDERFUL THING",
        "motto": "InterGlobe Aviation Limited",
        "tagline": "India's Preferred Airline Network",
        "shape": "circle"
    },
    {
        "ticker": "MARICO",
        "company": "Marico Limited",
        "brand": "Parachute",
        "sector": "Consumer Goods",
        "bg_color": "#0284C7",
        "accent_color": "#FACC15",
        "primary_text": "Parachute",
        "sub_text": "100% PURE COCONUT OIL",
        "motto": "Marico Limited • Saffola",
        "tagline": "Nourishing Indian Households",
        "shape": "card"
    },
    {
        "ticker": "NYKAA",
        "company": "FSN E-Commerce",
        "brand": "Nykaa",
        "sector": "Consumer Goods",
        "bg_color": "#EC4899",
        "accent_color": "#FFFFFF",
        "primary_text": "NYKAA",
        "sub_text": "BEAUTY • FASHION • GLAM",
        "motto": "Your Beauty Our Passion",
        "tagline": "India's Leading Beauty Destination",
        "shape": "card"
    },
    {
        "ticker": "PAGEIND",
        "company": "Page Industries",
        "brand": "Jockey",
        "sector": "Consumer Goods",
        "bg_color": "#0F172A",
        "accent_color": "#E11D48",
        "primary_text": "JOCKEY",
        "sub_text": "COMFORT & CONFIDENCE",
        "motto": "Page Industries Limited",
        "tagline": "India's #1 Innerwear & Athleisure",
        "shape": "card"
    },
    {
        "ticker": "PAYTM",
        "company": "One97 Communications",
        "brand": "Paytm",
        "sector": "Financials",
        "bg_color": "#002970",
        "accent_color": "#00BAF2",
        "primary_text": "Paytm",
        "sub_text": "PAYTM KARO!",
        "motto": "One97 Communications",
        "tagline": "Soundbox • UPI • QR Payments",
        "shape": "card"
    },
    {
        "ticker": "SIEMENS",
        "company": "Siemens India",
        "brand": "Siemens",
        "sector": "Industrial",
        "bg_color": "#00646E",
        "accent_color": "#EB780A",
        "primary_text": "SIEMENS",
        "sub_text": "INGENUITY FOR LIFE",
        "motto": "Siemens Limited",
        "tagline": "Smart Infrastructure & Automation",
        "shape": "card"
    },
    {
        "ticker": "TRENT",
        "company": "Trent Limited",
        "brand": "Zudio",
        "sector": "Consumer Goods",
        "bg_color": "#18181B",
        "accent_color": "#F43F5E",
        "primary_text": "ZUDIO",
        "sub_text": "WESTSIDE • STAR BAZAAR",
        "motto": "A Tata Enterprise • Trent",
        "tagline": "Fast Fashion Phenomenon",
        "shape": "card"
    },
    {
        "ticker": "TVSMOTOR",
        "company": "TVS Motor Company",
        "brand": "TVS Apache",
        "sector": "Automobile",
        "bg_color": "#1E3A8A",
        "accent_color": "#DC2626",
        "primary_text": "TVS Apache",
        "sub_text": "RACING DNA UNLEASHED",
        "motto": "TVS Motor Company",
        "tagline": "Jupiter • Raider • iQube EV",
        "shape": "card"
    },
    {
        "ticker": "VBL",
        "company": "Varun Beverages",
        "brand": "Pepsi / VBL",
        "sector": "Consumer Goods",
        "bg_color": "#004B93",
        "accent_color": "#EF4444",
        "primary_text": "PEPSI / VBL",
        "sub_text": "VARUN BEVERAGES LIMITED",
        "motto": "PepsiCo India Strategic Bottler",
        "tagline": "Sting • Mountain Dew • Mirinda",
        "shape": "card"
    }
]

def generate_vibrant_card(b, size=512):
    """
    Renders a 512x512 high-resolution, graphically balanced brand card.
    Every quadrant of the canvas is richly filled so jigsaw tiles (3x3, 4x4, 5x5) have
    clear geometric borders, emblem elements, brand typography, and color contrasts.
    """
    img = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    bg_color = b.get("bg_color", "#0F2847")
    accent_color = b.get("accent_color", "#F59E0B")
    shape = b.get("shape", "card")

    # Fonts
    font_header = get_font(FONT_BOLD, 18)
    font_large = get_font(FONT_BOLD, 36)
    font_sub = get_font(FONT_SEGOE, 20)
    font_motto = get_font(FONT_BOLD, 16)
    font_tag = get_font(FONT_REGULAR, 15)

    # 1. Background Fill with subtle stylish inner canvas
    margin = 16
    card_rect = [margin, margin, size - margin, size - margin]

    if shape == "circle":
        draw.ellipse(card_rect, fill=bg_color, outline=accent_color, width=10)
        # Inner decorative ring
        draw.ellipse([margin + 20, margin + 20, size - margin - 20, size - margin - 20], outline=(255, 255, 255, 90), width=3)
    else:
        # Rounded Card
        draw.rounded_rectangle(card_rect, radius=40, fill=bg_color, outline=accent_color, width=10)
        # Inner decorative frame
        draw.rounded_rectangle([margin + 18, margin + 18, size - margin - 18, size - margin - 18], radius=28, outline=(255, 255, 255, 90), width=3)

    # 2. Sector & Top Emblem Tag
    sector_str = f"• {b.get('sector', 'NIFTY 50').upper()} •"
    draw.text((size // 2, 60), sector_str, font=font_header, fill=accent_color, anchor="mm")

    # 3. Central Brand Emblem Badge Box
    badge_w, badge_h = 420, 190
    badge_top = (size - badge_h) // 2 - 10
    badge_left = (size - badge_w) // 2
    badge_rect = [badge_left, badge_top, badge_left + badge_w, badge_top + badge_h]

    # Semi-transparent dark/light glass backing for the primary brand
    draw.rounded_rectangle(badge_rect, radius=24, fill=(0, 0, 0, 80), outline=accent_color, width=3)

    # Primary Brand Text
    primary_text = b.get("primary_text", b.get("brand", ""))
    draw.text((size // 2, badge_top + 55), primary_text, font=font_large, fill="#FFFFFF", anchor="mm")

    # Accent Divider Line
    draw.line([(size // 2 - 120, badge_top + 100), (size // 2 + 120, badge_top + 100)], fill=accent_color, width=4)

    # Sub-text / Tagline inside badge
    sub_text = b.get("sub_text", "")
    draw.text((size // 2, badge_top + 135), sub_text, font=font_sub, fill=accent_color, anchor="mm")

    # 4. Lower Corporate Motto
    motto_text = b.get("motto", b.get("company", ""))
    draw.text((size // 2, size - 105), motto_text, font=font_motto, fill="#FFFFFF", anchor="mm")

    # 5. Bottom Brand Ecosystem Tag
    tag_text = b.get("tagline", "")
    draw.text((size // 2, size - 68), tag_text, font=font_tag, fill=(255, 255, 255, 200), anchor="mm")

    return img

print(f"Generating 512x512 HD Authentic Brand Cards for all {len(NIFTY50_DEFINITIONS)} Nifty 50 companies...")

count_generated = 0
count_preserved = 0

for b in NIFTY50_DEFINITIONS:
    ticker = b["ticker"]
    static_file = os.path.join(STATIC_LOGOS_DIR, f"{ticker}.png")
    frontend_file = os.path.join(FRONTEND_LOGOS_DIR, f"{ticker}.png")

    # Preserve user's verified LIC emblem
    if ticker == "LICI" and os.path.exists(static_file):
        try:
            im = Image.open(static_file)
            if im.size == (512, 512):
                print(f"[PRESERVED AUTHENTIC] {ticker}: Kept 512x512 official LIC emblem.")
                # Ensure frontend copy matches
                im.save(frontend_file, "PNG")
                count_preserved += 1
                continue
        except Exception:
            pass

    card = generate_vibrant_card(b, size=512)
    card.save(static_file, "PNG")
    card.save(frontend_file, "PNG")
    count_generated += 1
    print(f"[OK] Generated 512x512 HD card for {ticker} ({b['brand']})")

print(f"\n[COMPLETED] Generated: {count_generated}, Preserved: {count_preserved}, Total: {len(NIFTY50_DEFINITIONS)}")
