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

# @st.cache_data(ttl=3600*24)
def get_performance_stars(category="Nifty 50", period="1y", top_n=5):
    """
    Calculates top performing stocks (Stars) based on absolute return over a period.
    """
    # Map friendly period to yfinance period
    yf_period_map = {
        "1y": "1y",
        "3y": "5y", # Fetch 5y to be safe for 3y calc
        "5y": "5y",
        "5y+": "max" # Go max for long term
    }
    
    yf_period = yf_period_map.get(period, "1y")
    
    # Get tickers
    tickers = get_common_tickers(category=category)
    yf_tickers = [t.split(' - ')[0].strip() for t in tickers]
    
    if not yf_tickers:
        return []
        
    try:
        # Fetch data
        # Note: auto_adjust=True is default in newer versions, but we want explicit Close or Adj Close
        data = yf.download(yf_tickers, period=yf_period, interval="1wk", progress=False, group_by='ticker', auto_adjust=True)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

    results = []
    
    # Calculate target start date based on today
    today = datetime.datetime.now()
    if period == "1y":
        target_start = today - datetime.timedelta(days=365)
    elif period == "3y":
        target_start = today - datetime.timedelta(days=365*3)
    elif period == "5y":
        target_start = today - datetime.timedelta(days=365*5)
    elif period == "5y+":
        target_start = today - datetime.timedelta(days=365*10) # 10 Years
    else:
        target_start = today - datetime.timedelta(days=365)

    for ticker in yf_tickers:
        try:
            # Handle MultiIndex (Ticker, Price) or Flat
            if isinstance(data.columns, pd.MultiIndex):
                if ticker in data.columns:
                    series = data[ticker]['Close'].dropna()
                else:
                    continue
            else:
                # If flat (single ticker?)
                if ticker in data.columns: # Sometimes flat cols are just tickers if group_by='ticker' wasn't used or single ticker
                     series = data[ticker].dropna()
                elif 'Close' in data.columns:
                     series = data['Close'].dropna()
                else:
                     continue
            
            if series.empty:
                continue
                
            # Get current price
            current_price = series.iloc[-1]
            last_date = series.index[-1]
            
            # Helper to find nearest date price
            # We look for a date <= target_start
            # But since series is sorted, we can search sorted
            
            # Ensure target_start is localized if series is tz-aware
            ts = pd.Timestamp(target_start)
            if series.index.tz is not None and ts.tz is None:
                 ts = ts.tz_localize(series.index.tz)
            elif series.index.tz is None and ts.tz is not None:
                 ts = ts.tz_localize(None)


            # Find index of date closest to target_start
            # searchsorted finds the index where ts would be inserted. 
            idx = series.index.searchsorted(ts)
            
            if idx >= len(series):
                idx = len(series) - 1
            
            # This gives us a date >= target_start usually. 
            # If we want exact period return, we should try to get close.
            # Let's perform a simpler robust check:
            # If the Series starts AFTER target_start + buffer, skip (IPO usually)
            if series.index[0] > ts + pd.Timedelta(days=60):
                continue
                
            start_price = series.iloc[idx]
            start_date_actual = series.index[idx]
            
            # Simple CAGR validation check - if start date is too far off?
            # actually for "Stars" just absolute return from that approx date is fine.
            
            if start_price > 0:
                total_return = ((current_price - start_price) / start_price) * 100
                
                # Filter: Must be positive to be a "Star"
                if total_return > 0:
                     # Create label
                    results.append({
                        'ticker': ticker,
                        'total_return': total_return,
                        'current_price': current_price,
                        'start_price': start_price,
                        'years': round((last_date - start_date_actual).days / 365.25, 1)
                    })
        except Exception as e:
            continue
            
    # Sort
    df_results = pd.DataFrame(results)
    if df_results.empty:
        return []
        
    df_results = df_results.sort_values(by='total_return', ascending=False).head(top_n)
    
    final_list = []
    for _, row in df_results.iterrows():
         # Re-fetch full name string
         full_str = next((t for t in tickers if t.startswith(row['ticker'])), row['ticker'])
         final_list.append({
            'full_name': full_str,
            'ticker': row['ticker'],
            'total_return': row['total_return'],
            'label': f"{row['ticker']} (+{row['total_return']:.0f}%)"
        })
        
    return final_list
