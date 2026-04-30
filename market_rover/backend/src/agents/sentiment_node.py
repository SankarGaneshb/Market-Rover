import os
import asyncio
import yfinance as yf
from src.state import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def get_ticker_sentiment(ticker: str):
    """Fetches and analyzes sentiment for a single ticker in a thread."""
    try:
        # Wrap synchronous yfinance call in to_thread
        stock = yf.Ticker(ticker)
        news = await asyncio.to_thread(lambda: stock.news)

        # Simple keyword-based sentiment on recent headlines
        headlines = [n.get('title', '') for n in news[:5]]
        bullish_keywords = ['gain', 'buy', 'growth', 'positive', 'surge', 'high', 'profit', 'expansion']
        bearish_keywords = ['fall', 'loss', 'sell', 'warning', 'decline', 'low', 'debt', 'cut']

        score = 0
        for h in headlines:
            for w in bullish_keywords:
                if w in h.lower(): score += 1
            for w in bearish_keywords:
                if w in h.lower(): score -= 1

        final_sentiment = "neutral"
        if score > 0:
            final_sentiment = "positive"
        elif score < 0:
            final_sentiment = "negative"

        return {
            "ticker": ticker,
            "sentiment": final_sentiment,
            "news_count": len(news),
            "summary": headlines[0] if headlines else "No recent news."
        }
    except Exception as e:
        logger.error(f"Sentiment error for {ticker}: {e}")
        return {"ticker": ticker, "sentiment": "Data Unavailable"}

async def sentiment_node(state: AgentState) -> dict:
    """
    Node: Sentiment Analysis (Parallel)
    Classifies news as Fear/Greed. Identifies hype clusters.
    """
    logger.info("Executing Sentiment Node (Async/Parallel)...")
    tickers = state.get("tickers", [])

    if not tickers:
        return {"sentiment_data": [], "current_node": "sentiment"}

    # Run all ticker sentiment checks in parallel
    results = await asyncio.gather(*[get_ticker_sentiment(t) for t in tickers])

    bullish_count = sum(1 for r in results if r.get("sentiment") == "positive")
    celebrations = []

    # Interactive UX Trigger: Bullish Consensus
    if len(tickers) > 0 and (bullish_count / len(tickers)) >= 0.7:
        celebrations.append({
            "type": "CROWD_CHEER",
            "message": "SENTIMENT ALERT: 70%+ of your portfolio has a Strong Bullish Consensus! Institutional absorption likely.",
            "context": "sentiment_bullish_cluster"
        })

    return {
        "sentiment_data": results,
        "celebrations": celebrations,
        "current_node": "sentiment"
    }
