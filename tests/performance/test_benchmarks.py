
import pytest
from rover_tools.news_scraper_tool import scrape_stock_news  # Corrected path
from utils.metrics import PerformanceMonitor
import time

# We want to benchmark the REAL news scraper to see how slow it is.
# Note: This requires internet access and will hit the target site.

@pytest.mark.benchmark(group="news_fetching")
def test_fetch_news_latency_single(benchmark):
    """Benchmark fetching news for a single stock."""
    """Benchmark fetching news for a single stock."""
    # Using a stable, high-volume stock like RELIANCE
    # CrewAI tools must be called via .run() if they are Tool objects
    # Limit iterations since this hits the network
    result = benchmark.pedantic(scrape_stock_news.run, kwargs={"symbol": "RELIANCE"}, rounds=1, iterations=1)
    assert result is not None

@pytest.mark.benchmark(group="news_fetching")
def test_fetch_news_latency_batch(benchmark):
    """Benchmark fetching news for 3 stocks sequentially (simulating current state)."""
    tickers = ["RELIANCE", "TCS", "INFY"]
    
    def fetch_batch():
        results = {}
        with PerformanceMonitor().measure("benchmark_batch_fetch"):
            for t in tickers:
                results[t] = scrape_stock_news.run(symbol=t)
        return results

    results = benchmark.pedantic(fetch_batch, rounds=1, iterations=1)
    assert len(results) == 3
