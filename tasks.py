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
            
            **SELF-CORRECTION (Data Integrity)**:
            - **Format Check**: If the symbol is 'INFY', you MUST output 'INFY.NS'.
            - **Sanity Check**: Does the CSV contain valid text? If empty, flag an error immediately.
            - **Deduplication**: Remove any duplicate entries before passing them downstream.
        """),
        agent=agent,
        expected_output="A validated, deduplicated list of stock symbols with .NS suffix."
    )


def create_market_strategy_task(agent, context):
    """
    Task 2: Market Impact Strategy (Hybrid Funnel).
    """
    return Task(
        description=dedent("""
            Execute the 'Hybrid Intelligence Funnel' to gather comprehensive market insights:
            
            **DYNAMIC INVESTIGATION STRATEGY**:
            You have a toolkit (Macro Search, Global Cues, Official Data, Micro Scraper).
            1. **Primary Scan & REGIME CHECK**: 
               - Call `get_global_cues`.
               - **CRITICAL BRANCHING**:
                 - IF VIX > 22 OR Crude > 95 OR USD/INR > 84.5 -> **DECLARE REGIME: DEFENSIVE**.
                 - ELSE -> **DECLARE REGIME: GROWTH**.
               - You MUST explicitly state the 'REGIME' at the top of your report.
            2. **Deep Dive**: If `scrape_general_market_news` returns generic noise, pivot to `batch_scrape_news` for specific ticker details.
            3. **Conflict Resolution**: If News says "Results Bad" but Price is up, you MUST use `get_corporate_actions` to check if a Dividend was declared.
            
            **Synthesis**:
            Combine these layers. Example: "Asian Paints (Micro) is falling because Crude is up (Global), despite good results (Official)."

            **SELF-CORRECTION & LOGIC CHECK**:
            Before finalizing, review your hypothesis:
            1. **Causality Check**: Is the stock *really* moving due to the Macro factor, or is there a specific Corporate Action?
            2. **Validation**: If you claim a correlation (e.g. "USD up -> IT up"), is it actually happening in the price data?
            3. **Refinement**: Discard weak text. Keep only strong, evidence-backed insights.
        """),
        agent=agent,
        context=context, # Depends on Portfolio
        expected_output="A strategic report after self-correction, combining Global Cues, Macro Events, Corporate Actions, and Specific News."
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
            
            **DYNAMIC TOOL USAGE (Based on REGIME)**:
            - **Step 1**: Read the Strategy Report. What is the REGIME?
            - **Step 2**: Apply Regulatory Filter:
                - **IF REGIME = DEFENSIVE**:
                    - IGNORE all 'Breakout' signals. They are likely false.
                    - FOCUS on 'Major Support' levels only.
                    - Tactic: "Buy at Support, Do not Chase."
                - **IF REGIME = GROWTH**:
                    - SEEK 'Breakouts' and momentum.
                    - FOCUS on 'Resistance' levels to book profit.
            
            - Use `Batch Stock Data Fetcher` for all stocks.
            - **Trend Confirmation**: If the Daily Trend is unclear (Sideways), look for Breakout levels slightly above/below current price.
            - **Context Matters**: If Nifty is at All-Time Highs, judge 'Resistance' more leniently (Blue Sky Zone).
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
            
            **DYNAMIC FORENSIC STRATEGY**:
            1. **MEMORY CHECK (The Learning Layer)**: 
               - Call `read_past_predictions_tool` for each stock.
               - IF you were WRONG last time (e.g. Predicted Buy, Stock Fell), be **CONSERVATIVE** today.
            
            2. **The Trap Hunt**: Look for divergences.
            3. **Tool Pivoting**:
               - Check `fetch_block_deals_tool` first. If NO DATA, pivot to `analyze_sector_flow_tool` to see if the *Sector* is being bought.
               - If Sector Flow is neutral, check `get_trap_indicator_tool` for Retail Positioning.
            4. **Missing Data Protocol**: If a specific tool returns nothing, do NOT give up. Infer from the remaining datasets.
            
            **Your Mission**:
            1. **Detect Silent Accumulation**: If Sentiment is Fear/Negative but Price is at Support & Block Deals are happening -> CALL IT OUT.
            2. **Detect Bull Traps**: If Sentiment is Euphoria but Price is hitting Resistance -> CALL IT OUT.
            3. **Check Trap Indicators**: Use your tools to see if Retail is trapped.
            
            **INSTRUCTION**:
            - Use `Batch Shadow Scan` to analyze ALL stocks in the portfolio in one step.
            - Do NOT iterate one by one. Use the comma-separated list.
            
            **FORENSIC VERIFICATION (Self-Correction)**:
            - **Data Freshness**: Is the 'Block Deal' from today/yesterday? If it's 2 weeks old, IGNORE IT.
            - **Context**: If the entire Market (Nifty) is crashing, a 'Buy Signal' on one stock is high risk. Did you note this risk?
            - **Contrarian Logic**: Ensure you aren't just following the herd. The signal must be a *divergence*.
            - **Final Save**: Use `save_prediction_tool` to record your final Call and Confidence (High/Med/Low) for 1-2 key stocks.
            
            Generate a 'Contrarian Signal' for each stock.
        """),
        agent=agent,
        context=context, # Depends on Sentiment AND Technical Tasks
        expected_output="Forensic analysis report identifying Accumulation, Distribution, and Traps, informed by Past Accuracy."
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
