"""
Configuration settings for Market Rover system.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Root
PROJECT_ROOT = Path(__file__).parent

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# System Settings
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "5"))
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "7"))
PORTFOLIO_FILE = os.getenv("PORTFOLIO_FILE", "Portfolio.csv")

# Report Settings
REPORT_DIR = PROJECT_ROOT / os.getenv("REPORT_DIR", "reports")
CONVERT_TO_CRORES = os.getenv("CONVERT_TO_CRORES", "true").lower() == "true"

# Create reports directory if it doesn't exist
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# NSE Stock Symbol Settings
NSE_SUFFIX = ".NS"
BSE_SUFFIX = ".BO"

# Sentiment Thresholds
SENTIMENT_POSITIVE_THRESHOLD = 0.3
SENTIMENT_NEGATIVE_THRESHOLD = -0.3

# Parallel Execution Settings (Market-Rover 2.0)
MAX_PARALLEL_STOCKS = int(os.getenv("MAX_PARALLEL_STOCKS", "5"))
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))

# Web UI Settings (Market-Rover 2.0)
UPLOAD_DIR = PROJECT_ROOT / os.getenv("UPLOAD_DIR", "uploads")
WEB_PORT = int(os.getenv("WEB_PORT", "8501"))
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")

# Create upload directory if it doesn't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# News Sources
MONEYCONTROL_BASE_URL = "https://www.moneycontrol.com"

ONE_LAKH = 100_000
ONE_CRORE = 10_000_000
THOUSAND_CRORE = 10_000_000_000


def convert_to_crores(amount: float) -> str:
    """
    Convert amount to Crores format.
    
    Args:
        amount: Amount in regular units
        
    Returns:
        Formatted string in Crores
    """
    if amount >= THOUSAND_CRORE:
        return f"₹{amount / THOUSAND_CRORE:.2f} Thousand Crore"
    elif amount >= ONE_CRORE:
        return f"₹{amount / ONE_CRORE:.2f} Crore"
    elif amount >= ONE_LAKH:
        return f"₹{amount / ONE_LAKH:.2f} Lakh"
    else:
        return f"₹{amount:,.2f}"

def ensure_nse_suffix(symbol: str) -> str:
    """
    Ensure stock symbol has .NS suffix for NSE.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Symbol with .NS suffix
    """
    symbol = symbol.replace("$", "").strip().upper()
    if not symbol.endswith(NSE_SUFFIX) and not symbol.endswith(BSE_SUFFIX):
        symbol += NSE_SUFFIX
    return symbol


# Issue triage defaults
# Mapping of keyword -> list of GitHub usernames to assign
ISSUE_OWNERS = {
    'Visualizer': ['data-team'],
    'OptionChain': ['derivatives-team'],
    'Gemini': ['ml-team'],
    'Network': ['infra-team'],
    'MarketData': ['data-team'],
}

# Label rules: substring -> label
LABEL_RULES = [
    ('Visualizer', 'area:visualizer'),
    ('OptionChain', 'area:options'),
    ('nse_option', 'area:options'),
    ('Gemini', 'area:llm'),
    ('timeout', 'type:timeout'),
    ('ConnectionError', 'type:network'),
    ('ValueError', 'type:data'),
    ('KeyError', 'type:data'),
]

# Application Limits
MAX_STOCKS_PER_PORTFOLIO = int(os.getenv("MAX_STOCKS_PER_PORTFOLIO", "20"))
MAX_PORTFOLIOS_PER_USER = int(os.getenv("MAX_PORTFOLIOS_PER_USER", "3"))
