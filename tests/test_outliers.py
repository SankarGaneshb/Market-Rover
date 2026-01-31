
import pandas as pd
import numpy as np
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from rover_tools.analytics.core import AnalyticsCore
from rover_tools.analytics.forecast import AnalyticsForecast
from rover_tools.analytics import AnalyzersUnified

def test_volatility_outliers():
    print("Testing Volatility Outlier Exclusion...")
    core = AnalyzersUnified()
    
    # Create synthetic data: Stable with ONE massive spike
    dates = pd.date_range("2024-01-01", periods=100)
    prices = [100]
    for i in range(99):
        prices.append(prices[-1] * (1 + 0.01)) # Steady 1% growth
    
    # Introduce spike
    prices[50] = prices[49] * 1.50 # 50% jump
    prices[51] = prices[50] * 1.01 # Continue norm
    
    df = pd.DataFrame({'Close': prices}, index=dates)
    
    # Calc Volatility
    vol_raw = core.calculate_volatility(df, exclude_outliers=False)
    vol_clean = core.calculate_volatility(df, exclude_outliers=True)
    
    print(f"Raw Volatility: {vol_raw:.4f}")
    print(f"Clean Volatility: {vol_clean:.4f}")
    
    assert vol_clean < vol_raw, "Clean volatility should be lower than raw"
    print("✅ Volatility Test Passed")

def test_heatmap_matrix_outliers():
    print("\nTesting Heatmap Matrix Outlier Exclusion...")
    core = AnalyzersUnified()
    
    # Create data spanning 2 years
    dates = pd.date_range("2024-01-01", "2025-12-31", freq='ME') 
    # 24 months
    # Normal returns
    prices = [100]
    for _ in range(24):
        prices.append(prices[-1] * 1.05)
        
    df = pd.DataFrame({'Close': prices[:-1]}, index=dates)
    
    # Make one month an outlier return
    # If price jumps 2x, return is 100%
    date_outlier = pd.Timestamp("2024-06-30")
    idx = df.index.get_loc(date_outlier)
    # df.iloc[idx, 0] = df.iloc[idx-1, 0] * 3.0 # Big jump
    
    # We need to manipulate prices such that monthly return is outlier.
    # resample('ME').last().pct_change()
    # Let's just mock the calculate_monthly_returns_matrix method behavior
    # Actually, let's just run it
    
    # Insert specific price path to create outlier return
    df.loc["2024-06-30", "Close"] = df.loc["2024-05-31", "Close"] * 2.0 # 100% return
    
    mat_raw = core.calculate_monthly_returns_matrix(df, exclude_outliers=False)
    mat_clean = core.calculate_monthly_returns_matrix(df, exclude_outliers=True)
    
    val_raw = mat_raw.loc[2024, 'Jun']
    val_clean = mat_clean.loc[2024, 'Jun']
    
    print(f"Raw Matrix Value (Jun 2024): {val_raw}")
    print(f"Clean Matrix Value (Jun 2024): {val_clean}")
    
    assert not pd.isna(val_raw), "Raw value should exist"
    assert pd.isna(val_clean), "Clean value should be NaN (masked)"
    print("✅ Heatmap Test Passed")

def test_forecast_trend_outliers():
    print("\nTesting Forecast Trend Outlier Exclusion...")
    fc = AnalyzersUnified()
    
    # Linear trend with one massive outlier point
    x = np.arange(100)
    y = x * 1.0 # Perfect slope 1
    
    # Outlier at index 50
    y[50] = 500 # Should pull slope up significantly
    
    dates = pd.date_range("2020-01-01", periods=100)
    df = pd.DataFrame({'Close': y}, index=dates)
    
    # We need to patch calculate_volatility because forecast calls it
    # But since we test calculate_2026_forecast which calls linregress mostly..
    
    res_raw = fc.calculate_2026_forecast(df, exclude_outliers=False)
    res_clean = fc.calculate_2026_forecast(df, exclude_outliers=True)
    
    trend_raw = res_raw['models']['Trend (Linear Reg)']
    trend_clean = res_clean['models']['Trend (Linear Reg)']
    
    print(f"Raw Trend Target: {trend_raw:.2f}")
    print(f"Clean Trend Target: {trend_clean:.2f}")
    
    # Outlier (500 vs 50) pulls slope UP.
    # Clean version should ignore it and be closer to ~100 + projection
    # Actually, calculate_2026_forecast projects to 2026.
    
    assert trend_clean < trend_raw, "Clean trend should be lower (less affected by upward outlier)"
    print("✅ Forecast Trend Test Passed")

if __name__ == "__main__":
    try:
        test_volatility_outliers()
        test_heatmap_matrix_outliers()
        test_forecast_trend_outliers()
        print("\n🎉 ALL TESTS PASSED")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
