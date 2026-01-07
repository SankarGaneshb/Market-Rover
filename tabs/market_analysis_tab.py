import streamlit as st
import pandas as pd
from rover_tools.ticker_resources import get_common_tickers
from utils.security import sanitize_ticker

# Shared function to run analysis and render UI
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

            

            # === UI CONTROLS: Global Settings for this Analysis ===
            col_controls, _ = st.columns([2, 3])
            with col_controls:
                exclude_outliers = st.checkbox("🚫 Exclude Outliers (Statistical IQR)", value=False, 
                                             help="Robust Mode: Removes extreme volatility events from Heatmap, Risk Stats, and Forecasts.", 
                                             key=f"{key_prefix}_outlier_{ticker}")

            if exclude_outliers:
                st.info("ℹ️ **Robust Analysis Enabled**: Outliers removed from Heatmap, Seasonality, and Forecast Trends.")

            # Calculate monthly returns matrix
            returns_matrix = analyzer.calculate_monthly_returns_matrix(history, exclude_outliers=exclude_outliers)
            seasonality_stats = analyzer.calculate_seasonality(history, exclude_outliers=exclude_outliers)
            
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

                st.plotly_chart(fig_win, width="stretch")

                

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

                st.plotly_chart(fig_seasonality, width="stretch")

            

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
                        if save_forecast(ticker, current_price, forecast_baseline, "2026-12-31", active_name, backtest_res.get('confidence'), backtest_res.get('years_tested', [])):
                            st.success("✅ Saved!")



            else:

                 st.warning("Insufficient data for forecast")



         except Exception as e:

            st.error(f"Analysis error: {str(e)}")

            st.info("Check logs for details")


def show_market_analysis_tab():

    """Show the Unified Market Analysis Tab"""

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
                target_default = "Nifty 50"
                ticker_category = st.pills(
                    "1. Select Universe",
                    options=["All", "Nifty 50", "Sensex", "Bank Nifty", "Midcap", "Smallcap"],
                    default=target_default,
                    key="heatmap_category_pills"
                )
            
            with f_col2:
                 # 2. Strategy Filter
                seasonality_label_curr = f"🔥 Top 5 {current_month_name} Stars"
                seasonality_label_next = f"🔮 Top 5 {next_month_name} Stars"
                
                strategy_mode = st.radio(
                    "2. Filter Strategy",
                    options=["Standard View", seasonality_label_curr, seasonality_label_next],
                    horizontal=True,
                    key="heatmap_strategy_radio"
                )
        
        st.markdown("---")

        col_input, col_button, col_info = st.columns([2, 1, 3])
        
        # Remove old col_filter usage
        
        with col_input:
            
            # Logic Branching
            if strategy_mode == "Standard View":
                common_tickers = get_common_tickers(category=ticker_category)
                
            else:
                # Seasonality Logic
                from rover_tools.analytics.win_rate import calculate_seasonality_win_rate
                
                # Determine target month
                if strategy_mode == seasonality_label_curr:
                    target_m = current_month_idx
                    target_name = current_month_name
                else:
                    target_m = next_month_idx
                    target_name = next_month_name
                
                with st.spinner(f"Identifying historical {target_name} winners in {ticker_category}..."):
                   # Pass the selected category to the win rate calculator
                   top_season_stocks = calculate_seasonality_win_rate(category=ticker_category, target_month=target_m)
                   
                if top_season_stocks:
                     # Format: "TICKER - XX% Win Rate"
                     common_tickers = [f"{s['ticker']} - {s['win_rate']:.0f}% Historic Win Rate ({s['avg_return']:.1f}% Avg)" for s in top_season_stocks]
                else:
                     common_tickers = []
                     st.warning(f"No seasonality data found for {ticker_category} in {target_name}.")

            

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

                    

            ticker_options = ["✨ Select or Type to Search..."] + common_tickers + ["✏️ Custom Input"]

            

            selected_opt = st.selectbox(

                "Stock Selection", 

                options=ticker_options, 

                index=default_ix if default_ix < len(ticker_options) else 0,

                key="heatmap_ticker_select",

                help=f"Listing {ticker_category} stocks."

            )

            

            if selected_opt == "✏️ Custom Input" or selected_opt == "✨ Select or Type to Search...":

                 # Use query param if custom

                 def_val = qp_ticker if qp_ticker else "SBIN.NS"

                 ticker_raw = st.text_input("Enter Symbol (e.g. INFBEES.NS)", value=def_val, key="heatmap_ticker_custom")

            else:

                 ticker_raw = selected_opt.split(' - ')[0]

        

        with col_button:

            st.write("") 

            analyze_button = st.button("📊 Analyze", type="primary", width='stretch', key="btn_heatmap")



        with col_info:

             pass

            

        # Initialize session state for this tab

        if 'heatmap_active_ticker' not in st.session_state:

            st.session_state.heatmap_active_ticker = qp_ticker if qp_ticker else None

            

        if analyze_button:
             # Sanitize before setting active state
             clean_input = sanitize_ticker(ticker_raw)
             if clean_input:
                 st.session_state.heatmap_active_ticker = clean_input
             else:
                 st.error("Invalid ticker format. Please check your input.")

        

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
