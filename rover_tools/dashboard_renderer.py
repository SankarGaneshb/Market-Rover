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

    def _plot_monthly_heatmap(self, ax, returns_matrix, ticker):
        if returns_matrix is None or (hasattr(returns_matrix, 'empty') and returns_matrix.empty):
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
        if df.empty:
            ax.text(0.5, 0.5, "No recent price data", ha='center', va='center', color='white')
            return

        ax.plot(df.index, df['Close'], color='#00E5FF', linewidth=2, label='Price')

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
            ax.hlines(bull, last_date, next_date, colors='#00FF00', linestyles='dashed', label='Bull Target')
            ax.text(next_date, bull, f" Bull: {bull:.0f}", color='#00FF00', va='center')

        if bear is not None:
            ax.hlines(bear, last_date, next_date, colors='#FF0000', linestyles='dashed', label='Bear Target')
            ax.text(next_date, bear, f" Bear: {bear:.0f}", color='#FF0000', va='center')

        # Neutral Range (Shaded)
        if neutral and len(neutral) >= 2:
            ax.fill_between([last_date, next_date], neutral[0], neutral[1], color='#FFFF00', alpha=0.1, label='Neutral Zone')

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
