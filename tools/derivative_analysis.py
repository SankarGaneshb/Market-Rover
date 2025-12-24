import pandas as pd
import numpy as np

class DerivativeAnalyzer:
    def __init__(self):
        pass

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
        import calendar
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
        import calendar
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

    def analyze_oi(self, option_chain_json, ltp):
        """
        Analyzes Option Chain data for PCR, Max Pain, Support/Resistance, and IV.
        """
        if not option_chain_json or 'records' not in option_chain_json:
            return None

        data = option_chain_json['records']['data']
        expiry_dates = option_chain_json['records']['expiryDates']
        current_expiry = expiry_dates[0] # Focus on near expiry

        # Filter for current expiry
        chain = [x for x in data if x['expiryDate'] == current_expiry]
        
        total_ce_oi = 0
        total_pe_oi = 0
        max_pain_strike = 0
        min_pain_value = float('inf')
        
        strikes = []
        ce_ois = []
        pe_ois = []
        
        # Find ATM IV
        min_diff = float('inf')
        atm_iv = 0
        valid_ivs = []

        # Calculate PCR and collect data for Max Pain
        for row in chain:
            strike = row['strikePrice']
            ce_oi = row.get('CE', {}).get('openInterest', 0)
            pe_oi = row.get('PE', {}).get('openInterest', 0)
            
            # IV Extraction
            ce_iv = row.get('CE', {}).get('impliedVolatility', 0)
            pe_iv = row.get('PE', {}).get('impliedVolatility', 0)
            
            if ce_iv > 0: valid_ivs.append(ce_iv)
            if pe_iv > 0: valid_ivs.append(pe_iv)
            
            # Check for ATM
            diff = abs(strike - ltp)
            if diff < min_diff:
                min_diff = diff
                # Average IV of ATM Call and Put
                if ce_iv > 0 and pe_iv > 0:
                    atm_iv = (ce_iv + pe_iv) / 2
                elif ce_iv > 0:
                    atm_iv = ce_iv
                elif pe_iv > 0:
                    atm_iv = pe_iv
            
            total_ce_oi += ce_oi
            total_pe_oi += pe_oi
            
            strikes.append(strike)
            ce_ois.append(ce_oi)
            pe_ois.append(pe_oi)

        pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0

        # Calculate Max Pain (Simplified)
        for potential_settlement in strikes:
            total_loss = 0
            for row in chain:
                strike = row['strikePrice']
                ce_oi = row.get('CE', {}).get('openInterest', 0)
                pe_oi = row.get('PE', {}).get('openInterest', 0)
                
                call_loss = max(0, potential_settlement - strike) * ce_oi
                put_loss = max(0, strike - potential_settlement) * pe_oi
                
                total_loss += (call_loss + put_loss)
            
            if total_loss < min_pain_value:
                min_pain_value = total_loss
                max_pain_strike = potential_settlement

        # Identify Support (Max Put OI) and Resistance (Max Call OI)
        max_ce_oi = max(ce_ois) if ce_ois else 0
        max_pe_oi = max(pe_ois) if pe_ois else 0
        
        resistance_strike = strikes[ce_ois.index(max_ce_oi)] if ce_ois else 0
        support_strike = strikes[pe_ois.index(max_pe_oi)] if pe_ois else 0
        
        # If ATM IV is 0 (missing), try average of all valid IVs
        if atm_iv == 0 and valid_ivs:
            atm_iv = sum(valid_ivs) / len(valid_ivs)

        return {
            "pcr": round(pcr, 2),
            "max_pain": max_pain_strike,
            "resistance_strike": resistance_strike,
            "support_strike": support_strike,
            "expiry": current_expiry,
            "strikes": strikes,
            "ce_ois": ce_ois,
            "pe_ois": pe_ois,
            "atm_iv": atm_iv
        }

    def model_scenarios(self, ltp, volatility, max_pain, expiry_date=None, iv=0):
        """
        Generates Neutral, Bull, and Bear targets.
        Prioritizes Implied Volatility (IV) if available, otherwise uses Historical Volatility.
        """
        import datetime
        
        # Determine days to expiry
        if expiry_date:
            try:
                expiry_dt = pd.to_datetime(expiry_date, format="%d-%b-%Y")
                today = pd.Timestamp.now().normalize()
                
                # Handle timezone if expiry_dt is timezone-aware
                if expiry_dt.tz is not None and today.tz is None:
                    today = today.tz_localize(expiry_dt.tz)
                elif expiry_dt.tz is None and today.tz is not None:
                    expiry_dt = expiry_dt.tz_localize(today.tz)
                
                days_remaining = (expiry_dt - today).days
                days_remaining = max(1, days_remaining)
            except:
                days_remaining = 30
        else:
            days_remaining = 30

        # Use IV if available and valid (> 1%), else fallback to Historical Volatility
        # IV is usually in %, e.g., 15.5 -> 0.155
        # nsepython usually returns IV as a number like 15.5
        
        sigma = volatility # Default to HV
        
        if iv > 0:
            # Check if IV is percentage (e.g. 20) or decimal (0.20)
            # Indian markets IV is usually 10-50. If > 1, assume percentage.
            if iv > 1:
                sigma = iv / 100.0
            else:
                sigma = iv
                
        # Calculate expected move
        sigma_period = sigma * np.sqrt(days_remaining / 365)
        expected_move = ltp * sigma_period
        
        anchor = max_pain if max_pain > 0 else ltp
        
        neutral_range = (anchor - (expected_move * 0.5), anchor + (expected_move * 0.5))
        bull_target = anchor + expected_move
        bear_target = anchor - expected_move
        
        return {
            "neutral_range": neutral_range,
            "bull_target": bull_target,
            "bear_target": bear_target,
            "expected_move": expected_move,
            "days_remaining": days_remaining,
            "used_iv": (iv > 0)
        }

    def _remove_outliers(self, series):
        """Standard IQR method for outlier removal"""
        if len(series) < 4: return series
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return series[(series >= lower_bound) & (series <= upper_bound)]

    def calculate_sd_strategy_forecast(self, history_df, target_date="2026-12-31"):
        """
        Forecasts price based on 'Strategy SD' (Volatility of Last 1 Year vs Jan).
        Logic:
        1. Calculate Monthly Returns & Remove Outliers.
        2. Stats for 'Last 1 Year' and 'Historical Jan'.
        3. If SD(Last1Y) > SD(Jan):
             If Avg(Last1Y) > Avg(Jan): Bearish -> Use Median(Jan)
             Else: Bullish -> Use Avg(Last1Y)
           Else:
             Bullish -> Use Avg(Jan)
        4. Compound this monthly rate to 2026.
        """
        if history_df.empty:
            return None

        # 1. Prepare Monthly Returns
        history_df = history_df.copy()
        if history_df.index.tz is not None:
             history_df.index = history_df.index.tz_localize(None)
             
        monthly_returns = history_df['Close'].resample('ME').last().pct_change().dropna()
        
        if monthly_returns.empty: 
            return None

        # 2. Define Groups
        # Last 1 Year
        last_1_year = monthly_returns.iloc[-12:]
        # All Januaries
        jan_returns = monthly_returns[monthly_returns.index.month == 1]
        
        # Need enough data
        if len(last_1_year) < 6 or len(jan_returns) < 2:
            return None
            
        # 3. Remove Outliers
        last_1_year_clean = self._remove_outliers(last_1_year)
        jan_clean = self._remove_outliers(jan_returns)
        
        # 4. Calculate Stats
        sd_last_1y = last_1_year_clean.std()
        avg_last_1y = last_1_year_clean.mean()
        
        sd_jan = jan_clean.std()
        avg_jan = jan_clean.mean()
        median_jan = jan_clean.median()
        
        # 5. Apply Strategy Logic
        strategy_msg = ""
        growth_rate_monthly = 0.0
        
        # Logic: If SD(L1Y) > SD(Jan)
        if sd_last_1y > sd_jan:
            if avg_last_1y > avg_jan:
                # Bearish
                growth_rate_monthly = median_jan
                strategy_msg = "Bearish (SD High & Avg High) -> Target: Median of Jan"
            else:
                # Bullish
                growth_rate_monthly = avg_last_1y
                strategy_msg = "Bullish (SD High & Avg Low) -> Target: Avg of Last 1 Year"
        else:
            # Bullish
            growth_rate_monthly = avg_jan
            strategy_msg = "Bullish (SD Low) -> Target: Avg of Jan"
            
        # 6. Project to Target Date
        current_price = history_df['Close'].iloc[-1]
        today = pd.Timestamp.now()
        target_dt = pd.Timestamp(target_date)
        
        days_to_target = (target_dt - today).days
        months_to_target = days_to_target / 30.44
        
        # Compounding: Price * (1 + monthly_rate) ^ months
        forecast_price = current_price * ((1 + growth_rate_monthly) ** months_to_target)
        
        # Annualized Growth Rate
        annualized_growth = ((1 + growth_rate_monthly) ** 12 - 1) * 100
        
        return {
            "forecast_price": forecast_price,
            "annualized_growth": annualized_growth,
            "monthly_growth": growth_rate_monthly * 100,
            "strategy_description": strategy_msg,
            "stats": {
                "sd_last_1y": sd_last_1y,
                "sd_jan": sd_jan,
                "avg_last_1y": avg_last_1y,
                "avg_jan": avg_jan,
                "median_jan": median_jan
            }
        }



    def _get_strategy_monthly_rate(self, monthly_returns, target_month_idx, strategy_type='median'):
        """
        Calculates the projected return for a specific month (1-12) based on the strategy logic.
        """
        # Data Prep
        last_1_year = monthly_returns.iloc[-12:]
        if len(last_1_year) < 6: return 0.0
        
        # Historic data for this specific month (e.g. all Februaries)
        month_hist = monthly_returns[monthly_returns.index.month == target_month_idx]
        if len(month_hist) < 2: return 0.0 # Not enough history
        
        # Remove outliers
        last_1_clean = self._remove_outliers(last_1_year)
        hist_clean = self._remove_outliers(month_hist)
        
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

    def calculate_median_strategy_forecast(self, history_df, target_date="2026-12-31", reference_date=None):
        return self._calculate_iterative_forecast(history_df, target_date, 'median', reference_date)

    def calculate_sd_strategy_forecast(self, history_df, target_date="2026-12-31", reference_date=None):
         return self._calculate_iterative_forecast(history_df, target_date, 'sd', reference_date)

    def _calculate_iterative_forecast(self, history_df, target_date, strategy_type, reference_date=None):
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
        # Ensure we start from next month if today is close to month end, or just project forward
        # Simplification: specific month ends
        
        projection_path = []
        running_price = current_price
        
        strategy_logic_log = []
        
        for d in dates:
            month_idx = d.month
            # Calculate rate for THIS specific month
            rate = self._get_strategy_monthly_rate(monthly_returns, month_idx, strategy_type)
            
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

    def backtest_strategies(self, history_df, lookback_years=3, reference_date=None):
        """
        Backtests Median vs SD strategies on recent years to pick the winner.
        Returns detailed metrics and the winning strategy ('median' or 'sd').
        """
        import numpy as np
        
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
        detailed_metrics = [] # New: Store per-year details
        
        # Decide loop range (include current year if late in year)
        start_i = 0 if current_month >= 10 else 1
        
        for i in range(start_i, lookback_years + 1):
            test_year = current_year - i
            
            # Predict FOR test_year, using data UP TO test_year-1
            cutoff_date = pd.Timestamp(f"{test_year-1}-12-31")
            # Ensure we catch data even if timestamps are slightly off
            train_df = history_df[history_df.index <= cutoff_date]
            test_df = history_df[history_df.index.year == test_year]
            
            # Relaxed constraint: Need at least ~6 months (126 trading days) of history to form a trend
            if len(train_df) < 126 or test_df.empty: 
                continue
                
            # Generate Forecasts
            res_med = self.calculate_median_strategy_forecast(train_df, target_date=f"{test_year}-12-31")
            res_sd = self.calculate_sd_strategy_forecast(train_df, target_date=f"{test_year}-12-31")
            
            if not res_med or not res_sd:
                continue
            
            # Logic: Strategy predicts an Annualized Growth Rate
            # We compare this with the Actual Annual Return of test_year
            
            # NEW LOGIC: Calculate Average Monthly Error
            def calculate_monthly_error(path, actual_df):
                if not path or actual_df.empty: return 100.0
                
                monthly_errors = []
                for point in path:
                    pred_date = point['date']
                    pred_price = point['price']
                    
                    # Find actual price nearest to this date
                    # Filter actual_df for dates up to 5 days around pred_date to match trading days
                    # Simply finding nearest index
                    nearest_idx = actual_df.index.get_indexer([pred_date], method='nearest')[0]
                    actual_date = actual_df.index[nearest_idx]
                    
                    # Ensure the actual date is within reasonable range (e.g., same month)
                    if abs((actual_date - pred_date).days) > 20:
                        continue
                        
                    actual_price = actual_df.iloc[nearest_idx]['Close']
                    monthly_errors.append(abs((pred_price - actual_price) / actual_price) * 100)
                
                return np.mean(monthly_errors) if monthly_errors else 100.0

            # Compute Avg Monthly Errors
            path_med = res_med.get('projection_path')
            path_sd = res_sd.get('projection_path')
            
            err_med = calculate_monthly_error(path_med, test_df)
            err_sd = calculate_monthly_error(path_sd, test_df)
            
            errors['median'].append(err_med)
            errors['sd'].append(err_sd)
            tested_years.append(test_year)
            
            # Record detailed metrics
            detailed_metrics.append({
                'year': test_year,
                'median_error': err_med,
                'sd_error': err_sd,
            })
            
        # Determine Winner
        avg_err_med = np.mean(errors['median']) if errors['median'] else 100
        avg_err_sd = np.mean(errors['sd']) if errors['sd'] else 100
        
        winner = "median" # Default
        if avg_err_sd < avg_err_med:
            winner = "sd"
            
        return {
            "winner": winner,
            "median_avg_error": avg_err_med,
            "sd_avg_error": avg_err_sd,
            "years_tested": tested_years,
            "detailed_metrics": detailed_metrics, # Return the details
            "confidence": "High" if len(tested_years) >= 3 else ("Average" if len(tested_years) == 2 else "Low")
        }

    def calculate_2026_forecast(self, history_df):
        """
        Generates a long-term price forecast for year-end 2026 using 3 models:
        1. Linear Regression (Trend)
        2. CAGR (Compound Annual Growth Rate)
        3. Monte Carlo Simulation (Volatility-based)
        """
        if history_df.empty:
            return None

        # Prepare data
        df = history_df.copy()
        
        # Handle timezone mismatch
        now = pd.Timestamp.now()
        if df.index.tz is not None:
            # If index is tz-aware, make 'now' tz-aware too (or convert index to naive)
            # Safest is to convert index to tz-naive
            df.index = df.index.tz_localize(None)
            
        df = df[df.index >= now - pd.DateOffset(years=5)] # Use last 5 years for trend
        if df.empty:
            df = history_df.copy() # Fallback to whatever is available

        current_price = df['Close'].iloc[-1]
        
        # Target Date: End of 2026
        target_date = pd.Timestamp("2026-12-31")
        days_to_project = (target_date - pd.Timestamp.now()).days
        years_to_project = days_to_project / 365.25

        if days_to_project <= 0:
            return None # Already past 2026

        # --- Model 1: Linear Regression (Trend) ---
        from scipy import stats
        y = df['Close'].values
        x = np.arange(len(y))
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Project forward
        # We need to add 'trading days' for the projection period
        # Approx 252 trading days per year
        future_trading_days = int(years_to_project * 252)
        total_days = len(x) + future_trading_days
        
        trend_target = slope * total_days + intercept
        
        # --- Model 2: CAGR (Historical Growth) ---
        # Calculate CAGR over available history (up to 5 years)
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        years_past = (df.index[-1] - df.index[0]).days / 365.25
        
        if years_past > 0 and start_price > 0:
            cagr = (end_price / start_price) ** (1 / years_past) - 1
        else:
            cagr = 0.10 # Default 10% assumption if history is bad
            
        # Cap CAGR for realism (e.g., -20% to +30%) to avoid explosions
        cagr = max(-0.20, min(0.30, cagr))
        
        cagr_target = current_price * ((1 + cagr) ** years_to_project)
        
        # --- Model 3: Monte Carlo (Volatility) ---
        # Simple projection: drift + volatility based
        # We'll take a slightly conservative view: drift = risk-free rate (6%) - 0.5*variance
        volatility = self.calculate_volatility(df)
        drift = 0.06 - (0.5 * volatility**2) # Assuming 6% risk-free rate (India approx)
        
        std_dev_projection = volatility * np.sqrt(years_to_project)
        
        # Expected value (50th percentile)
        monte_carlo_target = current_price * np.exp(drift * years_to_project)
        
        # Range boundaries (1 Sigma ~ 68% confidence)
        mc_high = current_price * np.exp((drift * years_to_project) + std_dev_projection)
        mc_low = current_price * np.exp((drift * years_to_project) - std_dev_projection)

        # --- Consensus ---
        # Weighted average: 40% Trend, 30% CAGR, 30% Monte Carlo
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
            "range_high": max(mc_high, trend_target, cagr_target), # Upper bound of all models
            "range_low": min(mc_low, trend_target, cagr_target),   # Lower bound
            "cagr_percent": cagr * 100,
            "volatility": volatility
        }
