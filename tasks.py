"""
Task definitions for Market Rover system.
"""
from crewai import Task
from textwrap import dedent


def create_portfolio_retrieval_task(agent):
    """Task 1: Retrieve portfolio stocks."""
    return Task(
        description=dedent("""
            Read the user's stock portfolio to identify which companies to track.
            Return a validated list of symbols (including .NS suffix).
        """),
        agent=agent,
        expected_output="A list of stock symbols with .NS suffix and their company names"
    )


def create_market_strategy_task(agent, context):
    """
    Task 2: Market Impact Strategy (Hybrid Funnel).
    """
    return Task(
        description=dedent("""
            Execute the 'Hybrid Intelligence Funnel' to gather comprehensive market insights:
            
            1. **MACRO SCAN (High Speed)**:
               - Use `get_global_cues` to check Crude, Gold, Nasdaq, and USD/INR.
               - Use `scrape_general_market_news` to find top business headlines (Strikes, Budget, Policy).
               - Use `search_market_news` to investigate specific potential risks (e.g., "Impact of recent fog on airlines").
            
            2. **OFFICIAL DATA CHECK**:
               - For each portfolio stock, use `get_corporate_actions` to check for Board Meetings, Results, or Dividends.
            
            3. **MICRO NEWS SCRAPING**:
               - Use `scrape_stock_news` for each portfolio stock to catch specific media coverage.
            
            **Synthesis**:
            Combine these layers. Example: "Asian Paints (Micro) is falling because Crude is up (Global), despite good results (Official)."
        """),
        agent=agent,
        context=context, # Depends on Portfolio
        expected_output="A strategic report combining Global Cues, Macro Events, Corporate Actions, and Specific News for the portfolio."
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
            This output will be used by the Shadow Analyst to detect Traps.
        """),
        agent=agent,
        context=context, # Depends on Strategy Task
        expected_output="Sentiment classification with 'Extreme Sentiment' flags."
    )


def create_technical_analysis_task(agent, context):
    """
    Task 4: Technical Analysis (Price Action).
    """
    return Task(
        description=dedent("""
            Analyze the Technical structure of the market and portfolio stocks.
            Focus strictly on Price Action:
            - Trend (Uptrend/Downtrend)
            - Support/Resistance Levels
            - Relative Strength vs Nifty
            
            Do not focus on news (Agent B does that). Focus on the Chart.
        """),
        agent=agent,
        context=context, # Depends on Portfolio
        expected_output="Technical analysis report with Trend, Support, and Resistance levels."
    )


def create_shadow_analysis_task(agent, context):
    """
    Task 5: Shadow Analysis (The Trap Detector).
    **NEW SYNERGY TASK**
    """
    return Task(
        description=dedent("""
            Perform a 'Forensic Audit' by comparing Sentiment vs Reality.
            
            **Inputs**: 
            - Sentiment Report (Are people panicking?)
            - Technical Report (Is support holding?)
            
            **Your Mission**:
            1. **Detect Silent Accumulation**: If Sentiment is Fear/Negative but Price is at Support & Block Deals are happening -> CALL IT OUT.
            2. **Detect Bull Traps**: If Sentiment is Euphoria but Price is hitting Resistance -> CALL IT OUT.
            3. **Check Trap Indicators**: Use your tools to see if Retail is trapped.
            
            Generate a 'Contrarian Signal' for each stock.
        """),
        agent=agent,
        context=context, # Depends on Sentiment AND Technical Tasks
        expected_output="Forensic analysis report identifying Accumulation, Distribution, and Traps."
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
            Include the strict JSON block for visualization at the end.
        """),
        agent=agent,
        context=context, # Depends on ALL previous analysis
        expected_output="Comprehensive Intelligence Report with Institutional Radar."
    )



def create_market_snapshot_task(agent, ticker):
    """
    Task to generate a visual market snapshot for a single ticker.
    Used by the Visualizer Interface in the UI.
    """
    return Task(
        description=dedent(f"""
            Generate a comprehensive Visual Market Snapshot for {ticker}.
            
            1. Use `generate_market_snapshot` tool.
            2. The tool will calculate volatility, support/resistance, and option chain logic.
            3. It will save a chart to 'output/{{ticker}}_snapshot.png'.
            
            Return the final path of the image and a brief summary of the volatility data.
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
        
        # 6. Report Generation (Synthesizes everything)
        task6 = create_report_generation_task(
            agents['report_generator'],
            context=[task2, task3, task4, task5]
        )
        
        return [task1, task2, task3, task4, task5, task6]
