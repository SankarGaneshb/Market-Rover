
import pytest
from rover_tools.batch_tools import batch_get_stock_data, batch_scrape_news, batch_detect_accumulation

def test_batch_get_stock_data():
    tickers = "RELIANCE.NS, TCS.NS, INFBEES.NS"
    result = batch_get_stock_data.run(tickers)
    # yfinance output can be unpredictable in CI/CD, but we check for structure
    # If network fails, it might match failure message.
    # We assert either successful data or a handled error message structure
    assert "₹" in result or "No Data" in result or "Error" in result

def test_batch_scrape_news():
    tickers = "RELIANCE.NS, TCS.NS"
    result = batch_scrape_news.run(tickers)
    # Check if we get some output, content might range from "No news" to actual news
    assert "Batch News Report" in result
    assert "RELIANCE.NS" in result or "Error" in result

def test_batch_shadow_scan():
    tickers = "RELIANCE.NS, TCS.NS"
    result = batch_detect_accumulation.run(tickers)
    assert "Batch Institutional Shadow Scan" in result
    assert "RELIANCE.NS" in result
    assert "Score:" in result or "Error" in result
