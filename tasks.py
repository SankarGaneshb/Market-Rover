"""
Task definitions for Market Rover system.
"""
try:
    from crewai import Task
except Exception:
    # Fallback stub so tests can import and patch this module without crewai installed
    class Task:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass
from textwrap import dedent
import os

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)


def create_portfolio_retrieval_task(agent):
    """Task 1: Retrieve portfolio stocks."""
    return Task(
        description=dedent("""
            Read the user's stock portfolio to identify which companies to track.
            Return a validated list of symbols (including .NS suffix).

            **SELF-CORRECTION (Data Integrity)**:
            - **Format Check**: If the symbol is 'INFY', you MUST output 'INFY.NS'.
            - **Sanity Check**: Does the CSV contain valid text? If empty, flag an error immediately.
            - **Deduplication**: Remove any duplicate entries before passing them downstream.
        """),
        agent=agent,
        output_file="logs/task1_portfolio.txt",
        expected_output="A validated, deduplicated list of stock symbols with .NS suffix."
    )


def create_market_strategy_task(agent, context):
    """
    Task 2: Market Impact Strategy (Elite Regime Mapping).
    """
    return Task(
        description=dedent("""
            Execute the 'Elite Macro Mapping' protocol to identify the market's current Quadratic Regime:

            **QUADRATIC REGIME DIAGNOSTICS**:
            1. **Macro Scan**: Triangulate VIX, DXY, and 10Y Bond Yields.
            2. **Identify Quadrant**:
               - **GOLDILOCKS**: (Growth Up, VIX Low). Strategy: Buy aggressive tech/discretionary.
               - **REFLATION**: (Growth Up, Yields/DXY Up). Strategy: Focus on Commodities/Banks.
               - **STAGFLATION**: (Growth Down, Yields Up). Strategy: Focus on Defensives/FMCG.
               - **DEFLATIONARY**: (Growth Down, VIX High). Strategy: Cash/Bonds/Dividends.
            3. **Declaration**: You MUST explicitly declare the 'MACRO QUADRANT' at the top of your report.

            **SATYAM PROTOCOL (Accounting Integrity)**:
            - If a stock is a Smallcap OR news mentions "Audit" / "Governance", you MUST run `check_accounting_fraud`.

            **Synthesis**:
            Connect the Regime to the Portfolio. Example: "We are in REFLATION, therefore Tata Steel is a strategic buy despite high volatility."
        """),
        agent=agent,
        context=context,
        output_file="logs/task2_strategy.txt",
        expected_output="An Elite Strategic Report defining the Macro Quadrant and its impact on the portfolio."
    )


def create_sentiment_analysis_task(agent, context):
    """
    Task 3: Analyze sentiment (Fear/Greed).
    """
    return Task(
        description=dedent("""
            Analyze the Strategic Report from the previous task.
            Classify the sentiment for each stock and the overall market.

            **Critically**: Identify where the sentiment is 'Extreme' (Panic or Euphoria).
            Look for the 'REGIME' flag. If REGIME is DEFENSIVE, 'Fear' is the baseline, essentially ignore minor bad news.
            This output will be used by the Shadow Analyst to detect Traps.

            **CONTEXTUAL REFLECTION**:
            - **Nuance Check**: "Profit Down 10%" is bad. But "Profit Down 10% (Expected 20%)" is GOOD. Did you catch the beat/miss context?
            - **Hype Filter**: Is the news just a press release? If so, discount the 'Positive' score.
            - **Outcome**: A 'Negative' sentiment score requires *real* bad news, not just a red day.
        """),
        agent=agent,
        context=context, # Depends on Strategy Task
        async_execution=True,
        output_file="logs/task3_sentiment.txt",
        expected_output="Sentiment classification with 'Extreme Sentiment' flags."
    )


def create_technical_analysis_task(agent, context):
    """
    Task 4: Technical Analysis (Multi-Timeframe Concordance).
    """
    return Task(
        description=dedent("""
            Analyze the Technical structure of the market using 'Concordance Scanning':

            **MTC PROTOCOL (Multi-Timeframe Concordance)**:
            1. **Step 1**: Identify the Daily Trend (Primary).
            2. **Step 2**: Check 1-hour and 15-min price action.
            3. **Step 3: Concordance Check**:
               - IF Daily = UP, 1h = UP, 15m = UP -> **DECLARE: STRONG BUY CONCORDANCE**.
               - IF timeframes conflict -> **DECLARE: NOISY/NEUTRAL**.

            **VOLUME ANCHORING**:
            Identify the **Volume Point of Control (POC)** for each stock. Where is the most volume trading?
            - Price above POC = Institutional support.
            - Price below POC = Institutional distribution.

            **Actionable Output**: Filter out 'Retail Breakouts' that lack volume support.
        """),
        agent=agent,
        context=context,
        async_execution=True,
        output_file="logs/task4_technical.txt",
        expected_output="Technical report with MTC status and Volume POC levels."
    )


def create_shadow_analysis_task(agent, context):
    """
    Task 5: Shadow Analysis (The Forensic Fingerprint).
    """
    return Task(
        description=dedent("""
            Perform a 'Forensic Fingerprint' scan by looking for Institutional Footprints:

            **FINGERPRINTING PROTOCOL**:
            1. **Search for Absorption**: Is the stock in a 'High Volume, Low Volatility' zone? This is the fingerprint of stealth institutional buying.
            2. **Options Gamma Wall**: Identify the Call/Put strike with the highest Open Interest.
               - If price is approaching a major Call strike, warn of a 'Gamma Trap' where price will be pinned.
            3. **Contrarian Check**: If Sentiment is EXTREME PANIC but technical POC is holding, issue a **SHADOW ACCUMULATION ALERT**.

            **Mission**: Distinguish between 'Retail Noise' and 'Institutional Intent'.
        """),
        agent=agent,
        context=context,
        output_file="logs/task5_shadow.txt",
        expected_output="Forensic report identifying Institutional Absorption and Gamma Traps."
    )

def create_traditional_timing_task(agent, context):
    """
    Task 6: Cultural & Astrological Timing Analysis (The Traditional Analyst).
    **NEW TASK**
    """
    return Task(
        description=dedent("""
            Analyze the cultural and astrological timelines for the Indian market to identify 'when' to invest.

            **Inputs**:
            - Portfolio (What are we buying?)
            - Strategy Report (What is the regime?)

            **DYNAMIC CULTURAL STRATEGY**:
            1. **Macro Timing**: Call `fetch_subha_muhurtham_tool` for the current year. Identify if we are in a broader auspicious period.
            2. **Sector Timing**: If the Portfolio contains specific sectors (like Jewelry/Titan, Auto/Maruti), use `analyze_traditional_calendar_tool` to see if upcoming Indian festivals will drive retail flow.

            **SYNTHESIS**:
            Combine this cultural insight with the broader Strategy Report. If the market is in a GROWTH regime AND a major festival is approaching, issue a Strong Buy signal for culturally relevant sectors.

            Format: A brief, poetic, but actionable assessment of the auspiciousness of current market timing.
        """),
        agent=agent,
        context=context, # Depends on Portfolio and Strategy
        async_execution=True,
        output_file="logs/task_traditional.txt",
        expected_output="A cultural and traditional timing assessment for the portfolio."
    )

def create_report_generation_task(agent, context):
    """
    Task 6: Generate final weekly report.
    """
    return Task(
        description=dedent("""
            Create a Master Intelligence Report integrating all layers:

            1. **Executive Summary**: Global Cues & Macro Headwinds.
            2. **Portfolio Analysis**:
                - **Fundamental**: News & Corporate Actions.
                - **Technical**: Trends & Levels.
                - **Institutional Radar**: The 'Shadow Signals' (Accumulation/Traps).
            3. **Risk Highlights**: Specific warnings (e.g., "Crude Spike impacts Paints").

            Format: Professional, actionable, 2 pages max.

            **CRITICAL: ADAPTIVE TONE & JSON VALIDATION**:
            Step 1: **Check REGIME**.
                - If DEFENSIVE: Tone must be Cautious, Hedged, Risk-Averse. warning users against aggressive buying.
                - If GROWTH: Tone can be Optimistic, Opportunistic.

            Step 2: Draft the report.
            Step 3: **Review your own work**:
                - **JSON Check**: Did I include the JSON block at the end? is it Valid JSON (no trailing commas)?
                - **Consistency**: Did I mention a 'Sell' signal for a stock that I earlier said has 'Positive News'? Resolve conflicts.
            Step 4: Output the Final Report with the strict JSON block.
        """),
        agent=agent,
        context=context, # Depends on ALL previous analysis
        # No output_file here so user sees the Final Report in console
        expected_output="Comprehensive Intelligence Report with Institutional Radar."
    )



def create_market_snapshot_task(agent, ticker):
    """
    Task to generate a visual market snapshot for a single ticker.
    Used by the Visualizer Interface in the UI.
    """
    return Task(
        description=dedent(f"""
            Generate a comprehensive PDF Market Report for {ticker}.

            1. Use `MarketSnapshotTool` (Generate Market Snapshot).
            2. The tool will calculate volatility, seasonality, and run the 2026 forecast model.
            3. It will generate a high-quality multi-page PDF report.

            Return the final path of the PDF and a brief summary of the forecast.
        """),
        agent=agent,
        expected_output="Path to the generated image and a volatility summary."
    )


class TaskFactory:
    """Factory class to create all tasks with proper dependencies."""

    @staticmethod
    def create_all_tasks(agents):
        # 1. Get Portfolio
        task1 = create_portfolio_retrieval_task(agents['portfolio_manager'])

        # 2. Market Strategy (Hybrid Funnel)
        task2 = create_market_strategy_task(agents['news_scraper'], context=[task1])

        # 3. Sentiment Analysis (feeds on Strategy)
        task3 = create_sentiment_analysis_task(agents['sentiment_analyzer'], context=[task2])

        # 4. Technical Analysis (independent check on Portfolio)
        task4 = create_technical_analysis_task(agents['market_context'], context=[task1])

        # 5. Shadow Analysis (The Synergy Step: Sentiment + Technicals)
        task5 = create_shadow_analysis_task(agents['shadow_analyst'], context=[task3, task4])

        # 6. Traditional Timing (Cultural Alignment)
        task_traditional = create_traditional_timing_task(agents['traditional_timing'], context=[task1, task2])

        # 7. Report Generation (Synthesizes everything including Traditional Timing)
        task6 = create_report_generation_task(
            agents['report_generator'],
            context=[task2, task3, task4, task5, task_traditional]
        )

        return [task1, task2, task3, task4, task5, task_traditional, task6]
