import sys
import os
from pathlib import Path

# Fix path to allow importing from rover_tools
sys.path.append(str(Path(__file__).parent.parent))

from rover_tools.shadow_tools import fetch_block_deals, get_trap_indicator

print("--- Verifying Real Shadow Data Integration ---")

print("\n1. Fetching Block Deals (Live via nselib)...")
deals = fetch_block_deals()
if deals:
    print(f"✅ Success! Found {len(deals)} recent deals.")
    print("Sample:", deals[0])
else:
    print("⚠️ No deals found (Market might be closed or API issue).")

print("\n2. Fetching FII Trap Indicator (Live via nselib)...")
trap = get_trap_indicator()
print("Trap Result:", trap)

if trap['status'] != "Error":
    print("✅ Trap Indicator Logic Working.")
else:
    print(f"❌ Trap Indicator Failed. Message: {trap['message']}")
