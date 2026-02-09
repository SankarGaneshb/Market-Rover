import streamlit as st
import pandas as pd
import time
from datetime import datetime
from config import REPORT_DIR
from utils.portfolio_manager import PortfolioManager
from rover_tools.ticker_resources import get_common_tickers
from utils.security import sanitize_ticker

# Global helper needed for portfolio tab
def get_user_report_dir():
    """Get the report directory for the current user."""
    username = st.session_state.get('username', 'guest')
    user_dir = REPORT_DIR / username
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

def show_recent_reports():

    """Show recently generated PDF reports for the user"""

    user_dir = get_user_report_dir()

    if not user_dir.exists():
        st.info("No reports found.")
        return

    reports = sorted(user_dir.glob("*.pdf"), key=lambda x: x.stat().st_mtime, reverse=True)
    recent = reports[:5] # Show last 5
    if recent:
        for r in recent:
            col_rep, col_don = st.columns([4, 1])
            with col_rep:
                 st.text(f"📄 {r.name} ({datetime.fromtimestamp(r.stat().st_mtime).strftime('%Y-%m-%d %H:%M')})")
            with col_don:
                 with open(r, "rb") as pdf_file:
                     st.download_button("⬇️", pdf_file, file_name=r.name, mime="application/pdf", key=f"dl_{r.name}")
    else:
        st.info("No recent reports.")

# Helper function
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_portfolio_file(file_bytes, filename):

    """Load and validate portfolio CSV with caching"""

    import io

    df = pd.read_csv(io.BytesIO(file_bytes))

    

    # Validate columns
    df.columns = df.columns.str.strip() # Remove leading/trailing spaces from headers

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
            pass # Silently drop or log? Using pass avoids console clutter.

            

    except Exception as e:

        raise ValueError(f"Sanitization failed: {str(e)}")

    

    return df

def render_upload_section(max_parallel: int):

    """Show the upload and analysis tab"""

    # We need to import run_analysis from app or move it? 
    # run_analysis calls crew_engine. It seems intricate.
    # Ideally run_analysis should be in a separate controller or tool, but for now we might need to import it or pass it.
    # However, to avoid circular imports if run_analysis is in app.py, we should likely move `run_analysis` to `tabs/portfolio_tab.py` as well OR a `utils/analysis_runner.py`.
    # Let's check where run_analysis is defined. It wasn't in the snippet provided. It's likely in app.py lower down or I missed it.
    # Assuming it's in app.py for now, we have a problem. "run_analysis" is called in render_upload_section.
    # We should define run_analysis HERE or in a utils file.
    
    # Since I don't see run_analysis in the snippet, I will assume it uses `crew_engine`. 
    # I will create a placeholder or try to find it. 
    # Wait, I saw `show_portfolio_analysis_tab` calling `render_upload_section`. 
    # And `render_upload_section` calls `run_analysis`.
    
    # I'll check user context or file again if needed. But let's proceed with defining the UI parts.
    
    # CRITICAL: `run_analysis` function logic.
    # I will implement `run_analysis` inside this file if it's not too large, or check if I can extract it.
    
    pass 

# Since `run_analysis` is critical and I didn't see it fully, I should probably search for it or include it.
# Let's assume for now I will copy `show_portfolio_analysis_tab`, `render_upload_section`, `render_analytics_section`.
# And I need `run_analysis`.

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

            cat = st.pills("Filter:", ["All", "Nifty 50", "Sensex", "Nifty Next 50", "Midcap"], default="Nifty 50", key="corr_pills")

            

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

                normalized = custom_add.replace('\n', ',')

                normalized = custom_add.replace('\n', ',')
                
                # Sanitize each custom input
                clean_custom = []
                for c in normalized.split(','):
                    s = sanitize_ticker(c) 
                    if s: 
                        clean_custom.append(s)

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

            pm = PortfolioManager(st.session_state.get('username'))

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
                    candidate = f"{t}.NS" if '.' not in t else t
                    
                    clean = sanitize_ticker(candidate)
                    if clean:
                        tickers.append(clean)

                        

                # Re-instantiate to ensure fresh state

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

                    st.plotly_chart(fig, width="stretch")

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

            pm = PortfolioManager(st.session_state.get('username'))

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

                            

                        st.dataframe(
                            result.style.applymap(color_action, subset=['action']),
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


def show_portfolio_analysis_tab(max_parallel: int):

    """

    Unified Portfolio Analysis Tab (Merged Tab 1 & Analytics)

    Contains:

    1. Upload & Report Generation

    2. Advanced Analytics Tools (Correlation, Rebalancing)

    """

    # sub_tab1, sub_tab2 = st.tabs(["📊 Report Generator", "🧪 Analytics Lab"])
    # REMOVED Analytics Lab as per user request (redundant).
    # Renamed "Report Generator" flow to "Portfolio Analysis".

    render_upload_section_logic(max_parallel)

    # with sub_tab2:
    #     render_analytics_section()

def render_upload_section_logic(max_parallel):
    st.header("📤 Portfolio Analysis")

    from rover_tools.ticker_resources import (
        NIFTY_50_SECTOR_MAP, NIFTY_50_BRAND_META,
        NIFTY_NEXT_50_SECTOR_MAP, NIFTY_MIDCAP_SECTOR_MAP
    )
    from rover_tools.analytics.investor_profiler import InvestorPersona
    from utils.user_manager import UserProfileManager
    import base64
    import html

    pm = PortfolioManager(st.session_state.get('username'))
    saved_names = pm.get_portfolio_names()
    
    # 1. LOAD PORTFOLIO
    current_pf_name = st.session_state.get('loaded_portfolio_name', 'My Portfolio')
    
    if saved_names:
        col_sel, col_new = st.columns([3, 1])
        with col_sel:
            selected_load = st.selectbox(
                "📂 Active Portfolio", 
                saved_names, 
                index=saved_names.index(current_pf_name) if current_pf_name in saved_names else 0,
                key="pf_selector_main"
            )
            
            if selected_load != current_pf_name:
                st.session_state.loaded_portfolio_name = selected_load
                st.session_state.manual_portfolio_df = None
                st.rerun()
                
        with col_new:
            st.write("")
            st.write("")
            if st.button("➕ New"):
                st.session_state.manual_portfolio_df = pd.DataFrame(columns=["Symbol", "Company Name", "Quantity", "Average Price"])
                st.session_state.loaded_portfolio_name = "New Portfolio"
                st.rerun()

    # Load DF if needed
    if 'manual_portfolio_df' not in st.session_state or st.session_state.manual_portfolio_df is None:
        if current_pf_name in saved_names:
            st.session_state.manual_portfolio_df = pm.get_portfolio(current_pf_name)
        else:
             st.session_state.manual_portfolio_df = pd.DataFrame(columns=["Symbol", "Company Name", "Quantity", "Average Price"])
    
    # Ensure standard columns
    if 'Quantity' not in st.session_state.manual_portfolio_df.columns:
        st.session_state.manual_portfolio_df['Quantity'] = 0
    if 'Average Price' not in st.session_state.manual_portfolio_df.columns:
        st.session_state.manual_portfolio_df['Average Price'] = 0.0

    current_df = st.session_state.manual_portfolio_df
    current_symbols = current_df['Symbol'].tolist() if not current_df.empty else []

    # 2. DETERMINE ACCESS (PERSONA LOGIC)
    # Get Persona
    persona_val = st.session_state.get('persona')
    
    # Fallback if persona is missing (e.g. direct nav)
    if not persona_val:
        # Try fetch
        # Try fetch
        user_mgr = UserProfileManager()
        # Fixed: Use correct method name
        status = user_mgr.get_profile_status(st.session_state.get('username', 'guest'))
        persona_val = status.get('persona')
        
    # Default permissions
    show_nifty = True
    show_next50 = False
    show_midcap = False
    
    p_name = "Guest"
    
    if persona_val:
        # Resolve Enum/String
        p_str = persona_val.value if hasattr(persona_val, 'value') else str(persona_val)
        p_name = p_str
        
        # Logic matches Profiler
        # Hunter: All
        # Compounder: Nifty + Next 50
        # Preserver/Defender: Nifty Only
        
        if "Hunter" in p_str:
            show_next50 = True
            show_midcap = True
        elif "Compounder" in p_str:
            show_next50 = True
    else:
        # No profile? Show base Nifty 50
        st.warning("⚠️ No Persona detected. Showing Nifty 50 only. Go to 'Investor Profile' to unlock more assets.")

    st.info(f"👤 **Persona: {p_name}** | Access: Nifty 50 {'+ Next 50' if show_next50 else ''} {'+ Midcaps' if show_midcap else ''}")

    # 3. HELPER TO RENDER GRID
    def render_brand_grid(sector_map, category_name, key_prefix):
        st.markdown(f"### {category_name}")
        sectors = sorted(list(set(sector_map.values())))
        tabs = st.tabs(sectors)
        
        selected_in_category = []
        
        for i, sector in enumerate(sectors):
            with tabs[i]:
                tickers = [t for t, s in sector_map.items() if s == sector]
                cols = st.columns(4) # 4 Cols for compact view
                for j, ticker in enumerate(tickers):
                    col = cols[j % 4]
                    with col:
                        # Meta
                        meta = NIFTY_50_BRAND_META.get(ticker, {"name": ticker.replace('.NS',''), "color": "#333"})
                        
                        # SVG Icon
                        tick_short = getattr(html, 'escape', lambda s: s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))(ticker.replace('.NS', '')[:4])
                        color = meta['color']
                        text_color = "#000000" if color in ["#FFD200", "#FFF200"] else "#ffffff"
                        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="4" fill="{color}"/><text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" fill="{text_color}" font-family="Arial" font-weight="bold" font-size="9">{tick_short}</text></svg>'
                        b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
                        
                        # Card HTML
                        safe_name = getattr(html, 'escape', lambda s: s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))(meta['name'])
                        
                        st.markdown(f'''
                        <div style="border:1px solid #eee; border-radius:6px; padding:5px; margin-bottom:5px; display:flex; align-items:center;">
                            <img src="data:image/svg+xml;base64,{b64}" style="width:24px; height:24px; border-radius:4px; margin-right:8px;">
                            <div style="font-size:12px; font-weight:bold; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;">{safe_name}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                        
                        # Checkbox
                        is_checked = ticker in current_symbols
                        val = st.checkbox("Select", value=is_checked, key=f"{key_prefix}_{ticker}", label_visibility="collapsed")
                        
                        if val:
                            selected_in_category.append(ticker)
                            
        return selected_in_category

    # 4. RENDER GRIDS
    new_selection = []
    
    # Group 1: Nifty 50 (Always)
    sel_n50 = render_brand_grid(NIFTY_50_SECTOR_MAP, "🛒 Nifty 50 (Core)", "pf_n50")
    new_selection.extend(sel_n50)
    
    # Group 2: Next 50
    if show_next50:
        st.divider()
        sel_next = render_brand_grid(NIFTY_NEXT_50_SECTOR_MAP, "🚀 Nifty Next 50 (Growth)", "pf_next50")
        new_selection.extend(sel_next)
        
    # Group 3: Midcap
    if show_midcap:
        st.divider()
        sel_mid = render_brand_grid(NIFTY_MIDCAP_SECTOR_MAP, "🏹 Midcap (Alpha)", "pf_mid")
        new_selection.extend(sel_mid)

    # 5. SYNC LOGIC (Update DataFrame based on Checkbox State)
    # This runs on every rerun. We compare `new_selection` with `current_symbols`
    if set(new_selection) != set(current_symbols):
        # Determine items to ADD
        to_add = set(new_selection) - set(current_symbols)
        # Determine items to REMOVE
        to_remove = set(current_symbols) - set(new_selection)
        
        # Update DF
        df = st.session_state.manual_portfolio_df
        
        # 1. Remove
        if to_remove:
            df = df[~df['Symbol'].isin(to_remove)]
            
        # 2. Add
        if to_add:
            new_rows = []
            for t in to_add:
                # Try to find name in meta
                meta = NIFTY_50_BRAND_META.get(t, {"name": t})
                new_rows.append({
                    "Symbol": t,
                    "Company Name": meta['name'],
                    "Quantity": 10,  # Default
                    "Average Price": 0.0
                })
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            
        st.session_state.manual_portfolio_df = df
        st.rerun() # Refresh to update the Quantities table below
        
    # 6. QUANTITY EDITOR
    st.divider()
    st.markdown("### 📝 Allocation Details")
    
    if not st.session_state.manual_portfolio_df.empty:
        edited_pf = st.data_editor(
            st.session_state.manual_portfolio_df,
            column_config={
                "Symbol": st.column_config.TextColumn("Symbol", disabled=True), # Read Only, use Grid to add/remove
                "Company Name": st.column_config.TextColumn("Company Name", disabled=True),
                "Quantity": st.column_config.NumberColumn("Quantity", min_value=1, step=1, required=True),
                "Average Price": st.column_config.NumberColumn("Avg Price", min_value=0.0, format="₹ %.2f")
            },
            hide_index=True,
            use_container_width=True,
            key="qty_editor_pf",
            num_rows="fixed" # Disable add/delete rows here
        )
        st.session_state.manual_portfolio_df = edited_pf
        
        # Save Button
        if st.button("💾 Save Portfolio Changes", type="primary", use_container_width=True):
             success, msg = pm.save_portfolio(current_pf_name, edited_pf)
             if success:
                 from utils.celebration import trigger_celebration
                 trigger_celebration("Portfolio_Save", f"Saved portfolio: {current_pf_name}", {"portfolio_name": current_pf_name})
                 st.success("✅ Portfolio saved successfully!")
             else:
                 from utils.celebration import report_failure
                 report_failure("Portfolio_Save_Failed", msg, {"portfolio_name": current_pf_name})
                 st.error(f"Save failed: {msg}")
    else:
        st.info("Your shopping cart is empty. Select brands above to build your portfolio.")
    # 7. ANALYZE BUTTON
    if not st.session_state.manual_portfolio_df.empty:
        st.divider()
        if st.button("🚀 Analyze Risk & Performance", type="secondary", use_container_width=True):
             # Validate
             df_an = st.session_state.manual_portfolio_df
             clean_tickers = [str(x).strip() for x in df_an['Symbol'].tolist() if str(x).strip()] if 'Symbol' in df_an else []
             
             if not clean_tickers:
                 st.error("⚠️ Portfolio is empty!")
             else:
                 # Rate Limit
                 allowed, message = st.session_state.portfolio_limiter.is_allowed()
                 if not allowed:
                     st.error(f"⏱️ {message}")
                 else:
                     from utils.analysis_runner import run_analysis
                     # Pass just the name, function handles path
                     run_analysis(df_an, current_pf_name, max_parallel)
