from nselib import derivatives
from datetime import datetime

print("--- Debugging nselib Date ---")

today = datetime.now().strftime("%d-%m-%Y")
print(f"Trying date: {today}")

try:
    data = derivatives.fii_derivatives_statistics(trade_date=today)
    print("Success with explicit date!")
    print(data.head())
except Exception as e:
    print(f"Error with today: {e}")
    
# Try a known past date (e.g., yesterday or last friday)
# Just hardcode a recent valid trading date to be sure
known_date = "26-12-2025" 
print(f"\nTrying known date: {known_date}")
try:
    data = derivatives.fii_derivatives_statistics(trade_date=known_date)
    print("Success with known date!")
    print(data.head())
except Exception as e:
    print(f"Error with known date: {e}")
