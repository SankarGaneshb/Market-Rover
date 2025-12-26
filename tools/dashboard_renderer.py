import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import io
from PIL import Image

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
        gs = fig.add_gridspec(3, 1, height_ratios=[1.5, 1.5, 0.5])

        # --- 1. Price Chart (Top Row) ---
        ax1 = fig.add_subplot(gs[0])
        self._plot_price_chart(ax1, ticker, history_df, scenarios, forecast_2026)

        # --- 2. Monthly Returns Heatmap (Middle Row) ---
        ax2 = fig.add_subplot(gs[1])
        self._plot_monthly_heatmap(ax2, returns_matrix, ticker)

        # --- 3. Key Metrics (Bottom Row) ---
        ax3 = fig.add_subplot(gs[2])
        self._plot_metrics(ax3, scenarios)

        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#000000')
        buf.seek(0)
        plt.close(fig)
        
        return buf

    def _plot_monthly_heatmap(self, ax, returns_matrix, ticker):
        if returns_matrix.empty:
            ax.text(0.5, 0.5, "No Historical Data Available", ha='center', va='center', color='white')
            return

        # Create heatmap
        sns.heatmap(returns_matrix, ax=ax, cmap="RdYlGn", center=0, annot=True, fmt=".1f", 
                    cbar=False, linewidths=0.5, linecolor='#121212')
        
        ax.set_title(f"{ticker} - Monthly Returns (%)", fontsize=16, color='white', fontweight='bold')
        ax.tick_params(axis='x', colors='white', labelsize=10)
        ax.tick_params(axis='y', colors='white', labelsize=10)
        ax.set_ylabel("Year", color='white', fontsize=12)
        ax.set_xlabel("Month", color='white', fontsize=12)

    def _plot_price_chart(self, ax, ticker, history_df, scenarios, forecast_2026=None):
        # Filter last 6 months for clarity
        df = history_df.tail(126).copy()
        
        ax.plot(df.index, df['Close'], color='#00E5FF', linewidth=2, label='Price')
        
        # Add Bollinger-like bands or Volatility Cone if we had future dates
        # For now, plot the scenario targets as horizontal lines extending from last date
        last_date = df.index[-1]
        next_date = last_date + pd.Timedelta(days=30) # Visual projection
        
        # Bull Target
        ax.hlines(scenarios['bull_target'], last_date, next_date, colors='#00FF00', linestyles='dashed', label='Bull Target')
        ax.text(next_date, scenarios['bull_target'], f" Bull: {scenarios['bull_target']:.0f}", color='#00FF00', va='center')

        # Bear Target
        ax.hlines(scenarios['bear_target'], last_date, next_date, colors='#FF0000', linestyles='dashed', label='Bear Target')
        ax.text(next_date, scenarios['bear_target'], f" Bear: {scenarios['bear_target']:.0f}", color='#FF0000', va='center')

        # Neutral Range (Shaded)
        ax.fill_between([last_date, next_date], 
                        scenarios['neutral_range'][0], 
                        scenarios['neutral_range'][1], 
                        color='#FFFF00', alpha=0.1, label='Neutral Zone')

        ax.set_title(f"{ticker} - Price Action & Scenarios", fontsize=16, color='white', fontweight='bold')
        ax.legend(loc='upper left', facecolor='#1E1E1E', edgecolor='white')
        ax.grid(True, linestyle='--', alpha=0.3)

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
            ax.plot([last_date, target_date], [df['Close'].iloc[-1], forecast_2026['models']['Trend (Linear Reg)']], 
                    color='#3b82f6', linestyle=':', label='Trend Prediction')
            
            # CAGR (Purple)
            ax.plot([last_date, target_date], [df['Close'].iloc[-1], forecast_2026['models']['CAGR (Growth)']], 
                    color='#8b5cf6', linestyle=':', label=f"CAGR ({forecast_2026['cagr_percent']:.1f}%)")
            
            # Consensus Target (Star)
            consensus = forecast_2026['consensus_target']
            ax.scatter([target_date], [consensus], color='#f59e0b', s=100, marker='*', zorder=10, label=f"2026 Target: {consensus:.0f}")
            
            # Target Zone (Shaded vertical area at end)
            # We can't easily shade vertical efficiently on a time axis without correct limits,
            # but we can fill between the Low and High bounds at the target date
            ax.errorbar([target_date], [consensus], 
                        yerr=[[consensus - forecast_2026['range_low']], [forecast_2026['range_high'] - consensus]], 
                        color='#f59e0b', capsize=5, elinewidth=2)
            
            # Update legend to include new items
            ax.legend(loc='upper left', facecolor='#1E1E1E', edgecolor='white', fontsize=8)

    def _plot_metrics(self, ax, scenarios):
        ax.axis('off')
        
        # Create a display
        metrics = [
            ("Days Remaining", f"{scenarios.get('days_remaining', 30)}", "#FFFFFF"),
            ("Expected Move", f"±{scenarios['expected_move']:.2f}", "#00E5FF"),
            ("Bull Target", f"{scenarios['bull_target']:.2f}", "#69F0AE"),
            ("Bear Target", f"{scenarios['bear_target']:.2f}", "#FF5252"),
        ]
        
        # Draw horizontally roughly
        x_start = 0.1
        for label, value, color in metrics:
            ax.text(x_start, 0.6, label, color='gray', fontsize=12, ha='left')
            ax.text(x_start, 0.3, value, color=color, fontsize=16, fontweight='bold', ha='left')
            x_start += 0.25
        
        ax.text(0.5, 0.1, "Market Rover 4.1", color='#333333', fontsize=14, ha='center', fontweight='bold', alpha=0.5)

if __name__ == "__main__":
    pass
