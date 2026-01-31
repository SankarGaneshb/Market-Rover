
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import sys

# NSE Holidays 2026
holidays_2026 = [
    datetime(2026, 1, 26).date(), datetime(2026, 3, 3).date(), datetime(2026, 3, 26).date(),
    datetime(2026, 3, 31).date(), datetime(2026, 4, 3).date(), datetime(2026, 4, 14).date(),
    datetime(2026, 5, 1).date(), datetime(2026, 5, 28).date(), datetime(2026, 6, 26).date(),
    datetime(2026, 8, 15).date(), datetime(2026, 9, 14).date(), datetime(2026, 10, 2).date(),
    datetime(2026, 10, 20).date(), datetime(2026, 11, 10).date(), datetime(2026, 11, 24).date(),
    datetime(2026, 12, 25).date()
]

def adjust_date(d, m, year=2026, action='buy'):
    try:
        if m == 2 and d > 28: d = 28
        dt = datetime(year, m, d).date()
        
        while dt.weekday() >= 5 or dt in holidays_2026:
            if action=='buy': dt += timedelta(days=1)
            else: dt -= timedelta(days=1)
            
        return dt.strftime('%d (%a)')
    except: return "??"

# Fetch Data
ticker = "INFY.NS"
hist = yf.Ticker(ticker).history(period="max")
hist.index = pd.to_datetime(hist.index)

print(f"{'Month':<10} | {'Raw Buy':<7} | {'Raw Sell':<8} | {'Avg Gain':<8} | {'2026 Buy':<10} | {'2026 Sell':<10}")
print("-" * 75)

for month in range(1, 13):
    m_data = hist[hist.index.month == month].copy()
    if m_data.empty: continue
    
    m_data['Year'] = m_data.index.year
    m_data['Start'] = m_data.groupby('Year')['Close'].transform('first')
    m_data['Rel'] = ((m_data['Close'] - m_data['Start']) / m_data['Start']) * 100
    daily = m_data.groupby(m_data.index.day)['Rel'].mean()
    
    # Constrained Optimization (Buy < Sell)
    best_gain = -999.0
    best_buy = 1
    best_sell = 2
    days = sorted(daily.index.unique())
    
    for i in range(len(days)):
        for j in range(i+1, len(days)):
            g = daily[days[j]] - daily[days[i]]
            if g > best_gain:
                best_gain = g
                best_buy = days[i]
                best_sell = days[j]
    
    # 2026 Dates
    buy_26 = adjust_date(best_buy, month, 2026, 'buy')
    sell_26 = adjust_date(best_sell, month, 2026, 'sell')
    
    print(f"{month:<10} | {best_buy:<7} | {best_sell:<8} | {best_gain:.2f}%     | {buy_26:<10} | {sell_26:<10}")
