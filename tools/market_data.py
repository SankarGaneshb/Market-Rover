import yfinance as yf
from nsepython import nse_optionchain_scrapper
import pandas as pd
import datetime

class MarketDataFetcher:
    def __init__(self):
        pass

    def fetch_ltp(self, ticker):
        """
        Fetches the Last Traded Price (LTP) for a given ticker.
        """
        try:
            # Try yfinance first (works for both NSE/BSE if suffix is correct)
            # Assuming NSE for now, appending .NS if not present, UNLESS it's an index (starts with ^)
            if not ticker.startswith("^") and not ticker.endswith(".NS") and not ticker.endswith(".BO"):
                ticker += ".NS"
            
            stock = yf.Ticker(ticker)
            # fast_info is faster than .info
            price = stock.fast_info['last_price']
            return price
        except Exception as e:
            print(f"Error fetching LTP for {ticker}: {e}")
            return None

    def fetch_historical_data(self, ticker, period="max", interval="1mo"):
        """
        Fetches historical data for seasonality analysis.
        Default is max history with monthly interval.
        """
        try:
            if not ticker.startswith("^") and not ticker.endswith(".NS") and not ticker.endswith(".BO"):
                ticker += ".NS"
            
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, interval=interval)
            return hist
        except Exception as e:
            print(f"Error fetching history for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_full_history(self, ticker):
        """
        Fetches full historical data from IPO to date for the Monthly Returns Heatmap.
        Uses '1d' interval to ensure sufficient granularity (days) for backtesting thresholds.
        """
        return self.fetch_historical_data(ticker, period="max", interval="1d")

    def fetch_option_chain(self, ticker):
        """
        Fetches the Option Chain JSON using nsepython.
        """
        try:
            # nsepython expects symbol without .NS
            symbol = ticker.replace(".NS", "").replace(".BO", "")
            payload = nse_optionchain_scrapper(symbol)
            return payload
        except Exception as e:
            print(f"Error fetching Option Chain for {ticker}: {e}")
            return None

if __name__ == "__main__":
    # Test
    fetcher = MarketDataFetcher()
    print(f"LTP SBIN: {fetcher.fetch_ltp('SBIN')}")
    # print(f"Option Chain SBIN: {fetcher.fetch_option_chain('SBIN')}") # Verbose
