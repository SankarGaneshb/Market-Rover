from rover_tools.analytics.win_rate import calculate_seasonality_win_rate
import datetime

print("Testing Category-Based Seasonality...")

curr_m = datetime.datetime.now().month

categories = ["Nifty 50", "Midcap"]

for cat in categories:
    print(f"\n--- Testing {cat} for Month {curr_m} ---")
    results = calculate_seasonality_win_rate(category=cat, target_month=curr_m, period="2y", top_n=3)
    
    if results:
        for res in results:
            print(f"[{cat}] {res['ticker']}: {res['win_rate']:.0f}% Win Rate")
    else:
        print(f"No results for {cat}")
