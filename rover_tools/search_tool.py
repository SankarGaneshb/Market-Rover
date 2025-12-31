"""
Search Tool - Enables the agent to search the web for real-time market events.
Uses duckduckgo_search directly to avoid LangChain wrapper issues.
"""
from duckduckgo_search import DDGS
from crewai.tools import tool
from utils.logger import get_logger
from utils.metrics import track_error_detail

logger = get_logger(__name__)

@tool("Search Market News")
def search_market_news(query: str) -> str:
    """
    Search the web for real-time market news, macro events, or specific queries.
    Useful for finding information about strikes, weather impacts, policy changes, 
    or global events that might affect the market.
    
    Args:
        query: The search query string (e.g., "Impact of fog on Indian aviation stocks")
        
    Returns:
        A summary of the top search results.
    """
    try:
        logger.info(f"Searching web for: {query}")
        
        # Use DDGS directly
        results = []
        with DDGS() as ddgs:
            # text() returns generator of results
            # max_results limits the number
            search_gen = ddgs.text(query, max_results=5)
            for r in search_gen:
                results.append(r)
        
        if not results:
            return f"No search results found for: {query}"
            
        output = f"Search Results for '{query}':\n\n"
        for i, res in enumerate(results, 1):
            title = res.get('title', 'No Title')
            body = res.get('body', 'No Description')
            link = res.get('href', '')
            output += f"{i}. {title}\n   {body}\n   Source: {link}\n\n"
            
        return output
        
    except Exception as e:
        logger.error(f"Search failed for query '{query}': {e}")
        try:
            track_error_detail(type(e).__name__, str(e), context={"function": "search_market_news", "query": query})
        except Exception:
            pass
        return f"Error performing search: {str(e)}"
