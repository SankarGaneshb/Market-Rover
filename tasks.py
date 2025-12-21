"""
Task definitions for Market Rover system.
"""
from crewai import Task
from textwrap import dedent


def create_portfolio_retrieval_task(agent):
    """
    Task 1: Retrieve portfolio stocks.
    """
    return Task(
        description=dedent("""
            Read the user's stock portfolio from the Portfolio.csv file.
            Ensure all stock symbols have the .NS suffix for NSE stocks.
            Validate that the data is complete and properly formatted.
            
            Return a list of all stock symbols and company names.
        """),
        agent=agent,
        expected_output="A list of stock symbols with .NS suffix and their company names"
    )


def create_news_scraping_task(agent, context):
    """
    Task 2: Scrape news for each stock using Newspaper3k.
    """
    return Task(
        description=dedent("""
            For each stock in the portfolio, scrape recent news articles from Moneycontrol.
            Use Newspaper3k to extract article titles, summaries, and publication dates.
            Filter for news from the last 7 days only.
            
            Focus on finding the most relevant and impactful news stories.
            Each stock should have 3-5 recent news articles if available.
            
            Return a structured collection of news articles for each stock.
        """),
        agent=agent,
        context=context,
        expected_output="News articles for each stock with titles, summaries, and dates"
    )


def create_sentiment_analysis_task(agent, context):
    """
    Task 3: Analyze sentiment of news articles.
    """
    return Task(
        description=dedent("""
            Analyze each news article and classify its sentiment as:
            - POSITIVE: Bullish news that could drive stock price up
            - NEGATIVE: Bearish news that could drive stock price down
            - NEUTRAL: News with no clear directional impact
            
            For each article, provide:
            1. Sentiment classification
            2. Brief reasoning for the classification
            3. Impact level (High/Medium/Low)
            
            If you are uncertain about the sentiment, mark it as "FLAG_FOR_REVIEW"
            and explain why it's uncertain.
            
            Return sentiment analysis for all articles organized by stock.
        """),
        agent=agent,
        context=context,
        expected_output="Sentiment classification for each article with reasoning and impact level"
    )


def create_market_context_task(agent, context):
    """
    Task 4: Analyze market context.
    """
    return Task(
        description=dedent("""
            Analyze the broader market context to understand if individual stock
            movements are aligned with or contrary to market trends.
            
            IMPORTANT: Use the portfolio stocks from the previous task to intelligently
            determine which sector indices to analyze.
            
            Provide:
            1. Nifty 50 performance (last 7 days)
            2. Bank Nifty performance (always include)
            3. Relevant sectoral index performance based on portfolio stocks:
               - If portfolio has IT stocks (TCS, Infosys, Wipro, etc.) → analyze Nifty IT
               - If portfolio has Banking stocks (HDFC Bank, ICICI, SBI, etc.) → highlight Bank Nifty
               - If portfolio has Auto stocks → analyze Nifty Auto
               - If portfolio has Pharma stocks → analyze Nifty Pharma
               - And so on for other sectors
            4. Overall market sentiment (Positive/Negative)
            5. Key market drivers affecting the portfolio stocks
            
            This context will help understand whether negative news is amplified
            or dampened by market conditions, and how sector trends affect portfolio stocks.
        """),
        agent=agent,
        context=context,
        expected_output="Market context analysis with Nifty 50, Bank Nifty, portfolio-relevant sector indices, and overall sentiment"
    )


def create_report_generation_task(agent, context):
    """
    Task 5: Generate final weekly report.
    """
    return Task(
        description=dedent("""
            Create a comprehensive weekly intelligence report that includes:
            
            1. **EXECUTIVE SUMMARY**
               - Overall portfolio health
               - Market sentiment this week
               - Top 3 most important news stories affecting the portfolio
            
            2. **STOCK-BY-STOCK ANALYSIS**
               For each stock with significant news:
               - Stock name and current price
               - Key news stories with sentiment
               - Potential risks or opportunities
               - Recommendation: WATCH/HOLD/CONCERN
            
            3. **RISK HIGHLIGHTS**
               - Stocks with negative sentiment that need attention
               - Market-wide risks affecting the portfolio
               - Stocks flagged for review (uncertain sentiment)
            
            4. **FLAG FOR REVIEW**
               - List any stocks/news where sentiment was uncertain
               - Explain why human review is needed
            
            FORMAT REQUIREMENTS:
            - All financial figures in Crores (₹X.XX Crore)
            - Use clear section headers
            - Highlight risks in bold
            - Keep each stock analysis to 3-4 sentences
            - Total report should not exceed 2 pages
            
            This is a passive briefing - no action required from the user,
            but risks should be clearly highlighted.
        """),
        agent=agent,
        context=context,
        expected_output="A comprehensive 2-page weekly intelligence report with risk highlights and flagged items"
    )


def create_market_snapshot_task(agent, ticker):
    """
    Task 6: Generate Market Snapshot.
    """
    return Task(
        description=dedent(f"""
            Generate a high-fidelity market snapshot for {{ticker}}.
            
            1. Fetch real-time data (LTP, Option Chain).
            2. Perform derivative analysis (PCR, Max Pain, Volatility).
            3. Generate a visual dashboard showing Price Action, Volatility Bands, and OI Support/Resistance.
            
            Return the path to the generated image and a summary of key metrics.
        """).format(ticker=ticker),
        agent=agent,
        expected_output="A summary of market metrics and a path to the generated dashboard image."
    )


# Task factory for easy access
class TaskFactory:
    """Factory class to create all tasks with proper dependencies."""
    
    @staticmethod
    def create_all_tasks(agents):
        """
        Create all tasks with proper context dependencies.
        
        Args:
            agents: Dictionary of agents from AgentFactory
            
        Returns:
            List of tasks in execution order
        """
        # Task 1: Portfolio Retrieval
        task1 = create_portfolio_retrieval_task(agents['portfolio_manager'])
        
        # Task 2: News Scraping (depends on Task 1)
        task2 = create_news_scraping_task(agents['news_scraper'], context=[task1])
        
        # Task 3: Sentiment Analysis (depends on Task 2)
        task3 = create_sentiment_analysis_task(agents['sentiment_analyzer'], context=[task2])
        
        # Task 4: Market Context (depends on Task 1)
        task4 = create_market_context_task(agents['market_context'], context=[task1])
        
        # Task 5: Report Generation (depends on Tasks 3 and 4)
        task5 = create_report_generation_task(
            agents['report_generator'],
            context=[task3, task4]
        )
        
        return [task1, task2, task3, task4, task5]
