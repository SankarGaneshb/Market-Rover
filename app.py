"""
Market-Rover 4.0 - Streamlit Web Application
Interactive portfolio analysis with real-time progress tracking, visualizers, and forecasts.
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime
import time

# Add parent directory to path for imports
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import os
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

from crew import create_crew
from config import UPLOAD_DIR, REPORT_DIR
from utils.job_manager import JobManager
from utils.mock_data import mock_generator, simulate_analysis_delay
from utils.report_visualizer import ReportVisualizer
from utils.logger import get_logger, log_analysis_start, log_analysis_complete, log_error
from utils.metrics import (get_api_usage, get_performance_stats, get_cache_stats, 
                           get_error_stats, track_performance, track_api_call, track_error_detail)
from utils.visualizer_interface import generate_market_snapshot
from utils.security import sanitize_ticker, RateLimiter, validate_csv_content, sanitize_llm_input
from utils.forecast_tracker import get_forecast_history
import yfinance as yf

# Initialize logger
logger = get_logger(__name__)


# Page configuration
st.set_page_config(
    page_title="Market-Rover",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'job_manager' not in st.session_state:
    st.session_state.job_manager = JobManager()
if 'current_job_id' not in st.session_state:
    st.session_state.current_job_id = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'test_mode' not in st.session_state:
    st.session_state.test_mode = False
# Rate limiters for API protection
if 'visualizer_limiter' not in st.session_state:
    st.session_state.visualizer_limiter = RateLimiter(max_requests=30, time_window_seconds=60)
if 'heatmap_limiter' not in st.session_state:
    st.session_state.heatmap_limiter = RateLimiter(max_requests=20, time_window_seconds=60)
if 'portfolio_limiter' not in st.session_state:
    st.session_state.portfolio_limiter = RateLimiter(max_requests=5, time_window_seconds=300) # 5 per 5 mins


def main():
    """Main application entry point"""
    
    # Header
    st.title("🔍 Market-Rover")
    st.markdown("**AI-Powered Stock Intelligence System**")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("🚀 About")
        st.markdown("""
        **AI Stock Intelligence**
        
        **📤 Portfolio Analysis**  
        Upload → Analyze → View reports
        
        **📈 Market Visualizer**  
        Charts, price targets
        
        **🔥 Monthly Heatmap**  
        History, trends, 2026 forecast
        
        ---
        
        **Features:** ⚡ Fast | 🔒 Secure | 📊 Interactive
        
        ---
        ### ⚠️ Legal Disclaimer
        *Market-Rover is for informational purposes only. No financial advice provided. Past performance does not guarantee future results. Consult a financial advisor before investing.*
        """)
        
        st.markdown("---")
        st.markdown("### ⚙️ Settings")
        max_parallel = st.slider(
            "Concurrent Stocks",
            min_value=1,
            max_value=10,
            value=5,
            help="Number of stocks to analyze simultaneously"
        )
        
        # Test mode toggle (compact)
        test_mode = st.checkbox(
            "🧪 Test Mode",
            value=st.session_state.test_mode,
            help="Use mock data without API calls"
        )
        st.session_state.test_mode = test_mode

        
        if test_mode:
            st.info("🧪 Test mode enabled - using mock data")
        
        # Observability metrics
        st.markdown("---")
        with st.expander("📊 Observability", expanded=False):
            st.markdown("### Real-Time Metrics")
            
            # API Usage
            api_usage = get_api_usage()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("API Calls Today", f"{api_usage['today']}/{api_usage['limit']}")
            with col2:
                st.metric("Remaining", api_usage['remaining'])
            
            # Progress bar for API quota
            quota_pct = api_usage['today'] / api_usage['limit']
            st.progress(quota_pct, text=f"Quota: {quota_pct*100:.0f}%")
            
            st.markdown("---")
            
            # Performance Stats
            perf_stats = get_performance_stats()
            if perf_stats['total_analyses'] > 0:
                st.markdown("**Performance**")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Total Analyses",
                        perf_stats['total_analyses']
                    )
                with col2:
                    st.metric(
                        "Avg Duration",
                        f"{perf_stats['avg_duration']:.1f}s"
                    )
                st.markdown("---")
            
            # Cache Stats
            cache_stats = get_cache_stats()
            total_cache = cache_stats['hits'] + cache_stats['misses']
            if total_cache > 0:
                st.markdown("**Cache Performance**")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Hit Rate", f"{cache_stats['hit_rate']:.0f}%")
                with col2:
                    st.metric("Total Ops", total_cache)
                st.markdown("---")
            
            # Error Stats
            error_stats = get_error_stats()
            if error_stats['total'] > 0:
                st.markdown("**Errors**")
                st.metric("Total Errors", error_stats['total'])
                if error_stats['by_type']:
                    st.json(error_stats['by_type'], expanded=False)
            
            # Refresh button (note: refreshes entire app)
            if st.button("🔄 Refresh App", width="stretch", help="Refreshes the entire app to update all metrics"):
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📚 Recent Reports")
        show_recent_reports()

    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Portfolio Analysis", "📈 Market Visualizer", "🔍 Market Analysis", "🎯 Forecast Tracker"])
    
    with tab1:
        show_portfolio_analysis_tab(max_parallel)
    
    with tab2:
        show_visualizer_tab()

    with tab3:
        show_market_analysis_tab()

    with tab4:
        show_forecast_tracker_tab()


    # Tab 5 Removed (Merged into Tab 1)
    
    # Disclaimer at bottom - always visible like a status bar
    st.markdown("---")
    st.caption("⚠️ **Disclaimer:** Market-Rover is for informational purposes only. Not financial advice. Past performance ≠ future results. Consult a qualified advisor. No liability for losses. By using this app, you accept these terms.")

def render_analytics_section():
    st.header("🧪 Analytics Lab")
    st.info("Advanced tools to analyze portfolio risk and diversification.")
    
    from rover_tools.market_analytics import MarketAnalyzer
    analyzer = MarketAnalyzer()
    
    mode = st.radio("Select Tool", ["Correlation Matrix", "Portfolio Rebalancer"], horizontal=True)
    
    if mode == "Correlation Matrix":
        st.subheader("🔗 Correlation Matrix")
        st.markdown("Analyze how your stocks move in relation to each other. **High correlation** means they move together (less diversification).")
        
        # Input Method
        corr_input_mode = st.radio("Input Source:", ["Select Stocks 🏗️", "Select Saved Portfolio 📂", "Paste/Manual Entry ✏️"], horizontal=True, key="corr_input_mode")
        
        tickers_input = ""
        
        if corr_input_mode == "Select Stocks 🏗️":
            from rover_tools.ticker_resources import get_common_tickers
            
            # Filter Pills
            cat = st.pills("Filter:", ["All", "Nifty 50", "Sensex", "Bank Nifty", "Midcap", "Smallcap"], default="Nifty 50", key="corr_pills")
            
            # Multiselect
            options = get_common_tickers(category=cat)
            selected_common = st.multiselect("Choose Stocks:", options, key="corr_multiselect")
            
            # Custom Add
            custom_add = st.text_area("Add Custom Tickers (comma or new line separated):", height=68, 
                                      placeholder="e.g.\nBSE: 500325\nNSE: VEDL", key="corr_custom_add")
            
            # Combine
            final_list = []
            if selected_common:
                final_list.extend([s.split(' - ')[0] for s in selected_common])
            
            if custom_add:
                # Robust cleanup (handle newlines and commas)
                import re
                # Replace newlines with commas, then split by comma
                normalized = custom_add.replace('\n', ',')
                clean_custom = [c.strip() for c in normalized.split(',') if c.strip()]
                final_list.extend(clean_custom)
            
            # Remove duplicates while preserving order
            final_list = list(dict.fromkeys(final_list))
            
            tickers_input = ", ".join(final_list)
            
            if final_list:
                st.caption(f"✅ Selected {len(final_list)} stocks: {', '.join(final_list)}")
            else:
                st.info("Select stocks or add custom ones to begin.")
                
        elif corr_input_mode == "Select Saved Portfolio 📂":
            from utils.portfolio_manager import PortfolioManager
            pm = PortfolioManager()
            saved_names = pm.get_portfolio_names()
            
            if saved_names:
                selected_pf = st.selectbox("Choose Portfolio:", saved_names, key="corr_pf_select")
                pf_df = pm.get_portfolio(selected_pf)
                if pf_df is not None and not pf_df.empty:
                    tickers_list = pf_df['Symbol'].tolist()
                    st.success(f"Loaded {len(tickers_list)} stocks from '{selected_pf}'")
                    # Pre-fill for visibility (read-only or editable)
                    tickers_input = ", ".join(tickers_list)
            else:
                st.info("No saved portfolios found.")
                
        else:
            # Default stocks
            default_tickers = "RELIANCE.NS, TCS.NS, HDFCBANK.NS, INFY.NS, ITC.NS"
            tickers_input = st.text_area("Enter Stock Symbols (comma separated)", value=default_tickers)
        
        if tickers_input and st.button("Generate Matrix"):
            with st.spinner("Fetching data and calculating correlation..."):
                raw_tickers = [t.strip() for t in tickers_input.split(',') if t.strip()]
                tickers = []
                for t in raw_tickers:
                    # Auto-append .NS if no suffix is present (common user error)
                    if '.' not in t:
                        tickers.append(f"{t}.NS")
                    else:
                        tickers.append(t)
                        
                # Re-instantiate to ensure fresh state
                # from rover_tools.analytics import MarketAnalyzer # Already imported at top-level usually, but safe here
                analyzer = MarketAnalyzer()
                
                matrix = analyzer.calculate_correlation_matrix(tickers)
                
                if not matrix.empty:
                    st.write("### Correlation Heatmap")
                    import plotly.express as px
                        
                    fig = px.imshow(
                        matrix,
                        text_auto=".2f",
                        aspect="auto",
                        color_continuous_scale="RdBu_r", # Red=High, Blue=Low
                        zmin=-1, zmax=1
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Correlation Calculation Failed. Matrix is empty.")
                    
    elif mode == "Portfolio Rebalancer":
        st.subheader("⚖️ Portfolio Rebalancer (Risk Parity)")
        st.markdown("Suggests rebalancing actions to equalize risk contribution (Inverse Volatility).")
        
        # Input Method
        rebal_input_mode = st.radio("Input Source:", ["Manual Entry ✏️", "Select Saved Portfolio 📂"], horizontal=True, key="rebel_input_mode")
        
        # Load logic
        if rebal_input_mode == "Select Saved Portfolio 📂":
            from utils.portfolio_manager import PortfolioManager
            pm = PortfolioManager()
            saved_names_rebal = pm.get_portfolio_names()
            
            if saved_names_rebal:
                selected_pf_rebal = st.selectbox("Choose Portfolio:", saved_names_rebal, key="rebal_pf_select")
                pf_df_rebal = pm.get_portfolio(selected_pf_rebal)
                
                if pf_df_rebal is not None and not pf_df_rebal.empty:
                    # Convert to rebalancer format: symbol, value
                    # Assuming we use Average Price * Quantity = Value
                    # Ensure columns exist
                    if 'Symbol' in pf_df_rebal.columns and 'Quantity' in pf_df_rebal.columns and 'Average Price' in pf_df_rebal.columns:
                        rebal_data = []
                        for _, row in pf_df_rebal.iterrows():
                            val = row['Quantity'] * row['Average Price']
                            rebal_data.append({'symbol': row['Symbol'], 'value': val})
                        
                        st.session_state.rebal_portfolio = pd.DataFrame(rebal_data)
                        st.success(f"Loaded {len(rebal_data)} holdings from '{selected_pf_rebal}'")
            else:
                st.info("No saved portfolios found.")

        st.caption("Enter/Edit your current portfolio holdings below:")
        
        # Editable dataframe for portfolio input
        if 'rebal_portfolio' not in st.session_state:
            st.session_state.rebal_portfolio = pd.DataFrame([
                {'symbol': 'RELIANCE.NS', 'value': 50000},
                {'symbol': 'TCS.NS', 'value': 30000},
                {'symbol': 'HDFCBANK.NS', 'value': 40000},
            ])
            
        edited_df = st.data_editor(st.session_state.rebal_portfolio, num_rows="dynamic", key="rebal_editor")
        
        if edited_df is not None:
             # Strategy Selector
             strategy = st.radio(
                 "Rebalancing Strategy",
                 ["🛡️ Risk Parity (Lower Risk, Steady)", "⚖️ Growth Optimization (Risk-Adjusted Return)"],
                 horizontal=True
             )
             
             mode = "safety" if "Risk Parity" in strategy else "growth"
             
             if st.button("Analyze & Rebalance"):
                with st.spinner(f"Running {mode} optimization..."):
                    portfolio_data = edited_df.to_dict('records')
                    # Auto-append .NS if missing
                    for item in portfolio_data:
                        if 'symbol' in item and '.' not in item['symbol']:
                            item['symbol'] = f"{item['symbol']}.NS"
                            
                    # Pass the selected mode to the new engine
                    result, warnings = analyzer.analyze_rebalance(portfolio_data, mode=mode)
                    
                    if warnings:
                        st.warning("### ⚠️ Data Anomalies Detected")
                        for w in warnings:
                            st.write(w)
                    
                    if not result.empty:
                        # Calculate Portfolio Logic (Weighted Vol for display)
                        avg_vol = (result['volatility'] * result['current_weight']).sum()
                        risk_label = "Moderate"
                        if avg_vol < 0.15: risk_label = "Conservative 🛡️"
                        elif avg_vol > 0.25: risk_label = "Aggressive 🚀"
                        else: risk_label = "Moderate ⚖️"
                        
                        st.markdown(f"### 📋 {mode.title()} Rebalancing Plan")
                        st.info(f"**Current Portfolio Profile**: {risk_label} (Weighted Volatility: {avg_vol:.1%})")
                        
                        # Formatting
                        def color_action(val):
                            color = '#28a745' if val == 'Buy' else ('#dc3545' if val == 'Sell' else '#6c757d')
                            return f'color: {color}; font-weight: bold'
                            
                        st.dataframe(result.style.applymap(color_action, subset=['action'])
                                     .format({
                                         'current_weight': '{:.1%}', 
                                         'target_weight': '{:.1%}', 
                                         'volatility': '{:.1%}',
                                         'return': '{:.1%}'
                                     }), use_container_width=True)
                                     
                        if mode == "safety":
                            st.info("ℹ️ **Strategy**: Stocks with **lower volatility** get higher allocation.")
                        else:
                            st.info("ℹ️ **Strategy**: Stocks with **better Risk/Reward (Sharpe Ratio)** get higher allocation.")
                        
                        with st.expander("🎓 How is this calculated?"):
                            if mode == "safety":
                                st.markdown("""
                                **Inverse Volatility (Risk Parity)**:
                                *   **Goal**: Minimize Portfolio Risk.
                                *   **Logic**: Safer stocks (low fluctuation) get MORE money. Risky stocks get LESS.
                                *   **Formula**: `Target Weight ~ 1 / Volatility`
                                """)
                            else:
                                st.markdown("""
                                **Sharpe Ratio Optimization (Growth)**:
                                *   **Goal**: Maximize Return for every unit of Risk taken.
                                *   **Logic**: We prefer stocks that have **High Returns AND Low Risk**.
                                *   **Formula**: `Target Weight ~ Annual Return / Volatility`
                                *   (Negative return stocks are deprioritized).
                                """)
                            
                            st.markdown("""
                            ---
                            **Data Reliability**:
                            *   If historical data is missing or incomplete, the system will **Fallback to Equal Weight** for safety.
                            *   **Overweight Calculation**:
                            $$ \\text{Overweight} = \\text{Current Weight} - \\text{Target Weight} $$
                            """)
                    else:
                        st.error("Analysis failed. Please check tickers.")

def show_visualizer_tab():
    """Show the Market Visualizer tab (V3.0) - Generates comprehensive market snapshot image"""
    st.header("📈 Market Visualizer")
    st.markdown("Generate **comprehensive market snapshot** with Price Chart and Scenario Targets.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info("⚠️ **Disclaimer:** Automated analysis. Not financial advice.")
        ticker_raw = st.text_input("Enter Stock Ticker (e.g., SBIN, TCS)", value="SBIN", key="viz_ticker")
        
        if st.button("Generate Snapshot", type="primary", width="stretch", key="btn_viz"):
            # Sanitize input
            ticker = sanitize_ticker(ticker_raw)
            if not ticker:
                st.error("Please enter a ticker symbol.")
                return

            # Check rate limit
            allowed, message = st.session_state.visualizer_limiter.is_allowed()
            if not allowed:
                 st.warning(f"⏱️ {message}")
                 return

            with st.spinner(f"🎨 Generating snapshot for {ticker}... This may take a minute."):
                try:
                    result = generate_market_snapshot(ticker)
                    
                    if result['success']:
                        st.success("✅ Snapshot generated successfully!")
                        
                        # Display Image
                        if result['image_path']:
                            st.image(result['image_path'], caption=f"Market Snapshot: {ticker}", width="stretch")
                        
                        # Display Summary
                        st.markdown("### 📝 Analysis Summary")
                        st.markdown(result['message'])
                        
                    else:
                        st.error("❌ Generation Failed")
                        st.error(result['message'])
                        
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
                    try:
                        track_error_detail(type(e).__name__, str(e), context={"location": "show_visualizer_tab", "ticker": ticker})
                    except Exception:
                        pass
    
        st.markdown("""
        **Dashboard Features:**
        - 📊 **Price Chart**: With volatility bands and time-adjusted targets.
        - 🌡️ **Monthly Heatmap**: Historical performance from IPO to date.
        - 🔮 **2026 Forecast**: Long-term trend projection.
        """)

# --- TAB 3: UNIFIED MARKET ANALYSIS ---
def show_market_analysis_tab():
    """Show the Unified Market Analysis Tab (V4.1)"""
    st.header("🔍 Market Analysis")
    st.markdown("Deep-dive into **historical patterns** and get **AI-powered predictions** for individual Stocks or Market Indices.")
    
    mode_col, _ = st.columns([1, 2])
    with mode_col:
        analysis_mode = st.radio("Analysis Mode:", ["Stock Analysis 🏢", "Benchmark/Index 📊"], horizontal=True, label_visibility="collapsed")

    st.markdown("---")

    if analysis_mode == "Stock Analysis 🏢":
        # === STOCK LOGIC ===
        st.subheader("🏢 Stock Heatmap & Forecast")
        st.warning("⚠️ **Disclaimer:** Forecasts are AI-generated estimates based on historical patterns.")
        
        col_filter, col_input, col_button, col_info = st.columns([1.5, 2, 1, 3])
        from rover_tools.ticker_resources import get_common_tickers
        
        with col_filter:
            # Check for deep link
            default_cat = "All"
            
            ticker_category = st.pills(
                "Filter by Index",
                options=["All", "Nifty 50", "Sensex", "Bank Nifty", "Midcap", "Smallcap"],
                default=default_cat,
                key="heatmap_category_pills"
            )

        with col_input:
            common_tickers = get_common_tickers(category=ticker_category)
            
            # Check for query param ticker
            qp_ticker = st.query_params.get("ticker", None)
            default_ix = 0
            
            # If query param exists, try to find it
            if qp_ticker:
                qp_ticker = f"{qp_ticker}.NS" if not qp_ticker.endswith(".NS") else qp_ticker
                # Try to find in list
                matches = [i for i, t in enumerate(common_tickers) if qp_ticker in t]
                if matches:
                    default_ix = matches[0]
                else:
                    # If not in list, might need custom (logic below simplifies to just default sbins if not found in pills)
                    pass
            else:
                for i, t in enumerate(common_tickers):
                    if "SBIN.NS" in t:
                        default_ix = i + 1 
                        break
                    
            ticker_options = ["✨ Select or Type to Search..."] + common_tickers + ["✏️ ROI/Custom Input"]
            
            selected_opt = st.selectbox(
                "Stock Selection", 
                options=ticker_options, 
                index=default_ix if default_ix < len(ticker_options) else 0,
                key="heatmap_ticker_select",
                help=f"Listing {ticker_category} stocks."
            )
            
            if selected_opt == "✏️ ROI/Custom Input" or selected_opt == "✨ Select or Type to Search...":
                 # Use query param if custom
                 def_val = qp_ticker if qp_ticker else "SBIN.NS"
                 ticker_raw = st.text_input("Enter Symbol (e.g. INFBEES.NS)", value=def_val, key="heatmap_ticker_custom")
            else:
                 ticker_raw = selected_opt.split(' - ')[0]
        
        with col_button:
            st.write("") 
            analyze_button = st.button("📊 Analyze", type="primary", use_container_width=True, key="btn_heatmap")

        with col_info:
             pass
            
        # Initialize session state for this tab
        if 'heatmap_active_ticker' not in st.session_state:
            st.session_state.heatmap_active_ticker = qp_ticker if qp_ticker else None
            
        if analyze_button:
             st.session_state.heatmap_active_ticker = ticker_raw
        
        # Run analysis if a ticker is active
        if st.session_state.heatmap_active_ticker:
             run_analysis_ui(st.session_state.heatmap_active_ticker, st.session_state.heatmap_limiter, key_prefix="heatmap")

    else:
        # === BENCHMARK LOGIC ===
        st.subheader("📊 Benchmark Index Analysis")
        
        # Define Major Indices
        major_indices = {
            "Nifty 50": "^NSEI",
            "Sensex": "^BSESN",
            "Bank Nifty": "^NSEBANK",
            "Nifty IT": "^CNXIT",
            "Nifty Auto": "^CNXAUTO",
            "Nifty FMCG": "^CNXFMCG",
            "Nifty Metal": "^CNXMETAL",
            "Nifty Midcap 100": "^CRSLDX", 
            "Nifty Smallcap 100": "^CNXSC" 
        }
        
        index_names = list(major_indices.keys())
        
        st.markdown("##### ⚡ Quick Select Index")
        selected_index = st.pills("Choose an Index:", index_names, selection_mode="single", default="Nifty 50", key="bench_pills")
        
        if selected_index:
            ticker = major_indices[selected_index]
            st.markdown(f"### Analyzing: **{selected_index}** (`{ticker}`)")
            run_analysis_ui(ticker, st.session_state.heatmap_limiter, key_prefix="benchmark")

def show_forecast_tracker_tab():
    """Show the Forecast Tracker Dashboard (Tab 5)"""
    st.header("🎯 Forecast Tracker")
    st.markdown("Track the performance of your saved forecasts against live market prices.")
    
    # 1. Load History
    history = get_forecast_history()
    
    if not history:
        st.info("ℹ️ No saved forecasts yet. Use the **'Save Forecast'** button in the Analysis tabs to track predictions.")
        return
        
    st.caption(f"Found {len(history)} saved forecasts.")
    
    # 2. Get Unique Tickers for Bulk Fetch
    tickers = list(set([h['ticker'] for h in history]))
    
    # 3. Fetch Live Prices (with progress bar)
    live_prices = {}
    progress_bar = st.progress(0)
    
    for i, ticker in enumerate(tickers):
        try:
            # Use basic yfinance for speed
            t = yf.Ticker(ticker)
            # Use 'regularMarketPrice' or fast history
            todays_data = t.history(period="1d")
            if not todays_data.empty:
                live_prices[ticker] = todays_data['Close'].iloc[-1]
            else:
                live_prices[ticker] = None
        except Exception as e:
            time.sleep(0.1)
            live_prices[ticker] = None
        
        progress_bar.progress((i + 1) / len(tickers))
        
    progress_bar.empty()
    
    # 4. Build Table Data
    table_data = []
    for h in history:
        ticker = h['ticker']
        saved_price = h['current_price']
        curr_price = live_prices.get(ticker, 0)
        
        # Calculate performance
        if curr_price:
            change_pct = ((curr_price - saved_price) / saved_price) * 100
        else:
            change_pct = 0.0
            curr_price = 0.0 # N/A
            
        saved_date = datetime.fromisoformat(h['timestamp']).strftime("%Y-%m-%d")
        
        table_data.append({
            "Delete": False,  # Selection col
            "Date Saved": saved_date,
            "Ticker": ticker,
            "Entry Price": saved_price,
            "Current Price": curr_price,
            "Change %": change_pct,
            "Target (2026)": h['target_price'],
            "Strategy": h['strategy'],
            "Confidence": h['confidence'],
            "ID": h['timestamp'] # Hidden ID
        })
        
    # 5. Display Interactive Data Editor
    df = pd.DataFrame(table_data)
    
    # Configure columns
    # We want 'Delete' to be editable, others read-only ideally
    edited_df = st.data_editor(
        df,
        column_config={
            "Delete": st.column_config.CheckboxColumn(
                "Delete?",
                help="Select to delete",
                default=False,
            ),
            "Entry Price": st.column_config.NumberColumn(format="₹%.2f"),
            "Current Price": st.column_config.NumberColumn(format="₹%.2f"),
            "Change %": st.column_config.NumberColumn(format="%.2f%%"),
            "Target (2026)": st.column_config.NumberColumn(format="₹%.2f"),
            "ID": None # Hide ID column
        },
        disabled=["Date Saved", "Ticker", "Entry Price", "Current Price", "Change %", "Target (2026)", "Strategy", "Confidence"],
        hide_index=True,
        use_container_width=True,
        key="forecast_editor"
    )
    
    # 6. Deletion Logic
    if not edited_df.empty:
        to_delete = edited_df[edited_df["Delete"] == True]
        
        if not to_delete.empty:
            st.warning(f"⚠️ You have selected {len(to_delete)} forecasts for deletion.")
            if st.button("🗑️ Delete Selected Forecasts", type="primary"):
                # Get IDs (timestamps)
                ids_to_del = to_delete["ID"].tolist()
                
                from utils.forecast_tracker import delete_forecasts
                if delete_forecasts(ids_to_del):
                    st.success("✅ Forecasts deleted!")
                    st.rerun()
                else:
                    st.error("❌ Error deleting forecasts.")

    # 7. Summary Metrics
    st.markdown("---")

    avg_perf = df["Change %"].mean()
    col1, col2, col3 = st.columns([1, 1, 1])
    col1.metric("Avg Portfolio Performance", f"{avg_perf:+.2f}%")
    col2.metric("Active Forecasts", len(df))
    
    with col3:
        # CSV Export
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download CSV",
            csv,
            "forecast_history.csv",
            "text/csv",
            key='download-forecasts'
        )

def run_analysis_ui(ticker_raw, limiter, key_prefix="default"):
    """Shared function to run analysis and render UI"""
    # Sanitize input
    ticker = sanitize_ticker(ticker_raw)
    if not ticker:
        st.error(f"❌ Invalid ticker format: {ticker_raw}")
        return
    
    # Check rate limit
    allowed, message = limiter.is_allowed()
    if not allowed:
        st.warning(f"⏱️ {message}")
        return
        
    with st.spinner(f"🔥 Analyzing {ticker}..."):
         try:
            # Import necessary modules
            from rover_tools.market_data import MarketDataFetcher
            from rover_tools.market_analytics import MarketAnalyzer
            import plotly.graph_objects as go
            import plotly.express as px
            import pandas as pd
            
            # Fetch data
            fetcher = MarketDataFetcher()
            analyzer = MarketAnalyzer()
            
            history = fetcher.fetch_full_history(ticker)
            
            if history.empty:
                st.error(f"❌ Could not fetch data for {ticker}")
                return
            
            # Calculate monthly returns matrix
            returns_matrix = analyzer.calculate_monthly_returns_matrix(history)
            seasonality_stats = analyzer.calculate_seasonality(history)
            
            st.success(f"✅ Analysis complete! ({len(history)} days)")
            
            # === VISUALIZATION 1: Monthly Returns Heatmap ===
            st.markdown("### 🌡️ Monthly Returns Heatmap")
            
            if not returns_matrix.empty:
                fig_heatmap = px.imshow(
                    returns_matrix,
                    labels=dict(x="Month", y="Year", color="Return %"),
                    x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    y=returns_matrix.index,
                    color_continuous_scale="RdYlGn",
                    color_continuous_midpoint=0,
                    text_auto=".1f",
                    aspect="auto"
                )
                fig_heatmap.update_layout(height=500)
                st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.warning("Not enough data for heatmap")

            # === VISUALIZATION 2: Seasonality Profile ===
            col_h, col_check = st.columns([3, 1])
            col_h.markdown("### 📊 Seasonality Profile")
            exclude_outliers = col_check.checkbox("🚫 Exclude Outliers", value=False, help="Remove extreme months (>1.5x IQR) from stats", key=f"{key_prefix}_outlier_{ticker}")
            
            # Re-calculate with user preference
            seasonality_stats = analyzer.calculate_seasonality(history, exclude_outliers=exclude_outliers)
            
            if exclude_outliers:
                st.caption("ℹ️ *Displaying data with statistical outliers removed for clearer trend analysis.*")
            col1, col2 = st.columns(2)
            
            if not seasonality_stats.empty:
                # 1. Win Rate Chart
                fig_win = px.bar(
                    seasonality_stats, 
                    x='Month_Name', 
                    y='Win_Rate',
                    title='Win Rate % (Positive Months)',
                    color='Win_Rate',
                    color_continuous_scale='Greens',
                    range_y=[0, 100]
                )
                st.plotly_chart(fig_win, use_container_width=True)
                
                # 2. Avg Return Chart
                colors = ['green' if x > 0 else 'red' for x in seasonality_stats['Avg_Return']]
                fig_seasonality = go.Figure(data=[
                    go.Bar(
                        x=seasonality_stats['Month_Name'],
                        y=seasonality_stats['Avg_Return'],
                        marker_color=colors
                    )
                ])
                fig_seasonality.update_layout(
                    title="Average Monthly Return %",
                    yaxis_title="Return %",
                    xaxis_title="Month",
                    height=450
                )
                st.plotly_chart(fig_seasonality, use_container_width=True)
            
            # === VISUALIZATION 3: 2026 Forecast ===
            st.markdown("### 🔮 2026 Forecast")
            
            # Run Backtest
            with st.spinner("🔄 Backtesting strategies..."):
                backtest_res = analyzer.backtest_strategies(history)
            
            # Generate Forecasts
            forecast_median = analyzer.calculate_median_strategy_forecast(history)
            forecast_sd = analyzer.calculate_sd_strategy_forecast(history)
            
            if forecast_median and forecast_sd:
                 current_price = history['Close'].iloc[-1]
                 winner = backtest_res['winner']
                 
                 if winner == 'sd':
                    active_res = forecast_sd
                    alt_res = forecast_median
                    active_name = "SD Strategy"
                    alt_name = "Median Strategy"
                    active_color = "purple"
                    alt_color = "blue"
                 else:
                    active_res = forecast_median
                    alt_res = forecast_sd
                    active_name = "Median Strategy"
                    alt_name = "SD Strategy"
                    active_color = "blue"
                    alt_color = "purple"
                
                 baseline_growth = active_res['annualized_growth']
                 forecast_baseline = active_res['forecast_price']
                 
                 # Conservative/Aggressive logic
                 if baseline_growth > 0:
                    conservative_growth = baseline_growth * 0.8
                    aggressive_growth = baseline_growth * 1.2
                 else:
                    conservative_growth = baseline_growth * 1.2 
                    aggressive_growth = baseline_growth * 0.8
                 
                 today = history.index[-1] # Ensure it matches data start
                 if today.tz is not None: today = today.tz_localize(None)
                 
                 end_of_2026 = pd.Timestamp('2026-12-31')
                 years_fraction = (end_of_2026 - today).days / 365.25
                 
                 forecast_conservative = current_price * (1 + conservative_growth/100) ** years_fraction
                 forecast_aggressive = current_price * (1 + aggressive_growth/100) ** years_fraction
                  
                 # Metrics
                 col_a, col_b, col_c, col_d = st.columns(4)
                 col_a.metric("Strategy", active_name, f"Acc: ±{min(backtest_res['median_avg_error'], backtest_res['sd_avg_error']):.1f}%")
                 col_b.metric("🛡️ Conservative", f"₹{forecast_conservative:.2f}", f"{conservative_growth:.1f}%")
                 col_c.metric("🎯 Baseline", f"₹{forecast_baseline:.2f}", f"{baseline_growth:.1f}%")
                 col_d.metric("🐂 Aggressive", f"₹{forecast_aggressive:.2f}", f"{aggressive_growth:.1f}%")
                 
                 # Details with Low Data Warning
                 with st.expander(f"ℹ️ Strategy Details", expanded=True):
                    st.markdown(f"**Active ({active_name}):** {active_res['strategy_description']}")
                    
                    confidence = backtest_res.get('confidence', 'High')
                    years_tested = backtest_res.get('years_tested', [])
                    if years_tested:
                        st.caption(f"✅ Validation: {', '.join(map(str, years_tested))}")
                        if confidence in ["Low", "Insufficient"]:
                            st.markdown(f":red[⚠️ **Warning: Low Data Confidence ({len(years_tested)} years)**]")
                    else:
                        st.markdown(f":red[⚠️ **Backtest skipped due to limited history**]")


                 # Chart
                 fig_forecast = go.Figure()
                 
                 # Create range including today for continuous chart
                 dates_range = pd.date_range(today, end_of_2026, freq='ME')
                 dates = [today] + list(dates_range)
                 
                 # Smooth curves starting from current price
                 curr_p = current_price
                 cons_vals = [curr_p] + [curr_p * (1 + conservative_growth/100)**((d-today).days/365.25) for d in dates_range]
                 aggr_vals = [curr_p] + [curr_p * (1 + aggressive_growth/100)**((d-today).days/365.25) for d in dates_range]
                 
                 fig_forecast.add_trace(go.Scatter(x=dates, y=cons_vals, mode='lines', line=dict(width=0), showlegend=False))
                 fig_forecast.add_trace(go.Scatter(x=dates, y=aggr_vals, mode='lines', fill='tonexty', fillcolor='rgba(200,200,200,0.2)', line=dict(width=0), name='Range'))
                 
                 # Paths
                 def plot_path(res, color, name, dash=None):
                    if 'projection_path' in res:
                        p = res['projection_path']
                        fig_forecast.add_trace(go.Scatter(x=[x['date'] for x in p], y=[x['price'] for x in p], 
                                                        mode='lines', name=name, line=dict(color=color, dash=dash, width=3 if not dash else 2)))
                 
                 plot_path(active_res, active_color, f"Active: {active_name}")
                 plot_path(alt_res, alt_color, f"Alt: {alt_name}", 'dot')
                 
                 # Add Realized Actuals if available
                 chart_title = f"{ticker} Forecast"

                 fig_forecast.update_layout(
                     title=chart_title, 
                     height=500, 
                     hovermode='x unified',
                     xaxis=dict(range=[today - pd.Timedelta(days=10), end_of_2026 + pd.Timedelta(days=15)]) # Buffer to show Dec 2026
                 )
                 st.plotly_chart(fig_forecast, use_container_width=True)
                 
                 # Save Button
                 from utils.forecast_tracker import save_forecast
                 if st.button("💾 Save Forecast", key=f"save_{ticker}"):
                    if save_forecast(ticker, current_price, forecast_baseline, "2026-12-31", active_name, backtest_res.get('confidence'), backtest_res.get('years_tested', [])):
                        st.success("✅ Saved!")

            else:
                 st.warning("Insufficient data for forecast")

         except Exception as e:
            st.error(f"Analysis error: {str(e)}")
            st.info("Check logs for details")
            

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_portfolio_file(file_bytes, filename):
    """Load and validate portfolio CSV with caching"""
    import io
    df = pd.read_csv(io.BytesIO(file_bytes))
    
    # Validate columns
    required_columns = ['Symbol', 'Company Name']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"CSV must contain columns: {', '.join(required_columns)}")

    # Security: Sanitize inputs to prevent injection checks
    # Use local import if not globally available, but we added it to global imports
    from utils.security import sanitize_ticker, sanitize_llm_input
    
    try:
        # 1. Sanitize Tickers (Strict Regex)
        df['Symbol'] = df['Symbol'].astype(str).apply(sanitize_ticker)
        
        # 2. Sanitize Company Names (LLM Prompt Injection Prevention)
        df['Company Name'] = df['Company Name'].astype(str).apply(lambda x: sanitize_llm_input(x, max_length=100))
        
        # 3. Drop invalid rows
        initial_len = len(df)
        df = df.dropna(subset=['Symbol'])
        dropped = initial_len - len(df)
        
        if dropped > 0:
            print(f"⚠️ Security: Dropped {dropped} rows with invalid/malicious tickers")
            
    except Exception as e:
        raise ValueError(f"Sanitization failed: {str(e)}")
    
    return df

def show_portfolio_analysis_tab(max_parallel: int):
    """
    Unified Portfolio Analysis Tab (Merged Tab 1 & Analytics)
    Contains:
    1. Upload & Report Generation
    2. Advanced Analytics Tools (Correlation, Rebalancing)
    """
    # st.header("📤 Portfolio Analysis") # Already in tab name? No, title helps.
    
    sub_tab1, sub_tab2 = st.tabs(["📊 Report Generator", "🧪 Analytics Lab"])
    
    with sub_tab1:
        render_upload_section(max_parallel)
        
    with sub_tab2:
        render_analytics_section()

def render_upload_section(max_parallel: int):
    """Show the upload and analysis tab"""
    from rover_tools.ticker_resources import get_common_tickers
    from utils.portfolio_manager import PortfolioManager
    
    st.header("Upload Portfolio")

    # Mode Selection
    input_mode = st.radio(
        "Choose Input Method",
        ["📂 Upload CSV File", "✏️ Create Manually"],
        horizontal=True,
        help="Upload an existing CSV or create a portfolio from scratch."
    )
    
    df = None
    filename = None
    pm = PortfolioManager()
    saved_names = pm.get_portfolio_names()
    
    if input_mode == "📂 Upload CSV File":
        # Case 1: File upload
        uploaded_file = st.file_uploader(
            "Choose your Portfolio CSV file",
            type=['csv'],
            help="Upload a CSV file with columns: Symbol, Company Name, Quantity, Average Price"
        )
        
        if uploaded_file is not None:
            try:
                # Use cached loading
                file_bytes = uploaded_file.read()
                df = load_portfolio_file(file_bytes, uploaded_file.name)
                filename = uploaded_file.name
                st.success(f"✅ Portfolio loaded: {len(df)} stocks")
            except Exception as e:
                st.error(f"❌ Error reading CSV: {str(e)}")
                
    else:
        # Case 2: Manual Creation
        
        # Load Saved Portfolios
        saved_names = pm.get_portfolio_names()
        
        col_load, col_custom = st.columns([2, 1])
        with col_load:
            if saved_names:
                selected_load = st.selectbox("📂 Load Saved Portfolio", ["-- Select --"] + saved_names, key="load_portfolio_select")
                if selected_load != "-- Select --":
                    loaded_df = pm.get_portfolio(selected_load)
                    if loaded_df is not None:
                        st.session_state.manual_portfolio_df = loaded_df
                        st.toast(f"Loaded '{selected_load}'")
            else:
                 st.info("No saved portfolios yet.")
                 
        with col_custom:
             allow_custom = st.toggle("Allow Custom Symbols", help="Enable free text entry for symbols not in the list.")

        # Initialize Data
        if 'manual_portfolio_df' not in st.session_state:
            st.session_state.manual_portfolio_df = pd.DataFrame(columns=['Symbol', 'Company Name', 'Quantity', 'Average Price'])
            if st.session_state.manual_portfolio_df.empty:
                 st.session_state.manual_portfolio_df = pd.DataFrame(
                    [{"Symbol": "", "Company Name": "", "Quantity": 0, "Average Price": 0.0}] * 5
                )

        # Configure Column Types
        if allow_custom:
            symbol_col = st.column_config.TextColumn("Symbol (Custom)", help="Enter full ticker (e.g. INFBEES.NS)", required=True)
        else:
            symbol_col = st.column_config.SelectboxColumn(
                options=get_common_tickers(),
                required=True
            )
            
        from config import MAX_STOCKS_PER_PORTFOLIO
        
        # Check current length and warn
        current_rows = len(st.session_state.manual_portfolio_df)
        if current_rows > MAX_STOCKS_PER_PORTFOLIO:
             st.error(f"⚠️ You have {current_rows} stocks. Maximum allowed is {MAX_STOCKS_PER_PORTFOLIO}. Please remove some before saving.")
        else:
             st.caption(f"ℹ️ Limit: {MAX_STOCKS_PER_PORTFOLIO} stocks per portfolio.")

        edited_df = st.data_editor(
            st.session_state.manual_portfolio_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Symbol": symbol_col,
                "Company Name": st.column_config.TextColumn("Company Name", help="Auto-filled if using dropdown"),
                "Quantity": st.column_config.NumberColumn("Quantity", min_value=0, step=1),
                "Average Price": st.column_config.NumberColumn("Avg Price", min_value=0.0, format="₹ %.2f")
            },
            key="portfolio_editor"
        )
        
        # Process Edited Data
        if edited_df is not None:
             valid_df = edited_df[edited_df["Symbol"].astype(str).str.strip() != ""].copy()
             
             # Post-process symbols if using dropdown (split ' - ')
             if not allow_custom and not valid_df.empty:
                 def parse_row(row):
                     val = str(row['Symbol'])
                     if " - " in val:
                         parts = val.split(" - ")
                         ticker = parts[0]
                         comp = parts[1] if len(parts) > 1 else ""
                         # Fill company name if empty
                         if not row['Company Name'] or row['Company Name'] == "":
                             row['Company Name'] = comp
                         row['Symbol'] = ticker
                     return row
                 
                 valid_df = valid_df.apply(parse_row, axis=1)
             
                 if not valid_df.empty:
                     df = valid_df
                     filename = f"manual_portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


    # Common Preview & Analysis Logic
    if df is not None and not df.empty:
        # SAVE SECTION (Available for both Upload and Manual)
        with st.expander("💾 Save / Manage Portfolios"):
             col_sched_1, col_sched_2 = st.columns([3, 1])
             with col_sched_1:
                 save_name = st.text_input("Save as New Portfolio", placeholder="e.g., My October Holdings")
             with col_sched_2:
                 st.write("") # align
                 st.write("")
                 if st.button("Save", key="btn_save_pf_common"):
                      success, msg = pm.save_portfolio(save_name, df)
                      if success:
                          st.success(msg)
                          st.rerun()
                      else:
                          st.error(msg)
             
             # Delete option
             if saved_names:
                  st.markdown("---")
                  col_del_1, col_del_2 = st.columns([3, 1])
                  with col_del_1:
                      to_delete = st.selectbox("Delete Saved Portfolio", saved_names, key="del_pf_select_common")
                  with col_del_2:
                      st.write("")
                      st.write("")
                      if st.button("Delete", key="btn_del_pf_common"):
                          pm.delete_portfolio(to_delete)
                          st.rerun()

        if input_mode == "📂 Upload CSV File":
             # Preview only for upload mode
             st.subheader("📋 Portfolio Preview")
             st.dataframe(df, width="stretch")
             
        # Analysis button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 Analyze Portfolio", type="primary", width="stretch"):
                # Check rate limit
                allowed, message = st.session_state.portfolio_limiter.is_allowed()
                if not allowed:
                    st.error(f"⏱️ {message}")
                    st.info("Portfolio analysis is resource-intensive. Please wait before retrying.")
                else:
                    run_analysis(df, filename, max_parallel)
    
    elif input_mode == "📂 Upload CSV File":
        # Show example format if no file uploaded
        st.info("ℹ️ Upload a CSV file or switch to 'Create Manually' mode.")
        with st.expander("📄 See example CSV format"):
            example_df = pd.DataFrame({
                'Symbol': ['RELIANCE', 'TCS', 'INFY'],
                'Company Name': ['Reliance Industries Ltd', 'Tata Consultancy Services', 'Infosys Ltd'],
                'Quantity': [10, 5, 15],
                'Average Price': [2450.50, 3550.00, 1450.75]
            })
            st.dataframe(example_df, width="stretch")
            
            # Template Download
            template_csv = "Symbol,Company Name,Quantity,Average Price\nRELIANCE,Reliance Industries Ltd,10,2450.50\nTCS,Tata Consultancy Services,5,3550.00\nINFY,Infosys Ltd,15,1450.75"
            st.download_button(
                label="📥 Download Template CSV",
                data=template_csv,
                file_name="portfolio_template.csv",
                mime="text/csv",
                help="Download this sample as a CSV file to fill out."
            )
    
    # Add reports viewing section
    st.markdown("---")
    # Call the reports viewing functionality
    show_reports_tab()


def run_analysis(df: pd.DataFrame, filename: str, max_parallel: int):
    """Run portfolio analysis with improved progress tracking and error handling"""
    
    # Create job
    job_id = st.session_state.job_manager.create_job(filename, len(df))
    st.session_state.current_job_id = job_id
    st.session_state.job_manager.start_job(job_id)
    
    # Show progress
    st.subheader("⚡ Analysis in Progress")
    progress_bar = st.progress(0)
    status_text = st.empty()
    detail_text = st.empty()
    
    # Stock processing tracker
    total_stocks = len(df)
    processed_stocks = 0
    
    try:
        # Simulate progress updates (since CrewAI doesn't expose task-level hooks easily)
        # We'll update progress based on estimation
        status_text.text("🚀 Starting analysis...")
        progress_bar.progress(5)
        
        # Check if test mode is enabled
        if st.session_state.test_mode:
            # **MOCK MODE** - Simulate analysis without API calls
            status_text.text("🧪 Running in TEST MODE (mock data)...")
            detail_text.text("No API calls will be made")
            progress_bar.progress(10)
            
            # Simulate progress with delays
            stages = [
                (20, "📰 [MOCK] Scraping news articles..."),
                (40, "💭 [MOCK] Analyzing sentiment..."),
                (60, "📈 [MOCK] Evaluating market context..."),
                (80, "📝 [MOCK] Generating intelligence report..."),
            ]
            
            for pct, msg in stages:
                time.sleep(2)  # 2 second delay per stage
                progress_bar.progress(pct)
                status_text.text(msg)
                detail_text.text(f"Processing stocks: {', '.join(df['Symbol'].tolist())}")
            
            # Generate mock report
            stocks = df.to_dict('records')
            result = mock_generator.generate_mock_report(stocks)
            
        else:
            # **REAL MODE** - Actual API analysis
            
            # Save the current DataFrame to the default PORTFOLIO_FILE 
            # This ensures the agents (which read from disk) access the correct data
            try:
                from config import PORTFOLIO_FILE
                df.to_csv(PORTFOLIO_FILE, index=False)
                logger.info(f"Saved current analysis portfolio to {PORTFOLIO_FILE}")
            except Exception as e:
                logger.error(f"Failed to save temporary portfolio file: {e}")
                # We continue anyway, hoping the file exists or agents can handle it, 
                # but this log helps debugging.

            # Create crew
            crew = create_crew(max_parallel_stocks=max_parallel)
            
            # Start analysis
            status_text.text(f"📊 Analyzing {total_stocks} stocks in parallel...")
            detail_text.text("⏳ Loading portfolio data...")
            progress_bar.progress(10)
            
            # Run analysis (this will take time)
            # Update progress incrementally during execution
            import threading
            analysis_complete = False
            result = None
            error = None
            
            def run_crew():
                nonlocal result, error, analysis_complete
                try:
                    result = crew.run()
                except Exception as e:
                    error = e
                finally:
                    analysis_complete = True
            
            # Start crew in background thread
            thread = threading.Thread(target=run_crew)
            thread.start()
            
            # Simulate progress while waiting
            progress_steps = [
                (20, "📰 Scraping news articles..."),
                (40, "💭 Analyzing sentiment..."),
                (60, "📈 Evaluating market context..."),
                (80, "📝 Generating intelligence report..."),
            ]
            
            step_idx = 0
            while not analysis_complete and step_idx < len(progress_steps):
                time.sleep(15)  # Wait 15 seconds between updates
                if not analysis_complete:
                    pct, msg = progress_steps[step_idx]
                    progress_bar.progress(pct)
                    status_text.text(msg)
                    detail_text.text(f"Processing stocks: {', '.join(df['Symbol'].tolist())}")
                    step_idx += 1
            
            # Wait for thread to complete
            thread.join()
            
            # Check for errors
            if error:
                raise error
        
        # Complete
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        detail_text.text("")
        
        # Mark job complete
        st.session_state.job_manager.complete_job(job_id, result)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"market_rover_report_{timestamp}.txt"
        report_path = REPORT_DIR / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(" " * 25 + "MARKET ROVER 2.0 INTELLIGENCE REPORT\n")
            f.write(" " * 30 + f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            f.write(str(result))
        
        # Success message
        st.success(f"✅ Report saved: {report_filename}")
        st.session_state.analysis_complete = True
        
        # Generate visualizations
        st.subheader("📊 Visual Analytics")
        
        # Get stock data from portfolio
        stocks = df.to_dict('records')
        
        # Initialize visualizer
        visualizer = ReportVisualizer()
        
        # Create visualizations with mock data (in test mode) or extracted data (real mode)
        if st.session_state.test_mode:
            # Use mock data for visualizations
            sentiment_data = mock_generator.generate_sentiment_data(len(stocks) * 3)
            stock_risk_data = mock_generator.generate_stock_risk_data(stocks)
            news_timeline_data = mock_generator.generate_news_timeline(stocks)
        else:
            # Extract data from actual report using regex
            import re
            import json
            
            sentiment_data = {'positive': 0, 'negative': 0, 'neutral': 0}
            
            try:
                # Find JSON block in report
                report_text = str(result)
                json_match = re.search(r'```json\s*({.*?})\s*```', report_text, re.DOTALL)
                
                if json_match:
                    metadata = json.loads(json_match.group(1))
                    if 'sentiment_counts' in metadata:
                        counts = metadata['sentiment_counts']
                        sentiment_data = {
                            'positive': counts.get('positive', 0),
                            'negative': counts.get('negative', 0),
                            'neutral': counts.get('neutral', 0)
                        }
            except Exception as e:
                logger.error(f"Failed to parse sentiment JSON: {e}")
                # Fallback to simple regex on text if JSON fails
                sentiment_data['positive'] = len(re.findall(r'POSITIVE', str(result), re.IGNORECASE))
                sentiment_data['negative'] = len(re.findall(r'NEGATIVE', str(result), re.IGNORECASE))
                
            # Real Risk Calculation
            from rover_tools.market_analytics import MarketAnalyzer
            ma_risk = MarketAnalyzer()
            
            stock_risk_data = []
            for s in stocks:
                ticker_sym = s['Symbol']
                try:
                    r_score = ma_risk.calculate_risk_score(ticker_sym)
                except:
                    r_score = 50
                    
                stock_risk_data.append({
                    'symbol': ticker_sym, 
                    'company': s['Company Name'], 
                    'risk_score': r_score, 
                    'sentiment': 'neutral'
                })
            news_timeline_data = []
        
        # Display charts in columns
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment pie chart
            if sum(sentiment_data.values()) > 0:
                fig_sentiment = visualizer.create_sentiment_pie_chart(sentiment_data)
                st.plotly_chart(fig_sentiment, width="stretch")
        
        with col2:
            # Portfolio risk heatmap
            if stock_risk_data:
                fig_heatmap = visualizer.create_portfolio_heatmap(stock_risk_data)
                st.plotly_chart(fig_heatmap, width="stretch")
        
        # Individual stock risk gauges
        if stock_risk_data and len(stock_risk_data) <= 6:  # Show gauges for small portfolios
            st.markdown("### 🎯 Individual Stock Risk")
            gauge_cols = st.columns(min(3, len(stock_risk_data)))
            
            for idx, stock_data in enumerate(stock_risk_data):
                with gauge_cols[idx % 3]:
                    fig_gauge = visualizer.create_risk_gauge(
                        stock_data['risk_score'], 
                        stock_data['symbol']
                    )
                    st.plotly_chart(fig_gauge, width="stretch")
        
        # News timeline (if available)
        if news_timeline_data:
            st.markdown("### 📅 News Timeline")
            fig_timeline = visualizer.create_news_timeline(news_timeline_data)
            st.plotly_chart(fig_timeline, width="stretch")
        
        # Show report text in expander
        with st.expander("📄 Full Text Report", expanded=False):
            st.text(str(result)[:2000] + "..." if len(str(result)) > 2000 else str(result))
        
        # Download buttons
        st.markdown("### 📥 Download Report")
        download_col1, download_col2, download_col3 = st.columns(3)
        
        with download_col1:
            st.download_button(
                label="📄 Download TXT",
                data=str(result),
                file_name=report_filename.replace('.txt', '_text.txt'),
                mime="text/plain",
                width="stretch"
            )
        
        with download_col2:
            # HTML export with charts
            figures = []
            if sum(sentiment_data.values()) > 0:
                figures.append(visualizer.create_sentiment_pie_chart(sentiment_data))
            if stock_risk_data:
                figures.append(visualizer.create_portfolio_heatmap(stock_risk_data))
            
            html_path = REPORT_DIR / report_filename.replace('.txt', '.html')
            visualizer.export_to_html(figures, str(result), html_path)
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            st.download_button(
                label="🌐 Download HTML",
                data=html_content,
                file_name=report_filename.replace('.txt', '.html'),
                mime="text/html",
                width="stretch"
            )
        
        with download_col3:
            # CSV export (data only)
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📊 Download CSV",
                data=csv_data,
                file_name=report_filename.replace('.txt', '_data.csv'),
                mime="text/csv",
                width="stretch"
            )
    
    except Exception as e:
        # Mark job as failed
        st.session_state.job_manager.fail_job(job_id, str(e))
        try:
            track_error_detail(type(e).__name__, str(e), context={"location": "run_analysis", "job_id": job_id})
        except Exception:
            pass
        status_text.text("")
        detail_text.text("")
        
        # User-friendly error messages
        error_msg = str(e).lower()
        
        if "rate limit" in error_msg or "429" in error_msg:
            st.error("⏱️ **Rate Limit Reached**")
            st.warning("""
            The API rate limit has been exceeded. This happens when making too many requests in a short time.
            
            **What you can do:**
            - Wait 1-2 minutes and try again
            - Reduce the number of concurrent stocks in the sidebar (try 2-3 instead of 5)
            - Analyze smaller portfolios at a time
            
            **Technical details:** The Google Gemini API has usage limits to prevent abuse.
            """)
        
        elif "api" in error_msg and ("key" in error_msg or "auth" in error_msg):
            st.error("🔑 **API Authentication Error**")
            st.warning("""
            There's an issue with your API credentials.
            
            **What you can do:**
            - Check that your `.env` file contains a valid `GOOGLE_API_KEY`
            - Verify your API key is active at https://makersuite.google.com/app/apikey
            - Make sure the key hasn't expired
            """)
        
        elif "connection" in error_msg or "network" in error_msg:
            st.error("🌐 **Network Connection Error**")
            st.warning("""
            Unable to connect to the API services.
            
            **What you can do:**
            - Check your internet connection
            - Try again in a few moments
            - Check if a firewall is blocking the connection
            """)
        
        elif "portfolio" in error_msg or "csv" in error_msg:
            st.error("📊 **Portfolio Data Error**")
            st.warning(f"""
            There's an issue with the portfolio data.
            
            **Error details:** {str(e)}
            
            **What you can do:**
            - Verify your CSV has the required columns: Symbol, Company Name
            - Check that stock symbols are valid
            - Remove any special characters or formatting issues
            """)
        
        else:
            # Generic error
            st.error("❌ **Analysis Failed**")
            st.warning(f"""
            An unexpected error occurred during analysis.
            
            **Error details:** {str(e)}
            
            **What you can do:**
            - Try again with a smaller portfolio
            - Check the logs for more details
            - If the issue persists, contact support
            """)
        
        # Show error details in expander for debugging
        with st.expander("🔍 Technical Error Details (for debugging)"):
            st.code(str(e), language="text")


@st.cache_data(ttl=900)  # Cache for 15 minutes
def load_report_content(report_path_str):
    """Load report content with caching"""
    with open(report_path_str, 'r', encoding='utf-8') as f:
        return f.read()

def show_reports_tab():
    """Show the reports viewing tab"""
    
    st.header("📊 View Previous Reports")
    
    # List all reports
    if REPORT_DIR.exists():
        # Get all report files (both HTML and TXT)
        txt_reports = sorted(REPORT_DIR.glob("market_rover_report_*.txt"), reverse=True)
        html_reports = sorted(REPORT_DIR.glob("market_rover_report_*.html"), reverse=True)
        
        # Group reports by timestamp (basename without extension)
        report_groups = {}
        for txt_path in txt_reports:
            timestamp = txt_path.stem  # e.g., "market_rover_report_20251219_183658"
            if timestamp not in report_groups:
                report_groups[timestamp] = {}
            report_groups[timestamp]['txt'] = txt_path
        
        for html_path in html_reports:
            timestamp = html_path.stem
            if timestamp not in report_groups:
                report_groups[timestamp] = {}
            report_groups[timestamp]['html'] = html_path
        
        if report_groups:
            st.success(f"Found {len(report_groups)} reports")
            
            # Display reports (last 10)
            for timestamp in sorted(report_groups.keys(), reverse=True)[:10]:
                files = report_groups[timestamp]
                
                # Extract timestamp for display
                timestamp_str = timestamp.replace("market_rover_report_", "")
                try:
                    dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    display_name = dt.strftime("%B %d, %Y - %I:%M:%S %p")
                except Exception as e:
                    logger.debug(f"Failed to parse timestamp {timestamp_str}: {e}")
                    try:
                        track_error_detail(type(e).__name__, str(e), context={"location": "show_reports_tab", "timestamp_str": timestamp_str})
                    except Exception:
                        pass
                    display_name = timestamp_str
                
                # Determine available formats
                has_html = 'html' in files
                has_txt = 'txt' in files
                
                format_badges = []
                if has_html:
                    format_badges.append("📊 HTML")
                if has_txt:
                    format_badges.append("📄 TXT")
                
                with st.expander(f"📈 {display_name} - {' | '.join(format_badges)}"):
                    # Format selector
                    if has_html and has_txt:
                        view_format = st.radio(
                            "View Format:",
                            options=["HTML (with visualizations)", "Plain Text"],
                            horizontal=True,
                            key=f"format_{timestamp}"
                        )
                    elif has_html:
                        view_format = "HTML (with visualizations)"
                        st.info("📊 HTML report with interactive visualizations")
                    else:
                        view_format = "Plain Text"
                        st.info("📄 Text-only report")
                    
                    # Display content based on format
                    if view_format == "HTML (with visualizations)" and has_html:
                        # Display HTML report with visualizations
                        html_path = files['html']
                        
                        try:
                            # Use cached loading for better performance
                            html_content = load_report_content(str(html_path))
                            
                            # Use Streamlit's HTML component to render the full report
                            st.components.v1.html(html_content, height=800, scrolling=True)
                            
                        except Exception as e:
                                    st.error(f"❌ Error loading HTML report: {str(e)}")
                                    # Persist detailed error for daily aggregation
                                    try:
                                        track_error_detail(type(e).__name__, str(e), context={"location": "show_reports_tab", "file": str(html_path)})
                                    except Exception:
                                        pass
                                    # Fallback to TXT if available
                                    if has_txt:
                                        st.warning("Showing text version instead...")
                                        with open(files['txt'], 'r', encoding='utf-8') as f:
                                            st.text_area(
                                                "Report Content",
                                                f.read(),
                                                height=300,
                                                key=f"fallback_{timestamp}"
                                            )
                    
                    else:
                        # Display plain text report
                        txt_path = files['txt']
                        # Use cached loading
                        content = load_report_content(str(txt_path))
                        
                        st.text_area(
                            "Report Content",
                            content,
                            height=400,
                            key=f"txt_{timestamp}"
                        )
                    
                    # Download buttons
                    st.markdown("---")
                    download_cols = st.columns(3 if has_html and has_txt else 2)
                    
                    col_idx = 0
                    if has_txt:
                        with download_cols[col_idx]:
                            with open(files['txt'], 'r', encoding='utf-8') as f:
                                txt_content = f.read()
                            st.download_button(
                                label="📄 Download TXT",
                                data=txt_content,
                                file_name=files['txt'].name,
                                mime="text/plain",
                                key=f"download_txt_{timestamp}",
                                width="stretch"
                            )
                        col_idx += 1
                    
                    if has_html:
                        with download_cols[col_idx]:
                            with open(files['html'], 'r', encoding='utf-8') as f:
                                html_content = f.read()
                            st.download_button(
                                label="🌐 Download HTML",
                                data=html_content,
                                file_name=files['html'].name,
                                mime="text/html",
                                key=f"download_html_{timestamp}",
                                width="stretch"
                            )
        else:
            st.info("ℹ️ No reports found. Analyze a portfolio to generate reports.")
    else:
        st.info("ℹ️ Reports directory not found.")


def show_recent_reports():
    """Show recent reports in sidebar"""
    
    if REPORT_DIR.exists():
        reports = sorted(REPORT_DIR.glob("market_rover_report_*.txt"), reverse=True)
        
        if reports:
            for report_path in reports[:5]:  # Show last 5
                timestamp_str = report_path.stem.replace("market_rover_report_", "")
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    display_name = timestamp.strftime("%b %d, %Y %I:%M %p")
                except Exception as e:
                    logger.debug(f"Failed to parse timestamp {timestamp_str}: {e}")
                    try:
                        track_error_detail(type(e).__name__, str(e), context={"location": "show_recent_reports", "timestamp_str": timestamp_str})
                    except Exception:
                        pass
                    display_name = timestamp_str
                
                st.markdown(f"📄 {display_name}")
        else:
            st.markdown("*No reports yet*")
    else:
        st.markdown("*No reports yet*")


if __name__ == "__main__":
    main()
