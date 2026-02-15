import streamlit as st
import pandas as pd
from rover_tools.ticker_resources import (
    get_common_tickers, 
    NIFTY_50_SECTOR_MAP, 
    NIFTY_50_BRAND_META,
    NIFTY_MIDCAP_SECTOR_MAP,
    NIFTY_NEXT_50_SECTOR_MAP,
    get_ticker_name
)
from utils.security import sanitize_ticker
import base64
import html
import urllib.parse
from utils.visualizer_interface import generate_market_snapshot
from rover_tools.visualizer_tool import run_snapshot_logic

# Shared function to run analysis and render UI
def run_analysis_ui(ticker_raw, limiter, key_prefix="default", global_outlier=False, lookback_period="5y+ (Max)"):
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
            
            # Use global setting passed from parent
            exclude_outliers = global_outlier

            # Apply Time Filter
            if lookback_period != "5y+ (Max)":
                 try:
                     # Parse logic: 1y -> 365 days, etc.
                     years_map = {"1y": 1, "3y": 3, "5y": 5}
                     years = years_map.get(lookback_period, 5)
                     
                     cutoff_date = pd.Timestamp.now() - pd.DateOffset(years=years)
                     
                     # Ensure timezone awareness compatibility
                     if history.index.tz is not None:
                          if cutoff_date.tz is None:
                               cutoff_date = cutoff_date.tz_localize(history.index.tz)
                     else:
                          if cutoff_date.tz is not None:
                               cutoff_date = cutoff_date.tz_localize(None)

                     history = history[history.index >= cutoff_date]
                     
                     if history.empty:
                          st.warning(f"⚠️ No data found for the last {lookback_period}.")
                          return
                     

                 except Exception as ex:
                     st.error(f"Error applying time filter: {ex}")

            if exclude_outliers:
                st.info(f"ℹ️ **Robust Analysis Enabled**: Outliers removed from Heatmap, Seasonality, Forecast Trends, and Filter Strategy. Analysis filtered to last {lookback_period}.")

            # Calculate monthly returns matrix
            returns_matrix = analyzer.calculate_monthly_returns_matrix(history, exclude_outliers=exclude_outliers)
            seasonality_stats = analyzer.calculate_seasonality(history, exclude_outliers=exclude_outliers)
            
            from utils.celebration import trigger_celebration
            trigger_celebration("Analysis_Complete", f"Completed analysis for {ticker}", {"ticker": ticker})
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
                st.plotly_chart(fig_heatmap, key=f"{key_prefix}_heatmap_chart", width="stretch")
                
                # Download Button for Heatmap Data (Added in V4.1)
                csv = returns_matrix.to_csv().encode('utf-8')
                st.download_button(
                    label="📥 Download Matrix (CSV)",
                    data=csv,
                    file_name=f"{ticker}_monthly_returns.csv",
                    mime="text/csv",
                    key=f"{key_prefix}_download_heatmap_{ticker}"
                )

            else:
                st.warning("Not enough data for heatmap")

            # === VISUALIZATION 2: Seasonality Profile ===
            st.markdown("### 📊 Seasonality Profile")
            
            if not seasonality_stats.empty:
                from plotly.subplots import make_subplots
                
                # Create figure with secondary y-axis
                fig_seasonality = make_subplots(specs=[[{"secondary_y": True}]])

                # 1. Avg Return (Bars) - Primary Y
                colors = ['green' if x > 0 else 'red' for x in seasonality_stats['Avg_Return']]
                fig_seasonality.add_trace(
                    go.Bar(
                        x=seasonality_stats['Month_Name'],
                        y=seasonality_stats['Avg_Return'],
                        name="Avg Return %",
                        marker_color=colors,
                        text=seasonality_stats['Avg_Return'],
                        texttemplate='%{y:.1f}%',
                        hovertemplate='%{y:.1f}%',
                        textposition='auto',
                        opacity=0.7
                    ),
                    secondary_y=False
                )

                # 2. Win Rate (Line) - Secondary Y
                fig_seasonality.add_trace(
                    go.Scatter(
                        x=seasonality_stats['Month_Name'],
                        y=seasonality_stats['Win_Rate'],
                        name="Win Rate %",
                        mode='lines+markers+text',
                        line=dict(color='gold', width=3),
                        marker=dict(size=8, color='gold'),
                        text=seasonality_stats['Win_Rate'],
                        texttemplate='%{y:.0f}%',
                        hovertemplate='%{y:.1f}%',
                        textposition='top center'
                    ),
                    secondary_y=True
                )

                # Layout
                fig_seasonality.update_layout(
                    title="Seasonality: Return vs. Probability",
                    height=500,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    hovermode="x unified"
                )

                # Axis Titles
                fig_seasonality.update_yaxes(title_text="Avg Return %", secondary_y=False)
                fig_seasonality.update_yaxes(title_text="Win Rate %", range=[0, 110], secondary_y=True, showgrid=False)

                st.plotly_chart(fig_seasonality, use_container_width=True)
                
                st.caption("📊 **Combined Profile**: Bars represent the average return (Magnitude), while the Gold Line shows the % of positive months (consistency/probability).")

            

            st.markdown("---")

            # === VISUALIZATION 3: 2026 Forecast ===

            st.markdown("### 🔮 2026 Forecast")

            

            # Run Backtest

            with st.spinner("🔄 Backtesting strategies..."):

                backtest_res = analyzer.backtest_strategies(history, exclude_outliers=exclude_outliers)

            

            # Generate Forecasts

            forecast_median = analyzer.calculate_median_strategy_forecast(history, exclude_outliers=exclude_outliers)

            forecast_sd = analyzer.calculate_sd_strategy_forecast(history, exclude_outliers=exclude_outliers)

            

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

                 st.plotly_chart(fig_forecast, width="stretch")

                 

                 # Save Button

                 # Actions Row
                 col_dl, col_save = st.columns([1, 1])
                 
                 with col_dl:
                     # Prepare Download Data
                     # Reconstruct baseline for CSV consistency
                     base_vals = [curr_p] + [curr_p * (1 + baseline_growth/100)**((d-today).days/365.25) for d in dates_range]
                     
                     forecast_df = pd.DataFrame({
                         'Date': dates,
                         'Conservative (Low)': cons_vals,
                         'Baseline (Target)': base_vals,
                         'Aggressive (High)': aggr_vals
                     })
                     
                     st.download_button(
                         label="📥 Download Forecast Data",
                         data=forecast_df.to_csv(index=False).encode('utf-8'),
                         file_name=f"{ticker}_forecast_2026.csv",
                         mime="text/csv",
                         key=f"dl_forecast_{ticker}"
                     )

                 with col_save:
                     from utils.forecast_tracker import save_forecast
                     if st.button("💾 Save to Tracker", key=f"save_{ticker}", help="Save this forecast to track performance over time"):
                        # Get current user
                        curr_user = st.session_state.get('username', 'guest')
                        if save_forecast(ticker, current_price, forecast_baseline, "2026-12-31", active_name, backtest_res.get('confidence'), backtest_res.get('years_tested', []), username=curr_user):
                            from utils.celebration import trigger_celebration
                            trigger_celebration("Forecast_Saved", f"Saved forecast for {ticker}", {"ticker": ticker, "strategy": active_name})
                            st.success(f"✅ Saved for {curr_user}!")



            else:

                 st.warning("Insufficient data for forecast")



             

            # === SHARE ANALYSIS FEATURE ===
            try:
                with st.expander("📤 Download PDF Report", expanded=False):
                    st.caption("Generate a professional multi-page PDF report with watermarks to share with your network.")
                    
                    col_share_btn, col_share_links = st.columns([1, 2])
                    
                    with col_share_btn:
                        if st.button("📄 Generate PDF Report", key=f"snap_{key_prefix}_{ticker}", type="secondary"):
                            with st.spinner("Generating multi-page PDF (Direct)..."):
                                # Bypass Agent/LLM to avoid 429 Errors and Speed up
                                res = run_snapshot_logic(ticker)
                                
                                # Handle Strings (Errors)
                                if isinstance(res, str) and res.startswith("Error"):
                                    st.error(f"Report generation failed: {res}")
                                
                                # Handle Success Dict
                                elif isinstance(res, dict) and 'pdf_buffer' in res:
                                    pdf_buffer = res['pdf_buffer']
                                    
                                    # Provide Download Button
                                    st.download_button(
                                        label="⬇️ Download PDF",
                                        data=pdf_buffer,
                                        file_name=f"{ticker}_Market_Rover_Report.pdf",
                                        mime="application/pdf",
                                        key=f"dl_pdf_{ticker}"
                                    )
                                    
                                    from utils.celebration import trigger_celebration
                                    trigger_celebration("PDF_Generated", f"Generated report for {ticker}", {"ticker": ticker})
                                    st.success("✅ PDF Generated!")
                                    
                                    # Social Intent Links
                                    share_text = f"Check out my AI-powered analysis of {ticker} on Market-Rover! %23StockMarket %23{ticker} %23AI"
                                    
                                    st.markdown("##### 🔗 Share via:")
                                    s_col1, s_col2, s_col3 = st.columns(3)
                                    with s_col1:
                                        st.link_button("X (Twitter)", f"https://twitter.com/intent/tweet?text={share_text}")
                                    with s_col2:
                                        st.link_button("WhatsApp", f"https://wa.me/?text={share_text}")
                                    with s_col3:
                                        st.link_button("LinkedIn", f"https://www.linkedin.com/feed/?shareActive=true&text={share_text}") 
                                        
                                else:
                                    st.error(f"Report generation failed: Unknown response format.")
            except Exception as ex:
                st.warning(f"Share feature unavailable: {str(ex)}")

         except Exception as e:

            st.error(f"Analysis error: {str(e)}")

            st.info("Check logs for details")


def render_visual_ticker_selector(ticker_category):
    """
    Renders a visual, card-based selector for tickers, grouped by sector.
    Returns the selected ticker if one was clicked, else None.
    """
    selected_ticker = None
    
    # Determine which map to use
    sector_map = {}
    if ticker_category == "Nifty 50":
        sector_map = NIFTY_50_SECTOR_MAP
    elif ticker_category == "Sensex":
        sector_map = NIFTY_50_SECTOR_MAP # 90% Overlap
    elif ticker_category == "Nifty Next 50":
        sector_map = NIFTY_NEXT_50_SECTOR_MAP
    elif ticker_category == "Midcap":
        sector_map = NIFTY_MIDCAP_SECTOR_MAP
        
    # Get tickers for this category
    category_tickers_full = get_common_tickers(category=ticker_category)
    # Extract clean tickers
    category_tickers = [t.split(' - ')[0].strip() for t in category_tickers_full]
    
    # If we have a map, use it
    if sector_map:
        # Filter map items that are in this category
        # For Sensex, we might have tickers in category that are in NIFTY_50_SECTOR_MAP
        # For those NOT in map, assign "Others"
        
        mapped_data = {}
        for ticker in category_tickers:
            # Check direct map
            if ticker in sector_map:
                mapped_data[ticker] = sector_map[ticker]
            # Check fallback to Nifty 50 map (common for Sensex)
            elif ticker in NIFTY_50_SECTOR_MAP:
                mapped_data[ticker] = NIFTY_50_SECTOR_MAP[ticker]
            else:
                 mapped_data[ticker] = "Others"
                 
        # Group by Sector
        sectors = sorted(list(set(mapped_data.values())))
        # Move "Others" to end
        if "Others" in sectors:
            sectors.remove("Others")
            sectors.append("Others")
            
        st.markdown("##### 📂 Browse by Sector")
        tabs = st.tabs(sectors)
        
        for i, sector in enumerate(sectors):
            with tabs[i]:
                # Get tickers in this sector
                curr_sector_tickers = [t for t, s in mapped_data.items() if s == sector]
                
                # Grid for cards
                cols = st.columns(4)
                for j, ticker in enumerate(curr_sector_tickers):
                    col = cols[j % 4]
                    meta = NIFTY_50_BRAND_META.get(ticker, {"name": ticker, "color": "#333333"})
                    
                    # Generate SVG Logo (consistent with Brand Shop)
                    # Clean ticker for display (strip .NS but keep full code)
                    tick_short = ticker.split('.')[0]
                    color = meta.get('color', "#333333")
                    text_color = "#000000" if color in ["#FFD200", "#FFF200"] else "#ffffff"
                    
                    # Use a slightly larger font size for the full ticker code if it fits better
                    font_size = "9" if len(tick_short) <= 5 else "7"
                    
                    svg_raw = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="{color}"/><text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" fill="{text_color}" font-family="Arial" font-weight="bold" font-size="{font_size}">{tick_short}</text></svg>'
                    b64_svg = base64.b64encode(svg_raw.encode('utf-8')).decode('utf-8')
                    icon_src = f"data:image/svg+xml;base64,{b64_svg}"
                    
                    with col:
                        # Card UI (Visual Only)
                        meta = NIFTY_50_BRAND_META.get(ticker, {"name": ticker, "color": "#333333"})
                        
                        # Robust Name Fetching
                        company_name = get_ticker_name(ticker)
                        safe_name = html.escape(company_name)
                        
                        st.markdown(f"""
                            <div style="background: white; border-radius: 8px; padding: 8px; border: 1px solid #eee; display: flex; align-items: center; margin-bottom: 5px;">
                                <img src="{icon_src}" style="width: 25px; height: 25px; margin-right: 8px; border-radius: 4px;">
                                <div style="line-height: 1.1;">
                                    <div style="font-weight: bold; font-size: 11px; color: #333;">{tick_short}</div>
                                    <div style="font-size: 9px; color: #666;">{safe_name}</div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Use a native button for selection to preserve session state
                        if st.button(f"Analyze", key=f"vis_sel_{ticker}", use_container_width=True):
                            st.session_state.heatmap_active_ticker = ticker
                            st.query_params["ticker"] = ticker
                            st.query_params["category"] = ticker_category
                            # Note: No 'tab' param here as it defaults back to Market Analysis
                            st.rerun()
    else:
        # Fallback for undefined maps (e.g. strict All or unknown)
        if len(category_tickers) <= 100:
            st.markdown(f"##### 🏢 {ticker_category} Stocks")
            cols = st.columns(5)
            for i, ticker in enumerate(category_tickers):
                tick_short = ticker.split('.')[0]
                with cols[i % 5]:
                    if st.button(tick_short, key=f"vis_{ticker}", use_container_width=True):
                        selected_ticker = ticker
                        
    return selected_ticker

def show_market_analysis_tab():

    """Show the Unified Market Analysis Tab"""

    st.header("🔍 Market Analysis")

    st.markdown("Deep-dive into **historical patterns** and get **AI-powered predictions** for individual Stocks or Market Indices.")

    

    mode_col, setting_col = st.columns([1, 1])
    with mode_col:
        analysis_mode = st.radio("Analysis Mode:", ["Stock Analysis 🏢", "Benchmark/Index 📊"], index=1, horizontal=True, label_visibility="collapsed")
    
    with setting_col:
        # Global Outlier Toggle
        exclude_outliers_global = st.checkbox("🚫 Exclude Outliers (Robust Mode)", value=False, help="Removes extreme volatility events from all analysis (Heatmap, Win Rate, Seasonality, Forecasts).")
        
        # Time Filter
        lookback_period = st.selectbox(
            "",
            ["1y", "3y", "5y", "5y+ (Max)"],
            index=3, # Default to Max
            help="Limit analysis to specific time window. '5y+ (Max)' uses all available data.",
            label_visibility="collapsed"
        )

    # SECURE QPARAM SYNC: If URL changes, force session state to follow
    qp_ticker = st.query_params.get("ticker")
    current_active = st.session_state.get('heatmap_active_ticker')
    if qp_ticker and qp_ticker != current_active:
        st.session_state.heatmap_active_ticker = qp_ticker
        # If we have a category in QParams too, update navigations
        qp_cat = st.query_params.get("category")
        if qp_cat:
            st.session_state.heatmap_category_pills = qp_cat
            st.session_state.heatmap_strategy_radio = "📂 Sector Browser"

    st.markdown("---")

    if analysis_mode == "Stock Analysis 🏢":
        # === STOCK LOGIC ===
        st.subheader("🏢 Stock Heatmap & Forecast")
        st.warning("⚠️ **Disclaimer:** Forecasts are AI-generated estimates based on historical patterns.")
        
        # Move Filters to Full Width for better visibility
        with st.container():
             # Helper to get month name
            import datetime
            now = datetime.datetime.now()
            current_month_idx = now.month
            
            def get_month_name(idx):
                return datetime.date(2000, idx, 1).strftime("%B")
                
            current_month_name = get_month_name(current_month_idx)
            
            # Next month logic (handle Dec->Jan rollover)
            if current_month_idx == 12:
                next_month_idx = 1
            else:
                next_month_idx = current_month_idx + 1
            next_month_name = get_month_name(next_month_idx)

            # Use 2 cols for filters
            f_col1, f_col2 = st.columns(2)
            
            with f_col1:
                # 1. Index Filter (Universe)
                # Check for query param 'category'
                qp_category = st.query_params.get("category", None)
                target_default = qp_category if qp_category in ["All", "Nifty 50", "Sensex", "Nifty Next 50", "Midcap"] else "Nifty 50"
                
                ticker_category = st.pills(
                    "1. Select Universe",
                    options=["All", "Nifty 50", "Sensex", "Nifty Next 50", "Midcap"],
                    default=target_default,
                    key="heatmap_category_pills"
                )
            
            with f_col2:
                # 2. Strategy Filter
                stars_1y = "⭐Top 1Y Stars"
                stars_3y = "⭐⭐⭐ Top 3Y Stars"
                stars_5y = "⭐⭐⭐⭐⭐ Top 5Y Stars"
                stars_5y_plus = "🌟 Top 5Y+ Stars"
                
                # Check for query param 'ticker' to auto-select Sector Browser mode if coming from link
                qp_ticker = st.query_params.get("ticker", None)
                
                # Explicitly manage strategy selection based on state/params
                if qp_ticker:
                    default_strat = "📂 Sector Browser"
                else:
                    default_strat = stars_5y_plus

                strategy_options = [stars_1y, stars_3y, stars_5y, stars_5y_plus, "📂 Sector Browser"]
                
                strategy_mode = st.radio(
                    "2. Filter Strategy",
                    options=strategy_options,
                    index=strategy_options.index(default_strat),
                    horizontal=True,
                    key="heatmap_strategy_radio"
                )
        
        st.markdown("---")

        if strategy_mode == "📂 Sector Browser":
            # === SECTOR BROWSER LOGIC (Visual First) ===
            visual_selection = render_visual_ticker_selector(ticker_category)
            
            # Handle selection update
            if visual_selection:
                st.session_state.heatmap_active_ticker = visual_selection
                st.rerun()

            # Ensure session state is synced with URL params (for reload)
            if 'heatmap_active_ticker' not in st.session_state and qp_ticker:
                 st.session_state.heatmap_active_ticker = qp_ticker
                 
            # Display Analysis Logic
            active_ticker = st.session_state.get('heatmap_active_ticker')
            
            if active_ticker:
                 st.markdown("---")
                 st.subheader(f"📊 Analysis: {get_ticker_name(active_ticker)} ({active_ticker})")
                 run_analysis_ui(active_ticker, st.session_state.heatmap_limiter, key_prefix="heatmap", global_outlier=exclude_outliers_global, lookback_period=lookback_period)
            else:
                 st.info("👆 Select a stock from the Sector Browser above to view detailed analysis.")

        else:
            # === STANDARD LIST / STARS LOGIC ===
            col_input, col_button, col_info = st.columns([2, 1, 3])
            
            with col_input:
                # Stars Logic
                from rover_tools.analytics.win_rate import get_performance_stars
                
                # Determine period based on selection
                period = "1y"
                if "3Y Stars" in strategy_mode: period = "3y"
                elif "5Y+ Stars" in strategy_mode: period = "5y+"
                elif "5Y Stars" in strategy_mode: period = "5y"
                
                with st.spinner(f"Identifying {period} winners in {ticker_category}..."):
                   # Use GLOBAL setting
                   top_stars = get_performance_stars(category=ticker_category, period=period, top_n=5)
                   
                if top_stars:
                     # Format: "TICKER (+XX%)"
                     common_tickers = [s['label'] for s in top_stars]
                else:
                     common_tickers = []
                     st.warning(f"No data found for {ticker_category} (Period: {period}).")

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
                    # Default to SBIN if available, else 0
                    for i, t in enumerate(common_tickers):
                        if "SBIN.NS" in t:
                            default_ix = i 
                            break
                    
                    # Auto-select first stock if no specific default found (and list has items)
                    if len(common_tickers) > 0 and default_ix >= len(common_tickers):
                         default_ix = 0

                ticker_options = common_tickers
                
                if not ticker_options:
                     st.warning("No stocks found for this criteria.")
                     ticker_options = ["No Data"]
                
                selected_opt = st.selectbox(
                    "Stock Selection", 
                    options=ticker_options, 
                    index=default_ix if default_ix < len(ticker_options) else 0,
                    key="heatmap_ticker_select",
                    help=f"Listing {ticker_category} stocks."
                )
                
                if selected_opt and selected_opt != "No Data":
                     # Handle "TICKER - Name" AND "TICKER (+XX%)"
                     # Split by ' - ' first, then space to isolate ticker
                     ticker_raw = selected_opt.split(' - ')[0].split(' ')[0]
                else:
                     ticker_raw = None

            with col_button:
                st.write("") 
                analyze_button = st.button("📊 Analyze", type="primary", width='stretch', key="btn_heatmap")

            with col_info:
                 pass
                
            # Initialize session state for this tab
            if 'heatmap_active_ticker' not in st.session_state:
                # Auto-init with the default selection
                final_default = ticker_options[default_ix] if default_ix < len(ticker_options) else None
                # Extract ticker part
                if final_default:
                     final_default = final_default.split(' - ')[0].split(' ')[0]

                st.session_state.heatmap_active_ticker = qp_ticker if qp_ticker else final_default

            if analyze_button:
                 # Sanitize before setting active state
                 clean_input = sanitize_ticker(ticker_raw)
                 if clean_input:
                     st.session_state.heatmap_active_ticker = clean_input
                 else:
                     st.error("Invalid ticker format. Please check your input.")
            
            # Run analysis if a ticker is active
            if st.session_state.heatmap_active_ticker:
                 run_analysis_ui(st.session_state.heatmap_active_ticker, st.session_state.heatmap_limiter, key_prefix="heatmap", global_outlier=exclude_outliers_global, lookback_period=lookback_period)



    else:

        # === BENCHMARK LOGIC ===

        st.subheader("📊 Benchmark Index Analysis")

        

        # Define Major Indices

        major_indices = {

            "Nifty 50": "^NSEI",

            "Sensex": "^BSESN",
            
            "Nifty Next 50": "JUNIORBEES.NS",

            "Nifty Midcap 100": "^CRSLDX"

        }

        

        index_names = list(major_indices.keys())

        

        st.markdown("##### ⚡ Quick Select Index")
        selected_index = st.pills("Choose an Index:", index_names, selection_mode="single", default="Nifty 50", key="bench_pills")
        
        if selected_index:
            ticker = major_indices[selected_index]
            st.markdown(f"### Analyzing: **{selected_index}** (`{ticker}`)")
            run_analysis_ui(ticker, st.session_state.heatmap_limiter, key_prefix="benchmark", global_outlier=exclude_outliers_global, lookback_period=lookback_period)
