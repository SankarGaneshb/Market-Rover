
import sys
import os

# Ensure root is in path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

try:
    from rover_tools.batch_tools import batch_get_stock_data, batch_scrape_news, batch_detect_accumulation
    print("✅ Import successful")
    
    print("--- Testing Stock Data ---")
    res1 = batch_get_stock_data.run("RELIANCE.NS, TCS.NS")
    print(res1)
    
    print("--- Testing News ---")
    res2 = batch_scrape_news.run("RELIANCE.NS")
    print(res2[:200]) # Print first 200 chars
    
    print("--- Testing Shadow ---")
    res3 = batch_detect_accumulation.run("RELIANCE.NS")
    print(res3)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
