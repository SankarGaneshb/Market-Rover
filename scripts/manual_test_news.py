
from rover_tools.news_scraper_tool import scrape_stock_news
import time
import aiohttp
import asyncio

async def test_conn():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.google.com") as resp:
            print(f"Conn Check status: {resp.status}")

import requests
def test_requests_conn():
    url = "https://www.moneycontrol.com/news/tags/reliance.html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Requests Check status: {resp.status_code}")

try:
    test_requests_conn()
    asyncio.run(test_conn())
except Exception as e:
    print(f"Conn Code Failed: {e}")

print("Starting test...")
start = time.time()
try:
    result = scrape_stock_news.run(symbol="RELIANCE")
    print(f"Result length: {len(result)}")
    print("Content preview:", result[:100])
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()

end = time.time()
print(f"Finished in {end - start:.2f} seconds")
