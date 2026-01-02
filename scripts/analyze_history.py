import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

METRICS_DIR = Path("metrics")

def analyze_history():
    print("📜 Historical Metrics Analysis")
    print("="*40)
    
    data = []
    
    # scan for metrics_YYYY-MM-DD.json
    for f in METRICS_DIR.glob("metrics_*.json"):
        # Skip the generic "metrics.json" if it exists, only want dated ones or handle logic
        if not f.name.startswith("metrics_20"): continue
        
        date_str = f.stem.replace("metrics_", "")
        try:
            with open(f, 'r') as fp:
                d = json.load(fp)
                row = {
                    "date": date_str,
                    "api_calls": d.get("api_calls", {}).get("total", 0),
                    "errors": d.get("errors", {}).get("total", 0),
                    "avg_latency": d.get("performance", {}).get("avg_duration", 0),
                    "analyses": d.get("performance", {}).get("total_analyses", 0)
                }
                data.append(row)
        except:
            pass

    if not data:
        print("No historical data found.")
        return

    df = pd.DataFrame(data).sort_values("date")
    print(df.to_string(index=False))
    
    print("\n💡 Insight:")
    print(f"- Total Recorded Days: {len(df)}")
    print(f"- Total Analyses Run: {df['analyses'].sum()}")
    print(f"- Total Errors Logged: {df['errors'].sum()}")

if __name__ == "__main__":
    analyze_history()
