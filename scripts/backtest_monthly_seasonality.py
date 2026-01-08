
import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rover_tools.market_data import MarketDataFetcher
from utils.logger import get_logger

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

def analyze_seasonality_profile(hist):
    """
    Calculates the average 'path' of the stock within a month.
    Returns: DataFrame with Day (1-31) and Avg_Rel_Price
    """
    # 1. Normalize each month: Close / Month_Start_Close
    # Ensure index is Period for grouping
    hist['YearMonth'] = hist.index.to_period('M')
    
    # Get the opening price (or first close) for each month
    monthly_starts = hist.groupby('YearMonth')['Close'].transform('first')
    hist['Norm_Close'] = hist['Close'] / monthly_starts
    
    # 2. Group by Day of Month
    daily_stats = hist.groupby(hist.index.day)['Norm_Close'].agg(['mean', 'count'])
    
    # Calculate "Win Rate" (Probability Close > Open for that specific day relative to month start isn't quite right)
    # Let's simple show Average Relative Price.
    
    profile_df = pd.DataFrame({
        'Day': daily_stats.index,
        'Avg_Rel_Price': daily_stats['mean'],
        'Sample_Count': daily_stats['count']
    })
    
    return profile_df

def optimize_and_run(ticker, output_path, target_month=None):
    print(f"--- Analysis for {ticker} ---")
    
    # --- 1. Caching Layer ---
    os.makedirs('data_cache', exist_ok=True)
    cache_file = f"data_cache/{ticker}.csv"
    
    hist = pd.DataFrame()
    
    if os.path.exists(cache_file):
        print(f"Loading data from local cache: {cache_file} ...")
        hist = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    else:
        print(f"Fetching data from API (this takes time)...")
        try:
            fetcher = MarketDataFetcher()
            hist = fetcher.fetch_full_history(ticker)
            if not hist.empty:
                hist.to_csv(cache_file)
                print("Data saved to cache.")
        except Exception as e:
            print(f"Error fetching data: {e}")
            return
        
    if hist.empty:
        print("No data available.")
        return

    # --- 2. Filter for Month ---
    if target_month:
        month_name = datetime(2000, target_month, 1).strftime('%B')
        print(f"Filtering Data: Using only historic '{month_name}' data.")
        hist = hist[hist.index.month == target_month]
        
        if hist.empty:
            print(f"No history found for month {target_month}.")
            return
    else:
        month_name = "All Months"

    print(f"Analyzing {len(hist)} trading days ({len(hist.index.to_period('M').unique())} years of data).")

    # --- 3. Profile Analysis (Instant) ---
    profile = analyze_seasonality_profile(hist.copy())
    
    # Identify Best Days
    best_buy_day = profile['Avg_Rel_Price'].idxmin()
    best_sell_day = profile['Avg_Rel_Price'].idxmax()
    
    # Smart Sell: Find peak AFTER buy day if possible
    future_profile = profile[profile.index > best_buy_day]
    if not future_profile.empty:
        best_sell_day = future_profile['Avg_Rel_Price'].idxmax()
    
    # --- 4. Print Table (User Requested) ---
    print(f"\nAverage Daily Performance for {month_name}:")
    print(f"{'Day':<5} | {'Avg Norm Price':<15} | {'Trend'}")
    print("-" * 35)
    for index, row in profile.iterrows():
        day = int(row['Day'])
        val = row['Avg_Rel_Price']
        trend = "LOW" if day == best_buy_day else "HIGH" if day == best_sell_day else ""
        print(f"{day:<5} | {val:.4f}          | {trend}")
    
    print("-" * 35)
    print(f"Best Buy: Day {best_buy_day} (Avg Price Low)")
    print(f"Best Sell: Day {best_sell_day} (Avg Price peak after buy)")

    # --- 5. Visualization ---
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6))
    
    sns.lineplot(data=profile, x='Day', y='Avg_Rel_Price', marker='o', color='purple', linewidth=2, ax=ax)
    
    ax.set_title(f"Seasonality: {ticker} in {month_name}", fontsize=16)
    ax.set_ylabel("Avg Price (Relative to Month Start)")
    ax.set_xlabel("Day of Month")
    ax.set_xticks(range(1, 32))
    
    # Highlight
    ax.axvline(best_buy_day, color='green', linestyle='--', label=f'Best Buy: {best_buy_day}')
    ax.axvline(best_sell_day, color='red', linestyle='--', label=f'Best Sell: {best_sell_day}')
    ax.legend()
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    print(f"\nVisualization saved to {output_path}")

if __name__ == "__main__":
    # Usage: python script.py TICKER OUTPUT [MONTH_INT]
    ticker = sys.argv[1] if len(sys.argv) > 1 else "KALYANKJIL.NS"
    output = sys.argv[2] if len(sys.argv) > 2 else "output/seasonality.png"
    
    target_month = None
    if len(sys.argv) > 3:
        try:
            target_month = int(sys.argv[3])
        except ValueError:
            pass
            
    optimize_and_run(ticker, output, target_month)
