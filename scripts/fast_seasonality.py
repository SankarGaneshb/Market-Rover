
import yfinance as yf
import pandas as pd
import sys
import os
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_seasonality_profile(hist):
    # Normalize
    hist['YearMonth'] = hist.index.to_period('M')
    monthly_starts = hist.groupby('YearMonth')['Close'].transform('first')
    hist['Norm_Close'] = hist['Close'] / monthly_starts
    
    # Group by Day
    daily_stats = hist.groupby(hist.index.day)['Norm_Close'].agg(['mean', 'count'])
    
    return pd.DataFrame({
        'Day': daily_stats.index,
        'Avg_Rel_Price': daily_stats['mean'],
        'Sample_Count': daily_stats['count']
    })

def run(ticker, output_path, target_month=None):
    print(f"Fetching {ticker} data directly via yfinance...")
    
    # Force full history
    stock = yf.Ticker(ticker)
    hist = stock.history(period="max")
    
    if hist.empty:
        print("No data found.")
        return
        
    print(f"Downloaded {len(hist)} records.")
    
    # Save cache just in case
    os.makedirs('data_cache', exist_ok=True)
    hist.to_csv(f"data_cache/{ticker}.csv")

    if target_month:
        hist = hist[hist.index.month == target_month]
        print(f"Filtered for Month {target_month}. Records: {len(hist)}")

    profile = analyze_seasonality_profile(hist.copy())

    print(f"\nAverage Daily Performance (Target Month: {target_month if target_month else 'All'}):")
    print(f"{'Day':<5} | {'Avg Rel Price':<15} | {'Count'}")
    print("-" * 35)
    for index, row in profile.iterrows():
        print(f"{int(row['Day']):<5} | {row['Avg_Rel_Price']:.4f}          | {int(row['Sample_Count'])}")

    # Plot
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=profile, x='Day', y='Avg_Rel_Price', marker='o')
    plt.title(f"Seasonality: {ticker} (Month: {target_month})")
    plt.savefig(output_path)
    print(f"\nSaved plot to {output_path}")

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "KALYANKJIL.NS"
    output = sys.argv[2] if len(sys.argv) > 2 else "output/fast_seasonality.png"
    t_month = int(sys.argv[3]) if len(sys.argv) > 3 else None
    run(ticker, output, t_month)
