from rover_tools.analytics.win_rate import calculate_seasonality_win_rate
import datetime

print("Testing Expanded Seasonality Logic...")

# Test Current Month
curr_m = datetime.datetime.now().month
print(f"\n--- Testing Current Month ({curr_m}) ---")
results = calculate_seasonality_win_rate(target_month=curr_m, period="2y", top_n=3)
if results:
    for res in results:
        print(f"{res['ticker']}: {res['win_rate']:.0f}%")
else:
    print("No results for current month.")

# Test Next Month (Rollover Logic Check)
if curr_m == 12:
    next_m = 1
else:
    next_m = curr_m + 1
    
print(f"\n--- Testing Next Month ({next_m}) ---")
results_next = calculate_seasonality_win_rate(target_month=next_m, period="2y", top_n=3)
if results_next:
    for res in results_next:
         print(f"{res['ticker']}: {res['win_rate']:.0f}%")
else:
    print("No results for next month.")
