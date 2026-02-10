import streamlit as st
import pandas as pd
import datetime
import calendar
from rover_tools.market_data import MarketDataFetcher
from rover_tools.analytics.seasonality_calendar import SeasonalityCalendar
from rover_tools.ticker_resources import get_common_tickers
from utils.security import sanitize_ticker

def show_trading_calendar_tab():
    st.header("📅 Strategic & Subha Muhurta Trading Calendar")
    st.markdown("Generate a high-probability trading schedule for **2026-2027** based on historical seasonal patterns and auspicious trading dates.")

    # Ticker Selector
    col_input, col_settings = st.columns([1, 1])
    
    with col_input:
        universe = st.selectbox("Select Universe", ["Nifty 50", "Nifty Next 50", "Midcap", "All"], index=0)
        common_tickers = get_common_tickers(category=universe)
        
        default_ticker = "RELIANCE.NS" if universe == "Nifty 50" else common_tickers[0].split(' - ')[0]
        ticker_raw = st.selectbox("Select Ticker for Calendar:", common_tickers, index=0).split(' - ')[0]
        ticker = sanitize_ticker(ticker_raw)

    with col_settings:
        exclude_outliers = st.checkbox("🚫 Exclude Outliers (Robust Mode)", value=False, help="Removes extreme volatility events from seasonality analysis.")
        cal_type = st.radio(
            "Calendar Type:",
            ["Strategic", "Subha Muhurta"],
            index=1,
            horizontal=True,
            help="Strategic: Data-driven best monthly days. Subha Muhurta: Auspicious trading dates."
        )

    if not ticker:
        st.error("Invalid Ticker")
        return

    # Fetch Data
    fetcher = MarketDataFetcher()
    with st.spinner(f"📊 Analyzing {ticker} history..."):
        history = fetcher.fetch_full_history(ticker)
        
        if history.empty:
            st.error(f"Could not fetch data for {ticker}")
            return

        # Entry/Exit Year Calculation
        buy_year = datetime.datetime.now().year
        sell_year = buy_year + 1
        
        st.markdown("---")
        
        if cal_type == "Strategic":
            st.info(f"💡 **Strategic Plan**: Identifies the historical 'Natural Bottom' and 'Natural Peak' for each month to maximize returns.")
        else:
            st.info(f"🏮 **Subha Muhurta Plan**: Uses traditional auspicious dates for entry and the historical 'Natural Peak' for exit. Intra-month gain is the average of all Muhurta dates in the month.")

        # Run Calendar Logic
        calendar_tool = SeasonalityCalendar(history, exclude_outliers=exclude_outliers, calendar_type=cal_type)
        cal_df = calendar_tool.generate_analysis()
        
        # Plot
        fig_cal = calendar_tool.plot_calendar(cal_df)
        st.pyplot(fig_cal)
        
        # Detailed Table
        with st.expander("📝 View Detailed Table", expanded=True):
            display_df = cal_df.copy()
            display_df['Avg Intra-Month Gain Forecast'] = display_df['Avg_Gain_Pct'].apply(lambda x: f"+{x:.2f}%")
            display_df['Buy Date (Entry)'] = display_df.apply(lambda x: f"{x['Buy_Date_2026']} ({x['Buy_Weekday']})", axis=1)
            display_df['Sell Date (Exit)'] = display_df.apply(lambda x: f"{x['Sell_Date_2026']} ({x['Sell_Weekday']})", axis=1)
            
            cols_to_show = ['Month', 'Avg Intra-Month Gain Forecast', 'Buy Date (Entry)', 'Sell Date (Exit)']
            if cal_type == "Subha Muhurta":
                display_df['Shubh Muhurta Dates'] = display_df['Muhurta_Dates']
                cols_to_show.append('Shubh Muhurta Dates')

            st.dataframe(
                display_df[cols_to_show],
                use_container_width=True,
                hide_index=True
            )
            
            st.caption(f"Note: All dates are adjusted to the nearest NSE trading session (Mon-Fri, non-holiday).")
