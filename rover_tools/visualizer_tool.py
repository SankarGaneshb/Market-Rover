from crewai.tools import BaseTool
from rover_tools.market_data import MarketDataFetcher
from rover_tools.market_analytics import MarketAnalyzer
from rover_tools.dashboard_renderer import DashboardRenderer
from rover_tools.analytics.seasonality_calendar import SeasonalityCalendar
import os
from typing import Type
from pydantic import BaseModel, Field
from utils.logger import get_logger
from utils.metrics import track_error_detail
import streamlit as st

logger = get_logger(__name__)

# @st.cache_data(ttl=300, show_spinner=False)
def run_snapshot_logic(ticker: str):
    """
    Cached worker function for market snapshot analysis.
    Cache expires in 5 minutes (300s).
    """
    # Initialize components
    fetcher = MarketDataFetcher()
    analyzer = MarketAnalyzer()
    visualizer = DashboardRenderer()

    # 1. Fetch Data
    logger.info("Fetching data for %s...", ticker)
    ltp = fetcher.fetch_ltp(ticker)
    if ltp is None:
        return f"Error: Could not fetch LTP for {ticker}"

    # Fetch full history for heatmap
    history = fetcher.fetch_full_history(ticker)

    # 2. Analyze
    # Use long-term volatility (1 year) for stability
    volatility = analyzer.calculate_volatility(history, window=252)
    returns_matrix = analyzer.calculate_monthly_returns_matrix(history)
    
    # Scenarios based on Volatility only (No OI)
    scenarios = analyzer.model_scenarios(ltp, volatility, days_remaining=30)
    
    # Seasonality Stats (Win Rate, Avg Return)
    seasonality_stats = analyzer.calculate_seasonality(history)
    
    # 2026 Calendar Analysis
    calendar_tool = SeasonalityCalendar(history)
    calendar_df = calendar_tool.generate_analysis()
    # We will pass the tool or df to renderer to generate the plot
        
    # 2026 Forecast
    forecast_2026 = analyzer.calculate_2026_forecast(history)

    # 3. Visualize (Returns buffer)
    try:
        # 3. Visualize (Returns buffer)
        # Pass new data components (Seasonality, Calendar) to PDF generator
        pdf_buffer = visualizer.generate_pdf_report(
            ticker=ticker, 
            history_df=history, 
            scenarios=scenarios, 
            returns_matrix=returns_matrix, 
            forecast_2026=forecast_2026,
            seasonality_stats=seasonality_stats,
            calendar_tool=calendar_tool,
            calendar_df=calendar_df
        )
        
        return {
            "ltp": ltp,
            "volatility": volatility,
            "scenarios": scenarios,
            "forecast_2026": forecast_2026,
            "pdf_buffer": pdf_buffer
        }
    except Exception as e:
        logger.error(f"Snapshot logic failed for {ticker}: {e}", exc_info=True)
        return f"Error: {str(e)}"

class MarketSnapshotInput(BaseModel):
    """Input schema for Market Snapshot Tool."""
    ticker: str = Field(..., description="The stock ticker symbol (e.g., 'SBIN', 'TCS').")

class MarketSnapshotTool(BaseTool):
    name: str = "Generate Market Snapshot"
    description: str = (
        "Generates a multi-page PDF market report for a given stock ticker. "
        "Includes Price, Heatmap, Seasonality, and 2026 Forecast. "
        "Returns the path to the generated PDF report and a text summary."
    )
    args_schema: Type[BaseModel] = MarketSnapshotInput

    def _run(self, ticker: str) -> str:
        logger.debug(f"MarketSnapshotTool called for {ticker}")
        
        # Call cached logic
        result = run_snapshot_logic(ticker)
        
        if isinstance(result, str) and result.startswith("Error"):
            return result
        
        # Unpack
        ltp = result['ltp']
        volatility = result['volatility']
        scenarios = result['scenarios']
        forecast_2026 = result['forecast_2026']
        forecast_2026 = result['forecast_2026']
        pdf_buffer = result['pdf_buffer']

        # Save image (Side effect, must be done outside cache or cache returns path)
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/{ticker}_report.pdf"
        
        with open(filename, "wb") as f:
            f.write(pdf_buffer.getbuffer())

        # 4. Return Summary (Update link to PDF)
        neutral_start = scenarios['neutral_range'][0]
        neutral_end = scenarios['neutral_range'][1]
        bull_tgt = scenarios['bull_target']
        bear_tgt = scenarios['bear_target']
        
        iv_info = f"- **HV Used (Annual):** {volatility*100:.2f}%"
        
        summary = f"""
        **Market Snapshot for {ticker}**
        - **LTP:** {ltp:.2f}
        {iv_info}
        - **Expected Range (30 days):** {neutral_start:.0f} - {neutral_end:.0f}
        - **Bull Target:** {bull_tgt:.0f}
        - **Bear Target:** {bear_tgt:.0f}
        
        [Download PDF Report]({filename})
        """
        
        if forecast_2026:
            summary += f"""
            **2026 Long-Term Forecast (End of Year)**
            - **Consensus Target:** {forecast_2026['consensus_target']:.0f}
            - **Range:** {forecast_2026['range_low']:.0f} - {forecast_2026['range_high']:.0f}
            - **Models Used:** Trend (LinReg), CAGR ({forecast_2026['cagr_percent']:.1f}%), Monte Carlo
            """
        
        return summary

# Instantiate for import
generate_market_snapshot = MarketSnapshotTool()
