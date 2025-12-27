
try:
    from rover_tools.market_analytics import MarketAnalyzer
    print("Import Successful")
    analyzer = MarketAnalyzer()
    print("Instance Created")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
