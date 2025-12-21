from crewai.tools import BaseTool
from tools.market_data import MarketDataFetcher
from tools.derivative_analysis import DerivativeAnalyzer
from tools.visualizer import Visualizer
import os
from typing import Type
from pydantic import BaseModel, Field

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
        print(f"DEBUG: MarketSnapshotTool called for {ticker}")
        # Initialize components
        fetcher = MarketDataFetcher()
        analyzer = DerivativeAnalyzer()
        visualizer = Visualizer()

        # 1. Fetch Data
        print(f"Fetching data for {ticker}...")
        ltp = fetcher.fetch_ltp(ticker)
        if ltp is None:
            return f"Error: Could not fetch LTP for {ticker}"

        # Fetch full history for heatmap
        history = fetcher.fetch_full_history(ticker)
        option_chain = fetcher.fetch_option_chain(ticker)

        # 2. Analyze
        print(f"Analyzing {ticker}...")
        # 2. Analyze
        print(f"Analyzing {ticker}...")
        # Use long-term volatility (1 year) for stability if IV is missing
        volatility = analyzer.calculate_volatility(history, window=252)
        returns_matrix = analyzer.calculate_monthly_returns_matrix(history)
        
        # Pass LTP to analyze_oi for ATM IV extraction
        oi_data = analyzer.analyze_oi(option_chain, ltp)
        
        if not oi_data:
            print(f"Warning: No OI data found for {ticker}. Proceeding with Price Action only.")
            # Fallback scenarios without Max Pain
            # Use simple volatility based range around LTP
            # volatility is annual, convert to monthly (approx)
            sigma_monthly = volatility * (1 / 12**0.5)
            expected_move = ltp * sigma_monthly
            
            scenarios = {
                "neutral_range": (ltp - expected_move*0.5, ltp + expected_move*0.5),
                "bull_target": ltp + expected_move,
                "bear_target": ltp - expected_move,
                "expected_move": expected_move
            }
            
            # Create dummy OI data for visualizer to handle gracefully
            oi_data = {
                "pcr": "N/A",
                "max_pain": "N/A",
                "support_strike": "N/A",
                "resistance_strike": "N/A",
                "expiry": "N/A",
                "strikes": [],
                "ce_ois": [],
                "pe_ois": [],
                "atm_iv": 0
            }
        else:
            # Pass expiry date and IV for time-adjusted targets
            expiry_date = oi_data.get('expiry')
            iv = oi_data.get('atm_iv', 0)
            scenarios = analyzer.model_scenarios(ltp, volatility, oi_data['max_pain'], expiry_date=expiry_date, iv=iv)

        # 3. Visualize
        print(f"Generating dashboard for {ticker}...")
        image_buffer = visualizer.generate_dashboard(ticker, history, oi_data, scenarios, returns_matrix)
        
        # Save image
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/{ticker}_snapshot.png"
        
        with open(filename, "wb") as f:
            f.write(image_buffer.getbuffer())

        # 4. Return Summary
        # Handle N/A values gracefully for formatting
        neutral_start = scenarios['neutral_range'][0]
        neutral_end = scenarios['neutral_range'][1]
        bull_tgt = scenarios['bull_target']
        bear_tgt = scenarios['bear_target']
        
        # Add IV info to summary if used
        iv_info = f"- **IV Used:** {oi_data.get('atm_iv', 0):.2f}%" if scenarios.get('used_iv') else f"- **HV Used (Annual):** {volatility*100:.2f}%"
        
        summary = f"""
        **Market Snapshot for {ticker}**
        - **LTP:** {ltp:.2f}
        - **PCR:** {oi_data['pcr']}
        - **Max Pain:** {oi_data['max_pain']}
        {iv_info}
        - **Support (Put OI):** {oi_data['support_strike']}
        - **Resistance (Call OI):** {oi_data['resistance_strike']}
        - **Expected Range ({scenarios.get('days_remaining', 30)} days):** {neutral_start:.0f} - {neutral_end:.0f}
        - **Bull Target:** {bull_tgt:.0f}
        - **Bear Target:** {bear_tgt:.0f}
        
        [Dashboard Image]({filename})
        """
        return summary

# Instantiate for import
generate_market_snapshot = MarketSnapshotTool()
