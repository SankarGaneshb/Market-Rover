import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from rover_tools.analytics.seasonality_calendar import SeasonalityCalendar

@pytest.fixture
def history_data():
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    # Create cyclical data with some trend
    price = 100 + np.sin(np.arange(len(dates)) / 30) * 10 + np.random.normal(0, 1, len(dates))
    return pd.DataFrame({'Close': price}, index=dates)

@pytest.fixture
def calendar_tool(history_data):
    return SeasonalityCalendar(history_data, buy_year=2026, sell_year=2027)

def test_init(calendar_tool):
    assert calendar_tool.buy_year == 2026
    assert calendar_tool.sell_year == 2027
    assert 2026 in calendar_tool.holidays_map

def test_remove_outliers(calendar_tool):
    series = pd.Series([1, 2, 3, 4, 100]) # 100 is outlier
    clean = calendar_tool._remove_outliers(series)
    assert 100 not in clean.values
    assert 1 in clean.values

def test_get_best_days_for_month(calendar_tool):
    # Test for January (Month 1)
    b_day, s_day, gain = calendar_tool._get_best_days_for_month(1)
    
    assert 1 <= b_day <= 31
    assert 1 <= s_day <= 31
    assert b_day < s_day # Basic constraint
    assert isinstance(gain, float)

def test_calculate_annual_return(calendar_tool):
    # Buy roughly Jan 1, Sell Jan 20
    ret = calendar_tool._calculate_annual_return(1, 1, 20)
    assert isinstance(ret, float)

def test_adjust_date_for_holidays(calendar_tool):
    # Test weekend adjustment
    # Jan 3, 2026 is a Saturday
    dt, wd, adj = calendar_tool._adjust_date_for_holidays(2026, 1, 3, 'buy')
    
    # Should move forward to Monday Jan 5
    assert dt.weekday() < 5 # Not weekend
    assert dt.day >= 3
    assert adj is True

def test_generate_analysis(calendar_tool):
    df = calendar_tool.generate_analysis()
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert len(df) == 12 # 12 months
    
    required_cols = ['Month', 'Best_Buy_Day_Raw', 'Buy_Date_2026', 'Avg_Annual_Gain']
    for col in required_cols:
        assert col in df.columns

def test_plot_calendar(calendar_tool):
    df = calendar_tool.generate_analysis()
    
    with patch('rover_tools.analytics.seasonality_calendar.plt') as mock_plt:
        mock_fig = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, [MagicMock(), MagicMock()])
        
        fig = calendar_tool.plot_calendar(df)
        
        mock_plt.subplots.assert_called()
        assert fig == mock_fig

def test_muhurta_logic():
    # Test Subha Muhurta flow
    # Need to mock history data again
    history = pd.DataFrame({'Close': [100]}, index=pd.date_range('2020-01-01', periods=1))
    cal = SeasonalityCalendar(history, buy_year=2026, calendar_type="Subha Muhurta")
    
    # Mock _get_best_days logic partially via generate_analysis
    # Since we use real MUHURTA_DATA constant from module, 2026 has data
    df = cal.generate_analysis()
    
    # Check if Muhurta dates affected results
    # Jan 2026 has Muhurta dates [1, 7, ...]
    row_jan = df[df['Month_Num'] == 1].iloc[0]
    assert row_jan['Best_Buy_Day_Raw'] == 1 # First available date logic
