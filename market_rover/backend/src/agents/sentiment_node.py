import os
from src.state import AgentState
from rover_tools.advanced_skills import analyze_retail_sentiment_tool
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def sentiment_node(state: AgentState) -> dict:
    """
    Node: Sentiment Analysis (Parallel)
    Classifies news as Fear/Greed. Identifies hype clusters.
    """
    logger.info("Executing Sentiment Node...")
    tickers = state.get("tickers", [])
    regime = state.get("regime", "NEUTRAL")

    results = []
    celebrations = []

    bullish_count = 0
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            news = stock.news

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
                bullish_count += 1
            elif score < 0:
                final_sentiment = "negative"

            results.append({
                "ticker": ticker,
                "sentiment": final_sentiment,
                "news_count": len(news),
                "summary": headlines[0] if headlines else "No recent news."
            })
        except:
            results.append({"ticker": ticker, "sentiment": "Data Unavailable"})

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
