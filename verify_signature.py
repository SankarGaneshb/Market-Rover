from rover_tools.analytics.portfolio import AnalyticsPortfolio
import inspect

print("Checking signature of suggest_rebalance...")
sig = inspect.signature(AnalyticsPortfolio.suggest_rebalance)
print(f"Signature: {sig}")

if 'mode' in sig.parameters:
    print("SUCCESS: 'mode' parameter found.")
else:
    print("FAILURE: 'mode' parameter NOT found.")

# Test call
ap = AnalyticsPortfolio()
try:
    ap.suggest_rebalance([], mode="growth")
    print("Call with mode='growth' successful.")
except TypeError as e:
    print(f"Call failed: {e}")
