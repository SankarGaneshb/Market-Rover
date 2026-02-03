"""
Agent definitions for Market Rover system.

.. note::
    If you modify any agent roles or goals, please update `AI_AGENTS.md`.
"""
from crewai import Agent, LLM

from rover_tools.batch_tools import batch_scrape_news, batch_get_stock_data, batch_detect_accumulation
from rover_tools.portfolio_tool import read_portfolio
from rover_tools.news_scraper_tool import scrape_general_market_news
from rover_tools.search_tool import search_market_news
from rover_tools.global_market_tool import get_global_cues
from rover_tools.corporate_actions_tool import get_corporate_actions
from rover_tools.market_context_tool import analyze_market_context
from rover_tools.visualizer_tool import generate_market_snapshot
from config import MAX_ITERATIONS, GOOGLE_API_KEY
from rover_tools.shadow_tools import analyze_sector_flow_tool, fetch_block_deals_tool, get_trap_indicator_tool
from rover_tools.memory_tool import read_past_predictions_tool, save_prediction_tool
from rover_tools.autonomy_tools import announce_regime_tool, log_pivot_tool
from rover_tools.forensic_tool import check_accounting_fraud # NEW
from utils.logger import get_logger
from utils.metrics import track_error
import os

logger = get_logger(__name__)

# ... (existing imports)

# ...

# ... (existing imports)

# ...





_flash_llm = None
_pro_llm = None

def _create_llm(model_name: str, temp: float = 0.3):
    """Internal helper to create LLM instance."""
    if not GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY not found in environment variables.")
        raise ValueError("GOOGLE_API_KEY not found.")

    os.environ.setdefault("GOOGLE_API_KEY", GOOGLE_API_KEY)
    
    # CRITICAL: Unset OPENAI_API_KEY to prevent CrewAI from defaulting to GPT-4
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

    try:
        return LLM(
            model=f"gemini/{model_name}",
            temperature=temp,
            api_key=GOOGLE_API_KEY
        )
    except Exception as e:
        logger.error(f"Failed to initialize Gemini LLM ({model_name}): {e}")
        track_error("llm_initialization")
        raise

def get_flash_llm():
    """Create and cache the Gemini Flash LLM (Fast, Low Latency)."""
    global _flash_llm
    if _flash_llm is not None:
        return _flash_llm
    _flash_llm = _create_llm("gemini-1.5-flash-001")
    return _flash_llm

def get_pro_llm():
    """Create and cache the Gemini Pro LLM (Deep Reasoning)."""
    global _pro_llm
    if _pro_llm is not None:
        return _pro_llm
    # User specifically requested Gemini 3 Pro Preview
    _pro_llm = _create_llm("gemini-3-pro-preview")
    return _pro_llm

# Legacy accessor for compatibility (mapped to Pro for safety)
get_gemini_llm = get_pro_llm


def create_portfolio_manager_agent():
    """Agent A: Portfolio Manager (Low Complexity -> Flash)"""
    llm = get_flash_llm()
    return Agent(
        role="Portfolio Manager",
        goal="Read and process user's stock portfolio from CSV",
        backstory=(
            "You are an expert portfolio manager who meticulously tracks "
            "stock holdings. You ensure all stock symbols are properly formatted "
            "with NSE suffixes (.NS) and validate the data integrity."
        ),
        tools=[read_portfolio],
        verbose=True,
        max_iter=MAX_ITERATIONS,
        allow_delegation=False,
        llm=llm,
        function_calling_llm=llm # Explicitly set to prevent OpenAI fallback
    )


def create_news_scraper_agent():
    """
    Agent B: Market Impact Strategist (Formerly News Scraper)
    Uses a Hybrid Funnel strategies: Macro Search -> Global Cues -> Official Data -> Specific News.
    """
    llm = get_gemini_llm()
    return Agent(
        role="Market Impact Strategist",
        goal="Monitor macro events, global cues (Crude/Gold), corporate actions, and news to identify multi-layered impacts.",
        backstory=(
            "You are a hedge fund strategist who anticipates ripples. You know that fog "
            "grounds planes (Aviation) and strikes halt deliveries (Logistics). "
            "You triangulate data: \n"
            "1. Macro Events (via Search) \n"
            "2. Global Cues (Crude/Indices) \n"
            "3. Official Data (NSE Corporate Actions) \n"
            "4. News Media (Moneycontrol). \n"
            "You connect these dots to find risks others miss.\n"
            "CRITICAL: EFFICIENCY IS KEY. usage limits apply.\n"
            "1. Run 'Search Market News' ONCE for top headlines.\n"
            "2. Run 'Global Cues' ONCE.\n"
            "3. Synthesize immediately. DO NOT loop looking for more."
        ),
        tools=[
            search_market_news, 
            get_global_cues, 
            get_corporate_actions, 
            scrape_general_market_news, 
            batch_scrape_news,
            announce_regime_tool, # NEW
            log_pivot_tool,        # NEW
            check_accounting_fraud # INTEGRITY SHIELD
        ],
        verbose=True,
        max_iter=MAX_ITERATIONS,
        allow_delegation=False,
        llm=llm,
        function_calling_llm=llm
    )






def create_sentiment_analyzer_agent():
    """Agent C: Sentiment Analyzer (High Volume -> Flash)"""
    llm = get_flash_llm()
    return Agent(
        role="Sentiment Analysis Expert",
        goal="Analyze news articles and classify sentiment as Positive, Negative, or Neutral",
        backstory=(
            "You are a seasoned financial analyst. You read news articles and determine "
            "their emotion (Fear/Greed). You flag 'Hype' vs 'Panic'. Your output feeds "
            "into the Shadow Analyst to detect contrarian traps."
        ),
        tools=[],  # Uses LLM reasoning only
        verbose=True,
        max_iter=3, # Ultra strict limit for rate limiting
        allow_delegation=False,
        llm=llm,
        function_calling_llm=llm
    )


def create_market_context_agent():
    """
    Agent D: Technical Market Analyst (Formerly Market Context)
    Refocused on Technicals (Price Action) to complement the Strategist's Fundamentals.
    """
    llm = get_gemini_llm()
    return Agent(
        role="Technical Market Analyst",
        goal="Analyze Nifty/BankNifty Price Action, Trends, and Support/Resistance Levels",
        backstory=(
            "You are a Chartered Market Technician (CMT). You don't care about the news; "
            "you care about the Price. You analyze Charts, Trends, and Levels. "
            "You tell us WHERE the market can go based on structure, while the Strategist "
            "tells us WHY."
        ),
        tools=[analyze_market_context, batch_get_stock_data],
        verbose=True,
        max_iter=3, # Ultra strict limit for rate limiting
        allow_delegation=False,
        llm=llm,
        function_calling_llm=llm
    )


def create_report_generator_agent():
    """Agent E: Report Generator"""
    llm = get_gemini_llm()
    return Agent(
        role="Intelligence Report Writer",
        goal="Generate comprehensive weekly stock intelligence report with risk highlights",
        backstory=(
            "You are an expert financial report writer. You synthesize the 'Intelligence Mesh': "
            "combining Strategy, Technicals, and Shadow Alerts into a cohesive narrative. "
            "You highlight 'Silent Accumulation' or 'Bull Traps' identified by the team."
        ),
        tools=[],
        verbose=True,
        max_iter=3, # Ultra strict limit for rate limiting
        allow_delegation=False,
        llm=llm,
        function_calling_llm=llm
    )


def create_shadow_analyst_agent():
    """
    Agent G: Shadow Analyst
    Tracks "Smart Money" vs "Retail Sentiment" (Contrarian Logic).
    """
    llm = get_gemini_llm()
    return Agent(
        role="Institutional Shadow Analyst",
        goal="Detect Market Traps (Accumulation/Distribution) by comparing Sentiment vs Flow.",
        backstory=(
            "You are a forensic market detective. You look for DIVERGENCES. "
            "If Sentiment is PANIC but Block Deals are BUYING, you scream 'ACCUMULATION'. "
            "If Sentiment is EUPHORIA but Delivery is LOW, you scream 'TRAP'. "
            "You are the deeper truth behind the noise."
            "CRITICAL: You have a MEMORY. Always check if you were wrong last time before shouting."
        ),
        tools=[
            analyze_sector_flow_tool, 
            fetch_block_deals_tool, 
            batch_detect_accumulation, 
            get_trap_indicator_tool,
            read_past_predictions_tool,
            save_prediction_tool,
            log_pivot_tool
        ], 
        verbose=True,
        max_iter=5, # Strict limit to prevent loops
        allow_delegation=False,
        llm=llm,
        function_calling_llm=llm
    )


def create_visualizer_agent():
    """Agent F: Visualizer Agent"""
    llm = get_gemini_llm()
    return Agent(
        role="Market Data Visualizer",
        goal="Generate premium visual dashboards with derivative analysis",
        backstory=(
            "You are a specialized visualizer agent. You use Option Chain data to "
            "confirm breakouts. If the Technical Analyst says 'Up', you check if "
            "Call Writers are running away. If data is missing, you gracefully fall back "
            "to Historical Volatility."
        ),
        tools=[generate_market_snapshot],
        verbose=True,
        max_iter=MAX_ITERATIONS,
        allow_delegation=False,
        llm=llm,
        function_calling_llm=llm
    )


class AgentFactory:
    """Factory class to create all agents."""
    
    @staticmethod
    def create_all_agents():
        return {
            'portfolio_manager': create_portfolio_manager_agent(),
            'news_scraper': create_news_scraper_agent(), # Maintains key name for compatibility
            'sentiment_analyzer': create_sentiment_analyzer_agent(),
            'market_context': create_market_context_agent(),
            'report_generator': create_report_generator_agent(),
            'visualizer': create_visualizer_agent(),
            'shadow_analyst': create_shadow_analyst_agent()
        }
