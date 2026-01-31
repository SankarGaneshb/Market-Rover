"""
News Scraper Tool - Scrapes news from Moneycontrol using Newspaper3k.
Supports both General Market News (Macro) and Specific Stock News (Micro).
Optimized with AsyncIO/AIOHTTP for parallel fetching.
"""
import requests
import asyncio
import aiohttp
from newspaper import Article
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from crewai.tools import tool
from config import LOOKBACK_DAYS, MONEYCONTROL_BASE_URL
import time
from utils.logger import get_logger
from utils.metrics import track_error_detail, track_performance, PerformanceMonitor
from bs4 import BeautifulSoup

logger = get_logger(__name__)

# Re-use the same session/headers for consistency? Requests uses Session better.
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


@tool("Scrape General Market News")
def scrape_general_market_news(category: str = "business") -> str:
    """
    Scrapes top headlines from Moneycontrol's Business/Market/Economy sections.
    """
    try:
        cat_map = {
            "business": "news/business",
            "economy": "news/economy",
            "markets": "news/market"
        }
        suffix = cat_map.get(category.lower(), "news/business")
        url = f"{MONEYCONTROL_BASE_URL}/{suffix}"
        
        logger.info(f"Scraping General Market News from: {url}")
        
        with PerformanceMonitor().measure("general_news_fetch"):
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
            except Exception as e:
                return f"Failed to connect to news source: {str(e)}"
            
            if response.status_code != 200:
                return f"Failed to fetch news (Status: {response.status_code})"

            soup = BeautifulSoup(response.content, 'html.parser')
            stories = []
            seen_urls = set()
            
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                title = link.get_text(strip=True)
                
                if (
                    '/news/' in href 
                    and len(title) > 20 
                    and href not in seen_urls
                    and not 'moneycontrol.com' in title.lower()
                ):
                    seen_urls.add(href)
                    stories.append(f"- {title}")
                    if len(stories) >= 10: 
                        break
            
            if not stories:
                return "No significant headlines found."
                
            return f"📰 **Top Market Headlines ({category})**:\n" + "\n".join(stories)

    except Exception as e:
        logger.error(f"General News Scrape failed: {e}")
        track_error_detail(type(e).__name__, str(e), context={"function": "scrape_general_market_news"})
        return f"Error scraping general news: {str(e)}"


# --- Async Helper Functions for Stock News ---

async def fetch_url(url: str) -> Optional[str]:
    """Async fetch of a single URL using requests in a thread (to bypass 403s)."""
    def blocking_fetch():
        try:
            response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Fetch failed for {url} with status {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Fetch failed for {url}: {e}")
            return None

    return await asyncio.to_thread(blocking_fetch)

async def extract_links_from_search(symbol: str) -> List[str]:
    """Fetches article links from search pages in parallel."""
    clean_symbol = symbol.replace('.NS', '').replace('.BO', '')
    search_queries = [
        f"{MONEYCONTROL_BASE_URL}/news/tags/{clean_symbol.lower()}.html",
        f"{MONEYCONTROL_BASE_URL}/stocksmarketsindia/stocks/{clean_symbol.lower()}/news",
    ]
    
    # Run fetches in parallel
    tasks = [fetch_url(url) for url in search_queries]
    pages = await asyncio.gather(*tasks)
    
    article_urls = []
    seen = set()
    
    for page_content in pages:
        if not page_content:
            continue
            
        soup = BeautifulSoup(page_content, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/news/' in href and href not in seen:
                if not href.startswith('http'):
                    href = MONEYCONTROL_BASE_URL + href
                seen.add(href)
                article_urls.append(href)
                if len(article_urls) >= 10:
                    break
        if len(article_urls) >= 10:
            break
            
    return article_urls

async def process_article(url: str, date_threshold: datetime) -> Optional[Dict]:
    """Downloads and parses a single article using Newspaper3k (Sync library running in thread)."""
    # Newspaper3k is synchronous. To keep async loop unblocked, we *could* run it in a thread,
    # but concurrent.futures within asyncio is a bit much.
    # For now, we will just call it. Since we are parallelizing the *main* steps, optimization is mixed.
    # HOWEVER, Newspaper3k does network I/O.
    # Better approach: Use aiohttp to fetch HTML, then pass to Newspaper3k just for parsing.
    
    try:
        # Hybrid approach: Use Article just for parsing if possible, or just let it download.
        # Given complexity, we'll wrap the blocking call in to_thread.
        
        def blocking_parse():
            try:
                article = Article(url)
                article.download()
                article.parse()
                return article
            except Exception:
                return None

        article = await asyncio.to_thread(blocking_parse)
        
        if not article:
            return None
            
        pub_date = article.publish_date
        if pub_date:
            if pub_date.replace(tzinfo=None) < date_threshold:
                return None
        
        return {
            'title': article.title,
            'summary': article.text[:300] if article.text else "No content",
            'date': pub_date.strftime('%Y-%m-%d') if pub_date else "Recent"
        }
    except Exception:
        return None

async def async_scrape_stock_run(symbol: str) -> str:
    """Main async logic for scraping stock news."""
    try:
        date_threshold = datetime.now() - timedelta(days=LOOKBACK_DAYS)
        
        # 1. Fetch Links (Parallel)
        article_urls = await extract_links_from_search(symbol)
        
        if not article_urls:
            return f"No recent news found for {symbol}."
        
        # 2. Fetch Articles (Parallel using threads)
        # Limit to 5 articles
        # process_article ALREADY uses to_thread internally, effectively.
        # But we previously defined process_article to take 'url' and use Article.
        # We can just call it directly.
        
        tasks = [process_article(url, date_threshold) for url in article_urls[:5]]
        results = await asyncio.gather(*tasks)
        
        # Filter None
        articles = [r for r in results if r]
        
        if not articles:
            return f"No relevant news found for {symbol} in last {LOOKBACK_DAYS} days."
        
        output = f"Context: Found {len(articles)} articles for {symbol}:\n\n"
        for i, art in enumerate(articles, 1):
            output += f"{i}. {art['title']} ({art['date']})\n   {art['summary']}\n\n"
            
        return output

    except Exception as e:
        logger.error(f"Async Stock News Scrape failed for {symbol}: {e}")
        return f"Error scraping news for {symbol}: {str(e)}"

# --- Tool Entry Point ---

@tool("Scrape Stock Specific News")
@track_performance(name_override="scrape_stock_news")
def scrape_stock_news(symbol: str) -> str:
    """
    Scrapes recent news articles for a specific stock symbol from Moneycontrol.
    Uses Newspaper3k to extract content. Filters for last 7 days.
    
    Args:
        symbol: Stock symbol (e.g., RELIANCE.NS)
        
    Returns:
        Analysis-ready text of recent news articles.
    """
    # Create a new event loop for this thread if strictly necessary, 
    # but asyncio.run() creates one.
    try:
        return asyncio.run(async_scrape_stock_run(symbol))
    except RuntimeError:
        # If loop is already running (e.g. inside another async env), we need to handle it.
        # Streamlit doesn't run a loop by default in the script thread.
        # But if we are called from an Executor, it's fine.
        # Fallback: Just create a loop.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(async_scrape_stock_run(symbol))
