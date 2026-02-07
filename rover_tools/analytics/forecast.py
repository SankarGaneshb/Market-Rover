import pandas as pd
import numpy as np
from datetime import datetime

class AnalyticsForecast:
    def model_scenarios(self, ltp, volatility, days_remaining=30):
        """
        Generates Neutral, Bull, and Bear targets.
        Uses Historical Volatility.
        """
        sigma = volatility
        
        # Calculate expected move
        sigma_period = sigma * np.sqrt(days_remaining / 365)
        expected_move = ltp * sigma_period
        
        # Use LTP as anchor
        anchor = ltp
        
        neutral_range = (anchor - (expected_move * 0.5), anchor + (expected_move * 0.5))
        bull_target = anchor + expected_move
        bear_target = anchor - expected_move
        
        return {
            "neutral_range": neutral_range,
            "bull_target": bull_target,
            "bear_target": bear_target,
            "expected_move": expected_move,
            "days_remaining": days_remaining,
            "used_iv": False
        }

    def calculate_sd_strategy_forecast(self, history_df, target_date="2026-12-31", reference_date=None, exclude_outliers=True):
         return self._calculate_iterative_forecast(history_df, target_date, 'sd', reference_date, exclude_outliers)

    def calculate_median_strategy_forecast(self, history_df, target_date="2026-12-31", reference_date=None, exclude_outliers=True):
        return self._calculate_iterative_forecast(history_df, target_date, 'median', reference_date, exclude_outliers)

    def _calculate_iterative_forecast(self, history_df, target_date, strategy_type, reference_date=None, exclude_outliers=True):
        """
        Project price month-by-month using the specified strategy logic for EACH month.
        """
        if history_df.empty: return None

        # 1. Prepare Monthly Returns
        history_df = history_df.copy()
        if history_df.index.tz is not None:
             history_df.index = history_df.index.tz_localize(None)

        # Time Travel: Filter out "future" data if reference_date is set
        if reference_date:
            ref_dt = pd.Timestamp(reference_date)
            history_df = history_df[history_df.index <= ref_dt]
            if history_df.empty: return None

        monthly_returns = history_df['Close'].resample('ME').last().pct_change().dropna()
        if monthly_returns.empty: return None

        current_price = history_df['Close'].iloc[-1]
        today = history_df.index[-1]
        target_dt = pd.Timestamp(target_date)
        
        # Generate range of month-ends from now to target
        dates = pd.date_range(start=today, end=target_dt, freq='ME')
        
        projection_path = [{'date': today, 'price': current_price}]
        running_price = current_price
        
        for d in dates:
            month_idx = d.month
            # Calculate rate for THIS specific month
            rate = self._get_strategy_monthly_rate(monthly_returns, month_idx, strategy_type, exclude_outliers)
            
            # Apply rate
            running_price = running_price * (1 + rate)
            projection_path.append({'date': d, 'price': running_price})
            
        if not projection_path: return None
        
        final_price = projection_path[-1]['price']
        
        # Calculate resulting CAGR
        days_total = (target_dt - today).days
        if days_total > 0:
            annualized_growth = ((final_price / current_price) ** (365 / days_total) - 1) * 100
        else:
            annualized_growth = 0
            
        strategy_msg = f"Iterative {strategy_type.title()} Strategy (Month-by-Month)"

        return {
            "forecast_price": final_price,
            "annualized_growth": annualized_growth,
            "monthly_growth": None, 
            "strategy_description": strategy_msg,
            "projection_path": projection_path
        }

    def _get_strategy_monthly_rate(self, monthly_returns, target_month_idx, strategy_type='median', exclude_outliers=True):
        """
        Calculates the projected return for a specific month (1-12) based on the strategy logic.
        """
        # Data Prep
        last_1_year = monthly_returns.iloc[-12:]
        if len(last_1_year) < 6: return 0.0
        
        # Historic data for this specific month (e.g. all Februaries)
        month_hist = monthly_returns[monthly_returns.index.month == target_month_idx]
        if len(month_hist) < 2: return 0.0 # Not enough history
        
        # Remove outliers (relies on self._remove_outliers from Core)
        if exclude_outliers:
            last_1_clean = self._remove_outliers(last_1_year)
            hist_clean = self._remove_outliers(month_hist)
        else:
            last_1_clean = last_1_year
            hist_clean = month_hist
        
        if len(last_1_clean) == 0 or len(hist_clean) == 0: return 0.0

        # Stats
        mu_l1 = last_1_clean.mean()
        mu_hist = hist_clean.mean()
        
        rate = 0.0
        
        if strategy_type == 'median':
            med_l1 = last_1_clean.median()
            med_hist = hist_clean.median()
            
            # Logic: If Median(L1) > Median(Hist)
            if med_l1 > med_hist:
                if mu_l1 > mu_hist:
                     # Bearish -> Median Hist
                     rate = med_hist
                else:
                     # Bullish -> Avg L1
                     rate = mu_l1
            else:
                # Bullish -> Avg Hist
                rate = mu_hist
                
        elif strategy_type == 'sd':
            sd_l1 = last_1_clean.std()
            sd_hist = hist_clean.std()
            
            # Logic: If SD(L1) > SD(Hist)
            if sd_l1 > sd_hist:
                if mu_l1 > mu_hist:
                    # Bearish -> Median Hist
                    rate = hist_clean.median()
                else:
                    # Bullish -> Avg L1
                    rate = mu_l1
            else:
                 # Bullish -> Avg Hist
                 rate = mu_hist
                 
        return rate

    def backtest_strategies(self, history_df, lookback_years=3, reference_date=None, exclude_outliers=True):
        """
        Backtests Median vs SD strategies on recent years to pick the winner.
        """
        history_df = history_df.copy()
        if history_df.index.tz is not None:
             history_df.index = history_df.index.tz_localize(None)
             
        # Time Travel Logic
        if reference_date:
            ref_dt = pd.Timestamp(reference_date)
            history_df = history_df[history_df.index <= ref_dt]
            if history_df.empty:
                return {
                     "winner": "median",
                     "median_avg_error": 0, "sd_avg_error": 0,
                     "confidence": "Insufficient", "years_tested": []
                }

        # Determine current state
        last_date = history_df.index[-1]
        current_year = last_date.year
        current_month = last_date.month
        
        errors = {'median': [], 'sd': []}
        tested_years = []
        detailed_metrics = [] 
        
        start_i = 0 if current_month >= 10 else 1
        
        for i in range(start_i, lookback_years + 1):
            test_year = current_year - i
            
            cutoff_date = pd.Timestamp(f"{test_year-1}-12-31")
            train_df = history_df[history_df.index <= cutoff_date]
            test_df = history_df[history_df.index.year == test_year]
            
            if len(train_df) < 126 or test_df.empty: 
                continue
                
            res_med = self.calculate_median_strategy_forecast(train_df, target_date=f"{test_year}-12-31", exclude_outliers=exclude_outliers)
            res_sd = self.calculate_sd_strategy_forecast(train_df, target_date=f"{test_year}-12-31", exclude_outliers=exclude_outliers)
            
            if not res_med or not res_sd:
                continue
            
            def calculate_monthly_error(path, actual_df):
                if not path or actual_df.empty: return 100.0
                monthly_errors = []
                for point in path:
                    pred_date = point['date']
                    pred_price = point['price']
                    
                    nearest_idx = actual_df.index.get_indexer([pred_date], method='nearest')[0]
                    actual_date = actual_df.index[nearest_idx]
                    
                    if abs((actual_date - pred_date).days) > 20: continue
                        
                    actual_price = actual_df.iloc[nearest_idx]['Close']
                    monthly_errors.append(abs((pred_price - actual_price) / actual_price) * 100)
                
                return np.mean(monthly_errors) if monthly_errors else 100.0

            path_med = res_med.get('projection_path')
            path_sd = res_sd.get('projection_path')
            
            err_med = calculate_monthly_error(path_med, test_df)
            err_sd = calculate_monthly_error(path_sd, test_df)
            
            errors['median'].append(err_med)
            errors['sd'].append(err_sd)
            tested_years.append(test_year)
            
            detailed_metrics.append({
                'year': test_year,
                'median_error': err_med,
                'sd_error': err_sd,
            })
            
        avg_err_med = np.mean(errors['median']) if errors['median'] else 100
        avg_err_sd = np.mean(errors['sd']) if errors['sd'] else 100
        
        winner = "median"
        if avg_err_sd < avg_err_med:
            winner = "sd"
            
        return {
            "winner": winner,
            "median_avg_error": avg_err_med,
            "sd_avg_error": avg_err_sd,
            "years_tested": tested_years,
            "detailed_metrics": detailed_metrics,
            "confidence": "High" if len(tested_years) >= 3 else ("Average" if len(tested_years) == 2 else "Low")
        }

    def calculate_2026_forecast(self, history_df, exclude_outliers=False):
        """
        Generates a long-term price forecast for year-end 2026.
        """
        if history_df.empty: return None

        df = history_df.copy()
        now = pd.Timestamp.now()
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
            
        df = df[df.index >= now - pd.DateOffset(years=5)]
        if df.empty: df = history_df.copy()

        current_price = df['Close'].iloc[-1]
        target_date = pd.Timestamp("2026-12-31")
        days_to_project = (target_date - pd.Timestamp.now()).days
        years_to_project = days_to_project / 365.25

        if days_to_project <= 0: return None
        
        # Prepare data for regression (Outlier Exclusion logic)
        y = df['Close'].values
        x = np.arange(len(y))
        
        if exclude_outliers:
            # We calculate returns to identify extreme VOLATILITY events, not high prices (high prices are real)
            # But for trend, we might want to exclude "flash crash" prices.
            
            # Simple approach: Identify outliers in daily returns
            daily_returns = df['Close'].pct_change()
            
            # Reuse core logic slightly modified to return mask
            # Assuming self._remove_outliers returns clean series.
            # We need the INDEX of clean returns.
            if len(daily_returns) > 4:
                Q1 = daily_returns.quantile(0.25)
                Q3 = daily_returns.quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                
                # Keep days where returns are "Normal"
                # Note: This removes the rows from df where the *return form previous day* was anomalous
                mask = (daily_returns >= lower) & (daily_returns <= upper)
                
                # We align x and y to this mask
                # Shift mask to align with 'Close' (return for today depends on today close)
                # But pct_change aligns with the "end" date.
                # So if mask[i] is True, means price[i] was a normal move from price[i-1]
                
                # Filter x and y
                # First element of returns is NaN, usually, so mask length is len(df)
                valid_indices = mask[mask].index
                
                # We need integer indices for x
                # Let's just filter the regression arrays directly
                valid_mask = mask.fillna(True).values # Keep NaN (first day)
                
                x = x[valid_mask]
                y = y[valid_mask]

        from scipy import stats
        # If too much data removed (unlikely), fallback
        if len(y) < 2:
             y = df['Close'].values
             x = np.arange(len(y))

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        future_trading_days = int(years_to_project * 252)
        total_days = len(df) + future_trading_days # Use original length for projection base
        trend_target = slope * total_days + intercept
        
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        years_past = (df.index[-1] - df.index[0]).days / 365.25
        
        cagr = (end_price / start_price) ** (1 / years_past) - 1 if (years_past > 0 and start_price > 0) else 0.10
        cagr = max(-0.20, min(0.30, cagr))
        
        cagr_target = current_price * ((1 + cagr) ** years_to_project)
        
        cagr_target = current_price * ((1 + cagr) ** years_to_project)
        
        volatility = self.calculate_volatility(df, exclude_outliers=exclude_outliers)
        drift = 0.06 - (0.5 * volatility**2)
        
        std_dev_projection = volatility * np.sqrt(years_to_project)
        monte_carlo_target = current_price * np.exp(drift * years_to_project)
        
        mc_high = current_price * np.exp((drift * years_to_project) + std_dev_projection)
        mc_low = current_price * np.exp((drift * years_to_project) - std_dev_projection)

        consensus_target = (trend_target * 0.4) + (cagr_target * 0.3) + (monte_carlo_target * 0.3)

        return {
            "target_date": target_date,
            "current_price": current_price,
            "models": {
                "Trend (Linear Reg)": trend_target,
                "CAGR (Growth)": cagr_target,
                "Monte Carlo (Base)": monte_carlo_target
            },
            "consensus_target": consensus_target,
            "range_high": max(mc_high, trend_target, cagr_target),
            "range_low": min(mc_low, trend_target, cagr_target),
            "cagr_percent": cagr * 100,
            "volatility": volatility
        }
