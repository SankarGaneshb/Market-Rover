import pandas as pd
import numpy as np
from datetime import datetime
from rover_tools.analytics.seasonality_calendar import SeasonalityCalendar, MUHURTA_DATA
import calendar

def test_muhurta_calendar_logic():
    print("🚀 Starting Subha Muhurta Logic Verification...")
    
    # 1. Setup Mock History
    dates = pd.date_range(start="2020-01-01", end="2025-12-31", freq='D')
    mock_history = pd.DataFrame({
        'Close': np.linspace(100, 200, len(dates))
    }, index=dates)
    
    # 2. Test Dynamic Year Selection (Default)
    now = datetime.now()
    expected_buy_year = now.year
    expected_sell_year = now.year + 1
    
    cal = SeasonalityCalendar(mock_history, calendar_type="Subha Muhurta")
    print(f"✅ Dynamic Year Check: Buy Year={cal.buy_year} (Expected {expected_buy_year}), Sell Year={cal.sell_year} (Expected {expected_sell_year})")
    assert cal.buy_year == expected_buy_year
    assert cal.sell_year == expected_sell_year
    
    # 3. Test Subha Muhurta Entry & Exit Logic for 2026
    # For Jan 2026: Muhurta Dates = [1, 7, 8, 14, 21, 23]
    # We need to see what the best sell day would be for Jan in mock history
    # With linspace, best sell day is always the last day of the month
    
    cal_2026 = SeasonalityCalendar(mock_history, buy_year=2026, sell_year=2027, calendar_type="Subha Muhurta")
    df = cal_2026.generate_analysis()
    
    jan = df[df['Month_Num'] == 1].iloc[0]
    expected_entry = 1 # First in list
    print(f"✅ Jan 2026 Entry Check: {jan['Best_Buy_Day_Raw']} (Expected {expected_entry})")
    assert jan['Best_Buy_Day_Raw'] == expected_entry
    
    # Nov 2026: Muhurta Dates = [8, 14, 19]
    # If best sell day is normally e.g. 5th, it should pivot to end of month
    nov = df[df['Month_Num'] == 11].iloc[0]
    print(f"✅ Nov 2026 Muhurta Check: Entry={nov['Best_Buy_Day_Raw']}, Exit={nov['Best_Sell_Day_Raw']}")
    
    # 4. Test 2027 Data Presence
    cal_2027 = SeasonalityCalendar(mock_history, buy_year=2027, sell_year=2028, calendar_type="Subha Muhurta")
    df_2027 = cal_2027.generate_analysis()
    
    oct_2027 = df_2027[df_2027['Month_Num'] == 10].iloc[0]
    print(f"✅ Oct 2027 Muhurta Check: Dates={oct_2027['Muhurta_Dates']}")
    assert "29" in oct_2027['Muhurta_Dates']
    
    jan_2027 = df_2027[df_2027['Month_Num'] == 1].iloc[0]
    print(f"✅ Jan 2027 Muhurta Check: Avg Gain={jan_2027['Avg_Gain_Pct']:.2f}%")
    # In mock history (linspace 100-200), later entry means lower gain. 
    # The average should be between the gain of day 1 and day 15.
    
    print("🎉 Verification Complete!")

if __name__ == "__main__":
    test_muhurta_calendar_logic()
