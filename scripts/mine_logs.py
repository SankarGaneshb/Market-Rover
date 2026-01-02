import re
from pathlib import Path
from collections import Counter
import json

LOG_FILE = Path("logs/market_rover.log")
OUTPUT_FILE = Path("metrics/historical_mined.json")

def mine_logs():
    print("⛏️ Mining Market-Rover Logs...")
    
    if not LOG_FILE.exists():
        print("Log file not found.")
        return

    # Patterns
    # 2025-12-27 18:25:04 | market_rover | INFO | ðŸš€ Starting Market-Rover...
    p_start = r"Starting Market-Rover"
    p_complete = r"Analysis Complete!"
    p_error = r"\| ERROR \|"
    
    stats = {
        "starts": 0,
        "completions": 0,
        "errors": 0,
        "dates": Counter()
    }
    
    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # Extract Date
            # 2025-12-27 ...
            date_match = re.match(r"^(\d{4}-\d{2}-\d{2})", line)
            if date_match:
                date = date_match.group(1)
                
                if re.search(p_start, line):
                    stats["starts"] += 1
                    stats["dates"][date] += 1
                elif re.search(p_complete, line):
                    stats["completions"] += 1
                elif re.search(p_error, line):
                    stats["errors"] += 1

    print("\n📊 Mined Results:")
    print(f"- Total Sessions Started: {stats['starts']}")
    print(f"- Total Completions: {stats['completions']}")
    print(f"- Total Errors (Logged): {stats['errors']}")
    
    if stats['starts'] > 0:
        success_rate = (stats['completions'] / stats['starts']) * 100
        print(f"- Approx. Success Rate: {success_rate:.1f}%")
        
    print("\n📅 Activity by Day:")
    for date, count in sorted(stats['dates'].items()):
        print(f"  {date}: {count} sessions")

    # Save for persistence
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(stats, f, indent=2)

if __name__ == "__main__":
    mine_logs()
