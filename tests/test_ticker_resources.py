import pytest
from rover_tools import ticker_resources

def test_ticker_constants_exist():
    assert isinstance(ticker_resources.NIFTY_50, list)
    assert len(ticker_resources.NIFTY_50) > 0
    
    assert isinstance(ticker_resources.SENSEX, list)
    assert isinstance(ticker_resources.BANK_NIFTY, list)
    assert isinstance(ticker_resources.POPULAR_OTHERS, list)
    assert isinstance(ticker_resources.NIFTY_MIDCAP, list)
    assert isinstance(ticker_resources.NIFTY_NEXT_50, list)

def test_sector_maps_exist():
    assert isinstance(ticker_resources.NIFTY_50_SECTOR_MAP, dict)
    assert isinstance(ticker_resources.NIFTY_NEXT_50_SECTOR_MAP, dict)
    assert isinstance(ticker_resources.NIFTY_MIDCAP_SECTOR_MAP, dict)
    assert "RELIANCE.NS" in ticker_resources.NIFTY_50_SECTOR_MAP

def test_asset_proxies_exist():
    assert isinstance(ticker_resources.ASSET_PROXIES, dict)
    assert "Gold" in ticker_resources.ASSET_PROXIES

def test_brand_meta_exists():
    assert isinstance(ticker_resources.NIFTY_50_BRAND_META, dict)
    assert "RELIANCE.NS" in ticker_resources.NIFTY_50_BRAND_META
    assert "color" in ticker_resources.NIFTY_50_BRAND_META["RELIANCE.NS"]

def test_get_common_tickers():
    # Test all categories
    nifty = ticker_resources.get_common_tickers("Nifty 50")
    assert ticker_resources.NIFTY_50[0] in nifty
    
    sensex = ticker_resources.get_common_tickers("Sensex")
    assert len(sensex) > 0
    
    midcap = ticker_resources.get_common_tickers("Midcap")
    assert len(midcap) > 0
    
    next50 = ticker_resources.get_common_tickers("Nifty Next 50")
    assert len(next50) > 0
    
    all_tickers = ticker_resources.get_common_tickers("All")
    assert len(all_tickers) > len(nifty)

def test_get_ticker_name():
    # Test exact match
    name = ticker_resources.get_ticker_name("RELIANCE.NS")
    assert "Reliance" in name
    
    # Test without .NS suffix handling
    name_ns = ticker_resources.get_ticker_name("RELIANCE")
    assert "Reliance" in name_ns
    
    # Test list lookup
    name_tcs = ticker_resources.get_ticker_name("TCS.NS")
    assert "Tata Consultancy" in name_tcs
    
    # Test fallback
    unknown = ticker_resources.get_ticker_name("UNKNOWN123")
    assert unknown == "UNKNOWN123"
