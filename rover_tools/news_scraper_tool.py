"""
News Scraper Tool - Scrapes news from Moneycontrol using Newspaper3k.
Supports both General Market News (Macro) and Specific Stock News (Micro).
"""
import requests
from newspaper import Article
from datetime import datetime, timedelta
from typing import List, Dict
from crewai.tools import tool
from config import LOOKBACK_DAYS, MONEYCONTROL_BASE_URL
import time
from utils.logger import get_logger
from utils.metrics import track_error_detail

logger = get_logger(__name__)


@tool("Scrape General Market News")
def scrape_general_market_news(category: str = "business") -> str:
    """
    Scrapes top headlines from Moneycontrol's Business/Market/Economy sections.
    Useful for identifying broad market trends, policy changes, or macro events (e.g., Budget, Strikes).
    
    Args:
        category: 'business', 'economy', or 'markets' (default: 'business')
    
    Returns:
        Summary of top stories.
    """
    try:
        # Map category to URL suffix
        cat_map = {
            "business": "news/business",
            "economy": "news/economy",
            "markets": "news/market"
        }
        suffix = cat_map.get(category.lower(), "news/business")
        url = f"{MONEYCONTROL_BASE_URL}/{suffix}"
        
        logger.info(f"Scraping General Market News from: {url}")
        
        # Requests
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        except Exception as e:
            return f"Failed to connect to news source: {str(e)}"
            
        if response.status_code != 200:
            return f"Failed to fetch news (Status: {response.status_code})"

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract Headlines (logic specific to Moneycontrol structure)
        # Typically looking for h2/h3 tags in news list
        stories = []
        
        # Determine likely containers for news items
        # Moneycontrol usually puts main news in 'section_news_list' or similar
        # We'll use a generic approach: iterate all links, filtering for news-like patterns
        
        seen_urls = set()
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            title = link.get_text(strip=True)
            
            # Filter logic
            if (
                '/news/' in href 
                and len(title) > 20  # Avoid short links like "More"
                and href not in seen_urls
                and not 'moneycontrol.com' in title.lower() # Avoid navigational links
            ):
                seen_urls.add(href)
                stories.append(f"- {title}")
                if len(stories) >= 10: # Limit to top 10
                    break
        
        if not stories:
            return "No significant headlines found."
            
        return f"📰 **Top Market Headlines ({category})**:\n" + "\n".join(stories)

    except Exception as e:
        logger.error(f"General News Scrape failed: {e}")
        try:
            track_error_detail(type(e).__name__, str(e), context={"function": "scrape_general_market_news"})
        except Exception:
            pass
        return f"Error scraping general news: {str(e)}"


@tool("Scrape Stock Specific News")
def scrape_stock_news(symbol: str) -> str:
    """
    Scrapes recent news articles for a specific stock symbol from Moneycontrol.
    Uses Newspaper3k to extract content. Filters for last 7 days.
    
    Args:
        symbol: Stock symbol (e.g., RELIANCE.NS)
        
    Returns:
        Analysis-ready text of recent news articles.
    """
    try:
        # Calculate date threshold
        date_threshold = datetime.now() - timedelta(days=LOOKBACK_DAYS)
        
        # Clean symbol (remove .NS or .BO suffix)
        clean_symbol = symbol.replace('.NS', '').replace('.BO', '')
        
        # Search URLs to try
        search_queries = [
            f"{MONEYCONTROL_BASE_URL}/news/tags/{clean_symbol.lower()}.html",
            f"{MONEYCONTROL_BASE_URL}/stocksmarketsindia/stocks/{clean_symbol.lower()}/news",
        ]
        
        article_urls = []
        
        for url in search_queries:
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if '/news/' in href and href not in article_urls:
                            if not href.startswith('http'):
                                href = MONEYCONTROL_BASE_URL + href
                            article_urls.append(href)
                    
                    if len(article_urls) >= 10:
                        break
                        
            except Exception:
                continue
        
        if not article_urls:
            return f"No recent news found for {symbol}."
        
        # Scrape articles
        articles = []
        for url in article_urls[:5]: # Limit to 5 for speed
            try:
                article = Article(url)
                article.download()
                article.parse()
                
                pub_date = article.publish_date
                
                # Date Filter
                if pub_date:
                    if pub_date.replace(tzinfo=None) < date_threshold:
                        continue
                
                article_data = {
                    'title': article.title,
                    'summary': article.text[:300] if article.text else "No content",
                    'date': pub_date.strftime('%Y-%m-%d') if pub_date else "Recent"
                }
                articles.append(article_data)
                
                # Rate limit
                time.sleep(0.3)
                
            except Exception:
                continue
        
        if not articles:
            return f"No relevant news found for {symbol} in last {LOOKBACK_DAYS} days."
        
        output = f"Context: Found {len(articles)} articles for {symbol}:\n\n"
        for i, art in enumerate(articles, 1):
            output += f"{i}. {art['title']} ({art['date']})\n   {art['summary']}\n\n"
            
        return output
        
    except Exception as e:
        logger.error(f"Stock News Scrape failed for {symbol}: {e}")
        return f"Error scraping news for {symbol}: {str(e)}"
