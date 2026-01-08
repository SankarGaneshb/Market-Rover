
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

class SeasonalityCalendar:
    """
    Analyzes historical data to find optimal monthly Buy/Sell days 
    and maps them to a specific year's calendar (default 2026), 
    adjusting for weekends and holidays.
    """
    
    def __init__(self, history, year=2026):
        self.history = history
        self.year = year
        self.holidays = HOLIDAYS_2026  # Hardcoded for 2026 for now

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

    def _adjust_date_for_holidays(self, month, day, action):
        """
        Adjusts a date to avoid Weekends (Sat/Sun) and NSE Holidays.
        Buy -> Shift Forward (Monday/Next Open Day)
        Sell -> Shift Backward (Friday/Prev Open Day)
        Returns: (day, weekday_str, is_adjusted)
        """
        try:
            # Handle Feb 29 (Treat as Feb 28 for non-leap 2026)
            if month == 2 and day > 28: day = 28
            
            dt = datetime(self.year, month, day).date()
            
            # Protocol: 
            # Buy on Weekend -> Shift to Monday (Forward)
            # Sell on Weekend -> Shift to Friday (Backward)
            
            max_shifts = 10
            shifts = 0
            is_adjusted = False
            
            # Initial Check
            while shifts < max_shifts:
                wd = dt.weekday() # Mon=0, Sun=6
                is_holiday = (dt in self.holidays)
                
                if wd >= 5 or is_holiday:
                    is_adjusted = True
                    if action == 'buy':
                        dt += timedelta(days=1)
                    elif action == 'sell':
                        dt -= timedelta(days=1) # Shift backward
                        # Edge case: If backward shift pushes to prev month (e.g. May 1st -> Apr 30th)
                        # We should probably limit to current month or allow logic to handle it.
                        # For simplicity, if day becomes < 1, reset to 1 and try forward?
                        # Or just accept it falling into prev month (but for visual chart this might be weird).
                        # Let's just shift backward.
                    
                    shifts += 1
                else:
                    break
            
            # Safety for month boundary crossing (Plotting expects month 1-12)
            if dt.month != month:
                # If we shifted out of the month, force closest day within month?
                # Actually, strictly speaking, moving selling to prev month is valid "Calendar planning".
                # But for the chart (Y-Axis = Month), it might be confusing.
                # Let's keep simpler logic: if Sell shift back goes to prev month, try shift forward instead?
                # No, standard rule: Sell -> Friday.
                pass 

            return dt, dt.strftime("%a"), is_adjusted
            
        except Exception as e:
            # print(f"Error adjusting date: {e}")
            return datetime(self.year, month, 1).date(), "??", True

    def generate_analysis(self):
        """
        Generates the full analysis DataFrame
        """
        results = []
        for m in range(1, 13):
            month_name = calendar.month_name[m]
            b_day, s_day, gain = self._get_best_days_for_month(m)
            
            # Adjust
            b_dt, b_wd, b_adj = self._adjust_date_for_holidays(m, b_day, 'buy')
            s_dt, s_wd, s_adj = self._adjust_date_for_holidays(m, s_day, 'sell')
            
            results.append({
                "Month_Num": m,
                "Month": month_name,
                "Best_Buy_Day_Raw": b_day,
                "Best_Sell_Day_Raw": s_day,
                "Avg_Gain_Pct": gain,
                "Buy_Date_2026": b_dt,
                "Buy_Weekday": b_wd,
                "Buy_Adjusted": b_adj,
                "Sell_Date_2026": s_dt,
                "Sell_Weekday": s_wd,
                "Sell_Adjusted": s_adj,
                # For plotting original "Ghost" dots
                "Buy_Date_Orig": datetime(self.year, m, b_day).date() if not (m==2 and b_day>28) else datetime(2026, 2, 28).date(),
                "Sell_Date_Orig": datetime(self.year, m, s_day).date() if not (m==2 and s_day>28) else datetime(2026, 2, 28).date()
            })
            
        return pd.DataFrame(results)

    def plot_calendar(self, df):
        """
        Returns a Matplotlib Figure: Side-by-Side Layout (Jan-Jun, Jul-Dec)
        For Compact Viewing on Single Page. Force White Background.
        """
        # Force white style
        plt.style.use('default') 
        
        # Wide Layout: 16x6 inches (Fits screen better)
        fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=False)
        fig.patch.set_facecolor('white')
        
        # Split Data
        df1 = df[df['Month_Num'] <= 6]  # Jan-Jun
        df2 = df[df['Month_Num'] >= 7]  # Jul-Dec
        
        def plot_half_year(ax, sub_df, title):
            ax.set_facecolor('white')
            # Invert Y so first month is top
            display_months = sub_df['Month'].tolist()
            
            # Map month num to 0..5 index
            # We want top=0, bottom=5
            # Reset index to make loop easy
            sub_df = sub_df.reset_index(drop=True)
            
            for i, row in sub_df.iterrows():
                y_pos = (len(sub_df) - 1) - i # Top down
                
                # --- BUY ---
                b_date = row['Buy_Date_2026']
                if row['Buy_Adjusted']:
                    # Ghost
                    ax.scatter(x=row['Buy_Date_Orig'].day, y=y_pos, s=120, color='green', alpha=0.3, zorder=3)
                    # Connector
                    ax.plot([row['Buy_Date_Orig'].day, b_date.day], [y_pos, y_pos], color='green', linestyle=':', alpha=0.5, zorder=3)
                    # Hollow
                    ax.scatter(x=b_date.day, y=y_pos, s=180, edgecolors='green', facecolors='none', linewidth=2.0, zorder=4)
                else:
                    ax.scatter(x=b_date.day, y=y_pos, s=180, color='green', edgecolors='white', linewidth=1.5, zorder=4)

                # --- SELL ---
                s_date = row['Sell_Date_2026']
                if row['Sell_Adjusted']:
                    # Ghost
                    ax.scatter(x=row['Sell_Date_Orig'].day, y=y_pos, s=120, color='red', alpha=0.3, zorder=3)
                    # Connector
                    ax.plot([row['Sell_Date_Orig'].day, s_date.day], [y_pos, y_pos], color='red', linestyle=':', alpha=0.5, zorder=3)
                    # Hollow
                    ax.scatter(x=s_date.day, y=y_pos, s=180, edgecolors='red', facecolors='none', linewidth=2.0, zorder=4)
                else:
                    ax.scatter(x=s_date.day, y=y_pos, s=180, color='red', edgecolors='white', linewidth=1.5, zorder=4)
                
                # Annotations
                ax.text(b_date.day, y_pos + 0.35, f"{b_date.day}\n({row['Buy_Weekday']})", 
                        ha='center', va='top', color='green', fontsize=8, fontweight='bold')
                ax.text(s_date.day, y_pos + 0.35, f"{s_date.day}\n({row['Sell_Weekday']})", 
                        ha='center', va='top', color='red', fontsize=8, fontweight='bold')

            # Formatting
            ax.set_yticks(range(len(sub_df)))
            ax.set_yticklabels(display_months[::-1], fontsize=10, fontweight='bold', color='black')
            ax.set_xticks(range(1, 32, 2)) # Every 2nd day to save space
            ax.set_xlim(0, 32)
            ax.tick_params(axis='x', colors='black')
            ax.tick_params(axis='y', colors='black')
            ax.grid(True, linestyle='--', alpha=0.3, color='gray')
            ax.set_title(title, fontsize=12, fontweight='bold', color='black', pad=10)
            
            # Remove spines for cleaner look
            for spine in ax.spines.values():
                spine.set_color('#dddddd')

        # Plot Left (Jan-Jun)
        plot_half_year(axes[0], df1, "First Half (Jan - Jun)")
        
        # Plot Right (Jul-Dec)
        plot_half_year(axes[1], df2, "Second Half (Jul - Dec)")

        fig.suptitle(f"Strategic Trading Calendar {self.year} (Holiday Adjusted)", fontsize=16, fontweight='bold', color='black')
        plt.tight_layout()
        return fig
