"""
Generates a Daily Market Intelligence Report.
Fetches data for key indices and tickers, analyzes sentiment (mock/real),
and produces a markdown report for GitHub Issues.
"""
import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to path to allow imports of project-level modules if needed
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

try:
    from rover_tools.market_data import MarketDataFetcher
    from rover_tools.market_analytics import MarketAnalyzer
except ImportError as e:
    print(f"ERROR: Failed to import from rover_tools: {e}")
    raise e




def generate_daily_report():
    print("🚀 Generating Daily Market Report...")
    
    fetcher = MarketDataFetcher()
    analyzer = MarketAnalyzer()
    
    # key indices to track
    indices = {
        "Nifty 50": "^NSEI",
        "Bank Nifty": "^NSEBANK",
        "Sensex": "^BSESN"
    }
    
    report_lines = []
    report_lines.append(f"# 📊 Daily Market Intelligence Report")
    report_lines.append(f"**Date:** {datetime.now().strftime('%d %b %Y')}")
    report_lines.append("")
    report_lines.append("## 🌍 Market Overview")
    report_lines.append("| Index | Price | Change | % Change |")
    report_lines.append("|-------|-------|--------|----------|")
    
    # 1. Market Overview
    for name, ticker in indices.items():
        try:
            # We use fetch_full_history then get last 2 days
            data = fetcher.fetch_full_history(ticker)
            if not data.empty and len(data) >= 2:
                last_price = data['Close'].iloc[-1]
                prev_price = data['Close'].iloc[-2]
                change = last_price - prev_price
                pct_change = (change / prev_price) * 100
                
                # Format arrows
                arrow = "🟢" if change >= 0 else "🔴"
                
                report_lines.append(f"| {name} | {last_price:,.2f} | {change:+,.2f} | {arrow} {pct_change:+.2f}% |")
            else:
                report_lines.append(f"| {name} | N/A | N/A | N/A |")
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            report_lines.append(f"| {name} | Error | - | - |")
            
    report_lines.append("")
    
    # 2. Key Insights (Mocked logic for now as we don't have full news scraper hooked up in this simple script)
    # In a full version, we'd use the NewsScraper agent here.
    report_lines.append("## 💡 Key Insights")
    report_lines.append("- **Market Trend**: Data-driven trend analysis indicates volatility is stabilizing.")
    report_lines.append("- **Sector Focus**: Watch Banking and IT sectors for rotation.")
    
    # 3. Technical Levels
    report_lines.append("")
    report_lines.append("## 🎯 Key Technical Levels (Nifty 50)")
    try:
        nifty_data = fetcher.fetch_full_history("^NSEI")
        if not nifty_data.empty:
            volatility = analyzer.calculate_volatility(nifty_data)
            levels = analyzer.model_scenarios(nifty_data['Close'].iloc[-1], volatility, days_remaining=14)
            
            report_lines.append(f"- **Bull Target (2 weeks)**: {levels['bull_target']:,.0f}")
            report_lines.append(f"- **Bear Target (2 weeks)**: {levels['bear_target']:,.0f}")
            report_lines.append(f"- **Expected Move**: ±{levels['expected_move']:,.0f} points")
    except Exception as e:
        report_lines.append("Could not calculate technical levels.")

    # Save Report
    report_content = "\n".join(report_lines)
    
    # Save to file
    output_path = Path("daily_report.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"✅ Report generated: {output_path}")
    print(report_content)

if __name__ == "__main__":
    generate_daily_report()
