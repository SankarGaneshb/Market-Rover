
import pandas as pd
import yfinance as yf
import sys

# Re-implement the core logic briefly just to get the table numbers
ticker = "KALYANKJIL.NS"
stock = yf.Ticker(ticker)
hist = stock.history(period="max")
hist.index = pd.to_datetime(hist.index)

print(f"{'Month':<10} | {'Buy':<3} | {'Sell':<3} | {'Avg Gain':<8}")
print("-" * 35)

for month in range(1, 13):
    m_data = hist[hist.index.month == month].copy()
    if m_data.empty: continue
    
    m_data['Year'] = m_data.index.year
    m_data['Start'] = m_data.groupby('Year')['Close'].transform('first')
    m_data['Rel'] = ((m_data['Close'] - m_data['Start']) / m_data['Start']) * 100
    daily = m_data.groupby(m_data.index.day)['Rel'].mean()
    
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
                
    print(f"{month:<10} | {best_buy:<3} | {best_sell:<3} | {best_gain:.2f}%")
