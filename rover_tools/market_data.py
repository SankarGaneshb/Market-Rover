import yfinance as yf
from nsepython import nse_optionchain_scrapper
import pandas as pd
import datetime
from utils.logger import get_logger
from utils.metrics import track_error_detail
from utils.retry import retry_operation

logger = get_logger(__name__)

class MarketDataFetcher:
    def __init__(self):
        pass

    @retry_operation(max_retries=2, delay=1.0)
    def _fetch_yf_price_unsafe(self, ticker):
        """Internal helper with retry logic for fetching price."""
        stock = yf.Ticker(ticker)
        # fast_info access can fail network-wise
        price = stock.fast_info['last_price']
        if price is None:
             raise ValueError(f"Received None price for {ticker}")
        return price

    @retry_operation(max_retries=2, delay=1.0)
    def _fetch_yf_history_unsafe(self, ticker, period, interval):
        """Internal helper with retry logic for fetching history."""
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        if hist.empty:
             raise ValueError(f"Received empty history for {ticker}")
        return hist

    def fetch_ltp(self, ticker):
        """
        Fetches the Last Traded Price (LTP) with NSE -> BSE fallback.
        """
        # Sanitize input
        ticker = ticker.replace("$", "").strip().upper()
        
        # Determine strict NSE and BSE variants
        base_ticker = ticker.replace(".NS", "").replace(".BO", "")
        
        # If it's an index (starts with ^), try direct fetch
        if ticker.startswith("^"):
            try:
                return self._fetch_yf_price_unsafe(ticker)
            except Exception as e:
                logger.error(f"Failed to fetch index {ticker}: {e}")
                return None

        # Fallback Strategy for Stocks
        targets = [f"{base_ticker}.NS", f"{base_ticker}.BO"]
        if ticker.endswith(".BO"): # If user specifically asked for BSE, prioritize it
             targets = [f"{base_ticker}.BO", f"{base_ticker}.NS"]

        for t in targets:
            try:
                return self._fetch_yf_price_unsafe(t)
            except Exception:
                logger.warning(f"Fetch failed for {t}, attempting fallback...")
                continue
                
        logger.error(f"All attempts failed for {base_ticker} (NSE/BSE)")
        if targets: # Log error detail for the primary target
            track_error_detail("FetchError", "All sources failed", context={"ticker": base_ticker})
        return None

    def fetch_historical_data(self, ticker, period="max", interval="1mo"):
        """
        Fetches historical data with NSE -> BSE fallback.
        """
        # Sanitize input
        ticker = ticker.replace("$", "").strip().upper()
        base_ticker = ticker.replace(".NS", "").replace(".BO", "")
        
        # Index handling
        if ticker.startswith("^"):
            try:
                return self._fetch_yf_history_unsafe(ticker, period, interval)
            except Exception:
                return pd.DataFrame()

        targets = [f"{base_ticker}.NS", f"{base_ticker}.BO"]
        if ticker.endswith(".BO"):
             targets = [f"{base_ticker}.BO", f"{base_ticker}.NS"]

        for t in targets:
            try:
                return self._fetch_yf_history_unsafe(t, period, interval)
            except Exception:
                logger.warning(f"History fetch failed for {t}, attempting fallback...")
                continue
        
        logger.error(f"All history attempts failed for {base_ticker}")
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
            logger.error(f"Error fetching Option Chain for {ticker}: {e}")
            try:
                track_error_detail(type(e).__name__, str(e), context={"function": "fetch_option_chain", "ticker": ticker})
            except Exception:
                pass
            return None

if __name__ == "__main__":
    # Test
    fetcher = MarketDataFetcher()
    from utils.logger import logger
    logger.info("LTP SBIN: %s", fetcher.fetch_ltp('SBIN'))
    # print(f"Option Chain SBIN: {fetcher.fetch_option_chain('SBIN')}") # Verbose
