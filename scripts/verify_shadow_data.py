
import logging
from nsepython import *
import yfinance as yf
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataVerifier")

def verify_block_deals():
    logger.info("--- Verifying Block Deals ---")
    try:
        # NSEPython wrapper for block deals
        # Note: 'block_deals' might not be a direct function, usually it's under 'nse_block_deal' or similar
        # Let's try fetching from nse India website directly if wrapper fails
        # Trying a known nsepython function or simulating standard fetch
        
        # Method A: Direct Fno logic or scraping
        # nsepython doesn't have a stable 'block_deals' function in all versions, 
        # but let's try 'nse_get_fno_lot_sizes' to ensure library works first
        print(f"Library Check: {nse_get_fno_lot_sizes('SBIN')}")
        
    except Exception as e:
        logger.error(f"Block Deal Check Failed: {e}")

def verify_fii_data():
    logger.info("--- Verifying FII/DII Data ---")
    try:
        # FII DII trading activity
        fii_dii = nse_fii_dii()
        print("FII/DII Stats Fetched:")
        print(fii_dii)
        
        # FII Derivatives (Participant wise)
        # This is harder, usually requires downloading a CSV from NSE report
        # We will check if we can access the URL or if a wrapper exists
        logger.info("FII Derivative Data usually requires CSV parsing from NSE website.")
        
    except Exception as e:
        logger.error(f"FII Data Check Failed: {e}")

def verify_sectors():
    logger.info("--- Verifying Sector Indices (yfinance) ---")
    sectors = ["^NSEBANK", "^CNXAUTO", "^CNXIT", "^CNXMETAL", "^CNXPHARMA"]
    try:
        data = yf.download(sectors, period="5d", progress=False)
        if not data.empty:
            print(f"Sector Data Fetched for {len(sectors)} indices.")
            print(data['Close'].tail(2))
        else:
            logger.error("Sector Data Empty")
    except Exception as e:
        logger.error(f"Sector Check Failed: {e}")

def main():
    verify_block_deals()
    verify_fii_data()
    verify_sectors()

if __name__ == "__main__":
    main()
