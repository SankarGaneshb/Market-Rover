
import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import sys

# Ensure root is in path to import rover_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rover_tools.shadow_tools import analyze_sector_flow

def generate_report():
    """
    Generates a daily market intelligence report.
    """
    indices = {
        "Nifty 50": "^NSEI",
        "Bank Nifty": "^NSEBANK",
        "Sensex": "^BSESN"
    }

    report_date = datetime.now().strftime("%d %b %Y")
    
    markdown_content = f"# 📊 Daily Market Intelligence Report\n"
    markdown_content += f"**Date:** {report_date}\n\n"
    
    markdown_content += "## 🌍 Market Overview\n"
    markdown_content += "| Index | Price | Change | % Change |\n"
    markdown_content += "|-------|-------|--------|----------|\n"

    trend_signal = "Neutral"
    nifty_change = 0

    for name, ticker in indices.items():
        try:
            stock = yf.Ticker(ticker)
            # Get latest data
            hist = stock.history(period="5d") # Fetch slightly more to ensure we get 2 days
            if len(hist) >= 2:
                close_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change = close_price - prev_close
                pct_change = (change / prev_close) * 100
                
                # Format direction
                icon = "🟢" if change >= 0 else "🔴"
                sign = "+" if change >= 0 else ""
                
                # Capture Nifty trend for later
                if name == "Nifty 50":
                    nifty_change = pct_change
                    if pct_change > 0.5:
                        trend_signal = "Bullish"
                    elif pct_change < -0.5:
                        trend_signal = "Bearish"
                    else:
                        trend_signal = "Sideways/Neutral"

                markdown_content += f"| {name} | {close_price:,.2f} | {sign}{change:,.2f} | {icon} {sign}{pct_change:.2f}% |\n"
            else:
                 markdown_content += f"| {name} | N/A | N/A | N/A |\n"

        except Exception as e:
            print(f"Error fetching {name}: {e}")
            markdown_content += f"| {name} | Error | Error | Error |\n"

    # --- Sector Rotation Section ---
    markdown_content += "\n## 🕸️ The Spider Web (Sector Rotation)\n"
    markdown_content += "Relative strength of major sectors to detect capital flow.\n\n"
    
    try:
        sector_df = analyze_sector_flow()
        if not sector_df.empty:
            markdown_content += "| Rank | Sector | Momentum Score | 1W % | 1M % |\n"
            markdown_content += "|------|--------|----------------|------|------|\n"
            
            # Show top 5
            for _, row in sector_df.head(5).iterrows():
                markdown_content += f"| {row['Rank']} | {row['Sector']} | {row['Momentum Score']:.2f} | {row['1W %']}% | {row['1M %']}% |\n"
        else:
            markdown_content += "Sector data unavailable.\n"
    except Exception as e:
        markdown_content += f"Error performing sector analysis: {e}\n"

    markdown_content += "\n## 💡 Key Insights\n"
    markdown_content += f"- **Market Trend**: Short-term trend appears **{trend_signal}** based on Nifty 50 performance.\n"
    markdown_content += "- **Sector Focus**: Analyze individual sector indices for rotation opportunities.\n"
    
    # Save to file
    with open("daily_report.md", "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    print("Report generated successfully: daily_report.md")

if __name__ == "__main__":
    generate_report()
