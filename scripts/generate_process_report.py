"""
Generate Process Metrics Report
Analyzes workflow sessions and events to calculate cycle time and stability scores.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

METRICS_DIR = Path("metrics")

def load_jsonl(filename_pattern):
    data = []
    for file_path in METRICS_DIR.glob(filename_pattern):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except:
                    continue
    return pd.DataFrame(data)

def generate_report():
    print("📊 Market-Rover Process Report")
    print("="*40)

    # 1. Load Data
    df_events = load_jsonl("workflow_events_*.jsonl")
    
    if df_events.empty:
        print("No workflow data found.")
        return

    # 2. Separate Sessions and Point Events
    # Sessions are defined by 'start' and 'end' types in the log
    df_starts = df_events[df_events['type'] == 'start'].set_index('session_id')
    df_ends = df_events[df_events['type'] == 'end'].set_index('session_id')
    df_point_events = df_events[df_events['type'] == 'event']

    # 3. Calculate Cycle Time
    if not df_starts.empty and not df_ends.empty:
        # Join on session_id
        df_sessions = df_starts.join(df_ends, lsuffix='_start', rsuffix='_end')
        
        # Filter completed sessions
        df_completed = df_sessions.dropna(subset=['ts_end'])
        
        # Calculate Duration
        df_completed['duration_minutes'] = (
            pd.to_datetime(df_completed['ts_end']) - pd.to_datetime(df_completed['ts_start'])
        ).dt.total_seconds() / 60

        print(f"\n⏱️ Cycle Time Analysis ({len(df_completed)} sessions)")
        print("-" * 30)
        print(df_completed.groupby('workflow_start')['duration_minutes'].describe()[['count', 'mean', 'min', 'max']])

    # 4. Event Analysis (Flexibility & Stability)
    print("\n🛡️ Stability & Flexibility")
    print("-" * 30)
    
    if not df_point_events.empty:
        event_counts = df_point_events['event_name'].value_counts()
        print(event_counts)
        
        # Special callout for Emergency Overrides
        overrides = len(df_point_events[df_point_events['event_name'] == 'emergency_override'])
        print(f"\n🔥 Emergency Overrides: {overrides}")
    else:
        print("No exceptions or overrides recorded.")

if __name__ == "__main__":
    generate_report()
