import streamlit as st
import pandas as pd
import datetime
import calendar
import base64
import html
import urllib.parse
from rover_tools.market_data import MarketDataFetcher
from rover_tools.analytics.seasonality_calendar import SeasonalityCalendar
from rover_tools.ticker_resources import (
    get_common_tickers, 
    NIFTY_50_SECTOR_MAP, 
    NIFTY_50_BRAND_META,
    NIFTY_MIDCAP_SECTOR_MAP,
    NIFTY_NEXT_50_SECTOR_MAP,
    get_ticker_name
)
from utils.security import sanitize_ticker

def render_visual_ticker_selector(ticker_category):
    """
    Renders a visual, card-based selector for tickers, grouped by sector.
    Uses Streamlit buttons to prevent session loss on selection.
    """
    selected_ticker = None
    
    # Determine which map to use
    sector_map = {}
    if ticker_category == "Nifty 50":
        sector_map = NIFTY_50_SECTOR_MAP
    elif ticker_category == "Sensex":
        sector_map = NIFTY_50_SECTOR_MAP
    elif ticker_category == "Nifty Next 50":
        sector_map = NIFTY_NEXT_50_SECTOR_MAP
    elif ticker_category == "Midcap":
        sector_map = NIFTY_MIDCAP_SECTOR_MAP
        
    # Get tickers for this category
    category_tickers_full = get_common_tickers(category=ticker_category)
    category_tickers = [t.split(' - ')[0].strip() for t in category_tickers_full]
    
    if sector_map:
        mapped_data = {}
        for ticker in category_tickers:
            if ticker in sector_map:
                mapped_data[ticker] = sector_map[ticker]
            elif ticker in NIFTY_50_SECTOR_MAP:
                mapped_data[ticker] = NIFTY_50_SECTOR_MAP[ticker]
            else:
                 mapped_data[ticker] = "Others"
                 
        sectors = sorted(list(set(mapped_data.values())))
        if "Others" in sectors:
            sectors.remove("Others")
            sectors.append("Others")
            
        st.markdown("##### 📂 Browse by Sector")
        tabs = st.tabs(sectors)
        
        for i, sector in enumerate(sectors):
            with tabs[i]:
                curr_sector_tickers = [t for t, s in mapped_data.items() if s == sector]
                
                cols = st.columns(4)
                for j, ticker in enumerate(curr_sector_tickers):
                    col = cols[j % 4]
                    meta = NIFTY_50_BRAND_META.get(ticker, {"name": ticker, "color": "#333333"})
                    
                    # Robust Name Fetching
                    company_name = get_ticker_name(ticker)
                    
                    tick_short = ticker.replace('.NS', '')[:4]
                    color = meta.get('color', "#333333")
                    text_color = "#000000" if color in ["#FFD200", "#FFF200"] else "#ffffff"
                    
                    svg_raw = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="{color}"/><text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" fill="{text_color}" font-family="Arial" font-weight="bold" font-size="9">{tick_short}</text></svg>'
                    b64_svg = base64.b64encode(svg_raw.encode('utf-8')).decode('utf-8')
                    icon_src = f"data:image/svg+xml;base64,{b64_svg}"
                    
                    with col:
                        safe_name = html.escape(company_name)
                        # Card UI (Visual Only)
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
                        if st.button(f"Analyze", key=f"cal_sel_{ticker}", use_container_width=True):
                            st.session_state.calendar_active_ticker = ticker
                            st.query_params["ticker"] = ticker
                            st.query_params["category"] = ticker_category
                            st.query_params["tab"] = "calendar"
                            st.rerun()
    else:
        if len(category_tickers) <= 100:
            st.markdown(f"##### 🏢 {ticker_category} Stocks")
            cols = st.columns(5)
            for i, ticker in enumerate(category_tickers):
                tick_short = ticker.replace('.NS', '')
                with cols[i % 5]:
                    if st.button(tick_short, key=f"cal_fallback_vis_{ticker}", use_container_width=True):
                         st.session_state.calendar_active_ticker = ticker
                         st.query_params["ticker"] = ticker
                         st.rerun()
                        
    return selected_ticker

def show_trading_calendar_tab():
    st.header("📅 Strategic & Subha Muhurta Trading Calendar")
    st.markdown("Generate high-probability trading schedules based on historical patterns and auspicious dates.")

    # 1. Handle Query Params for Ticker Selection
    # If we have query params, they should populate session state ONCE or when changed
    qp_ticker = st.query_params.get("ticker")
    if qp_ticker:
        st.session_state.calendar_active_ticker = qp_ticker
        qp_cat = st.query_params.get("category")
        if qp_cat:
            st.session_state.calendar_universe_choice = qp_cat

    # Initialize session state if missing
    if 'calendar_active_ticker' not in st.session_state:
        st.session_state.calendar_active_ticker = "RELIANCE.NS"
    if 'calendar_universe_choice' not in st.session_state:
        st.session_state.calendar_universe_choice = "Nifty 50"

    # Settings Row
    col_u, col_o, col_t = st.columns([1, 1, 1])
    
    with col_u:
        universe = st.selectbox(
            "Select Universe", 
            ["Nifty 50", "Sensex", "Nifty Next 50", "Midcap", "All"], 
            index=["Nifty 50", "Sensex", "Nifty Next 50", "Midcap", "All"].index(st.session_state.calendar_universe_choice),
            key="calendar_universe_selectbox"
        )
        st.session_state.calendar_universe_choice = universe

    with col_o:
        exclude_outliers = st.checkbox("🚫 Robust Mode", value=False, help="Exclude outliers.")

    with col_t:
        cal_type = st.radio("Mode:", ["Strategic", "Subha Muhurta"], index=1, horizontal=True)

    # 2. Visual Browser
    st.markdown("---")
    render_visual_ticker_selector(universe)

    ticker = sanitize_ticker(st.session_state.calendar_active_ticker)
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

        st.markdown(f"### 📈 Analysis for **{ticker}**")
        
        calendar_tool = SeasonalityCalendar(history, exclude_outliers=exclude_outliers, calendar_type=cal_type)
        cal_df = calendar_tool.generate_analysis()
        
        fig_cal = calendar_tool.plot_calendar(cal_df)
        st.pyplot(fig_cal)
        
        with st.expander("📝 View Detailed Table", expanded=True):
            display_df = cal_df.copy()
            display_df['Avg Gain Forecast'] = display_df['Avg_Gain_Pct'].apply(lambda x: f"+{x:.2f}%")
            display_df['Buy (Entry)'] = display_df.apply(lambda x: f"{x['Buy_Date_2026']} ({x['Buy_Weekday']})", axis=1)
            display_df['Sell (Exit)'] = display_df.apply(lambda x: f"{x['Sell_Date_2026']} ({x['Sell_Weekday']})", axis=1)
            
            cols_to_show = ['Month', 'Avg Gain Forecast', 'Buy (Entry)', 'Sell (Exit)']
            if cal_type == "Subha Muhurta":
                display_df['Auspicious Dates'] = display_df['Muhurta_Dates']
                cols_to_show.append('Auspicious Dates')

            st.dataframe(display_df[cols_to_show], use_container_width=True, hide_index=True)
