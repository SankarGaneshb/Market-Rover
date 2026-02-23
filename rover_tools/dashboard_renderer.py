import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import pandas as pd
import io
import warnings
from PIL import Image

# === MONKEY PATCH FOR STREAMLIT/PYDANTIC CONFLICT ===
# Matplotlib 3.8+ passes 'skip_file_prefixes' to warnings.warn, which
# Pydantic's filtered_warn (used by Streamlit) doesn't accept.
_original_warn = warnings.warn
def _patched_warn(message, category=None, stacklevel=1, source=None, **kwargs):
    kwargs.pop('skip_file_prefixes', None)
    return _original_warn(message, category, stacklevel, source, **kwargs)
warnings.warn = _patched_warn
# ====================================================

# Set premium style
try:
    plt.style.use('dark_background')
except:
    pass # Fallback

sns.set_theme(style="darkgrid", rc={"axes.facecolor": "#121212", "grid.color": "#2A2A2A"})

class DashboardRenderer:
    def __init__(self):
        pass

    def generate_dashboard(self, ticker, history_df, oi_data, scenarios, returns_matrix, forecast_2026=None):
        """
        Generates a composite dashboard image containing:
        1. Price Chart with Volatility Bands & Scenario Targets
        2. Monthly Returns Heatmap (Historical Performance)
        3. Key Analysis Metrics
        """
        # Ensure non-interactive backend for production safety
        plt.switch_backend('Agg')
        
        fig = plt.figure(figsize=(16, 12), constrained_layout=True)
        gs = fig.add_gridspec(3, 2, height_ratios=[1.5, 1.5, 0.8])

        # --- 1. Price Chart (Top Row, spans both cols) ---
        ax1 = fig.add_subplot(gs[0, :])
        try:
            self._plot_price_chart(ax1, ticker, history_df, scenarios, forecast_2026)
        except Exception:
            ax1.text(0.5, 0.5, "Price chart unavailable", ha='center', va='center', color='white')

        # --- 2. Monthly Returns Heatmap (Middle Row, spans both cols) ---
        ax2 = fig.add_subplot(gs[1, :])
        self._plot_monthly_heatmap(ax2, returns_matrix, ticker)

        # --- 3. OI Chart (Bottom Left) ---
        ax3 = fig.add_subplot(gs[2, 0])
        try:
            self._plot_oi_chart(ax3, oi_data)
        except Exception:
            ax3.text(0.5, 0.5, "OI chart unavailable", ha='center', va='center', color='white')

        # --- 4. Key Metrics (Bottom Right) ---
        ax4 = fig.add_subplot(gs[2, 1])
        try:
            self._plot_metrics(ax4, oi_data, scenarios)
        except Exception:
             ax4.axis('off')

        # Watermark
        fig.text(0.98, 0.02, "Market-Rover", color='white', fontsize=18, fontweight='bold', ha='right', alpha=0.3)

        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#000000')
        buf.seek(0)
        plt.close(fig)
        
        return buf

    def generate_pdf_report(self, ticker, history_df, scenarios, returns_matrix, forecast_2026, seasonality_stats, calendar_tool, calendar_df_strategic, calendar_df_muhurta):
        """
        Generates a detailed multi-page PDF report matching Market Analysis Tab.
        Pages:
        1. Executive Summary: Price Chart + Monthly Returns Heatmap
        2. Seasonality Intelligence: Win Rate & Avg Return Charts
        3. Strategic Calendar: 2026 Trading Plan
        4. Subha Muhurta Calendar: 2026 Auspicious Date Plan
        5. Detailed Data Table: Monthly Breakdowns
        6. AI Forecast: 2026 Prediction Models
        """
        # Suppress Matplotlib Font Warnings that crash due to Pydantic conflict
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            plt.switch_backend('Agg')
            # Force Light Mode for PDF
            with plt.style.context('default'):
                buf = io.BytesIO()
                
                with PdfPages(buf) as pdf:
                    # === PAGE 1: EXECUTIVE SUMMARY (Price + Heatmap) ===
                    fig1 = plt.figure(figsize=(11.69, 8.27)) # Landscape A4
                    fig1.patch.set_facecolor('white')
                    # Grid: Title top, Price Middle, Heatmap Bottom
                    gs1 = fig1.add_gridspec(2, 1, height_ratios=[1, 1])
                    
                    # 1. Price Chart
                    ax1 = fig1.add_subplot(gs1[0])
                    self._plot_price_chart(ax1, ticker, history_df, scenarios, forecast_2026, theme='light')
                    
                    # 2. Monthly Returns Heatmap
                    ax2 = fig1.add_subplot(gs1[1])
                    self._plot_monthly_heatmap(ax2, returns_matrix, ticker, theme='light')
                    
                    # Watermark
                    fig1.text(0.98, 0.02, "Market-Rover Report", color='black', fontsize=12, fontweight='bold', ha='right', alpha=0.5)
                    fig1.suptitle(f"{ticker} - Executive Market Analysis", fontsize=20, color='black', fontweight='bold', y=0.98)
                    
                    pdf.savefig(fig1)
                    plt.close(fig1)

                    # === PAGE 2: SEASONALITY INTELLIGENCE ===
                    if not seasonality_stats.empty:
                        fig2 = plt.figure(figsize=(11.69, 8.27))
                        fig2.patch.set_facecolor('white')
                        
                        # Text Description
                        fig2.text(0.1, 0.92, "Seasonality Intelligence", fontsize=18, color='black', fontweight='bold')
                        fig2.text(0.1, 0.89, "Historical performance analysis identifying the strongest and weakest months for this stock.", fontsize=12, color='gray')

                        # 1. Combined Chart (Return vs Probability)
                        # Use a large area for the chart
                        gs2 = fig2.add_gridspec(1, 1)
                        ax_ret = fig2.add_subplot(gs2[0])
                        # Move chart down slightly to fit description
                        pos = ax_ret.get_position()
                        ax_ret.set_position([pos.x0, pos.y0, pos.width, pos.height * 0.8])

                        # Primary Y: Avg Return (Bar Chart)
                        colors = ['#008000' if x > 0 else '#FF0000' for x in seasonality_stats['Avg_Return']] # Darker Green/Red for visibility on white
                        sns.barplot(data=seasonality_stats, x='Month_Name', y='Avg_Return', ax=ax_ret, palette=colors, alpha=0.7)
                        
                        ax_ret.set_ylabel("Average Return %", color='black', fontsize=12)
                        ax_ret.set_xlabel("Month", color='black', fontsize=12)
                        ax_ret.set_title("Seasonality: Return vs. Probability", color='black', fontsize=16, fontweight='bold', pad=20)
                        ax_ret.tick_params(axis='y', colors='black')
                        ax_ret.tick_params(axis='x', colors='black', labelsize=10)
                        # Add simple grid
                        ax_ret.grid(axis='y', linestyle='--', alpha=0.2, color='gray')

                        # Secondary Y: Win Rate (Line Chart)
                        ax_win = ax_ret.twinx()
                        # Use Gold/Orange for contrast on white
                        sns.lineplot(data=seasonality_stats, x='Month_Name', y='Win_Rate', ax=ax_win, color='#FFA500', marker='o', linewidth=3, markersize=8, label='Win Rate %')
                        
                        # Style Secondary Axis
                        ax_win.set_ylabel("Win Rate %", color='#FFA500', fontsize=12)
                        ax_win.set_ylim(0, 110) # 0-100% + buffer for labels
                        ax_win.tick_params(axis='y', colors='#FFA500')
                        ax_win.grid(False) # Remove grid overlap
                        
                        # Add value labels for Win Rate
                        import numpy as np
                        for i, val in enumerate(seasonality_stats['Win_Rate']):
                             # Adjust vertical position slightly
                             offset = 5 if val < 90 else -5
                             ax_win.text(i, val + offset, f"{val:.0f}%", color='#FFA500', ha='center', fontweight='bold', fontsize=9)
                        
                        # Custom Legend
                        import matplotlib.patches as mpatches
                        patch_ret = mpatches.Patch(color='green', label='Avg Return %', alpha=0.7)
                        line_win = plt.Line2D([0], [0], color='#FFA500', linewidth=3, marker='o', label='Win Rate %')
                        
                        ax_win.legend(handles=[patch_ret, line_win], loc='upper center', bbox_to_anchor=(0.5, 1.08), ncol=2, frameon=False, labelcolor='black')

                        # Watermark
                        fig2.text(0.98, 0.02, "Market-Rover Report", color='black', fontsize=12, fontweight='bold', ha='right', alpha=0.5)
                        pdf.savefig(fig2)
                        plt.close(fig2)

                    # === PAGE 3: 2026 STRATEGIC CALENDAR ===
                    # This returns a generated figure, so we save it directly
                    # Calendar tool already uses 'default' style (white bg), so it fits
                    fig3 = calendar_tool.plot_calendar(calendar_df_strategic)
                    
                    # Watermark (Matplotlib default style uses white bg, so use black text watermark)
                    fig3.text(0.98, 0.02, "Market-Rover Report", color='black', fontsize=12, fontweight='bold', ha='right', alpha=0.5)
                    
                    # DESCRIPTION OVERLAY (REMOVED ITALICS/SPECIAL CHARS)
                    fig3.text(0.5, 0.05, "Optimized Trading Schedule: Based on historic best BUY/SELL days. Adjusted for 2026/27 Holidays.", 
                              ha='center', fontsize=10, color='#333333')
                    
                    pdf.savefig(fig3) # No facecolor needed
                    plt.close(fig3)
                    
                    # === PAGE 4: SUBHA MUHURTA CALENDAR ===
                    if not calendar_df_muhurta.empty:
                        # Re-use plot logic but with different title/data
                        # We need to temporarily modify calendar_tool's type or make a new plot call
                        # Ideally pass title, but plot_calendar uses self.calendar_type
                        
                        # Create a new temporary figure using the helper method directly if possible
                        # Or just modify the title after generation? No, title is set hardcoded.
                        # Actually, we passed `calendar_tool` instance which has 'Strategic' type.
                        # But we generated `calendar_df_muhurta` using a SECOND tool instance in `visualizer_tool`.
                        # We didn't receive the second tool instance here, only the DF.
                        # Hack: We can use the first tool to plot the second df, but title will say "Strategic".
                        # Better: Modify title on the returned figure.
                        
                        fig4 = calendar_tool.plot_calendar(calendar_df_muhurta)
                        
                        # Find and update title
                        # fig.suptitle is a Text object
                        fig4._suptitle.set_text(f"Subha Muhurta Trading Calendar {calendar_tool.buy_year}-{calendar_tool.sell_year}")
                        
                        fig4.text(0.98, 0.02, "Market-Rover Report", color='black', fontsize=12, fontweight='bold', ha='right', alpha=0.5)
                        fig4.text(0.5, 0.05, "Auspicious Dates: Based on Hindu Panchang & Market Tradition. Optimized for 2026/27.", 
                                  ha='center', fontsize=10, color='#333333')
                        
                        pdf.savefig(fig4)
                        plt.close(fig4)

                    # === PAGE 5: DETAILED DATA TABLE ===
                    if not calendar_df_strategic.empty:
                        fig5 = plt.figure(figsize=(11.69, 8.27))
                        fig5.patch.set_facecolor('white')
                        
                        ax_table = fig5.add_subplot(111)
                        ax_table.axis('off')
                        
                        self._plot_calendar_table(ax_table, calendar_df_strategic)
                        
                        fig5.text(0.98, 0.02, "Market-Rover Report", color='black', fontsize=12, fontweight='bold', ha='right', alpha=0.5)
                        fig5.suptitle(f"{ticker} - Detailed Seasonality Data", fontsize=18, color='black', fontweight='bold', y=0.95)
                        
                        pdf.savefig(fig5)
                        plt.close(fig5)

                    # === PAGE 6: DETAILED FORECAST NOTES ===
                    fig6 = plt.figure(figsize=(11.69, 8.27))
                    fig6.patch.set_facecolor('white')
                    ax_text = fig6.add_subplot(111)
                    ax_text.axis('off')
                    
                    # Extract forecast numbers
                    cagr = forecast_2026.get('cagr_percent', 0)
                    tgt = forecast_2026.get('consensus_target', 0)
                    low = forecast_2026.get('range_low', 0)
                    high = forecast_2026.get('range_high', 0)
                    
                    summary_text = (
                        f"2026 AI FORECAST SUMMARY: {ticker}\n"
                        f"--------------------------------------------------\n\n"
                        f"TARGET PRICE (Dec 2026):  Rs. {tgt:.2f}\n"
                        f"POTENTIAL UPSIDE (CAGR):  {cagr:.1f}%\n"
                        f"FORECAST RANGE:           {low:.2f}  -  {high:.2f}\n\n"
                        f"METHODOLOGY:\n"
                        f"This forecast is generated using a composite AI model that weighs:\n"
                        f"1. Linear Trend Regression (Baseline Trend)\n"
                        f"2. Compounded Annual Growth Rate (Historical Momentum)\n"
                        f"3. Volatility-Adjusted Scenarios\n\n"
                        f"DISCLAIMER:\n"
                        f"This report is for educational purposes only. Market-Rover uses statistical\n"
                        f"models to project future possibilities based on past data.\n"
                        f"It does not constitute financial advice.\n"
                    )
                    
                    ax_text.text(0.1, 0.8, summary_text, color='black', fontsize=14, family='monospace', va='top')
                    
                    # Watermark
                    fig6.text(0.98, 0.02, "Market-Rover Report", color='black', fontsize=12, fontweight='bold', ha='right', alpha=0.5)
                    pdf.savefig(fig6)
                    plt.close(fig6)
                        
                buf.seek(0)
                return buf

    def _plot_calendar_table(self, ax, df):
        """Draws a nice table of the seasonality data"""
        # Prepare display data
        display_cols = ['Month', 'Best_Buy_Day_Raw', 'Best_Sell_Day_Raw', 'Avg_Gain_Pct', 'Avg_Annual_Gain']
        # Rename for display
        table_data = df[display_cols].copy()
        table_data.columns = ['Month', 'Buy Day', 'Sell Day', 'Avg Mth Gain %', 'Avg Annual %']
        
        # Format numbers
        table_data['Avg Mth Gain %'] = table_data['Avg Mth Gain %'].map('{:.2f}%'.format)
        table_data['Avg Annual %'] = table_data['Avg Annual %'].map('{:.2f}%'.format)
        
        # Create Table
        cell_text = []
        for row in table_data.values:
            cell_text.append(list(row))
            
        table = ax.table(cellText=cell_text, colLabels=table_data.columns, loc='center', cellLoc='center',
                        colColours=['#f2f2f2']*len(table_data.columns))
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2) # Taller rows
        
        # Style
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(weight='bold', color='black')
                cell.set_facecolor('#e0e0e0')
            else:
                cell.set_text_props(color='black')
                if row % 2 == 0:
                     cell.set_facecolor('white')
                else:
                     cell.set_facecolor('#f9f9f9')
            cell.set_edgecolor('#dddddd')

    def _plot_monthly_heatmap(self, ax, returns_matrix, ticker, theme='dark'):
        if returns_matrix is None or (hasattr(returns_matrix, 'empty') and returns_matrix.empty):
            color = 'black' if theme == 'light' else 'white'
            ax.text(0.5, 0.5, "No Historical Data Available", ha='center', va='center', color=color)
            return

        # Text/Line Colors
        text_color = 'black' if theme == 'light' else 'white'
        grid_color = '#dddddd' if theme == 'light' else '#121212'

        # Create heatmap
        sns.heatmap(returns_matrix, ax=ax, cmap="RdYlGn", center=0, annot=True, fmt=".1f", 
                    cbar=False, linewidths=0.5, linecolor=grid_color)
        
        ax.set_title(f"{ticker} - Monthly Returns (%)", fontsize=16, color=text_color, fontweight='bold')
        ax.tick_params(axis='x', colors=text_color, labelsize=10)
        ax.tick_params(axis='y', colors=text_color, labelsize=10)
        ax.set_ylabel("Year", color=text_color, fontsize=12)
        ax.set_xlabel("Month", color=text_color, fontsize=12)

    def _plot_price_chart(self, ax, ticker, history_df, scenarios, forecast_2026=None, theme='dark'):
        # Colors
        text_color = 'black' if theme == 'light' else 'white'
        bg_color = 'white' if theme == 'light' else '#121212'
        grid_color = 'gray' if theme == 'light' else 'gray'
        price_color = '#1f77b4' if theme == 'light' else '#00E5FF' # Standard Blue vs Cyan
        legend_bg = 'white' if theme == 'light' else '#1E1E1E'
        legend_edge = 'gray' if theme == 'light' else 'white'
        
        # Filter last 6 months for clarity
        df = history_df.tail(126).copy()
        if df.empty:
            ax.text(0.5, 0.5, "No recent price data", ha='center', va='center', color=text_color)
            return

        ax.plot(df.index, df['Close'], color=price_color, linewidth=2, label='Price')
        
        # Configure Axis
        ax.set_facecolor(bg_color)
        ax.tick_params(colors=text_color)
        for spine in ax.spines.values():
            spine.set_color(text_color)

        # Determine projection dates
        try:
            last_date = df.index[-1]
        except Exception:
            last_date = pd.Timestamp.now()
        next_date = last_date + pd.Timedelta(days=30)  # Visual projection

        # Safely get scenario targets
        bull = scenarios.get('bull_target') if isinstance(scenarios, dict) else None
        bear = scenarios.get('bear_target') if isinstance(scenarios, dict) else None
        neutral = scenarios.get('neutral_range') if isinstance(scenarios, dict) else None

        if bull is not None:
            ax.hlines(bull, last_date, next_date, colors='#008000', linestyles='dashed', label='Bull Target') # Darker green
            ax.text(next_date, bull, f" Bull: {bull:.0f}", color='#008000', va='center')

        if bear is not None:
            ax.hlines(bear, last_date, next_date, colors='#FF0000', linestyles='dashed', label='Bear Target')
            ax.text(next_date, bear, f" Bear: {bear:.0f}", color='#FF0000', va='center')

        # Neutral Range (Shaded)
        if neutral and len(neutral) >= 2:
            ax.fill_between([last_date, next_date], neutral[0], neutral[1], color='#FFD700', alpha=0.1, label='Neutral Zone') # Gold

        ax.set_title(f"{ticker} - Price Action & Scenarios", fontsize=16, color=text_color, fontweight='bold')
        ax.legend(loc='upper left', facecolor=legend_bg, edgecolor=legend_edge, labelcolor=text_color)
        ax.grid(True, linestyle='--', alpha=0.3, color=grid_color)

        # --- 2026 Prediction Overlay ---
        if forecast_2026:
            target_date = forecast_2026['target_date']
            
            # Ensure timezone compatibility for plotting
            if last_date.tz is not None and target_date.tz is None:
                target_date = target_date.tz_localize(last_date.tz)
            elif last_date.tz is None and target_date.tz is not None:
                target_date = target_date.tz_localize(None)

            # Plot connection lines (dotted) from last price to targets
            
            # Trend (Blue)
            trend_color = '#3b82f6' # Blue
            cagr_color = '#8b5cf6' # Purple
            
            ax.plot([last_date, target_date], [df['Close'].iloc[-1], forecast_2026['models']['Trend (Linear Reg)']], 
                    color=trend_color, linestyle=':', label='Trend Prediction')
            
            # CAGR (Purple)
            ax.plot([last_date, target_date], [df['Close'].iloc[-1], forecast_2026['models']['CAGR (Growth)']], 
                    color=cagr_color, linestyle=':', label=f"CAGR ({forecast_2026['cagr_percent']:.1f}%)")
            
            # Consensus Target (Star)
            consensus = forecast_2026['consensus_target']
            ax.scatter([target_date], [consensus], color='#f59e0b', s=100, marker='*', zorder=10, label=f"2026 Target: {consensus:.0f}")
            
            # Target Zone (Shaded vertical area at end)
            ax.errorbar([target_date], [consensus], 
                        yerr=[[consensus - forecast_2026['range_low']], [forecast_2026['range_high'] - consensus]], 
                        color='#f59e0b', capsize=5, elinewidth=2)
            
            # Update legend to include new items
            ax.legend(loc='upper left', facecolor=legend_bg, edgecolor=legend_edge, fontsize=8, labelcolor=text_color)

    def _plot_oi_chart(self, ax, oi_data):
        if not oi_data or not isinstance(oi_data, dict):
            ax.text(0.5, 0.5, "No OI Data Available", ha='center', va='center', color='white')
            return

        strikes = oi_data.get('strikes', []) or []
        ce_ois = oi_data.get('ce_ois', []) or []
        pe_ois = oi_data.get('pe_ois', []) or []

        if len(strikes) == 0:
            ax.text(0.5, 0.5, "No strike data available", ha='center', va='center', color='white')
            return

        # Filter to show only relevant strikes (near ATM)
        mid_idx = len(strikes) // 2
        start = max(0, mid_idx - 10)
        end = min(len(strikes), mid_idx + 10)

        subset_strikes = strikes[start:end]
        subset_ce = ce_ois[start:end]
        subset_pe = pe_ois[start:end]

        if not subset_strikes:
            ax.text(0.5, 0.5, "No nearby strike data", ha='center', va='center', color='white')
            return

        x = range(len(subset_strikes))

        ax.bar(x, subset_ce, width=0.4, label='Call OI (Res)', color='#FF5252', align='center')
        ax.bar(x, subset_pe, width=0.4, label='Put OI (Sup)', color='#69F0AE', align='edge')

        ax.set_xticks(x)
        ax.set_xticklabels(subset_strikes, rotation=45)
        expiry = oi_data.get('expiry', 'N/A')
        ax.set_title(f"Open Interest Distribution (Expiry: {expiry})", fontsize=14, color='white')
        ax.legend(facecolor='#1E1E1E')

    def _plot_metrics(self, ax, oi_data, scenarios):
        ax.axis('off')
        
        # Create a display
        metrics = [
            ("PCR (Put-Call Ratio)", f"{oi_data.get('pcr', 'N/A')}", "#FFFFFF"),
            ("Max Pain Strike", f"{oi_data.get('max_pain', 'N/A')}", "#FFFF00"),
            ("Support (Max Put OI)", f"{oi_data.get('support_strike', 'N/A')}", "#69F0AE"),
            ("Resistance (Max Call OI)", f"{oi_data.get('resistance_strike', 'N/A')}", "#FF5252"),
            ("Expected Move (Monthly)", f"±{scenarios.get('expected_move', 0):.2f}", "#00E5FF")
        ]
        
        # Draw horizontally roughly
        x_start = 0.1
        for label, value, color in metrics:
            ax.text(x_start, 0.6, label, color='gray', fontsize=12, ha='left')
            ax.text(x_start, 0.3, value, color=color, fontsize=16, fontweight='bold', ha='left')
            x_start += 0.25
        


if __name__ == "__main__":
    pass
