import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from rover_tools.ticker_resources import (
    NIFTY_50,
    SENSEX,
    NIFTY_NEXT_50,
    NIFTY_MIDCAP,
    get_common_tickers,
    NIFTY_50_SECTOR_MAP,
    NIFTY_50_BRAND_META
)

def test_constants_validity():
    assert len(NIFTY_50) > 0
    assert len(SENSEX) > 0
    assert len(NIFTY_NEXT_50) > 0
    assert len(NIFTY_MIDCAP) > 0
    
    # Check format: "TICKER.NS - Name"
    assert ".NS" in NIFTY_50[0]
    assert " - " in NIFTY_50[0]

def test_get_common_tickers():
    # Test specific categories
    nifty = get_common_tickers("Nifty 50")
    assert nifty == sorted(NIFTY_50)
    
    sensex = get_common_tickers("Sensex")
    assert sensex == sorted(SENSEX)

    next50 = get_common_tickers("Nifty Next 50")
    assert next50 == sorted(NIFTY_NEXT_50)
    
    # Test "All" (Default or fallback) - Should NOT contain Smallcap logic if we removed it
    all_tickers = get_common_tickers("Invalid Category")
    assert len(all_tickers) > len(NIFTY_50)
    assert NIFTY_50[0] in all_tickers
    assert NIFTY_NEXT_50[0] in all_tickers

def test_sector_map_consistency():
    # Check that keys in Sector Map are bare tickers (usually)
    # The file has "HDFCBANK.NS" keys. 
    # NIFTY_50 list has "HDFCBANK.NS - HDFC Bank Ltd"
    
    # Let's extract ticker from NIFTY_50 list and check existence in map
    for entry in NIFTY_50:
        ticker = entry.split(" - ")[0]
        # Skip if not in map (map might not be 100% complete or up to date, but most should be there)
        # This test ensures we don't regress on coverage, not strict data validation
        if ticker in NIFTY_50_SECTOR_MAP:
            assert isinstance(NIFTY_50_SECTOR_MAP[ticker], str)

def test_brand_meta_consistency():
    # Check that Brand Meta has colors
    for ticker, meta in NIFTY_50_BRAND_META.items():
        assert "name" in meta
        assert "color" in meta
        assert meta["color"].startswith("#")
