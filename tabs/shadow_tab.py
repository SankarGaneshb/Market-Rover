import streamlit as st
import pandas as pd
from rover_tools.shadow_tools import analyze_sector_flow, fetch_block_deals, detect_silent_accumulation, get_trap_indicator
from rover_tools.ticker_resources import get_common_tickers
from utils.portfolio_manager import PortfolioManager

def show_shadow_tracker_tab():
    """Show the Shadow Tracker Tab - Unconventional Institutional Analytics"""
    st.header("🕵️ Shadow Tracker (Beta)")
    st.markdown("Decode **'Smart Money'** with unconventional metrics: *Block Deals, Silent Accumulation, and Sector Rotation*.")
    
    # Create two columns main layout
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # === 1. SPIDER WEB (Sector Rotation) ===
        st.subheader("🕸️ The Spider Web (Sector Rotation)")
        st.caption("Identify sectors where institutional money is secretly rotating using relative strength.")
        
        if st.button("Scan Sector Flows 🌊"):
            with st.spinner("Analyzing Sector Shifts..."):
                sector_df = analyze_sector_flow()
                if not sector_df.empty:
                    # Highlight top 3
                    top_sectors = sector_df.head(3)['Sector'].tolist()
                    st.success(f"🔥 Smart Money Flow detected in: **{', '.join(top_sectors)}**")
                    
                    # Stylized Radar/Table
                    st.dataframe(
                        sector_df.style.background_gradient(subset=['Momentum Score'], cmap='Greens'),
                        width='stretch',
                        column_config={
                            "Rank": st.column_config.NumberColumn("Rank", format="#%d"),
                            "Momentum Score": st.column_config.ProgressColumn("Relative Strength", min_value=0, max_value=10, format="%.1f")
                        }
                    )
                else:
                    st.warning("⚠️ Could not fetch sector data. Check connection.")
        
        st.divider()
        
        # === 3. SILENT ACCUMULATION (Scanner) ===
        st.subheader("🤫 Silent Accumulation Scanner")
        st.caption("Detect 'The Stealth Buy': High Delivery + Low Volatility (Smart Money hiding tracks).")
        
        # 1. Index Filter
        shadow_cat = st.pills(
            "Filter:", 
            ["All", "Nifty 50", "Sensex", "Bank Nifty", "Midcap", "Smallcap"], 
            default="Nifty 50",
            key="shadow_cat_pills"
        )
        
        # 2. Dropdown
        shadow_options = get_common_tickers(category=shadow_cat)
        selected_shadow_ticker = st.selectbox(
            "Select Stock:", 
            options=shadow_options,
            key="shadow_stock_select"
        )
        
        # Extract symbol
        if " - " in selected_shadow_ticker:
            acc_ticker = selected_shadow_ticker.split(' - ')[0]
        else:
            acc_ticker = selected_shadow_ticker

        col_acc_btn, _ = st.columns([1, 2])
        with col_acc_btn:
             st.write("")
             acc_btn = st.button("🕵️ Detect Accumulation", type="primary", width='stretch')
             
        if acc_btn:
            with st.spinner(f"Forensic analysis of {acc_ticker}..."):
                res = detect_silent_accumulation(acc_ticker)
                score = res.get('score', 0)
                signals = res.get('signals', [])
                
                # Visual Meter
                st.metric("Shadow Score", f"{score}/100", help=">70 indicates strong probability of accumulation")
                st.progress(score / 100)
                
                if score > 60:
                    st.success("✅ **Accumulation Detected!**")
                    for sig in signals:
                        st.markdown(f"- 🟢 {sig}")
                elif score < 30:
                    st.error("❌ **No Signs of Accumulation** (Distribution or Random)")
                else:
                    st.info("ℹ️ **Neutral / Inconclusive**")
    
    with col_right:
        # === 2. WHALE ALERT ===
        st.subheader("🐋 Whale Activity")
        deals = fetch_block_deals()
        
        if deals:
             st.markdown("**Recent Large Deals**")
             for d in deals:
                 color = "green" if d['Type'] == 'BUY' else "red"
                 icon = "🟢" if d['Type'] == 'BUY' else "🔴"
                 st.markdown(f"""
                 <div style='padding: 10px; border-radius: 5px; background-color: #262730; margin-bottom: 5px; border-left: 5px solid {color}'>
                    <b>{icon} {d['Symbol']}</b><br>
                    <small>{d['Client']}</small><br>
                    <span style='color:{color}; font-weight:bold'>{d['Type']}</span> @ ₹{d['Price']} ({d['Qty']})
                 </div>
                 """, unsafe_allow_html=True)
        else:
            st.info("No recent block deals found.")
            
        st.divider()
        
        # === 4. TRAP DETECTOR ===
        st.subheader("🪤 FII Trap Detector")
        trap = get_trap_indicator()
        
        status = trap['status']
        long_pct = trap['fii_long_pct']
        
        st.metric("FII Index Long %", f"{long_pct}%", delta=status)
        
        if long_pct > 80:
             st.warning("⚠️ **Bull Trap Zone!** Market Overbought.")
        elif long_pct < 20:
             st.success("✅ **Bear Trap Zone!** Market Oversold (Reversal Likely).")
        else:
             st.info("⚖️ **Balanced Zone**")
        st.caption(trap['message'])
