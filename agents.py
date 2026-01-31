"""
Agent definitions for Market Rover system.
"""
from crewai import Agent
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

# Global LLM instance (cached inside proxy)


class GeminiLLMProxy:
    """Lightweight proxy to lazily initialize Gemini LLM on first use.

    This avoids import-time failures when `GOOGLE_API_KEY` or the
    Gemini client library is unavailable. The proxy exposes an `invoke`
    method that forwards calls to the real LLM instance.
    """

    def __init__(self):
        self._llm = None

    def _ensure(self):
        if self._llm is not None:
            return self._llm

        if not GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY not found in environment variables.")
            raise ValueError("GOOGLE_API_KEY not configured")

        # Defer imports until actually needed
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.callbacks import BaseCallbackHandler

            class MetricsCallbackHandler(BaseCallbackHandler):
                def on_llm_start(self, *args, **kwargs):
                    track_api_call("gemini", "generate")
                    logger.debug("Gemini API call started")

            os.environ.setdefault("GOOGLE_API_KEY", GOOGLE_API_KEY)

            self._llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.3,
                convert_system_message_to_human=True,
                callbacks=[MetricsCallbackHandler()],
            )
            logger.info("Gemini LLM initialized successfully")
            return self._llm
        except Exception as e:
            logger.exception("Failed to initialize Gemini LLM: %s", e)
            track_error("llm_initialization")
            raise

    def invoke(self, *args, **kwargs):
        llm = self._ensure()
        # Some LLM interfaces expose different method names; prefer `invoke` if present
        if hasattr(llm, "invoke"):
            return llm.invoke(*args, **kwargs)
        elif hasattr(llm, "generate"):
            return llm.generate(*args, **kwargs)
        else:
            raise RuntimeError("Underlying LLM object has no known call method")


# Public proxy instance used by tests and other modules. This keeps import_safe.
gemini_llm = GeminiLLMProxy()


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


