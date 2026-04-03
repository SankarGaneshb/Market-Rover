import asyncio
from rover_tools.news_scraper_tool import scrape_stock_news

def test_scrape():
    symbol = "RELIANCE.NS"
    print(f"Testing scrape for {symbol}...")
    # The tool is a CrewAI Tool object, call its .run method
    result = scrape_stock_news.run(symbol)
    print("\n--- Scrape Result ---")
    print(result)
    print("--- End Result ---")

if __name__ == "__main__":
    test_scrape()
