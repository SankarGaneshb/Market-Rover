
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
from datetime import datetime, timedelta

def run_analysis(ticker="KALYANKJIL.NS", target_month=1):
    print(f"--- FRESH SEASONALITY ANALYSIS: {ticker} (Month: {target_month}) ---")
    
    # 1. Fetch Data
    print("Downloading historical data...")
    try:
        # Download full history
        hist = yf.download(ticker, progress=False)
        
        # yfinance sometimes returns MultiIndex columns if ticker is list, or single. 
        # Ensure simple columns.
        if isinstance(hist.columns, pd.MultiIndex):
             hist.columns = hist.columns.get_level_values(0)
             
        hist.index = pd.to_datetime(hist.index)
        
    except Exception as e:
        print(f"Error downloading data: {e}")
        return

    if hist.empty:
        print("No data received.")
        return

    print(f"Total History: {len(hist)} trading days.")

    # 2. Filter for Target Month (January)
    print(f"Isolating data for Month {target_month}...")
    jan_data = hist[hist.index.month == target_month].copy()
    
    if jan_data.empty:
        print("No data found for this month.")
        return
        
    years_found = jan_data.index.year.unique()
    print(f"Found data for years: {list(years_found)} ({len(jan_data)} days)")

    # 3. Normalization (Calculate % Return relative to Month Start)
    # We need to process year by year to normalize correctly.
    
    jan_data['Year'] = jan_data.index.year
    jan_data['Month_Start_Price'] = jan_data.groupby('Year')['Close'].transform('first')
    # Percentage Change from first day of month
    jan_data['Rel_Return_Pct'] = ((jan_data['Close'] - jan_data['Month_Start_Price']) / jan_data['Month_Start_Price']) * 100
    
    # 4. Aggregation by Day of Month
    # We want to know: For "Day 5", what is the average return?
    # Create a full 1-31 index to detect holes.
    
    jan_data['Day'] = jan_data.index.day
    
    # Group
    daily_stats = jan_data.groupby('Day')['Rel_Return_Pct'].agg(['mean', 'count', 'min', 'max'])
    daily_prices = jan_data.groupby('Day')['Close'].mean() # Just for reference context
    
    # 5. Reporting
    print("\n" + "="*65)
    print(f" AVERAGE DAILY PERFORMANCE (JANUARY ONLY) - {ticker}")
    print("="*65)
    print(f"{'Day':<4} | {'Avg Return':<12} | {'Win Count':<10} | {'Status'}")
    print("-" * 65)

    plot_data = []

    for day in range(1, 32):
        if day in daily_stats.index:
            avg_ret = daily_stats.loc[day, 'mean']
            count = int(daily_stats.loc[day, 'count'])
            total_years = len(years_found)
            
            # Simple inference: if count is low, it's often a weekend.
            status = ""
            if count == 0:
                status = "HOLIDAY / CLOSED"
            elif count < total_years / 2:
                status = "Often Weekend"
            else:
                 status = "Active"
                 
            # Trend Check
            # We can't say Buy/Sell easily without looking at the curve, but we can print the val.
            
            print(f"{day:<4} | {avg_ret:>7.2f}%    | {count}/{total_years:<7} | {status}")
            
            plot_data.append({'Day': day, 'Avg_Return': avg_ret})
        else:
            # Day never existed in trading history (Is this possible? Jan 26 always holiday)
            print(f"{day:<4} | {'---':>7}     | 0/{len(years_found):<7} | MARKET CLOSED (Holiday?)")
            
    print("="*65)
    
    # 6. Find Best Days (Min and Max of the average curve)
    df_plot = pd.DataFrame(plot_data)
    
    if not df_plot.empty:
        best_buy = df_plot.loc[df_plot['Avg_Return'].idxmin()]
        best_sell = df_plot.loc[df_plot['Avg_Return'].idxmax()]
        
        print(f"\n[ANALYSIS RESULT]")
        print(f"Based on history, the Monthly Low typically occurs around Day {int(best_buy['Day'])} ({best_buy['Avg_Return']:.2f}% avg drop).")
        print(f"The Monthly High typically occurs around Day {int(best_sell['Day'])} ({best_sell['Avg_Return']:.2f}% avg gain).")

        # 7. Visualization
        # Save to output/kalyan_jan_fresh.png
        
        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(12, 6))
        
        sns.lineplot(data=df_plot, x='Day', y='Avg_Return', marker='o', linewidth=2, color='blue')
        
        # Add labels
        plt.title(f"Average Price Path for {ticker} in JANUARY (Relative to Jan 1st)", fontsize=14)
        plt.ylabel("Average Return (%)")
        plt.xlabel("Day of Month")
        plt.xticks(range(1, 32))
        plt.axhline(0, color='black', linewidth=0.5)
        
        # Highlight markers
        plt.plot(best_buy['Day'], best_buy['Avg_Return'], 'go', markersize=10, label=f"Low: Day {int(best_buy['Day'])}")
        plt.plot(best_sell['Day'], best_sell['Avg_Return'], 'ro', markersize=10, label=f"High: Day {int(best_sell['Day'])}")
        plt.legend()
        
        out_path = "output/kalyan_jan_fresh.png"
        os.makedirs("output", exist_ok=True)
        plt.savefig(out_path)
        print(f"\nChart saved to: {os.path.abspath(out_path)}")

def run_full_year_analysis(ticker):
    print(f"--- FULL YEAR SEASONALITY ANALYSIS: {ticker} ---")
    
    # 1. Fetch Data (Once)
    print("Downloading historical data...")
    try:
        # Use Ticker.history instead of download (more reliable structure)
        stock = yf.Ticker(ticker)
        hist = stock.history(period="max")
        
        # history() returns nice SingleIndex columns usually, but check index
        if hist.empty:
            print("No data received via history().")
            return
            
        # Ensure index is datetime
        hist.index = pd.to_datetime(hist.index)
        
        print(f"Data Loaded: {len(hist)} rows. Index: {hist.index[0]} to {hist.index[-1]}")
        
    except Exception as e:
        print(f"Error: {e}")
        return

    if hist.empty: return

    # 2. Setup Plot
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(4, 3, figsize=(20, 15))
    axes = axes.flatten()
    
    summary_data = []
    
    # 3. Iterate Months
    for month in range(1, 13):
        month_name = datetime(2000, month, 1).strftime('%B')
        print(f"Processing {month_name}...", end=" ")
        
        # Filter
        m_data = hist[hist.index.month == month].copy()
        if m_data.empty: 
            print("No data.")
            continue
            
        # Normalize
        m_data['Year'] = m_data.index.year
        m_data['Start_Price'] = m_data.groupby('Year')['Close'].transform('first')
        m_data['Rel_Return'] = ((m_data['Close'] - m_data['Start_Price']) / m_data['Start_Price']) * 100
        m_data['Day'] = m_data.index.day
        
        # Aggregation
        daily = m_data.groupby('Day')['Rel_Return'].mean()
        
        if daily.empty:
            print("Empty.")
            continue
            
        # Stats
        # NEW LOGIC: Constrained Optimization (Buy Date < Sell Date)
        best_gain = -9999.0
        best_buy = 1
        best_sell = 2
        
        days_sorted = sorted(daily.index.unique())
        
        # O(N^2) search on average curve (N=31, very fast)
        for i in range(len(days_sorted)):
            b_day = days_sorted[i]
            b_val = daily[b_day]
            
            for j in range(i+1, len(days_sorted)):
                s_day = days_sorted[j]
                s_val = daily[s_day]
                
                # Check gain
                gain = s_val - b_val
                
                if gain > best_gain:
                    best_gain = gain
                    best_buy = b_day
                    best_sell = s_day
        
        if best_gain == -9999.0:
            # Fallback if mostly empty or single day
            best_buy = days_sorted[0]
            best_sell = days_sorted[-1]
            best_gain = 0.0

        summary_data.append({
            'Month': month_name,
            'Best_Buy_Day': best_buy,
            'Avg_Low': daily[best_buy], # Value on that day
            'Best_Sell_Day': best_sell,
            'Avg_High': daily[best_sell] # Value on that day
        })
        
        print(f"Done. (Buy: {best_buy}, Sell: {best_sell}, Avg Gain: {best_gain:.2f}%)")
        
        # Plot Subplot
        ax = axes[month-1]
        sns.lineplot(x=daily.index, y=daily.values, ax=ax, color='tab:blue', marker='o', markersize=4)
        ax.set_title(month_name)
        ax.set_xlabel("")
        ax.set_ylabel("Ret %")
        ax.axhline(0, color='black', linewidth=0.5, alpha=0.5)
        
        # Highlights
        ax.plot(best_buy, daily[best_buy], 'go', markersize=8) # Buy
        ax.plot(best_sell, daily[best_sell], 'ro', markersize=8) # Sell (now guaranteed > Buy)

    # 4. Finalize
    plt.tight_layout()
    out_path = "output/kalyan_full_year_seasonality.png"
    os.makedirs("output", exist_ok=True)
    plt.savefig(out_path)
    print(f"\nSaved Full Year Chart to: {out_path}")
    
    # 5. Print Summary Table
    print("\n" + "="*60)
    print(f"{'Month':<12} | {'Buy Day':<8} | {'Avg Low%':<10} | {'Sell Day':<8} | {'Avg High%'}")
    print("-" * 60)
    for row in summary_data:
        print(f"{row['Month']:<12} | {row['Best_Buy_Day']:<8} | {row['Avg_Low']:>7.2f}%   | {row['Best_Sell_Day']:<8} | {row['Avg_High']:>7.2f}%")
    print("="*60)
    
    # 6. Consolidated Calendar Plot (User Requested)
    plot_annual_calendar(summary_data, ticker)


def plot_annual_calendar(summary_data, ticker):
    """
    Creates a single chart with Months on Y-axis and Days on X-axis.
    Shows Buy and Sell days as distinct markers.
    """
    # Create a mapping for month sorting
    month_map = {datetime(2000, m, 1).strftime('%B'): m for m in range(1, 13)}
    
    df = pd.DataFrame(summary_data)
    # Ensure sorted by Calendar Month (Jan->Dec)
    df['MonthNum'] = df['Month'].map(month_map)
    df = df.sort_values('MonthNum')
    
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(14, 10))
    
    # Y Positions (0 to 11) - Inverted so Jan is at Top
    # explicit range
    y_pos = range(len(df))
    
    # Plot grid lines for every month
    for y in y_pos:
        plt.axhline(y, color='gray', linestyle='-', alpha=0.3)
    
    # Buy Dots (Green Circles)
    plt.scatter(x=df['Best_Buy_Day'], y=y_pos, color='green', s=200, alpha=1.0, label='Best Buy (Low)', edgecolors='white', linewidth=1.5, zorder=3)
    
    # Sell Dots (Red Circles - User Requested)
    plt.scatter(x=df['Best_Sell_Day'], y=y_pos, color='red', s=200, alpha=1.0, label='Best Sell (High)', edgecolors='white', linewidth=1.5, zorder=3)
    
    # Labels
    plt.yticks(y_pos, df['Month'], fontsize=12)
    plt.xticks(range(1, 32), fontsize=10)
    plt.gca().invert_yaxis() # Jan at Top
    
    plt.xlabel("Day of Month", fontsize=12)
    plt.title(f"Optimal Monthly Trading Days - {ticker} (Yearly Calendar)", fontsize=16)
    
    # Legend
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=2, frameon=True)
    
    # Limit Axes to show everything nicely
    plt.ylim(len(df)-0.5, -0.5) 
    plt.xlim(0.5, 31.5)
    
    # Annotate
    # Reset index to 0..11 to match y_pos
    df = df.reset_index(drop=True)
    
    # Helper for 2026 Weekday Adjustment
    def adjust_for_weekend_2026(m_name, d, action):
        """
        Returns (adj_day, adj_weekday_str, is_adjusted)
        """
        try:
            m_num = datetime.strptime(m_name, "%B").month
            if m_num == 2 and d > 28: d = 28
            
            # Define dt first!
            dt = datetime(2026, m_num, d)

            # NSE Holidays 2026 (Confirmed)
            holidays_2026 = [
                datetime(2026, 1, 26),  # Republic Day
                datetime(2026, 3, 3),   # Holi
                datetime(2026, 3, 26),  # Ram Navami
                datetime(2026, 3, 31),  # Mahavir Jayanti
                datetime(2026, 4, 3),   # Good Friday
                datetime(2026, 4, 14),  # Ambedkar Jayanti
                datetime(2026, 5, 1),   # Maharashtra Day
                datetime(2026, 5, 28),  # Eid
                datetime(2026, 6, 26),  # Muharram
                datetime(2026, 8, 15),  # Independence Day (Sat)
                datetime(2026, 9, 14),  # Ganesh Chaturthi
                datetime(2026, 10, 2),  # Gandhi Jayanti
                datetime(2026, 10, 20), # Dussehra
                datetime(2026, 11, 10), # Diwali
                datetime(2026, 11, 24), # Gurpurb
                datetime(2026, 12, 25)  # Christmas
            ]
            
            # Iterative likely adjustment if colliding with weekends OR holidays
            # We use a while True loop to keep shifting until open
            
            max_shifts = 7 # Safety break
            shifts = 0
            is_adj = False # Initialize!
            
            # Initial Check
            while shifts < max_shifts:
                wd = dt.weekday()
                is_holiday = any(h.date() == dt.date() for h in holidays_2026)
                
                if wd >= 5 or is_holiday:
                    is_adj = True
                    if action == 'buy':
                        dt += timedelta(days=1)
                    elif action == 'sell':
                        dt -= timedelta(days=1)
                    shifts += 1
                else:
                    break
            
            return dt.day, dt.strftime('%a'), is_adj
            
        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            return d, "??", False

    # Plotting Loop
    for i, row in df.iterrows():
        # BUY Adjustment
        b_orig = row['Best_Buy_Day']
        b_day, b_wd, b_adj = adjust_for_weekend_2026(row['Month'], b_orig, 'buy')
        
        # SELL Adjustment
        s_orig = row['Best_Sell_Day']
        s_day, s_wd, s_adj = adjust_for_weekend_2026(row['Month'], s_orig, 'sell')

        # --- Plot BUY ---
        if b_adj:
            # Ghost (Original)
            plt.scatter(x=b_orig, y=i, s=150, color='green', alpha=0.3, zorder=3)
            # Connector
            plt.plot([b_orig, b_day], [i, i], color='green', linestyle=':', alpha=0.5, zorder=3)
            # Adjusted (Hollow)
            plt.scatter(x=b_day, y=i, s=200, edgecolors='green', facecolors='none', linewidth=2.0, zorder=4)
        else:
            # Normal (Solid)
            plt.scatter(x=b_day, y=i, s=200, color='green', edgecolors='white', linewidth=1.5, zorder=4)

        # --- Plot SELL ---
        if s_adj:
            # Ghost (Original)
            plt.scatter(x=s_orig, y=i, s=150, color='red', alpha=0.3, zorder=3)
            # Connector
            plt.plot([s_orig, s_day], [i, i], color='red', linestyle=':', alpha=0.5, zorder=3)
            # Adjusted (Hollow)
            plt.scatter(x=s_day, y=i, s=200, edgecolors='red', facecolors='none', linewidth=2.0, zorder=4)
        else:
            # Normal (Solid)
            plt.scatter(x=s_day, y=i, s=200, color='red', edgecolors='white', linewidth=1.5, zorder=4)
        
        # Annotate (Only on the final Actionable Day)
        plt.text(b_day, i + 0.25, f"{b_day}\n({b_wd})", ha='center', va='top', color='green', fontsize=9, fontweight='bold')
        plt.text(s_day, i + 0.25, f"{s_day}\n({s_wd})", ha='center', va='top', color='red', fontsize=9, fontweight='bold')

    plt.tight_layout()
    # Dynamic filename
    clean_ticker = ticker.replace('.NS', '').replace('.BO', '').lower()
    out_path = f"output/{clean_ticker}_annual_calendar.png"
    plt.savefig(out_path)
    print(f"Saved Calendar Chart to: {out_path}")

if __name__ == "__main__":
    from datetime import datetime
    ticker = sys.argv[1] if len(sys.argv) > 1 else "KALYANKJIL.NS"
    
    # Check if a specific month arg is provided
    if len(sys.argv) > 2:
        # Run single month mode (legacy function)
        t_month = int(sys.argv[2])
        run_analysis(ticker, t_month)
    else:
        # Run full year mode
        run_full_year_analysis(ticker)
