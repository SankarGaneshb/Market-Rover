import sys
import os
import pandas as pd
import numpy as np
import pytest

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.derivative_analysis import DerivativeAnalyzer
from utils.mock_data import mock_generator

class TestDerivativeAnalyzer:
    def setup_method(self):
        self.analyzer = DerivativeAnalyzer()
        # Generate mock history dataframe directly
        dates = pd.date_range(end=pd.Timestamp.now(), periods=365*4, freq='D')
        prices = np.random.lognormal(mean=0, sigma=0.01, size=len(dates)).cumprod() * 100
        self.mock_hist = pd.DataFrame({'Close': prices}, index=dates)
        
    def test_seasonality_calculation(self):
        """Test if seasonality stats are calculated correctly"""
        stats = self.analyzer.calculate_seasonality(self.mock_hist)
        assert not stats.empty
        assert 'Win_Rate' in stats.columns
        assert 'Avg_Return' in stats.columns
        assert len(stats) == 12 # 12 months
        
    def test_outlier_filtering(self):
        """Test outlier removal logic"""
        # Create a series with obvious outlier
        data = pd.Series([1, 2, 3, 4, 100]) # 100 is outlier
        filtered = self.analyzer._remove_outliers(data)
        assert 100 not in filtered.values
        assert 4 in filtered.values
        
    def test_forecast_generation_2026(self):
        """Test 2026 forecast generation"""
        forecast = self.analyzer.calculate_2026_forecast(self.mock_hist)
        assert forecast is not None
        assert 'consensus_target' in forecast
        assert forecast['target_date'] == pd.Timestamp("2026-12-31")
        
    def test_sd_strategy_path_continuity(self):
        """Test if projection path includes starting point (fix verification)"""
        res = self.analyzer.calculate_sd_strategy_forecast(self.mock_hist)
        assert res is not None
        path = res['projection_path']
        assert len(path) > 0
        
        # Check first point matches last history point roughly (same date or close)
        last_hist_date = self.mock_hist.index[-1]
        if last_hist_date.tz is not None: last_hist_date = last_hist_date.tz_localize(None)
        
        first_path_point = path[0]
        assert first_path_point['date'] == last_hist_date
        
    def test_backtest_strategies(self):
        """Test strategy backtesting engine"""
        res = self.analyzer.backtest_strategies(self.mock_hist, lookback_years=2)
        assert res is not None
        assert 'winner' in res
        assert res['winner'] in ['median', 'sd']

if __name__ == "__main__":
    # Manual run if needed
    t = TestDerivativeAnalyzer()
    t.setup_method()
    t.test_seasonality_calculation()
    t.test_outlier_filtering()
    t.test_forecast_generation_2026()
    t.test_sd_strategy_path_continuity()
    print("All core regression tests passed manually.")
