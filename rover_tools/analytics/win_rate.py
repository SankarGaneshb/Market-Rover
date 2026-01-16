import yfinance as yf
import pandas as pd
import streamlit as st
import datetime
from rover_tools.ticker_resources import get_common_tickers

# @st.cache_data(ttl=3600*24) # Cache for 24 hours as historical data for past years won't change
def calculate_seasonality_win_rate(category="Nifty 50", target_month=None, period="10y", top_n=5, exclude_outliers=False):
    """
    Calculates the historical win rate for the specified month and category.
    
    Args:
        category (str): Index category to fetch tickers for (e.g., "Nifty 50", "Midcap").
        target_month (int): Month to analyze (1-12). Defaults to current month.
        period (str): Historical period to fetch.
        top_n (int): Number of top stocks to return.
        exclude_outliers (bool): If True, removes IQR outliers from calculations.
        
    Returns:
        list: Top N tickers with their stats dictionary.
    """
    if target_month is None:
        target_month = datetime.datetime.now().month
        
    # Get tickers based on category
    tickers = get_common_tickers(category=category)
    
    # Clean tickers for yfinance (ensure .NS)
    # Tickers are in format "SYMBOL.NS - Name"
    yf_tickers = [t.split(' - ')[0].strip() for t in tickers]
    
    # Download data in batch
    # We need monthly data. 
    try:
        data = yf.download(yf_tickers, period=period, interval="1mo", progress=False)['Close']
    except Exception as e:
        st.error(f"Failed to fetch seasonality data: {e}")
        return []
    
    results = []
    
    # Analyze each ticker
    for ticker in yf_tickers:
        if ticker not in data.columns:
            continue
            
        series = data[ticker].dropna()
        if series.empty:
            continue
            
        # Resample is likely not needed if interval is 1mo, but ensuring we have datetime index
        # Filter for target month
        # Note: series index is Timestamp
        
        # We need monthly returns. 
        # Calculate pct_change first to get returns
        monthly_returns = series.pct_change()
        
        # Filter for the specific month
        # We only look at completed months or current month if available? 
        # Usually seasonality looks at historicals.
        season_data = monthly_returns[monthly_returns.index.month == target_month]
        
        # Outlier Exclusion Logic
        if exclude_outliers and len(season_data) >= 4:
            Q1 = season_data.quantile(0.25)
            Q3 = season_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            season_data = season_data[(season_data >= lower_bound) & (season_data <= upper_bound)]
        
        if len(season_data) < 2: # Need at least some data points
            continue
            
        positive_years = season_data[season_data > 0].count()
        total_years = season_data.count()
        
        win_rate = (positive_years / total_years) * 100
        avg_return = season_data.mean() * 100
        
        results.append({
            'ticker': ticker,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'years': total_years
        })
        
    # Sort by Win Rate then Avg Return
    df_results = pd.DataFrame(results)
    if df_results.empty:
        return []
        
    df_results = df_results.sort_values(by=['win_rate', 'avg_return'], ascending=[False, False])
    
    top_stocks = df_results.head(top_n)
    
    # Format for return
    # We want to return a list of tickers, maybe with a formatted string for the UI?
    # Or just the list of tickers to feed into the dropdown logic.
    
    final_list = []
    for _, row in top_stocks.iterrows():
        # Find full name if possible
        full_str = next((t for t in tickers if row['ticker'] in t), row['ticker'])
        final_list.append({
            'full_name': full_str,
            'ticker': row['ticker'],
            'win_rate': row['win_rate'],
            'avg_return': row['avg_return']
        })
        
    return final_list
