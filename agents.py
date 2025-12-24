"""
Agent definitions for Market Rover system.
"""
from crewai import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.portfolio_tool import read_portfolio
from tools.news_scraper_tool import scrape_moneycontrol_news
from tools.stock_data_tool import get_stock_data
from tools.market_context_tool import analyze_market_context
from tools.visualizer_tool import generate_market_snapshot
from config import MAX_ITERATIONS, GOOGLE_API_KEY
import os

# Import metrics tracking
from utils.metrics import track_api_call, track_error
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Global LLM instance (lazy initialized)
_gemini_llm_instance = None


def get_gemini_llm():
    """
    Get or create the Gemini LLM instance.
    Lazy loading to avoid import-time errors if API key is missing.
    """
    global _gemini_llm_instance
    
    if _gemini_llm_instance:
        return _gemini_llm_instance

    # Check API key only when LLM is actually requested
    if not GOOGLE_API_KEY:
        error_msg = "GOOGLE_API_KEY not found in environment variables. Please check your .env file or GitHub Secrets."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    
    try:
        from langchain_core.callbacks import BaseCallbackHandler
        
        class MetricsCallbackHandler(BaseCallbackHandler):
            """Track API calls for observability"""
            def on_llm_start(self, *args, **kwargs):
                track_api_call("gemini", "generate")
                logger.debug("Gemini API call started")
        
        _gemini_llm_instance = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            convert_system_message_to_human=True,
            callbacks=[MetricsCallbackHandler()]
        )
        logger.info("Gemini LLM initialized successfully")
        return _gemini_llm_instance
        
    except Exception as e:
        logger.error(f"Failed to initialize Gemini LLM: {e}")
        track_error("llm_initialization")
        raise


def create_portfolio_manager_agent():
    """
    Agent A: Portfolio Manager
    Responsible for retrieving and validating the user's stock portfolio.
    """
    return Agent(
        role="Portfolio Manager",
        goal="Retrieve and validate the user's stock portfolio from CSV file",
        backstory=(
            "You are an expert portfolio manager who meticulously tracks "
            "stock holdings. You ensure all stock symbols are properly formatted "
            "with NSE suffixes (.NS) and validate the data integrity."
        ),
        tools=[read_portfolio],
        verbose=True,
        max_iter=MAX_ITERATIONS,
        allow_delegation=False,
        llm=get_gemini_llm()
    )


def create_news_scraper_agent():
    """
    Agent B: News Scraper
    Uses Newspaper3k to scrape news from Moneycontrol for each stock.
    """
    return Agent(
        role="Financial News Researcher",
        goal="Scrape and collect recent news articles for stocks from Moneycontrol",
        backstory=(
            "You are a skilled financial journalist who knows how to find "
            "the most relevant news stories for stocks. You use Newspaper3k "
            "to scrape articles from Moneycontrol and filter for the last 7 days. "
            "You're thorough and always verify your sources."
        ),
        tools=[scrape_moneycontrol_news],
        verbose=True,
        max_iter=MAX_ITERATIONS,
        allow_delegation=False,
        llm=get_gemini_llm()
    )


def create_sentiment_analyzer_agent():
    """
    Agent C: Sentiment Analyzer
    Analyzes news sentiment and classifies as Positive, Negative, or Neutral.
    """
    return Agent(
        role="Sentiment Analysis Expert",
        goal="Analyze news articles and classify sentiment as Positive, Negative, or Neutral",
        backstory=(
            "You are a seasoned financial analyst with expertise in sentiment analysis. "
            "You read news articles and determine their impact on stock prices. "
            "You classify each article as Positive (bullish), Negative (bearish), "
            "or Neutral (no clear impact). When you're uncertain about the sentiment, "
            "you flag it for human review."
        ),
        tools=[],  # Uses LLM reasoning only
        verbose=True,
        max_iter=MAX_ITERATIONS,
        allow_delegation=False,
        llm=get_gemini_llm()
    )


def create_market_context_agent():
    """
    Agent D: Market Context Analyzer
    Analyzes Nifty 50 and sector trends for broader market context.
    """
    return Agent(
        role="Market Context Analyst",
        goal="Analyze Nifty 50, sector indices, and global market cues for context",
        backstory=(
            "You are a macro-level market analyst who understands how broader "
            "market trends affect individual stocks. You track Nifty 50, sectoral "
            "indices, and global cues to provide context for stock movements. "
            "You can identify whether the overall market is positive or negative."
        ),
        tools=[analyze_market_context, get_stock_data],
        verbose=True,
        max_iter=MAX_ITERATIONS,
        allow_delegation=False,
        llm=get_gemini_llm()
    )


def create_report_generator_agent():
    """
    Agent E: Report Generator
    Creates the final weekly intelligence report with risk highlights.
    """
    return Agent(
        role="Intelligence Report Writer",
        goal="Generate comprehensive weekly stock intelligence report with risk highlights",
        backstory=(
            "You are an expert financial report writer who creates clear, "
            "actionable intelligence briefings. You synthesize information from "
            "multiple sources into concise summaries. You highlight the three "
            "most important news stories affecting the portfolio and identify "
            "potential risks. All financial figures are presented in Crores "
            "for consistency. You include a 'Flag for Review' section for "
            "uncertain analyses."
        ),
        tools=[],  # Uses LLM reasoning to synthesize information
        verbose=True,
        max_iter=MAX_ITERATIONS,
        allow_delegation=False,
        llm=get_gemini_llm()
    )


# Agent factory for easy access
class AgentFactory:
    """Factory class to create all agents."""
    
    @staticmethod
    def create_all_agents():
        """Create all agents at once."""
        return {
            'portfolio_manager': create_portfolio_manager_agent(),
            'news_scraper': create_news_scraper_agent(),
            'sentiment_analyzer': create_sentiment_analyzer_agent(),
            'market_context': create_market_context_agent(),
            'report_generator': create_report_generator_agent(),
            'visualizer': create_visualizer_agent()
        }


def create_visualizer_agent():
    """
    Agent F: Visualizer Agent
    Generates high-fidelity market snapshots with derivative analysis.
    """
    return Agent(
        role="Market Data Visualizer",
        goal="Generate premium visual dashboards with quantitative derivative analysis",
        backstory=(
            "You are a specialized visualizer agent that turns complex market data "
            "into beautiful, easy-to-understand dashboards. You analyze Option Chain "
            "dynamics (PCR, Max Pain) and volatility to forecast price ranges. "
            "Your output is not just numbers, but a visual story of the market."
        ),
        tools=[generate_market_snapshot],
        verbose=True,
        max_iter=MAX_ITERATIONS,
        allow_delegation=False,
        llm=get_gemini_llm()
    )


