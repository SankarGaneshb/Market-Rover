
import pandas as pd
import json
import time
import os
from datetime import datetime
from rover_tools.market_data import MarketDataFetcher
from rover_tools.market_analytics import MarketAnalyzer
from rover_tools.ticker_resources import get_common_tickers
from rover_tools.memory_tool import evaluate_pending_predictions

from utils.notifications import EmailManager

# Configuration
OUTPUT_FILE = "data/backtest_registry.json"
SUMMARY_FILE = "backtest_summary.md"
DELAY_SECONDS = 2 # To avoid rate limits

def generate_email_summary(results_map, updated_count, failed_count):
    """
    Generates an HTML summary for email.
    """
    if updated_count == 0 and failed_count == 0:
        return None
        
    report_date = datetime.now().strftime("%d %b %Y")
    
    # Sort results
    results_list = []
    for ticker, data in results_map.items():
        if data.get("last_updated") == datetime.now().strftime("%Y-%m-%d"):
            data["ticker"] = ticker
            data["error_score"] = min(data["median_error"], data["sd_error"])
            results_list.append(data)
            
    results_list.sort(key=lambda x: x["error_score"])
    
    top_performers_count = sum(1 for x in results_list if x['error_score'] < 10.0)
    high_error_count = sum(1 for x in results_list if x['error_score'] > 20.0)

    # Simple HTML Table
    html = f"<h2>Weekly Strategy Backtest Report ({report_date})</h2>"
    html += f"<p><b>Strategies Tested:</b> {updated_count} (across Nifty 50, Nifty Next 50, and Midcap)<br><b>Failures:</b> {failed_count}</p>"
    html += "<p><i><b>What does this mean?</b> We test 2 distinct strategies (Median vs SD) by predicting historical prices month-by-month. <b>Error %</b> represents how far off our mathematical prediction was from the actual stock price (lower is better).</i></p>"
    html += f"<p>✅ <b>Highly Predictable (< 10% Error):</b> {top_performers_count}<br>"
    html += f"⚠️ <b>Unpredictable (> 20% Error):</b> {high_error_count}</p>"
    
    if results_list:
        html += "<h3>🏆 Top 10 Most Predictable Stocks</h3>"
        html += "<table border='1' cellspacing='0' cellpadding='5' style='border-collapse: collapse;'>"
        html += "<tr style='background-color: #f2f2f2;'><th>Ticker</th><th>Strategy</th><th>Error %</th><th>Tested (Years)</th></tr>"
        
        for item in results_list[:10]: # Top 10
            html += f"<tr><td>{item['ticker']}</td><td>{item['winner'].upper()}</td><td>{item['error_score']}%</td><td>{len(item['years_tested'])}</td></tr>"
        html += "</table>"
        
    return html

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
    
    top_performers_count = sum(1 for x in results_list if x['error_score'] < 10.0)
    high_error_count = sum(1 for x in results_list if x['error_score'] > 20.0)

    md = f"# 🧪 Weekly Strategy Backtest Report\n"
    md += f"**Date:** {report_date}\n\n"
    md += "> **What does this mean?** We evaluated 2 distinct strategies (Median Return vs Standard Deviation) for each stock by predicting historical prices month-by-month. The **Error %** represents how far off the mathematical model's final prediction was from the *actual* historical stock price (lower is better).\n\n"
    md += f"- **Total Stocks Tested:** {updated_count} (across Nifty 50, Nifty Next 50, and Midcap)\n"
    md += f"- **Failures:** {failed_count}\n"
    md += f"- **Highly Predictable (< 10% Error):** {top_performers_count} stocks\n"
    md += f"- **Unpredictable (> 20% Error):** {high_error_count} stocks\n\n"
    
    md += "## 🏆 Top 5 Most Predictable Stocks (Lowest Error)\n"
    if results_list:
        md += "| Ticker | Strategy | Error % | Tested |\n"
        md += "|--------|----------|---------|--------|\n"
        for item in results_list[:5]:
            md += f"| {item['ticker']} | {item['winner'].upper()} | {item['error_score']}% | {len(item['years_tested'])}y |\n"
    else:
        md += "No updates found for this run.\n"

    md += "\n## 📉 Top 5 Least Accurate Stocks (High Error)\n"
    if results_list:
        md += "| Ticker | Strategy | Error % | Tested |\n"
        md += "|--------|----------|---------|--------|\n"
        for item in results_list[-5:][::-1]: # Show worst 5
             md += f"| {item['ticker']} | {item['winner'].upper()} | {item['error_score']}% | {len(item['years_tested'])}y |\n"

    md += "\n## 🔍 Month-by-Month Breakdown (Top 5 Predictable Stocks)\n"
    md += "Here is the exact mathematical prediction versus the actual recorded stock price for the most recent year tested.\n\n"
    
    for item in results_list[:5]:
        ticker = item['ticker']
        path = item.get('detailed_path', [])
        md += f"### {ticker} ({item['winner'].upper()} Strategy)\n"
        if not path:
             md += "_No detailed monthly data available._\n\n"
             continue
        md += "| Date | Predicted Price | Actual Price | Error % |\n"
        md += "|---|---|---|---|\n"
        for p in path:
            md += f"| {p['date']} | ₹{p['predicted_price']:.2f} | ₹{p['actual_price']:.2f} | {p['error_pct']:.2f}% |\n"
        md += "\n"

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write(md)
        
    os.makedirs("reports", exist_ok=True)
    archive_file = f"reports/backtest_summary_{datetime.now().strftime('%Y-%m-%d')}.md"
    import shutil
    shutil.copy(SUMMARY_FILE, archive_file)
    
    print(f"Summary report generated: {SUMMARY_FILE}")
    print(f"Archived to: {archive_file}")

def run_batch_backtest():
    """
    Runs backtest on all common tickers and saves results to a JSON registry.
    """
    print("🚀 Starting Weekly Batch Backtest...")
    
    import shutil
    fetcher = MarketDataFetcher()
    analyzer = MarketAnalyzer()
    tickers = get_common_tickers("Nifty 50")
    
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
            
            winner = backtest_res["winner"]
            latest_metrics = backtest_res.get("detailed_metrics", [{}])[0] if backtest_res.get("detailed_metrics") else {}
            detailed_path = latest_metrics.get(f"{winner}_path", [])
            
            # Store simplified result
            results_map[ticker] = {
                "winner": winner,
                "median_error": float(round(backtest_res["median_avg_error"], 2)),
                "sd_error": float(round(backtest_res["sd_avg_error"], 2)),
                "years_tested": backtest_res["years_tested"],
                "detailed_path": detailed_path,
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
    
    print("🧠 Evaluating Long-Term Memory (LTM) Outcomes...")
    evaluate_pending_predictions()
    
    # Send Email Notification
    email_body = generate_email_summary(results_map, updated_count, failed_count)
    if email_body:
        emailer = EmailManager()
        if emailer.is_configured():
            print("📧 Sending Email Report...")
            subject = f"Market-Rover Strategy Report: {datetime.now().strftime('%d %b %Y')}"
            emailer.send_email(subject, email_body, is_html=True)
        else:
            print("⚠️ Email not configured. Skipping notification.")

if __name__ == "__main__":
    run_batch_backtest()
