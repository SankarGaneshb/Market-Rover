import sys
import os
import time
# Add root to path
sys.path.append(os.getcwd())

from utils.metrics import track_workflow_start, track_workflow_end, track_workflow_event
from scripts.generate_process_report import generate_report

print("🧪 Starting verification test...")

# 1. Start Session
print("\nStep 1: Starting 'test-verification' workflow...")
session_id = track_workflow_start("test-verification")
print(f"Session ID: {session_id}")

# 2. Log Event
print("\nStep 2: Logging 'flexibility_protocol' event...")
track_workflow_event("flexibility_protocol", "Testing explicit trade-off verification")

# 3. Wait (simulated work)
time.sleep(0.1)

# 4. Stop Session
print("\nStep 3: Stopping session...")
track_workflow_end(session_id, "success")

# 5. Generate Report
print("\nStep 4: Running Report Generator...")
generate_report()

print("\n✅ Verification Complete.")
