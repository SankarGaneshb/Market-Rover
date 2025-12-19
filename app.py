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


# Page configuration
st.set_page_config(
    page_title="Market-Rover 2.0",
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


def main():
    """Main application entry point"""
    
    # Header
    st.title("🔍 Market-Rover 2.0")
    st.markdown("**AI-Powered Stock Intelligence System**")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 About")
        st.markdown("""
        Market-Rover 2.0 analyzes your stock portfolio using AI agents to:
        - 📰 Scrape latest news
        - 💭 Analyze sentiment
        - 📈 Evaluate market context
        - 📝 Generate intelligence reports
        
        **Features:**
        - ⚡ Parallel processing (5x faster)
        - 📊 Interactive visualizations
        - 📄 Multiple export formats (HTML, PDF, CSV)
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
        
        st.markdown("---")
        st.markdown("### 📚 Recent Reports")
        show_recent_reports()
    
    # Main content area
    tab1, tab2 = st.tabs(["📤 Upload & Analyze", "📊 View Reports"])
    
    with tab1:
        show_upload_tab(max_parallel)
    
    with tab2:
        show_reports_tab()


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
            df = pd.read_csv(uploaded_file)
            
            # Validate columns
            required_columns = ['Symbol', 'Company Name']
            if not all(col in df.columns for col in required_columns):
                st.error(f"❌ CSV must contain columns: {', '.join(required_columns)}")
                return
            
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


def show_reports_tab():
    """Show the reports viewing tab"""
    
    st.header("📊 Analysis Reports")
    
    # List all reports
    if REPORT_DIR.exists():
        reports = sorted(REPORT_DIR.glob("market_rover_report_*.txt"), reverse=True)
        
        if reports:
            st.success(f"Found {len(reports)} reports")
            
            for report_path in reports[:10]:  # Show last 10 reports
                with st.expander(f"📄 {report_path.name}"):
                    with open(report_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    st.text_area(
                        "Report Content",
                        content,
                        height=300,
                        key=report_path.name
                    )
                    
                    st.download_button(
                        label="📥 Download",
                        data=content,
                        file_name=report_path.name,
                        mime="text/plain",
                        key=f"download_{report_path.name}"
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
