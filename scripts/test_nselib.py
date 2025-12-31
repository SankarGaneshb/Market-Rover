from nselib import capital_market, derivatives

print("--- Testing nselib ---")

try:
    print("\n1. Fetching FII Derivatives Data...")
    # NOTE: nselib docs are sparse, usually get_fii_derivatives_turnover or similar
    # Using inspection or common known methods
    data = derivatives.fii_derivatives_statistics()
    print(data.head())
except Exception as e:
    print(f"FII Error: {e}")

try:
    print("\n2. Fetching Block Deals...")
    data = capital_market.block_deals_data(period='1M')
    print(data.head())
except Exception as e:
    print(f"Block Deal Error: {e}")
