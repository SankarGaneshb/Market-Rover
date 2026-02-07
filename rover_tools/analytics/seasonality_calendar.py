
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import calendar

# NSE Holidays 2026 (Confirmed)
HOLIDAYS_2026 = [
    datetime(2026, 1, 26).date(),
    datetime(2026, 3, 3).date(),
    datetime(2026, 3, 26).date(),
    datetime(2026, 3, 31).date(),
    datetime(2026, 4, 3).date(),
    datetime(2026, 4, 14).date(),
    datetime(2026, 5, 1).date(),
    datetime(2026, 5, 28).date(),
    datetime(2026, 6, 26).date(),
    datetime(2026, 8, 15).date(),
    datetime(2026, 9, 14).date(),
    datetime(2026, 10, 2).date(),
    datetime(2026, 10, 20).date(),
    datetime(2026, 11, 10).date(),
    datetime(2026, 11, 24).date(),
    datetime(2026, 12, 25).date()
]

# NSE Holidays 2027 (Projected)
HOLIDAYS_2027 = [
    datetime(2027, 1, 26).date(),
    datetime(2027, 3, 6).date(),
    datetime(2027, 3, 10).date(),
    datetime(2027, 3, 22).date(),
    datetime(2027, 3, 26).date(),
    datetime(2027, 4, 14).date(),
    datetime(2027, 4, 15).date(),
    datetime(2027, 4, 19).date(),
    datetime(2027, 5, 1).date(),
    datetime(2027, 5, 17).date(),
    datetime(2027, 6, 15).date(),
    datetime(2027, 8, 15).date(),
    datetime(2027, 9, 4).date(),
    datetime(2027, 10, 2).date(),
    datetime(2027, 10, 10).date(),
    datetime(2027, 10, 29).date(), # Diwali
    datetime(2027, 11, 14).date(),
    datetime(2027, 12, 25).date()
]

class SeasonalityCalendar:
    """
    Analyzes historical data to find optimal monthly Buy/Sell days 
    and maps them to a specific strategy: Buy in 2026, Sell in 2027.
    """
    
    def __init__(self, history, buy_year=2026, sell_year=2027, exclude_outliers=False):
        self.history = history
        self.buy_year = buy_year
        self.sell_year = sell_year
        self.holidays_map = {
            2026: HOLIDAYS_2026,
            2027: HOLIDAYS_2027
        }
        self.exclude_outliers = exclude_outliers

    def _remove_outliers(self, series):
        """Standard IQR method for outlier removal"""
        if len(series) < 4: return series
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return series[(series >= lower_bound) & (series <= upper_bound)]

    def _get_best_days_for_month(self, month):
        """Finds best buy/sell days for a given month index (1-12)"""
        m_data = self.history[self.history.index.month == month].copy()
        if m_data.empty:
            return 1, 28, 0.0 # Fallback
            
        # Normalize to month start = 0%
        m_data['Year'] = m_data.index.year
        # Handle cases where multiple years exist
        # Calculate daily relative performance avg
        
        # We need relative change from month START
        m_data['Month_Start_Price'] = m_data.groupby('Year')['Close'].transform('first')
        m_data['Rel_Change'] = ((m_data['Close'] - m_data['Month_Start_Price']) / m_data['Month_Start_Price']) * 100
        
        # Apply outlier removal if requested
        if self.exclude_outliers:
            clean_idx = self._remove_outliers(m_data['Rel_Change']).index
            m_data = m_data.loc[clean_idx]
        
        # Group by Day of Month
        daily_seasonality = m_data.groupby(m_data.index.day)['Rel_Change'].mean()
        
        # Constrained Optimization: Buy Day < Sell Day
        best_gain = -999.0
        best_buy = 1
        best_sell = 28
        
        days = sorted(daily_seasonality.index.unique())
        if len(days) < 2:
             return 1, 1, 0.0

        for i in range(len(days)):
            for j in range(i+1, len(days)):
                gain = daily_seasonality[days[j]] - daily_seasonality[days[i]]
                if gain > best_gain:
                    best_gain = gain
                    best_buy = days[i]
                    best_sell = days[j]
                    
        return best_buy, best_sell, best_gain

    def _calculate_annual_return(self, month, buy_day, sell_day):
        """
        Calculates the average return for a strategy of:
        Buy on Month/Day in Year T
        Sell on Month/Day in Year T+1
        """
        try:
            # Get all unique years in history
            years = sorted(self.history.index.year.unique())
            returns = []
            
            for y in years[:-1]: # Can't sell in T+1 if T is last year
                try:
                    # Buy Date
                    b_date = pd.Timestamp(year=y, month=month, day=buy_day)
                    # Sell Date (Next Year)
                    s_date = pd.Timestamp(year=y+1, month=month, day=sell_day)
                    
                    # Get nearest trading days if exact dates missing
                    # We use 'asof' or searchsorted-like logic, but simple way is to limit to history
                    
                    # Filter history for dates (ensure checking valid range)
                    if b_date >= self.history.index[0] and s_date <= self.history.index[-1]:
                         # Get exact or next available price
                        buy_row = self.history.loc[self.history.index >= b_date]
                        sell_row = self.history.loc[self.history.index >= s_date]
                        
                        if not buy_row.empty and not sell_row.empty:
                            b_price = buy_row.iloc[0]['Close']
                            s_price = sell_row.iloc[0]['Close']
                            
                            # Valid trade
                            ret = ((s_price - b_price) / b_price) * 100
                            returns.append(ret)
                            
                except ValueError:
                    # Handle Feb 29 etc
                    continue
            
            if not returns:
                return 0.0
                
            return np.mean(returns)
            
        except Exception as e:
            return 0.0

    def _adjust_date_for_holidays(self, year, month, day, action):
        """
        Adjusts a date to avoid Weekends (Sat/Sun) and NSE Holidays.
        Buy -> Shift Forward (Monday/Next Open Day)
        Sell -> Shift Backward (Friday/Prev Open Day)
        Returns: (day, weekday_str, is_adjusted)
        """
        try:
            # Handle Feb 29 
            if month == 2 and day > 28:
                 # Check leap year
                 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                     day = 29
                 else:
                     day = 28
            
            # Additional safety for 31st on 30-day months
            if day == 31 and month in [4, 6, 9, 11]:
                day = 30

            dt = datetime(year, month, day).date()
            
            # Protocol: 
            # Buy on Weekend -> Shift to Monday (Forward)
            # Sell on Weekend -> Shift to Friday (Backward)
            
            max_shifts = 10
            shifts = 0
            is_adjusted = False
            
            holidays = self.holidays_map.get(year, [])

            # Initial Check
            while shifts < max_shifts:
                wd = dt.weekday() # Mon=0, Sun=6
                is_holiday = (dt in holidays)
                
                if wd >= 5 or is_holiday:
                    is_adjusted = True
                    if action == 'buy':
                        dt += timedelta(days=1)
                    elif action == 'sell':
                        dt -= timedelta(days=1) # Shift backward
                    
                    shifts += 1
                else:
                    break
            
            return dt, dt.strftime("%a"), is_adjusted
            
        except Exception as e:
            # print(f"Error adjusting date: {e}")
            return datetime(year, month, 1).date(), "??", True

    def generate_analysis(self):
        """
        Generates the full analysis DataFrame
        """
        results = []
        for m in range(1, 13):
            month_name = calendar.month_name[m]
            b_day, s_day, intra_month_gain = self._get_best_days_for_month(m)
            
            # Calculate 1-Year Hold Return
            annual_gain = self._calculate_annual_return(m, b_day, s_day)

            # Adjust
            b_dt, b_wd, b_adj = self._adjust_date_for_holidays(self.buy_year, m, b_day, 'buy')
            s_dt, s_wd, s_adj = self._adjust_date_for_holidays(self.sell_year, m, s_day, 'sell')
            
            results.append({
                "Month_Num": m,
                "Month": month_name,
                "Best_Buy_Day_Raw": b_day,
                "Best_Sell_Day_Raw": s_day,
                "Avg_Gain_Pct": intra_month_gain,
                "Avg_Annual_Gain": annual_gain,
                "Buy_Date_2026": b_dt,
                "Buy_Weekday": b_wd,
                "Buy_Adjusted": b_adj,
                "Sell_Date_2026": s_dt, # Variable name kept for compatibility, but is actually sell_year
                "Sell_Weekday": s_wd,
                "Sell_Adjusted": s_adj,
                # For plotting original "Ghost" dots
                "Buy_Date_Orig": datetime(self.buy_year, m, b_day).date() if not (m==2 and b_day>28) else datetime(self.buy_year, 2, 28).date(),
                "Sell_Date_Orig": datetime(self.sell_year, m, s_day).date() if not (m==2 and s_day>28) else datetime(self.sell_year, 2, 28).date()
            })
            
        return pd.DataFrame(results)

    def plot_calendar(self, df):
        """
        Returns a Matplotlib Figure: Side-by-Side Layout (2026 Buy vs 2027 Sell)
        """
        # Force white style
        plt.style.use('default') 
        
        # Taller Layout to fit 12 months: 16x10 inches
        fig, axes = plt.subplots(1, 2, figsize=(16, 12), sharey=True)
        fig.patch.set_facecolor('white')
        
        # Both plots show all 12 months
        
        def plot_year_column(ax, sub_df, title, mode):
            ax.set_facecolor('white')
            # Invert Y so first month is top
            display_months = sub_df['Month'].tolist()
            
            # Map month num to 0..11 index
            sub_df = sub_df.reset_index(drop=True)
            
            for i, row in sub_df.iterrows():
                y_pos = (len(sub_df) - 1) - i # Top down
                
                if mode == 'buy':
                    # --- BUY (Green) ---
                    date_col = 'Buy_Date_2026'
                    wd_col = 'Buy_Weekday'
                    adj_col = 'Buy_Adjusted'
                    orig_col = 'Buy_Date_Orig'
                    color = 'green'
                else:
                    # --- SELL (Red) ---
                    date_col = 'Sell_Date_2026'
                    wd_col = 'Sell_Weekday'
                    adj_col = 'Sell_Adjusted'
                    orig_col = 'Sell_Date_Orig'
                    color = 'red'

                act_date = row[date_col]
                
                if row[adj_col]:
                    # Ghost
                    ax.scatter(x=row[orig_col].day, y=y_pos, s=120, color=color, alpha=0.3, zorder=3)
                    # Connector
                    ax.plot([row[orig_col].day, act_date.day], [y_pos, y_pos], color=color, linestyle=':', alpha=0.5, zorder=3)
                    # Hollow
                    ax.scatter(x=act_date.day, y=y_pos, s=180, edgecolors=color, facecolors='none', linewidth=2.0, zorder=4)
                else:
                    ax.scatter(x=act_date.day, y=y_pos, s=180, color=color, edgecolors='white', linewidth=1.5, zorder=4)

                # Annotations
                ax.text(act_date.day, y_pos - 0.2, f"{act_date.day}\n({row[wd_col]})", 
                        ha='center', va='top', color=color, fontsize=9, fontweight='bold')

            # Formatting
            ax.set_yticks(range(len(sub_df)))
            ax.set_yticklabels(display_months[::-1], fontsize=11, fontweight='bold', color='black')
            ax.set_xticks(range(1, 32, 2)) # Every 2nd day
            ax.set_xlim(0, 32)
            ax.tick_params(axis='x', colors='black')
            ax.tick_params(axis='y', colors='black')
            ax.grid(True, linestyle='--', alpha=0.3, color='gray')
            ax.set_title(title, fontsize=14, fontweight='bold', color='black', pad=15)
            
            # Remove spines for cleaner look
            for spine in ax.spines.values():
                spine.set_color('#dddddd')

        # Plot Left (2026 Buy)
        plot_year_column(axes[0], df, f"Entry Plan ({self.buy_year})", 'buy')
        
        # Plot Right (2027 Sell)
        plot_year_column(axes[1], df, f"Exit Plan ({self.sell_year})", 'sell')

        fig.suptitle(f"Strategic Trading Calendar {self.buy_year}-{self.sell_year}", fontsize=18, fontweight='bold', color='black')
        plt.tight_layout()
        return fig
