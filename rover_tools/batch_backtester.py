
import pandas as pd
import json
import time
import os
from datetime import datetime
from market_data import MarketDataFetcher
from market_analytics import MarketAnalyzer
from ticker_resources import get_common_tickers

# Configuration
OUTPUT_FILE = "data/backtest_registry.json"
SUMMARY_FILE = "backtest_summary.md"
DELAY_SECONDS = 2 # To avoid rate limits

def generate_markdown_report(results_map, updated_count, failed_count):
    """
    Generates a markdown summary of the backtest results.
    """
    report_date = datetime.now().strftime("%d %b %Y")
    
    # Convert map to list for sorting
    results_list = []
    for ticker, data in results_map.items():
        # Filter for only recently updated items (today)
        if data.get("last_updated") == datetime.now().strftime("%Y-%m-%d"):
            data["ticker"] = ticker
            # Calculate a combined error score for sorting
            data["error_score"] = min(data["median_error"], data["sd_error"])
            results_list.append(data)
            
    # Sort by error score (lower is better)
    results_list.sort(key=lambda x: x["error_score"])
    
    md = f"# 🧪 Weekly Strategy Backtest Report\n"
    md += f"**Date:** {report_date}\n\n"
    md += f"- **Strategies Tested:** {updated_count}\n"
    md += f"- **Failures:** {failed_count}\n\n"
    
    md += "## 🏆 Top Performers (Lowest Error)\n"
    if results_list:
        md += "| Ticker | Strategy | Error % | Tested |\n"
        md += "|--------|----------|---------|--------|\n"
        for item in results_list[:5]:
            md += f"| {item['ticker']} | {item['winner'].upper()} | {item['error_score']}% | {item['years_tested']}y |\n"
    else:
        md += "No updates found for this run.\n"

    md += "\n## 📉 Least Accurate (High Error)\n"
    if results_list:
        md += "| Ticker | Strategy | Error % | Tested |\n"
        md += "|--------|----------|---------|--------|\n"
        for item in results_list[-5:][::-1]: # Show worst 5
             md += f"| {item['ticker']} | {item['winner'].upper()} | {item['error_score']}% | {item['years_tested']}y |\n"

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write(md)
    
    print(f"Summary report generated: {SUMMARY_FILE}")

def run_batch_backtest():
    """
    Runs backtest on all common tickers and saves results to a JSON registry.
    """
    print("🚀 Starting Weekly Batch Backtest...")
    
    fetcher = MarketDataFetcher()
    analyzer = MarketAnalyzer()
    tickers = get_common_tickers()
    
    # Load existing registry if exists to preserve old data
    registry = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r') as f:
                registry = json.load(f)
        except:
            pass
            
    results_map = registry.get("results", {})
    
    updated_count = 0
    failed_count = 0
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    total = len(tickers)
    
    for i, full_ticker in enumerate(tickers):
        # Format: "SBIN.NS - State Bank..."
        ticker = full_ticker.split(' - ')[0]
        print(f"[{i+1}/{total}] Analyzing {ticker}...")
        
        try:
            # Fetch Data
            history = fetcher.fetch_full_history(ticker)
            
            if history.empty:
                print(f"  ❌ No data for {ticker}")
                failed_count += 1
                continue
                
            # Run Backtest
            backtest_res = analyzer.backtest_strategies(history)
            
            # Store simplified result
            results_map[ticker] = {
                "winner": backtest_res["winner"],
                "median_error": round(backtest_res["median_avg_error"], 2),
                "sd_error": round(backtest_res["sd_avg_error"], 2),
                "years_tested": backtest_res["years_tested"],
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
            
            updated_count += 1
            print(f"  ✅ Winner: {backtest_res['winner'].upper()} (Err: {min(backtest_res['median_avg_error'], backtest_res['sd_avg_error']):.1f}%)")
            
        except Exception as e:
            print(f"  ⚠️ Error processing {ticker}: {e}")
            failed_count += 1
            
        # Rate limit
        time.sleep(DELAY_SECONDS)
        
    # Save Registry
    registry["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    registry["results"] = results_map
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(registry, f, indent=4)
        
    print(f"\n🎉 Batch Backtest Complete. Updated: {updated_count}, Failed: {failed_count}")
    print(f"Results saved to {OUTPUT_FILE}")
    
    generate_markdown_report(results_map, updated_count, failed_count)

if __name__ == "__main__":
    run_batch_backtest()
