import streamlit as st
import pandas as pd
from rover_tools.shadow_tools import (
    analyze_sector_flow, fetch_block_deals, 
    detect_silent_accumulation, get_trap_indicator,
    get_sector_stocks_accumulation
)
from rover_tools.ticker_resources import get_common_tickers, NIFTY_50_SECTOR_MAP
from utils.portfolio_manager import PortfolioManager

def show_shadow_tracker_tab():
    """Show the Shadow Tracker Tab - Unconventional Institutional Analytics"""
    st.header("🕵️ Shadow Tracker (Beta)")
    st.markdown("Decode **'Smart Money'** with unconventional metrics: *Block Deals, Silent Accumulation, and Sector Rotation*.")
    
    # Create Tabs
    tab_across, tab_sector, tab_stock = st.tabs([
        "🌐 Across Sectors", 
        "📂 Specific Sector", 
        "🎯 Specific Stock"
    ])
    
    with tab_across:
        col_flow, col_trap = st.columns([2, 1])
        
        with col_flow:
            st.subheader("🕸️ The Spider Web (Sector Rotation)")
            st.caption("Identify sectors where institutional money is secretly rotating.")
            
            with st.spinner("Analyzing Sector Shifts..."):
                sector_df = analyze_sector_flow()
                if not sector_df.empty:
                    top_sectors = sector_df.head(3)['Sector'].tolist()
                    st.success(f"🔥 Smart Money Flow detected in: **{', '.join(top_sectors)}**")
                    
                    st.dataframe(
                        sector_df.style.background_gradient(subset=['Momentum Score'], cmap='Greens'),
                        width='stretch',
                        column_config={
                            "Rank": st.column_config.NumberColumn("Rank", format="#%d"),
                            "Momentum Score": st.column_config.ProgressColumn("Relative Strength", min_value=0, max_value=10, format="%.1f")
                        }
                    )
                else:
                    st.warning("⚠️ Could not fetch sector data.")

        with col_trap:
            st.subheader("🪤 FII Trap Detector")
            st.caption("FII positioning in Index Futures.")
            trap = get_trap_indicator()
            
            status = trap['status']
            long_pct = trap['fii_long_pct']
            
            st.metric("FII Index Long %", f"{long_pct}%", delta=status)
            
            if long_pct > 70:
                 st.warning("⚠️ **Bull Trap Zone!** Overbought.")
            elif long_pct < 30:
                 st.success("✅ **Bear Trap Zone!** Oversold.")
            else:
                 st.info("⚖️ **Balanced Zone**")
            st.caption(trap['message'])

    with tab_sector:
        st.subheader("📂 Sector Deep-Dive")
        st.caption("Select a sector tab to analyze 'Smart Money' accumulation across its stocks.")
        
        available_sectors = sorted(list(set(NIFTY_50_SECTOR_MAP.values())))
        
        # Sector selection via pills (visual, like Brand Shop tabs, but returns a value for auto-scan)
        selected_sector = st.pills(
            "Select Sector Cluster:", 
            options=available_sectors, 
            default=available_sectors[0],
            key="sector_pill_selector"
        )
        
        if selected_sector:
            st.markdown(f"### 📊 Institutional Flow: {selected_sector}")
            with st.spinner(f"Forensic scan of {selected_sector} stocks..."):
                sector_acc_df = get_sector_stocks_accumulation(selected_sector)
                if not sector_acc_df.empty:
                    st.dataframe(
                        sector_acc_df.style.background_gradient(subset=['Shadow Score'], cmap='Blues'),
                        width='stretch',
                        column_config={
                            "Shadow Score": st.column_config.ProgressColumn("Accumulation Score", min_value=0, max_value=100, format="%d")
                        }
                    )
                else:
                    st.info(f"No deep-dive data available for {selected_sector}.")

    with tab_stock:
        st.subheader("🎯 Specific Stock Forensic")
        st.caption("Combine Accumulation metrics with recent Whale Activity (Block Deals).")
        
        col_sel, col_btn = st.columns([3, 1])
        with col_sel:
            shadow_cat_stock = st.pills(
                "Filter Index:", 
                ["All", "Nifty 50", "Sensex", "Bank Nifty", "Midcap", "Smallcap"], 
                default="Nifty 50",
                key="shadow_stock_index_pills"
            )
            shadow_options = get_common_tickers(category=shadow_cat_stock)
            selected_shadow_ticker = st.selectbox(
                "Search Stock:", 
                options=shadow_options,
                key="shadow_stock_select_tab_final"
            )
            acc_ticker = selected_shadow_ticker.split(' - ')[0] if " - " in selected_shadow_ticker else selected_shadow_ticker

        with col_btn:
             st.write("<div style='height: 45px'></div>", unsafe_allow_html=True)
             # Stock specific scan remains manual as it can be heavy and triggered multiple times
             scan_stock = st.button("🕵️ Run Stock Scan", type="primary", use_container_width=True)
             
        if scan_stock:
            # 1. Silent Accumulation
            st.markdown(f"### 🤫 Accumulation Scan: {acc_ticker}")
            with st.spinner(f"Analyzing {acc_ticker}..."):
                res = detect_silent_accumulation(acc_ticker)
                score = res.get('score', 0)
                signals = res.get('signals', [])
                
                col_m1, col_m2 = st.columns([1, 2])
                with col_m1:
                    st.metric("Shadow Score", f"{score}/100")
                with col_m2:
                    st.progress(score / 100)
                
                if score > 60:
                    st.success("✅ **Accumulation Detected!**")
                elif score < 30:
                    st.error("❌ **No Signs of Accumulation**")
                else:
                    st.info("ℹ️ **Neutral / Inconclusive**")
                
                for sig in signals:
                    st.markdown(f"- 🟢 {sig}")
            
            st.divider()
            
            # 2. Whale Activity
            st.markdown(f"### 🐋 Whale Activity (Recent Block Deals)")
            with st.spinner("Fetching specific block deals..."):
                stock_deals = fetch_block_deals(symbol=acc_ticker)
                
                if stock_deals:
                     import html
                     for d in stock_deals:
                         color = "green" if d['Type'] == 'BUY' else "red"
                         icon = "🟢" if d['Type'] == 'BUY' else "🔴"
                         safe_symbol = html.escape(str(d['Symbol']))
                         safe_client = html.escape(str(d['Client']))
                         
                         st.markdown(f"""
                         <div style='padding: 10px; border-radius: 5px; background-color: #262730; margin-bottom: 5px; border-left: 5px solid {color}'>
                            <b>{icon} {safe_symbol}</b> | {d['Date']}<br>
                            <small>{safe_client}</small><br>
                            <span style='color:{color}; font-weight:bold'>{d['Type']}</span> @ ₹{d['Price']} ({d['Qty']})
                         </div>
                         """, unsafe_allow_html=True)
                else:
                    st.info(f"No recent specific block deals found for {acc_ticker} in the last 1 month.")
