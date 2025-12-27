import pandas as pd
import numpy as np
import calendar

class AnalyticsCore:
    def calculate_seasonality(self, history_df, exclude_outliers=False):
        """
        Analyzes historical monthly returns to find seasonality patterns.
        Returns a DataFrame with Month_Name, Avg_Return, Win_Rate.
        """
        if history_df.empty:
            return pd.DataFrame()
        
        # Ensure index is datetime
        history_df = history_df.copy() # Avoid SettingWithCopy
        if history_df.index.tz is not None:
             history_df.index = history_df.index.tz_localize(None)

        # Calculate monthly returns
        monthly_returns = history_df['Close'].resample('ME').last().pct_change().dropna()
        
        if monthly_returns.empty:
             return pd.DataFrame()
             
        # Group by month
        groups = monthly_returns.groupby(monthly_returns.index.month)
        
        # Prepare storage
        results = []
        
        for month, data in groups:
            # Apply outlier removal if requested
            if exclude_outliers:
                data = self._remove_outliers(data)
                
            if data.empty:
                results.append({'Month': month, 'Avg_Return': 0, 'Win_Rate': 0, 'Count': 0})
            else:
                results.append({
                    'Month': month,
                    'Avg_Return': data.mean() * 100,
                    'Win_Rate': (data > 0).sum() / len(data) * 100,
                    'Count': len(data)
                })
        
        stats = pd.DataFrame(results).set_index('Month')
        
        # Add Month_Name
        stats['Month_Name'] = [calendar.month_abbr[i] for i in stats.index]
        
        return stats

    def calculate_monthly_returns_matrix(self, history_df):
        """
        Transforms historical data into a Year x Month matrix of % returns.
        """
        if history_df.empty:
            return pd.DataFrame()

        # Ensure index is datetime
        history_df.index = pd.to_datetime(history_df.index)
        
        # Resample to monthly returns
        monthly_returns = history_df['Close'].resample('ME').last().pct_change() * 100
        
        # Create a DataFrame with Year and Month columns
        returns_df = pd.DataFrame({
            'Year': monthly_returns.index.year,
            'Month': monthly_returns.index.month,
            'Return': monthly_returns.values
        })
        
        # Pivot to create the matrix (Year x Month)
        returns_matrix = returns_df.pivot(index='Year', columns='Month', values='Return')
        
        # Rename columns to month names
        returns_matrix.columns = [calendar.month_abbr[i] for i in returns_matrix.columns]
        
        # Sort index descending (newest years on top)
        returns_matrix = returns_matrix.sort_index(ascending=False)
        
        return returns_matrix

    def calculate_volatility(self, history_df, window=252):
        """
        Calculates annualized volatility.
        Defaults to 252 days (1 year) for a stable long-term view if short-term is too noisy.
        """
        if history_df.empty:
            return 0.0
        
        daily_returns = history_df['Close'].pct_change().dropna()
        
        # If history is shorter than window, use available data
        actual_window = min(window, len(daily_returns))
        if actual_window < 2:
            return 0.0
            
        # Annualized standard deviation
        volatility = daily_returns.rolling(window=actual_window).std().iloc[-1] * np.sqrt(252)
        return volatility

    def _remove_outliers(self, series):
        """Standard IQR method for outlier removal"""
        if len(series) < 4: return series
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return series[(series >= lower_bound) & (series <= upper_bound)]
