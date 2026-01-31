from crewai.tools import BaseTool
from tools.market_data import MarketDataFetcher
from tools.derivative_analysis import DerivativeAnalyzer
from tools.dashboard_renderer import DashboardRenderer
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
        logger.info("Analyzing %s...", ticker)
        # Use long-term volatility (1 year) for stability if IV is missing
        volatility = analyzer.calculate_volatility(history, window=252)
        returns_matrix = analyzer.calculate_monthly_returns_matrix(history)

        # Pass LTP to analyze_oi for ATM IV extraction
        oi_data = analyzer.analyze_oi(option_chain, ltp)

        if not oi_data:
            logger.warning("No OI data found for %s. Proceeding with Price Action only.", ticker)
            # Fallback scenarios without Max Pain
            sigma_monthly = volatility * (1 / 12**0.5) if volatility else 0
            expected_move = ltp * sigma_monthly if ltp else 0

            scenarios = {
                "neutral_range": (ltp - expected_move * 0.5 if ltp else 0, ltp + expected_move * 0.5 if ltp else 0),
                "bull_target": ltp + expected_move if ltp else 0,
                "bear_target": ltp - expected_move if ltp else 0,
                "expected_move": expected_move,
                "used_iv": False,
            }

            # Create dummy OI data for visualizer to handle gracefully
            oi_data = {
                "pcr": None,
                "max_pain": None,
                "support_strike": None,
                "resistance_strike": None,
                "expiry": None,
                "strikes": [],
                "ce_ois": [],
                "pe_ois": [],
                "atm_iv": None,
            }
        else:
            expiry_date = oi_data.get("expiry")
            iv = oi_data.get("atm_iv", 0)
            scenarios = analyzer.model_scenarios(ltp, volatility, oi_data.get("max_pain"), expiry_date=expiry_date, iv=iv)

        # 3. Visualize
        logger.debug("Generating dashboard for %s...", ticker)
        try:
            image_buffer = visualizer.generate_dashboard(ticker, history, oi_data, scenarios, returns_matrix, None)
        except Exception as e:
            logger.error("Visualizer failed for %s: %s", ticker, e)
            try:
                track_error_detail(type(e).__name__, str(e), context={"function": "generate_dashboard", "ticker": ticker})
            except Exception:
                pass
            raise
        
        # Save image
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/{ticker}_snapshot.png"
        
        with open(filename, "wb") as f:
            f.write(image_buffer.getbuffer())

        # 4. Return Summary
        # Handle potential None values and ensure numeric formatting is safe
        neutral_start = scenarios.get('neutral_range', (ltp, ltp))[0]
        neutral_end = scenarios.get('neutral_range', (ltp, ltp))[1]
        bull_tgt = scenarios.get('bull_target', ltp)
        bear_tgt = scenarios.get('bear_target', ltp)

        # Add IV info to summary if used
        if scenarios.get('used_iv') and oi_data.get('atm_iv') is not None:
            iv_info = f"- **IV Used:** {float(oi_data.get('atm_iv', 0)):.2f}%"
        else:
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
