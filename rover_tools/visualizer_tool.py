from crewai.tools import BaseTool
from rover_tools.market_data import MarketDataFetcher
from rover_tools.market_analytics import MarketAnalyzer
from rover_tools.dashboard_renderer import DashboardRenderer
import os
from typing import Type
from pydantic import BaseModel, Field
from utils.logger import get_logger
from utils.metrics import track_error_detail

logger = get_logger(__name__)

class MarketSnapshotInput(BaseModel):
    """Input schema for Market Snapshot Tool."""
    ticker: str = Field(..., description="The stock ticker symbol (e.g., 'SBIN', 'TCS').")

class MarketSnapshotTool(BaseTool):
    name: str = "Generate Market Snapshot"
    description: str = (
        "Generates a high-fidelity market snapshot for a given stock ticker. "
        "Fetches data, performs derivative analysis (PCR, Max Pain, Volatility), "
        "and creates a visual dashboard. "
        "Returns the path to the generated image and a text summary."
    )
    args_schema: Type[BaseModel] = MarketSnapshotInput

    def _run(self, ticker: str) -> str:
        logger.debug(f"MarketSnapshotTool called for {ticker}")
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
        # Fetch option chain for OI analysis
        option_chain = fetcher.fetch_option_chain(ticker)

        # 2. Analyze
        print(f"Analyzing {ticker}...")
        # Use long-term volatility (1 year) for stability
        volatility = analyzer.calculate_volatility(history, window=252)
        returns_matrix = analyzer.calculate_monthly_returns_matrix(history)
        
        # Scenarios based on Volatility only (No OI)
        scenarios = analyzer.model_scenarios(ltp, volatility, days_remaining=30)
            
        # 2026 Forecast
        forecast_2026 = analyzer.calculate_2026_forecast(history)

        # 3. Visualize
        print(f"Generating dashboard for {ticker}...")
        image_buffer = visualizer.generate_dashboard(ticker, history, None, scenarios, returns_matrix, forecast_2026)
        
        # Save image
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/{ticker}_snapshot.png"
        
        with open(filename, "wb") as f:
            f.write(image_buffer.getbuffer())

        # 4. Return Summary
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
        
        [Dashboard Image]({filename})
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
