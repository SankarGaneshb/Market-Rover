
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

def summarize_errors():
    metrics_dir = Path("metrics")
    if not metrics_dir.exists():
        print("Metrics directory not found.")
        return

    # target window: last 7 days
    today = datetime.now().date()
    start_date = today - timedelta(days=7)
    
    print(f"Analyzing errors from {start_date} to {today}...\n")
    
    error_files = sorted(metrics_dir.glob("errors_*.jsonl"))
    
    total_errors = 0
    error_counts = Counter()
    detailed_messages = []

    for file_path in error_files:
        # Extract date from filename errors_YYYY-MM-DD.jsonl
        try:
            date_str = file_path.stem.split('_')[1]
            file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
            
        if file_date < start_date:
            continue
            
        print(f"Reading {file_path.name}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    total_errors += 1
                    err_type = data.get("type", "Unknown")
                    err_msg = data.get("message", "No message")
                    
                    # Store for summary
                    error_counts[err_type] += 1
                    
                    # Keep track of unique recent errors
                    detailed_messages.append(f"[{date_str}] {err_type}: {err_msg}")
                    
                except json.JSONDecodeError:
                    continue

    print(f"\nTotal Errors Found: {total_errors}")
    print("\nError Types Breakdown:")
    for err_type, count in error_counts.most_common():
        print(f"  - {err_type}: {count}")
        
    print("\nRecent Error Detail Samples (Last 10):")
    for msg in detailed_messages[-10:]:
        print(f"  {msg}")

if __name__ == "__main__":
    summarize_errors()
