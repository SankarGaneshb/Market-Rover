
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from rover_tools.analytics.win_rate import get_performance_stars
from unittest.mock import MagicMock, patch
import pandas as pd

def run_debug():
    print("Starting debug run...")
    
    # Create mock data
    dates = pd.date_range(start="2020-01-01", end="2025-01-01", freq="ME")
    data_a = pd.Series(range(len(dates)), index=dates, name="STOCK_A.NS") * 10 
    mock_yf_data = pd.DataFrame({"STOCK_A.NS": data_a})
    
    with patch("rover_tools.analytics.win_rate.yf.download") as mock_download, \
         patch("rover_tools.analytics.win_rate.get_common_tickers") as mock_get_tickers:
        
        mock_get_tickers.return_value = ["STOCK_A.NS"]
        
        # Mocking the MultiIndex return
        mock_df_full = pd.concat([mock_yf_data], axis=1, keys=['Close'])
        mock_download.return_value = mock_df_full
        
        print("Calling get_performance_stars...")
        stars = get_performance_stars(category="Test", period="1y", top_n=5)
        print(f"Result stars: {stars}")

if __name__ == "__main__":
    run_debug()
