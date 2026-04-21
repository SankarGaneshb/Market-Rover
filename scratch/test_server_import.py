import os
import sys

# Simulate the Docker environment
# Assume we are in /app/backend (which corresponds to market_rover/backend locally)
sys.path.append(os.path.abspath("market_rover/backend"))

try:
    from src.server import app
    print("[OK] Server imported successfully")
except Exception as e:
    print(f"[FAIL] Server import failed: {e}")
    import traceback
    traceback.print_exc()
