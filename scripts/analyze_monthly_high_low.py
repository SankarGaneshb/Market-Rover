
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Ensure project root is in path to import rover_tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rover_tools.market_data import MarketDataFetcher
from utils.logger import get_logger

logger = get_logger(__name__)

def analyze_monthly_seasonality(ticker="KALYANKJIL.NS", save_path="output/kalyan_monthly_seasonality.png"):
    """
    Analyzes historical data to find the day of the month with high/low closes.
    Generates a visualization.
    """
    print(f"Fetching data for {ticker}...")
    fetcher = MarketDataFetcher()
    # Fetch full history with daily resolution
    hist = fetcher.fetch_full_history(ticker)
    
    if hist.empty:
        print("No data found.")
        return

    print(f"Data fetched: {len(hist)} records from {hist.index.min().date()} to {hist.index.max().date()}")

    # Resample to get Monthly Highs and Lows indices
    # We want the DATE of the high and low, not just the value.
    
    monthly_stats = []
    
    # Iterate by month
    # Group by Year-Month
    hist['YearMonth'] = hist.index.to_period('M')
    
    for ym, group in hist.groupby('YearMonth'):
        if len(group) < 15: # Skip incomplete months (e.g., start/end partial months)
            continue
            
        high_idx = group['Close'].idxmax()
        low_idx = group['Close'].idxmin()
        
        monthly_stats.append({
            'YearMonth': ym,
            'Month': high_idx.month,
            'Year': high_idx.year,
            'High_Date': high_idx,
            'High_Day': high_idx.day,
            'High_Price': group.loc[high_idx, 'Close'],
            'Low_Date': low_idx,
            'Low_Day': low_idx.day,
            'Low_Price': group.loc[low_idx, 'Close']
        })
        
    df_stats = pd.DataFrame(monthly_stats)
    
    if df_stats.empty:
        print("Not enough monthly data to analyze.")
        return

    print(f"Analyzed {len(df_stats)} months.")
    print("Sample Data:")
    print(df_stats[['YearMonth', 'High_Day', 'Low_Day']].head())

    # --- Visualization ---
    sns.set_theme(style="whitegrid")
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2)

    # Plot 1: Scatter of High Dates over time
    ax1 = fig.add_subplot(gs[0, 0])
    sns.scatterplot(data=df_stats, x='High_Date', y='High_Day', color='green', alpha=0.6, ax=ax1, s=50, label='Monthly High')
    ax1.set_title(f'Day of Month for Highest Close ({ticker})', fontsize=12)
    ax1.set_ylabel('Day of Month')
    ax1.set_xlabel('Year')
    ax1.set_ylim(1, 31)

    # Plot 2: Scatter of Low Dates over time
    ax2 = fig.add_subplot(gs[0, 1])
    sns.scatterplot(data=df_stats, x='Low_Date', y='Low_Day', color='red', alpha=0.6, ax=ax2, s=50, label='Monthly Low')
    ax2.set_title(f'Day of Month for Lowest Close ({ticker})', fontsize=12)
    ax2.set_ylabel('Day of Month')
    ax2.set_xlabel('Year')
    ax2.set_ylim(1, 31)

    # Plot 3: Distribution (KDE/Hist) Comparison
    ax3 = fig.add_subplot(gs[1, :])
    sns.kdeplot(data=df_stats, x='High_Day', color='green', fill=True, label='Highs', ax=ax3, bw_adjust=0.5)
    sns.kdeplot(data=df_stats, x='Low_Day', color='red', fill=True, label='Lows', ax=ax3, bw_adjust=0.5)
    ax3.set_title('Distribution of High vs Low Days in Month', fontsize=12)
    ax3.set_xlim(1, 31)
    ax3.set_xticks(range(1, 32))
    ax3.set_xlabel('Day of Month')
    ax3.legend()

    plt.suptitle(f"Monthly High/Low Closing Price Analysis: {ticker}\n(From {hist.index.min().date()} to {hist.index.max().date()})", fontsize=16)
    plt.tight_layout()
    
    # Ensure output dir
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    plt.savefig(save_path)
    print(f"\nVisualization saved to: {os.path.abspath(save_path)}")
    
    # Summary Analysis
    print("\n--- Summary Statistics ---")
    
    # Calculate Hit Rates
    high_counts = df_stats['High_Day'].value_counts()
    best_high_day = high_counts.idxmax()
    best_high_count = high_counts.max()
    best_high_pct = (best_high_count / len(df_stats)) * 100
    
    low_counts = df_stats['Low_Day'].value_counts()
    best_low_day = low_counts.idxmax()
    best_low_count = low_counts.max()
    best_low_pct = (best_low_count / len(df_stats)) * 100

    print(f"Total Months Analyzed: {len(df_stats)}")
    print(f"Best Day to Sell (High): {best_high_day}th (Hit Rate: {best_high_pct:.1f}% - {best_high_count}/{len(df_stats)} months)")
    print(f"Best Day to Buy (Low): {best_low_day}th (Hit Rate: {best_low_pct:.1f}% - {best_low_count}/{len(df_stats)} months)")
    
    print(f"Average 'High' Day: {df_stats['High_Day'].mean():.1f}")
    print(f"Average 'Low' Day: {df_stats['Low_Day'].mean():.1f}")
    
    # Segmented analysis (e.g., First Week vs Last Week)
    high_early = len(df_stats[df_stats['High_Day'] <= 10])
    high_late = len(df_stats[df_stats['High_Day'] >= 20])
    low_early = len(df_stats[df_stats['Low_Day'] <= 10])
    low_late = len(df_stats[df_stats['Low_Day'] >= 20])
    
    print("\n--- Segmentation ---")
    print(f"Highs in First 10 days: {high_early} ({high_early/len(df_stats)*100:.1f}%)")
    print(f"Highs in Last ~10 days (>=20th): {high_late} ({high_late/len(df_stats)*100:.1f}%)")
    print(f"Lows in First 10 days: {low_early} ({low_early/len(df_stats)*100:.1f}%)")
    print(f"Lows in Last ~10 days (>=20th): {low_late} ({low_late/len(df_stats)*100:.1f}%)")

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "KALYANKJIL.NS"
    output = sys.argv[2] if len(sys.argv) > 2 else "output/kalyan_monthly_seasonality.png"
    analyze_monthly_seasonality(ticker, output)
