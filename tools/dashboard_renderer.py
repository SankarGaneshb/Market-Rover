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

    def generate_dashboard(self, ticker, history_df, oi_data, scenarios, returns_matrix):
        """
        Generates a composite dashboard image containing:
        1. Price Chart with Volatility Bands & Scenario Targets
        2. Monthly Returns Heatmap (Historical Performance)
        3. Open Interest Distribution (Support/Resistance)
        """
        # Ensure non-interactive backend for production safety
        plt.switch_backend('Agg')
        
        fig = plt.figure(figsize=(16, 14), constrained_layout=True)
        gs = fig.add_gridspec(3, 2, height_ratios=[1.5, 1.5, 1])

        # --- 1. Price Chart (Top Row, spans both cols) ---
        ax1 = fig.add_subplot(gs[0, :])
        self._plot_price_chart(ax1, ticker, history_df, scenarios)

        # --- 2. Monthly Returns Heatmap (Middle Row, spans both cols) ---
        ax2 = fig.add_subplot(gs[1, :])
        self._plot_monthly_heatmap(ax2, returns_matrix, ticker)

        # --- 3. OI Chart (Bottom Left) ---
        ax3 = fig.add_subplot(gs[2, 0])
        self._plot_oi_chart(ax3, oi_data)

        # --- 4. Key Metrics (Bottom Right) ---
        ax4 = fig.add_subplot(gs[2, 1])
        self._plot_metrics(ax4, oi_data, scenarios)

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

    def _plot_price_chart(self, ax, ticker, history_df, scenarios):
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

    def _plot_oi_chart(self, ax, oi_data):
        if not oi_data:
            ax.text(0.5, 0.5, "No OI Data Available", ha='center', va='center', color='white')
            return

        strikes = oi_data['strikes']
        ce_ois = oi_data['ce_ois']
        pe_ois = oi_data['pe_ois']

        # Filter to show only relevant strikes (near ATM)
        # Find index of max pain or ATM
        # Simple logic: take middle 20 strikes
        mid_idx = len(strikes) // 2
        start = max(0, mid_idx - 10)
        end = min(len(strikes), mid_idx + 10)
        
        subset_strikes = strikes[start:end]
        subset_ce = ce_ois[start:end]
        subset_pe = pe_ois[start:end]

        x = range(len(subset_strikes))
        
        ax.bar(x, subset_ce, width=0.4, label='Call OI (Res)', color='#FF5252', align='center')
        ax.bar(x, subset_pe, width=0.4, label='Put OI (Sup)', color='#69F0AE', align='edge')
        
        ax.set_xticks(x)
        ax.set_xticklabels(subset_strikes, rotation=45)
        ax.set_title(f"Open Interest Distribution (Expiry: {oi_data['expiry']})", fontsize=14, color='white')
        ax.legend(facecolor='#1E1E1E')

    def _plot_metrics(self, ax, oi_data, scenarios):
        ax.axis('off')
        
        # Create a table-like display
        metrics = [
            ("PCR (Put-Call Ratio)", f"{oi_data['pcr']}", "#FFFFFF"),
            ("Max Pain Strike", f"{oi_data['max_pain']}", "#FFFF00"),
            ("Support (Max Put OI)", f"{oi_data['support_strike']}", "#69F0AE"),
            ("Resistance (Max Call OI)", f"{oi_data['resistance_strike']}", "#FF5252"),
            ("Expected Move (Monthly)", f"±{scenarios['expected_move']:.2f}", "#00E5FF")
        ]
        
        y_start = 0.9
        for label, value, color in metrics:
            ax.text(0.1, y_start, label, color='gray', fontsize=12, ha='left')
            ax.text(0.9, y_start, value, color=color, fontsize=14, fontweight='bold', ha='right')
            y_start -= 0.15
        
        ax.text(0.5, 0.1, "Market Rover 3.0", color='#333333', fontsize=20, ha='center', fontweight='bold', alpha=0.5)

if __name__ == "__main__":
    pass
