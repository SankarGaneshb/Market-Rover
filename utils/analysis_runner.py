import streamlit as st
import pandas as pd
import time
import os
import threading
from datetime import datetime
from config import PORTFOLIO_FILE, REPORT_DIR
from crew_engine import create_crew
from utils.mock_data import mock_generator
from utils.report_visualizer import ReportVisualizer
from utils.logger import get_logger
from utils.metrics import track_error_detail
from rover_tools.shadow_tools import detect_silent_accumulation

logger = get_logger(__name__)

def get_user_report_dir():
    """Get the report directory for the current user."""
    username = st.session_state.get('username', 'guest')
    user_dir = REPORT_DIR / username
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

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

            

            analysis_complete = False

            result = None
            
            # Using a list to hold error to allow modification in closure if needed, though nonlocal works too
            error_container = []

            

            def run_crew():

                nonlocal result, analysis_complete

                try:

                    result = crew.run()

                except RuntimeError as re:

                    # Handle "cannot schedule new futures" error specifically
                    logger.error(f"RuntimeError in Crew execution: {re}")
                    error_container.append(Exception("Model Overload/Timeout. The AI model took too long or generated too much text. Please try analyzing fewer stocks or check your connection."))

                except Exception as e:

                    error_container.append(e)

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

            if error_container:

                raise error_container[0]

        

        # Complete

        progress_bar.progress(100)

        status_text.text("✅ Analysis complete!")

        detail_text.text("")

        

        # Mark job complete

        st.session_state.job_manager.complete_job(job_id, result)

        

        # Save report

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        report_filename = f"market_rover_report_{timestamp}.txt"

        target_dir = get_user_report_dir()
        report_path = target_dir / report_filename

        

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

            # Real Risk Calculation
            from rover_tools.market_analytics import MarketAnalyzer
            ma_risk = MarketAnalyzer()
            
            stock_risk_data = []
            
            # UX: Progress for Post-Analysis
            risk_progress = st.progress(0)
            risk_status = st.empty()
            
            # Collect Tickers for Correlation
            all_tickers = [s['Symbol'] for s in stocks]
            
            for i, s in enumerate(stocks):
                risk_status.text(f"📊 Calculating Risk Metrics for {s.get('Symbol')}...")
                risk_progress.progress((i + 1) / len(stocks))
                
                ticker_sym = s['Symbol']
                try:
                    r_score = ma_risk.calculate_risk_score(ticker_sym)
                except:
                    r_score = 50
                    
                # Shadow Score Calculation
                try:
                    shadow_res = detect_silent_accumulation(ticker_sym)
                    shadow_score = shadow_res.get('score', 0)
                    shadow_signals = ", ".join(shadow_res.get('signals', []))
                except Exception as e:
                    logger.error(f"Shadow score failed for {ticker_sym}: {e}")
                    shadow_score = 0
                    shadow_signals = "Error"

                stock_risk_data.append({
                    'symbol': ticker_sym, 
                    'company': s['Company Name'], 
                    'risk_score': r_score, 
                    'sentiment': 'neutral', # Could rely on previous sentiment logic if granuallar
                    'shadow_score': shadow_score,
                    'shadow_signals': shadow_signals
                })

            news_timeline_data = []

        # --- CORRELATION MATRIX ---
        risk_status.text("🔗 Calculating Correlation Matrix...")
        try:
            # Clean tickers
            clean_tickers = []
            for t in all_tickers:
                 full = f"{t}.NS" if '.' not in t else t
                 clean_tickers.append(full)
                 
            corr_matrix = ma_risk.calculate_correlation_matrix(clean_tickers)
        except Exception as e:
            logger.error(f"Correlation failed: {e}")
            corr_matrix = pd.DataFrame()

        # Display charts in columns
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment pie chart
            if sum(sentiment_data.values()) > 0:
                fig_sentiment = visualizer.create_sentiment_pie_chart(sentiment_data)
                fig_sentiment.update_layout(height=400) # Ensure fixed height
                st.plotly_chart(fig_sentiment, width="stretch", use_container_width=True)
        
        with col2:
            # Portfolio risk heatmap
            if stock_risk_data:
                fig_heatmap = visualizer.create_portfolio_heatmap(stock_risk_data)
                fig_heatmap.update_layout(height=400) # Ensure fixed height matches sentiment
                st.plotly_chart(fig_heatmap, width="stretch", use_container_width=True)

        # Row 2: Correlation & Individual Risk
        col3, col4 = st.columns(2)
        with col3:
             if not corr_matrix.empty:
                 # Use the new masked heatmap function
                 fig_corr = visualizer.create_correlation_heatmap(corr_matrix)
                 st.plotly_chart(fig_corr, width="stretch", use_container_width=True)
                 
        with col4:
             # Individual stock risk gauges (Top 3 Riskiest)
             if stock_risk_data:
                 sorted_risk = sorted(stock_risk_data, key=lambda x: x['risk_score'], reverse=True)[:3]
                 for idx, stock_data in enumerate(sorted_risk):
                     # Show mini-gauges
                     fig_gauge = visualizer.create_risk_gauge(
                         stock_data['risk_score'], 
                         stock_data['symbol']
                     )
                     fig_gauge.update_layout(height=130, margin=dict(l=20, r=20, t=30, b=20))
                     st.plotly_chart(fig_gauge, use_container_width=True)

        
        # --- REBALANCING ---
        st.markdown("### ⚖️ Rebalancing Opportunities")
        with st.expander("Show Rebalancing Strategies", expanded=True):
             # Quick Rebalance Preview
             # Transform data for rebalancer
             rebal_input = []
             for s in stocks:
                 # Estimate value if not present (Quantity * Price)
                 qty = s.get('Quantity', 10)
                 price = s.get('Average Price', 1000.0)
                 rebal_input.append({
                     'symbol': f"{s['Symbol']}.NS" if '.' not in s['Symbol'] else s['Symbol'],
                     'value': float(qty) * float(price)
                 })
             
             col_strategies = st.columns(2)
             
             # Helper for color-coded actions
             def color_action(val):
                 color = '#28a745' if val == 'Buy' else ('#dc3545' if val == 'Sell' else '#6c757d')
                 return f'color: {color}; font-weight: bold'

             # Risk Parity
             with col_strategies[0]:
                 st.markdown("**🛡️ Risk Parity**")
                 try:
                    res_safe, _ = ma_risk.analyze_rebalance(rebal_input, mode='safety')
                    if not res_safe.empty:
                        st.dataframe(
                            res_safe.style.applymap(color_action, subset=['action']),
                            width='stretch',
                            column_order=("symbol", "name", "current_weight", "target_weight", "action", "volatility", "return", "comment"),
                            column_config={
                                "symbol": "Ticker",
                                "name": "Company Name",
                                "current_weight": st.column_config.NumberColumn("Current %", format="%.1f%%"),
                                "target_weight": st.column_config.NumberColumn("Target %", format="%.1f%%"),
                                "volatility": st.column_config.NumberColumn("Volatility (Risk)", format="%.1f%%"),
                                "return": st.column_config.NumberColumn("Return (Annual)", format="%.1f%%"),
                                "action": "Action",
                                "comment": "Reasoning"
                            }
                        )
                 except:
                    st.caption("Not enough data")

             # Growth
             with col_strategies[1]:
                 st.markdown("**🚀 Growth Opt.**")
                 try:
                    res_growth, _ = ma_risk.analyze_rebalance(rebal_input, mode='growth')
                    if not res_growth.empty:
                         st.dataframe(
                            res_growth.style.applymap(color_action, subset=['action']),
                            width='stretch',
                            column_order=("symbol", "name", "current_weight", "target_weight", "action", "volatility", "return", "comment"),
                            column_config={
                                "symbol": "Ticker",
                                "name": "Company Name",
                                "current_weight": st.column_config.NumberColumn("Current %", format="%.1f%%"),
                                "target_weight": st.column_config.NumberColumn("Target %", format="%.1f%%"),
                                "volatility": st.column_config.NumberColumn("Volatility (Risk)", format="%.1f%%"),
                                "return": st.column_config.NumberColumn("Return (Annual)", format="%.1f%%"),
                                "action": "Action",
                                "comment": "Reasoning"
                            }
                        )
                 except:
                    st.caption("Not enough data")


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
            if not corr_matrix.empty:
                 figures.append(visualizer.create_correlation_heatmap(corr_matrix))
            
            html_path = target_dir / report_filename.replace('.txt', '.html')
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
            - Ensure symbols are valid (e.g. RELIANCE.NS)
            """)
        
        else:
             st.error(f"❌ Analysis Failed: {str(e)}")
             logger.error(f"Unknown analysis error: {e}")
