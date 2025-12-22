"""
Market-Rover 2.0 - Streamlit Web Application
Interactive portfolio analysis with real-time progress tracking and data visualizations
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime
import time

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from crew import create_crew
from config import UPLOAD_DIR, REPORT_DIR
from utils.job_manager import JobManager
from utils.mock_data import mock_generator, simulate_analysis_delay
from utils.report_visualizer import ReportVisualizer
from utils.logger import get_logger, log_analysis_start, log_analysis_complete, log_error
from utils.metrics import (get_api_usage, get_performance_stats, get_cache_stats, 
                           get_error_stats, track_performance, track_api_call)
from utils.visualizer_interface import generate_market_snapshot
from utils.security import sanitize_ticker, RateLimiter, validate_csv_content

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
        Charts, OI analysis, price targets
        
        **🔥 Monthly Heatmap**  
        History, trends, 2026 forecast
        
        ---
        
        **Features:** ⚡ Fast | 🔒 Secure | 📊 Interactive
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
        
        # Test mode toggle
        st.markdown("---")
        st.markdown("### 🧪 Testing")
        test_mode = st.checkbox(
            "Test Mode (No API Calls)",
            value=st.session_state.test_mode,
            help="Use mock data for testing without API rate limits"
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
            
            # Error Stats
            error_stats = get_error_stats()
            if error_stats['total'] > 0:
                st.markdown("**Errors**")
                st.metric("Total Errors", error_stats['total'])
                if error_stats['by_type']:
                    st.json(error_stats['by_type'], expanded=False)
            
            # Refresh button (note: refreshes entire app)
            if st.button("🔄 Refresh App", use_container_width=True, help="Refreshes the entire app to update all metrics"):
                st.rerun()
        
        st.markdown("---")
        # Make Recent Reports collapsible to save space
        with st.expander("📚 Recent Reports", expanded=False):
            show_recent_reports()
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📤 Portfolio Analysis", "📈 Market Visualizer", "🔥 Monthly Heatmap"])
    
    with tab1:
        show_upload_tab(max_parallel)
    
    with tab2:
        show_visualizer_tab()

    with tab3:
        show_heatmap_tab()
    
    # Disclaimer at bottom - always visible like a status bar
    st.markdown("---")
    st.caption("⚠️ **Disclaimer:** Market-Rover is for informational purposes only. Not financial advice. Past performance ≠ future results. Consult a qualified advisor. No liability for losses. By using this app, you accept these terms.")

def show_visualizer_tab():
    """Show the Market Visualizer tab (V3.0) - Generates comprehensive market snapshot image"""
    st.header("📈 Market Visualizer")
    st.markdown("Generate **comprehensive market snapshot** with Price Chart, OI Analysis, and Scenario Targets.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        ticker_raw = st.text_input("Enter Stock Ticker (e.g., SBIN, TCS)", value="SBIN", key="viz_ticker")
        
        if st.button("Generate Snapshot", type="primary", use_container_width=True, key="btn_viz"):
            # Sanitize input
            ticker = sanitize_ticker(ticker_raw)
            if not ticker:
                st.error("❌ Invalid ticker format. Please enter a valid stock symbol (e.g., SBIN, TCS, RELIANCE)")
                return
            
            # Check rate limit
            allowed, message = st.session_state.visualizer_limiter.is_allowed()
            if not allowed:
                st.warning(f"⏱️ {message}")
                remaining = st.session_state.visualizer_limiter.get_remaining()
                st.info(f"Remaining requests: {remaining}/30 per minute")
                return
                
            with st.spinner(f"🎨 Generating snapshot for {ticker}... This may take a minute."):
                try:
                    result = generate_market_snapshot(ticker)
                    
                    if result['success']:
                        st.success("✅ Snapshot generated successfully!")
                        
                        # Display Image
                        if result['image_path']:
                            st.image(result['image_path'], caption=f"Market Snapshot: {ticker}", use_container_width=True)
                        
                        # Display Summary
                        st.markdown("### 📝 Analysis Summary")
                        st.markdown(result['message'])
                        
                    else:
                        st.error("❌ Generation Failed")
                        st.error(result['message'])
                        
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
    
    with col2:
        st.info("💡 **Tip:** Use liquid stocks with F&O data for best results (Heatmap + OI Analysis).")
        st.markdown("""
        **What you get (Single composite image):**
        - 📊 **Price Chart**: 6-month price action with volatility bands and scenario targets
        - 🌡️ **Monthly Heatmap**: Historical monthly returns matrix (color-coded)
        - 🧱 **OI Walls**: Support & Resistance levels from Options Open Interest
        - 🎯 **Scenario Targets**: Bull/Bear/Neutral price targets for current expiry
        
        **Output:** Premium dashboard image (PNG) with all 4 panels combined
        """)

def show_heatmap_tab():
    """Show the Monthly Heatmap & 2026 Forecast tab (V4.0) - Interactive historical analysis and predictions"""
    st.header("🔥 Monthly Heatmap & 2026 Forecast")
    st.markdown("Deep-dive into **historical monthly patterns** and get **AI-powered 2026 price predictions** with interactive charts.")
    
    # Compact input row at top
    col_input, col_button, col_info = st.columns([2, 2, 3])
    with col_input:
        ticker_raw = st.text_input("Stock Ticker", value="SBIN", key="heatmap_ticker", placeholder="e.g., SBIN, TCS")
    
    with col_button:
        st.write("")  # Spacer for alignment
        analyze_button = st.button("📊 Generate Analysis", type="primary", use_container_width=True, key="btn_heatmap")
    
    with col_info:
        with st.expander("ℹ️ What you get", expanded=False):
            st.markdown("""
            **Interactive Analysis:**
            - 🌡️ Monthly Heatmap (Year × Month returns)
            - 📅 Seasonality Trends (Best/worst months)
            - 🔮 2026 Forecast (Conservative/Baseline/Aggressive)
            - 📈 Projection Chart + Key Insights
            """)
    
    st.markdown("---")
    
    # Full-width area for chart display
    if analyze_button:
        # Sanitize input
        ticker = sanitize_ticker(ticker_raw)
        if not ticker:
            st.error("❌ Invalid ticker format. Please enter a valid stock symbol (e.g., SBIN, TCS, RELIANCE)")
            return
        
        # Check rate limit
        allowed, message = st.session_state.heatmap_limiter.is_allowed()
        if not allowed:
            st.warning(f"⏱️ {message}")
            remaining = st.session_state.heatmap_limiter.get_remaining()
            st.info(f"Remaining requests: {remaining}/20 per minute")
            return
            
        with st.spinner(f"🔥 Analyzing {ticker}... Fetching historical data & building forecast..."):
            try:
                # Import necessary modules
                from tools.market_data import MarketDataFetcher
                from tools.derivative_analysis import DerivativeAnalyzer
                import plotly.graph_objects as go
                import plotly.express as px
                from plotly.subplots import make_subplots
                import pandas as pd
                import numpy as np
                
                # Fetch data
                fetcher = MarketDataFetcher()
                analyzer = DerivativeAnalyzer()
                
                st.info(f"📥 Fetching historical data for {ticker}...")
                history = fetcher.fetch_full_history(ticker)
                
                if history.empty:
                    st.error(f"❌ Could not fetch data for {ticker}")
                    return
                
                # Calculate monthly returns matrix
                st.info("🧮 Calculating monthly returns...")
                returns_matrix = analyzer.calculate_monthly_returns_matrix(history)
                
                # Calculate seasonality
                seasonality_stats = analyzer.calculate_seasonality(history)
                
                # Display success
                st.success(f"✅ Analysis complete! Analyzed {len(history)} trading days")
                
                # === VISUALIZATION 1: Monthly Returns Heatmap ===
                st.markdown("### 🌡️ Monthly Returns Heatmap")
                st.markdown(f"**Historical performance matrix showing monthly % returns for {ticker}**")
                
                if not returns_matrix.empty:
                    fig_heatmap = px.imshow(
                        returns_matrix,
                        labels=dict(x="Month", y="Year", color="Return %"),
                        x=returns_matrix.columns,
                        y=returns_matrix.index,
                        color_continuous_scale="RdYlGn",
                        color_continuous_midpoint=0,
                        aspect="auto",
                        text_auto=".1f"
                    )
                    fig_heatmap.update_layout(
                        title=f"{ticker} - Monthly Returns Heatmap (% Change)",
                        height=600,  # Increased from 500
                        xaxis_title="Month",
                        yaxis_title="Year"
                    )
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                else:
                    st.warning("No monthly data available for heatmap")
                
                # === VISUALIZATION 2: Seasonality Analysis ===
                st.markdown("### 📅 Seasonality Trends")
                st.markdown("**Which months historically perform best?**")
                
                if seasonality_stats:
                    months = list(seasonality_stats.keys())
                    avg_returns = [seasonality_stats[m]['mean'] * 100 for m in months]
                    
                    fig_seasonality = go.Figure()
                    fig_seasonality.add_trace(go.Bar(
                        x=months,
                        y=avg_returns,
                        marker_color=['green' if x > 0 else 'red' for x in avg_returns],
                        text=[f"{x:.2f}%" for x in avg_returns],
                        textposition='auto'
                    ))
                    fig_seasonality.update_layout(
                        title=f"{ticker} - Average Monthly Performance",
                        xaxis_title="Month",
                        yaxis_title="Average Return (%)",
                        height=450  # Increased from 400
                    )
                    st.plotly_chart(fig_seasonality, use_container_width=True)
                
                # === VISUALIZATION 3: 2026 Forecast ===
                st.markdown("### 🔮 2026 Forecast")
                st.markdown("**AI-powered prediction based on 2025 YTD performance**")
                
                # Get current price
                current_price = history['Close'].iloc[-1]
                
                # Calculate 2025 YTD growth rate
                today = pd.Timestamp.now()
                start_of_2025 = pd.Timestamp('2025-01-01')
                
                # Make start_of_2025 timezone-aware if history index is timezone-aware
                if history.index.tz is not None:
                    start_of_2025 = start_of_2025.tz_localize(history.index.tz)
                    if today.tz is None:
                        today = today.tz_localize(history.index.tz)
                
                # Filter for 2025 data
                history_2025 = history[history.index >= start_of_2025]
                
                if len(history_2025) > 0:
                    price_start_2025 = history_2025['Close'].iloc[0]
                    price_current = history_2025['Close'].iloc[-1]
                    
                    # Calculate YTD return
                    ytd_return = ((price_current / price_start_2025) - 1) * 100
                    
                    # Annualize the YTD return
                    # Use timezone-aware today for calculation
                    days_elapsed_2025 = (today - start_of_2025).days
                    if days_elapsed_2025 > 0:
                        annual_growth = (((price_current / price_start_2025) ** (365 / days_elapsed_2025)) - 1) * 100
                    else:
                        annual_growth = 0
                else:
                    # Fallback to 1-year if no 2025 data
                    if len(history) >= 252:
                        year_ago_price = history['Close'].iloc[-252]
                        annual_growth = ((current_price / year_ago_price) - 1) * 100
                        ytd_return = annual_growth
                    else:
                        annual_growth = 0
                        ytd_return = 0
                
                # Project to 2026 - ensure end_of_2026 is also timezone-aware
                end_of_2026 = pd.Timestamp('2026-12-31')
                if history.index.tz is not None:
                    end_of_2026 = end_of_2026.tz_localize(history.index.tz)
                
                days_to_2026 = (end_of_2026 - today).days
                years_fraction = days_to_2026 / 365
                
                # Conservative, baseline, and aggressive scenarios based on 2025 performance
                conservative_growth = annual_growth * 0.5  # Half the 2025 rate
                baseline_growth = annual_growth  # Same as 2025
                aggressive_growth = annual_growth * 1.5  # 1.5x the 2025 rate
                
                forecast_conservative = current_price * (1 + conservative_growth/100) ** years_fraction
                forecast_baseline = current_price * (1 + baseline_growth/100) ** years_fraction
                forecast_aggressive = current_price * (1 + aggressive_growth/100) ** years_fraction
                
                # Display forecast - now in full width
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.metric(
                        "� Current Price",
                        f"₹{current_price:.2f}",
                        f"{annual_growth:.1f}% p.a."
                    )
                with col_b:
                    st.metric(
                        "� Conservative",
                        f"₹{forecast_conservative:.2f}",
                        f"+{((forecast_conservative/current_price - 1) * 100):.1f}%"
                    )
                with col_c:
                    st.metric(
                        "� Baseline",
                        f"₹{forecast_baseline:.2f}",
                        f"+{((forecast_baseline/current_price - 1) * 100):.1f}%"
                    )
                with col_d:
                    st.metric(
                        "🐂 Aggressive",
                        f"₹{forecast_aggressive:.2f}",
                        f"+{((forecast_aggressive/current_price - 1) * 100):.1f}%"
                    )
                
                # Projection chart - full width
                projection_dates = pd.date_range(today, end_of_2026, freq='ME')
                conservative_proj = [current_price * (1 + conservative_growth/100) ** ((d - today).days/365) for d in projection_dates]
                baseline_proj = [current_price * (1 + baseline_growth/100) ** ((d - today).days/365) for d in projection_dates]
                aggressive_proj = [current_price * (1 + aggressive_growth/100) ** ((d - today).days/365) for d in projection_dates]
                
                fig_forecast = go.Figure()
                fig_forecast.add_trace(go.Scatter(
                    x=projection_dates, y=conservative_proj,
                    mode='lines', name='Conservative',
                    line=dict(color='red', dash='dash', width=2)
                ))
                fig_forecast.add_trace(go.Scatter(
                    x=projection_dates, y=baseline_proj,
                    mode='lines', name='Baseline',
                    line=dict(color='blue', width=4)
                ))
                fig_forecast.add_trace(go.Scatter(
                    x=projection_dates, y=aggressive_proj,
                    mode='lines', name='Aggressive',
                    line=dict(color='green', dash='dash', width=2)
                ))
                
                # Add current price as starting point
                fig_forecast.add_trace(go.Scatter(
                    x=[today],
                    y=[current_price],
                    mode='markers',
                    name='Current Price',
                    marker=dict(color='orange', size=12, symbol='star')
                ))
                
                fig_forecast.update_layout(
                    title=f"{ticker} - 2026 Price Projection (Based on 2025 YTD: {annual_growth:.1f}% annualized)",
                    xaxis_title="Date",
                    yaxis_title="Price (₹)",
                    height=500,  # Increased from 400
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                st.plotly_chart(fig_forecast, use_container_width=True)
                
                # Summary insights - compact
                st.markdown("### 📝 Key Insights")
                best_month = max(seasonality_stats.items(), key=lambda x: x[1]['mean'])[0] if seasonality_stats else "N/A"
                worst_month = min(seasonality_stats.items(), key=lambda x: x[1]['mean'])[0] if seasonality_stats else "N/A"
                
                col_insight1, col_insight2 = st.columns(2)
                with col_insight1:
                    st.markdown(f"""
                    - **Best Historical Month:** {best_month}
                    - **Worst Historical Month:** {worst_month}
                    - **2026 Baseline Target:** ₹{forecast_baseline:.2f}
                    """)
                with col_insight2:
                    st.markdown(f"""
                    - **Projected Annual Return:** {baseline_growth:.2f}%
                    - **Potential Upside:** +{((forecast_aggressive/current_price - 1) * 100):.1f}%
                    - **Data Range:** {history.index[0].strftime('%Y-%m-%d')} to {history.index[-1].strftime('%Y-%m-%d')}
                    """)
                
            except Exception as e:
                st.error(f"❌ Analysis Failed: {str(e)}")
                with st.expander("🔍 Error Details"):
                    st.code(str(e))


@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_portfolio_file(file_bytes, filename):
    """Load and validate portfolio CSV with caching"""
    import io
    df = pd.read_csv(io.BytesIO(file_bytes))
    
    # Validate columns
    required_columns = ['Symbol', 'Company Name']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"CSV must contain columns: {', '.join(required_columns)}")
    
    return df

def show_upload_tab(max_parallel: int):
    """Show the upload and analysis tab"""
    
    st.header("Upload Portfolio")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose your Portfolio CSV file",
        type=['csv'],
        help="Upload a CSV file with columns: Symbol, Company Name, Quantity, Average Price"
    )
    
    if uploaded_file is not None:
        # Display portfolio preview
        try:
            # Use cached loading for better performance
            file_bytes = uploaded_file.read()
            df = load_portfolio_file(file_bytes, uploaded_file.name)
            
            st.success(f"✅ Portfolio loaded: {len(df)} stocks")
            
            # Portfolio preview
            st.subheader("📋 Portfolio Preview")
            st.dataframe(df, use_container_width=True)
            
            # Analysis button
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                if st.button("🚀 Analyze Portfolio", type="primary", use_container_width=True):
                    run_analysis(df, uploaded_file.name, max_parallel)
        
        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")
    
    else:
        # Show example format
        st.info("ℹ️ Upload a CSV file to get started")
        with st.expander("📄 See example CSV format"):
            example_df = pd.DataFrame({
                'Symbol': ['RELIANCE', 'TCS', 'INFY'],
                'Company Name': ['Reliance Industries Ltd', 'Tata Consultancy Services', 'Infosys Ltd'],
                'Quantity': [10, 5, 15],
                'Average Price': [2450.50, 3550.00, 1450.75]
            })
            st.dataframe(example_df, use_container_width=True)
    
    # Add reports viewing section
    st.markdown("---")
    st.subheader("📊 View Previous Reports")
    
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
            # Extract data from actual report (simplified for now)
            # In a real implementation, would parse the report text
            sentiment_data = {'positive': 5, 'negative': 3, 'neutral': 4}
            stock_risk_data = [
                {'symbol': s['Symbol'], 'company': s['Company Name'], 
                 'risk_score': 50, 'sentiment': 'neutral'} 
                for s in stocks
            ]
            news_timeline_data = []
        
        # Display charts in columns
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment pie chart
            if sum(sentiment_data.values()) > 0:
                fig_sentiment = visualizer.create_sentiment_pie_chart(sentiment_data)
                st.plotly_chart(fig_sentiment, use_container_width=True)
        
        with col2:
            # Portfolio risk heatmap
            if stock_risk_data:
                fig_heatmap = visualizer.create_portfolio_heatmap(stock_risk_data)
                st.plotly_chart(fig_heatmap, use_container_width=True)
        
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
                    st.plotly_chart(fig_gauge, use_container_width=True)
        
        # News timeline (if available)
        if news_timeline_data:
            st.markdown("### 📅 News Timeline")
            fig_timeline = visualizer.create_news_timeline(news_timeline_data)
            st.plotly_chart(fig_timeline, use_container_width=True)
        
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
                use_container_width=True
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
                use_container_width=True
            )
        
        with download_col3:
            # CSV export (data only)
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📊 Download CSV",
                data=csv_data,
                file_name=report_filename.replace('.txt', '_data.csv'),
                mime="text/csv",
                use_container_width=True
            )
    
    except Exception as e:
        # Mark job as failed
        st.session_state.job_manager.fail_job(job_id, str(e))
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
    
    st.header("📊 Analysis Reports")
    
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
                except:
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
                                use_container_width=True
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
                                use_container_width=True
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
                except:
                    display_name = timestamp_str
                
                st.markdown(f"📄 {display_name}")
        else:
            st.markdown("*No reports yet*")
    else:
        st.markdown("*No reports yet*")


if __name__ == "__main__":
    main()
