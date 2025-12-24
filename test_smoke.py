
try:
    from tools.derivative_analysis import DerivativeAnalyzer
    print("Import Successful")
    analyzer = DerivativeAnalyzer()
    print("Instance Created")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
