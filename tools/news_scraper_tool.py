"""
News Scraper Tool - Scrapes news from Moneycontrol using Newspaper3k.
"""
import requests
from newspaper import Article
from datetime import datetime, timedelta
from typing import List, Dict
from crewai.tools import tool
from config import LOOKBACK_DAYS, MONEYCONTROL_BASE_URL
import time


@tool("Moneycontrol News Scraper")
def scrape_moneycontrol_news(symbol: str, company_name: str = "") -> str:
    """
    Scrapes recent news articles from Moneycontrol for a given stock symbol.
    Uses Newspaper3k to extract article content, title, and publication date.
    Filters for news from the last 7 days.
    
    Args:
        symbol: Stock symbol (e.g., RELIANCE.NS)
        company_name: Company name (optional)
        
    Returns:
        String with formatted news articles
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
                    # Simple extraction of article links
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find article links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if '/news/' in href and href not in article_urls:
                            if not href.startswith('http'):
                                href = MONEYCONTROL_BASE_URL + href
                            article_urls.append(href)
                    
                    # Limit to first 10 articles
                    if len(article_urls) >= 10:
                        break
                        
            except Exception as e:
                continue
        
        if not article_urls:
            return f"No recent news found for {symbol} on Moneycontrol."
        
        # Scrape articles
        articles = []
        for url in article_urls[:10]:
            try:
                article = Article(url)
                article.download()
                article.parse()
                
                # Try to get publish date
                pub_date = article.publish_date
                
                article_data = {
                    'url': url,
                    'title': article.title,
                    'text': article.text[:500],
                    'publish_date': pub_date,
                    'summary': article.text[:200] if article.text else ""
                }
                
                if article_data['title']:
                    # Filter by date if available
                    if pub_date:
                        if pub_date.replace(tzinfo=None) >= date_threshold:
                            articles.append(article_data)
                    else:
                        # Include if date not available
                        articles.append(article_data)
                
                # Rate limiting
                time.sleep(0.5)
                
                # Stop if we have enough
                if len(articles) >= 5:
                    break
                    
            except Exception as e:
                continue
        
        if not articles:
            return f"No recent news (last {LOOKBACK_DAYS} days) found for {symbol}."
        
        # Format output
        output = f"Found {len(articles)} recent news article(s) for {symbol}:\n\n"
        
        for i, article in enumerate(articles, 1):
            output += f"{i}. {article['title']}\n"
            if article['publish_date']:
                output += f"   Date: {article['publish_date'].strftime('%Y-%m-%d')}\n"
            output += f"   Summary: {article['summary']}\n"
            output += f"   URL: {article['url']}\n\n"
        
        return output
        
    except Exception as e:
        return f"Error scraping news for {symbol}: {str(e)}"
