import pandas as pd
import numpy as np
from utils.logger import get_logger
from utils.metrics import track_error_detail

logger = get_logger(__name__)

class DerivativeAnalyzer:
    def __init__(self):
        pass

    def calculate_seasonality(self, history_df):
        """
        Analyzes historical monthly returns to find seasonality patterns.
        """
        if history_df.empty:
            return {}
        
        # Ensure index is datetime
        history_df.index = pd.to_datetime(history_df.index)
        
        # Calculate monthly returns
        monthly_returns = history_df['Close'].pct_change().dropna()
        
        # Group by month
        monthly_stats = monthly_returns.groupby(monthly_returns.index.month).agg(['mean', 'std', 'count'])
        
        # Map month numbers to names
        import calendar
        monthly_stats.index = [calendar.month_abbr[i] for i in monthly_stats.index]
        
        return monthly_stats.to_dict('index')

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
        try:
            if not option_chain_json or 'records' not in option_chain_json:
                return None

            data = option_chain_json['records']['data']
            expiry_dates = option_chain_json['records'].get('expiryDates', [])
            if not expiry_dates:
                return None
            current_expiry = expiry_dates[0]  # Focus on near expiry

            # Filter for current expiry
            chain = [x for x in data if x.get('expiryDate') == current_expiry]

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
                strike = row.get('strikePrice')
                ce_oi = row.get('CE', {}).get('openInterest', 0)
                pe_oi = row.get('PE', {}).get('openInterest', 0)

                # IV Extraction
                ce_iv = row.get('CE', {}).get('impliedVolatility', 0) or 0
                pe_iv = row.get('PE', {}).get('impliedVolatility', 0) or 0

                if ce_iv > 0:
                    valid_ivs.append(ce_iv)
                if pe_iv > 0:
                    valid_ivs.append(pe_iv)

                # Check for ATM
                try:
                    diff = abs(strike - ltp)
                except Exception:
                    diff = float('inf')

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
                    strike = row.get('strikePrice')
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
        except Exception as e:
            logger.error(f"analyze_oi failed: {e}")
            try:
                track_error_detail(type(e).__name__, str(e), context={"function": "analyze_oi"})
            except Exception:
                pass
            return None


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
                days_remaining = (expiry_dt - today).days
                days_remaining = max(1, days_remaining)
            except Exception as e:
                logger.debug(f"Failed to parse expiry_date {expiry_date}: {e}")
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
