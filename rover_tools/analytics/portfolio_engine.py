import pandas as pd
import numpy as np
import yfinance as yf
from rover_tools.ticker_resources import get_ticker_name

class AnalyticsPortfolio:
    def calculate_correlation_matrix(self, tickers, period="1y"):
        """
        Calculates the correlation matrix for a list of tickers.
        """
        if not tickers or len(tickers) < 2:
            return pd.DataFrame()
            
        try:
            # Force structure to avoid ambiguity
            # Note: auto_adjust=True is new default.
            data = yf.download(tickers, period=period, progress=False)
            
            close_data = pd.DataFrame() # Default empty

            # Case 1: MultiIndex columns (PriceType, Ticker) or (Ticker, PriceType)
            if isinstance(data.columns, pd.MultiIndex):
                # Try to find 'Close' in level 0
                if 'Close' in data.columns.get_level_values(0):
                    close_data = data.xs('Close', axis=1, level=0)
                # Try to find 'Close' in level 1
                elif 'Close' in data.columns.get_level_values(1):
                     close_data = data.xs('Close', axis=1, level=1)
                else:
                    # Fallback check for 'Adj Close'
                     if 'Adj Close' in data.columns.get_level_values(0):
                         close_data = data.xs('Adj Close', axis=1, level=0)
            else:
                # Case 2: Flat Index
                if 'Close' in data.columns:
                    close_data = data['Close']
                elif 'Adj Close' in data.columns:
                    close_data = data['Adj Close']
                else:
                    # Case 3: Maybe the columns ARE the tickers
                    # Check if at least one ticker matches
                    common_cols = set(data.columns) & set(tickers)
                    if common_cols:
                         # Assume data is already the Close/Adj Close prices
                         close_data = data

            if close_data.empty:
               return pd.DataFrame()
               
            # Handle single ticker case (Series -> DataFrame)
            if isinstance(close_data, pd.Series):
                close_data = close_data.to_frame()
                
            # 1. Calc Returns
            returns = close_data.pct_change()
            
            # 2. Drop columns that are completely empty (invalid tickers/no data)
            returns = returns.dropna(axis=1, how='all')
            
            # 3. If less than 2 valid columns remain, correlation is impossible
            if len(returns.columns) < 2:
                return pd.DataFrame()
            
            # 4. Calculate correlation (pandas ignores pairwise NaNs automatically)
            # min_periods=1 ensures even partial overlap generates a score
            corr_matrix = returns.corr(min_periods=1)
            
            return corr_matrix
        except Exception as e:
            print(f"Error calculating correlation: {e}")
            return pd.DataFrame()

    def _remove_outliers(self, returns):
        """
        Removes statistical outliers from a return series using IQR.
        """
        if returns.empty:
            return returns
            
        Q1 = returns.quantile(0.25)
        Q3 = returns.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        return returns[(returns >= lower) & (returns <= upper)]

    def calculate_volatility(self, data):
        """
        Calculates annualized volatility from price data.
        """
        if data.empty or len(data) < 2:
            return 0.0
        
        # Calculate daily returns
        if 'Close' in data.columns:
            daily_returns = data['Close'].pct_change().dropna()
        else:
             daily_returns = data.iloc[:,0].pct_change().dropna()
             
        if daily_returns.empty:
            return 0.0

        # Annualize standard deviation
        return daily_returns.std() * np.sqrt(252)

    def analyze_rebalance(self, portfolio_data, mode="safety"):
        """
        Suggests rebalancing based on selected strategy:
        - safety: Risk Parity (Inverse Volatility)
        - growth: Risk-Adjusted Return (Sharpe Ratio heuristic)
        """
        if not portfolio_data:
            return pd.DataFrame(), []
            
        df = pd.DataFrame(portfolio_data)
        if 'symbol' not in df.columns or 'value' not in df.columns:
            return pd.DataFrame(), []
            
        total_value = df['value'].sum()
        df['current_weight'] = df['value'] / total_value
        
        vols = {}
        means = {} # For growth mode
        tickers = df['symbol'].tolist()
        
        warnings = []
        
        try:
            # Force structure to avoid ambiguity (same logic as correlation)
            data = yf.download(tickers, period="1y", progress=False)
            
            # Extract Close price logic ... (reusing existing extractor logic if possible or assuming data is valid)
            hist_data = pd.DataFrame()
            if isinstance(data.columns, pd.MultiIndex):
                if 'Close' in data.columns.get_level_values(0):
                    hist_data = data.xs('Close', axis=1, level=0)
                elif 'Close' in data.columns.get_level_values(1):
                     hist_data = data.xs('Close', axis=1, level=1)
            elif 'Close' in data.columns:
                hist_data = data['Close']
            else:
                 # Check if cols are tickers
                 if set(data.columns) & set(tickers):
                     hist_data = data
            
            if hist_data.empty:
                raise Exception("No data")
                
            for ticker in tickers:
                if ticker in hist_data.columns:
                    series = hist_data[ticker].dropna()
                    if len(series) > 10:
                        # 1. Detect Anomaly First (Standardized IQR)
                        # We use the unified outlier removal from Core
                        clean_series = series.copy()
                        
                        # Calculate returns
                        daily_pct = series.pct_change().dropna()
                        
                        # Use unified method
                        # Note: _remove_outliers returns the CLEAN series.
                        clean_returns = self._remove_outliers(daily_pct)
                        
                        # Identify what was removed
                        removed_indices = daily_pct.index.difference(clean_returns.index)
                        
                        if not removed_indices.empty:
                            dropped_count = len(removed_indices)
                            warnings.append(f"⚠️ **{ticker}**: Excluded {dropped_count} outlier days (Statistical IQR) from analysis.")
                            # Filter the series based on cleaned returns
                            # We keep dates where returns exist in clean_returns (plus adjacent for price continuity, but simplify to returns based calc)
                            clean_series = series.loc[clean_returns.index]

                        # 2. Calculate Metrics on CLEAN Series
                        mini_df = clean_series.to_frame(name='Close')
                        vols[ticker] = self.calculate_volatility(mini_df)
                        
                        # Mean annual return (approx)
                        daily_ret = clean_returns.mean()
                        means[ticker] = daily_ret * 252 # Annualized
                    else:
                        vols[ticker] = 0.0
                        means[ticker] = 0.0
                        warnings.append(f"⚠️ **{ticker}**: Insufficient data (<10 days). Please check symbol.")
                else:
                    vols[ticker] = 0.0
                    means[ticker] = 0.0
                    warnings.append(f"⚠️ **{ticker}**: No data found. Is the symbol correct?")
        except Exception as e:
            print(f"Rebalance Data Error: {e}")
            for ticker in tickers:
                vols[ticker] = 0.0
                means[ticker] = 0.0
                
        df['volatility'] = df['symbol'].map(vols)
        df['return'] = df['symbol'].map(means)
        
        avg_vol = df[df['volatility'] > 0]['volatility'].mean()
        if pd.isna(avg_vol): avg_vol = 0.20
        # Replace 0 with average, then clip to minimum 1% to prevent infinite Sharpe ratios
        df['volatility'] = df['volatility'].replace(0, avg_vol).clip(lower=0.01)
        
        if mode == "growth":
            # Growth Strategy: Weight ~ Return / Volatility (Sharpe)
            # Clip negative returns to 0 for weight calculation (don't bet on losers)
            df['score'] = df['return'].apply(lambda x: max(0, x)) / df['volatility']
            
            # Handle case where all scores are 0 (all losing stocks) -> Fallback to Equal Weight
            if df['score'].sum() == 0:
                 df['target_weight'] = 1.0 / len(df)
            else:
                 df['target_weight'] = df['score'] / df['score'].sum()
        else:
            # Safety Strategy: Weight ~ 1 / Volatility
            df['inv_vol'] = 1 / df['volatility']
            df['target_weight'] = df['inv_vol'] / df['inv_vol'].sum()

        df['diff'] = df['target_weight'] - df['current_weight']
        
        def get_action_reason(row):
            diff = row['diff']
            vol = row['volatility'] * 100
            ret = row.get('return', 0) * 100
            
            if mode == "growth":
                if ret < 0:
                     metric = f"Negative Return ({ret:.1f}%)"
                else:
                     metric = f"Sharpe (Ret {ret:.1f}% / Vol {vol:.1f}%)"
            else:
                metric = f"Risk (Vol {vol:.1f}%)"

            if diff > 0.02: 
                return "Buy", f"Underweight by {diff*100:.1f}%. Favorable {metric} profile."
            if diff < -0.02: 
                return "Sell", f"Overweight by {abs(diff)*100:.1f}%. Reducing exposure due to {metric}."
            return "Hold", f"Allocation aligns with {metric}."
            
        # Apply and expand to two columns
        df[['action', 'comment']] = df.apply(
            lambda row: pd.Series(get_action_reason(row)), axis=1
        )
            
        # Add Name Column
        df['name'] = df['symbol'].apply(get_ticker_name)
            
        # Return helpful columns for display
        return df[['symbol', 'name', 'current_weight', 'target_weight', 'volatility', 'return', 'action', 'comment']], warnings

    def calculate_risk_score(self, ticker, period="1y"):
        """
        Calculates a 0-100 Risk Score based on Annualized Volatility.
        """
        try:
            # Sanitize
            ticker = ticker.replace("$", "").strip().upper()
            if not ticker.endswith(('.NS', '.BO')) and 'NIFTY' not in ticker and 'SENSEX' not in ticker and '^' not in ticker:
                 ticker += ".NS"

            hist = yf.Ticker(ticker).history(period=period)
            if hist.empty:
                return 50 
            
            # Use calculate_volatility from Core mixin
            vol = self.calculate_volatility(hist)
            score = min(100, max(0, vol * 200))
            return int(score)
        except Exception as e:
            print(f"Error calculating risk for {ticker}: {e}")
            return 50
