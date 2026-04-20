"""
Agent definitions for Market Rover system.

.. note::
    If you modify any agent roles or goals, please update `AI_AGENTS.md`.
"""
try:
    from crewai import Agent, LLM
except Exception:
    # Fallback stubs so tests can import and patch this module without crewai installed
    class Agent:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

    class LLM:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

try:
    from rover_tools.batch_tools import batch_scrape_news, batch_get_stock_data, batch_detect_accumulation
    from rover_tools.portfolio_tool import read_portfolio
    from rover_tools.news_scraper_tool import scrape_general_market_news
    from rover_tools.search_tool import search_market_news
    from rover_tools.global_market_tool import get_global_cues
    from rover_tools.corporate_actions_tool import get_corporate_actions
    from rover_tools.market_context_tool import analyze_market_context
    from rover_tools.visualizer_tool import generate_market_snapshot
    from rover_tools.shadow_tools import analyze_sector_flow_tool, fetch_block_deals_tool, get_trap_indicator_tool
    from rover_tools.memory_tool import read_past_predictions_tool, save_prediction_tool
    from rover_tools.autonomy_tools import announce_regime_tool, log_pivot_tool
    from rover_tools.forensic_tool import check_accounting_fraud
    from rover_tools.sre_tools import propose_system_remediation
    from rover_tools.advanced_skills import (
        calculate_portfolio_risk_tool,
        fetch_economic_calendar_tool,
        analyze_retail_sentiment_tool,
        detect_technical_patterns_tool,
        fetch_fii_dii_flow_tool,
        fetch_subha_muhurtham_tool,
        analyze_traditional_calendar_tool,
        fetch_historical_context_tool,
        generate_sector_heatmap_tool,
        fetch_options_skew_tool,
        calculate_mtc_score_tool,
        detect_institutional_absorption_tool
    )
except ImportError as e:
    import sys
    print(f"[WARN] Some rover_tools could not be imported: {e}", file=sys.stderr)
    # Define stubs for critical missing tools if needed, or rely on them being optional
    # For now, we assume most are needed but we'd rather warn than crash during collection.

from config import MAX_ITERATIONS, GOOGLE_API_KEY
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
    # Primary model per rule #2.1
    _flash_llm = _create_llm("gemini-3-flash-preview")
    return _flash_llm

def get_pro_llm():
    """Create and cache the Gemini Pro LLM (Deep Reasoning)."""
    global _pro_llm
    if _pro_llm is not None:
        return _pro_llm
    # Using 1.5 Flash as higher-fidelity fallback for long-context tasks per rule #2.1
    try:
        _pro_llm = _create_llm("gemini-3-flash-preview")
    except:
        _pro_llm = _create_llm("gemini-3-flash-preview")
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
        tools=[read_portfolio, calculate_portfolio_risk_tool],
        verbose=True,
        max_iter=MAX_ITERATIONS,
        allow_delegation=False,
        llm=llm,
        function_calling_llm=llm # Explicitly set to prevent OpenAI fallback
    )


def create_news_scraper_agent():
    """
    Agent B: Market Impact Strategist (Formerly News Scraper)
    Elite Upgrade: Uses Quadratic Regime Mapping (Goldilocks/Reflation/Stagflation/Deflation).
    """
    llm = get_gemini_llm()
    return Agent(
        role="Market Impact Strategist",
        goal="Orchestrate macro strategy by mapping the global 'Quadratic Regime' and identifying interest-rate sensitive risks.",
        backstory=(
            "You are a top-tier hedge fund strategist. You don't just 'scrape news'; you 'map regimes.' "
            "You categorize the market into one of four quadrants (Goldilocks, Reflation, Stagflation, Deflation) "
            "by triangulating VIX, DXY, and 10Y Yields. Your 'brain' is trained to see interest-rate ripples "
            "before they hit the stock price. You follow the 'Governance Heartbeat' protocol but with an "
            "elite layer of macro-causality. You tell the team what the 'vibe' of the market is, and why."
        ),
        tools=[
            search_market_news,
            get_global_cues,
            get_corporate_actions,
            scrape_general_market_news,
            batch_scrape_news,
            announce_regime_tool,
            log_pivot_tool,
            check_accounting_fraud,
            fetch_economic_calendar_tool,
            calculate_portfolio_risk_tool # Re-added for cross-functional support
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
        tools=[analyze_retail_sentiment_tool],  # Uses LLM reasoning and retail sentiment tool
        verbose=True,
        max_iter=3, # Ultra strict limit for rate limiting
        allow_delegation=False,
        llm=llm,
        function_calling_llm=llm
    )


def create_market_context_agent():
    """
    Agent D: Technical Market Analyst (Formerly Market Context)
    Elite Upgrade: Multi-Timeframe Concordance (MTC) and Volume Profile Anchoring.
    """
    llm = get_gemini_llm()
    return Agent(
        role="Technical Market Analyst",
        goal="Confirm high-conviction entries using Multi-Timeframe Concordance (15m, 1h, Day) and Volume Points of Control.",
        backstory=(
            "You are a CMT trained in 'Concordance Scanning.' You believe a breakout on the Daily chart "
            "is a trap unless it is confirmed by the 1-hour and 15-minute flows. You focus on 'Institutional "
            "Footprints'—zones with the highest volume (POC)—rather than just lines on a chart. "
            "You provide the 'Structural High Ground' for the team, filtering out 90% of retail noise."
        ),
        tools=[
            analyze_market_context,
            batch_get_stock_data,
            detect_technical_patterns_tool,
            calculate_mtc_score_tool # NEW ELITE SKILL
        ],
        verbose=True,
        max_iter=3,
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
        tools=[fetch_historical_context_tool],
        verbose=True,
        max_iter=3, # Ultra strict limit for rate limiting
        allow_delegation=False,
        llm=llm,
        function_calling_llm=llm
    )


def create_shadow_analyst_agent():
    """
    Agent G: Shadow Analyst
    Elite Upgrade: Institutional Fingerprinting and Options Gamma Squeeze Detection.
    """
    llm = get_gemini_llm()
    return Agent(
        role="Institutional Shadow Analyst",
        goal="Detect stealth institutional flows using Volume-at-Price (VAP) and Options Gamma Skew to expose retail traps.",
        backstory=(
            "You are a forensic market detective who specializes in 'Fingerprinting.' "
            "You search for 'Dead Zones' where retail is panicking but large blocks are being "
            "silently absorbed. You also track the 'Gamma Wall'—identifying where market makers "
            "will force a squeeze. You are the ultimate contrarian brain of the team, "
            "trained to see the 'Shadow' behind the price action."
        ),
        tools=[
            analyze_sector_flow_tool,
            fetch_block_deals_tool,
            batch_detect_accumulation,
            get_trap_indicator_tool,
            read_past_predictions_tool,
            save_prediction_tool,
            log_pivot_tool,
            fetch_fii_dii_flow_tool,
            fetch_options_skew_tool,         # NEW ELITE SKILL
            detect_institutional_absorption_tool # NEW ELITE SKILL
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
        tools=[generate_market_snapshot, generate_sector_heatmap_tool],
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
            'shadow_analyst': create_shadow_analyst_agent(),
            'traditional_timing': create_traditional_timing_agent(),
            'sre_support': create_sre_support_agent()
        }

def create_traditional_timing_agent():
    """Agent H: Traditional Timing Analyst"""
    llm = get_gemini_llm()
    return Agent(
        role="Traditional Timing Analyst",
        goal="Analyze traditional Indian calendars, astrological dates, and festive timelines to identify culturally significant investing windows.",
        backstory=(
            "You are the master of Indian cultural timelines. You know that retail flow into gold or autos "
            "surges on certain Nakshatras or festivals (Akshaya Tritiya, Dhanteras). You provide the cultural 'When' "
            "to the broader strategy, advising if today is an auspicious day for sector-specific accumulation."
        ),
        tools=[fetch_subha_muhurtham_tool, analyze_traditional_calendar_tool],
        verbose=True,
        max_iter=3,
        allow_delegation=False,
        llm=llm,
        function_calling_llm=llm
    )


def create_sre_support_agent():
    """Agent I: SRE Support Sentinel"""
    llm = get_flash_llm()
    return Agent(
        role="SRE Support Sentinel",
        goal="Ensure 99.9% uptime and optimal latency of the Market-Rover ecosystem.",
        backstory=(
            "You are the sentinel of infrastructure. You monitor token costs, build logs, and "
            "deployment latency. You follow Rule #7 and #8. You are 'Timezone-Aware' of your "
            "Primary User (IST). During working hours (09:00 - 19:00 IST), you escalate "
            "CI/CD failures as 'Mission Critical' requests to the HIL Dashboard. "
            "Outside of these hours, you batch alerts and focus on automated self-healing. "
            "When the system is breathing heavy, you use the 'propose_system_remediation' "
            "tool to ask the Human-In-The-Loop for a mission-critical fix."
        ),
        tools=[propose_system_remediation],
        verbose=True,
        max_iter=3,
        allow_delegation=False,
        llm=llm,
        function_calling_llm=llm
    )
