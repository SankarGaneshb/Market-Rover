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

            cat = st.pills("Filter:", ["All", "Nifty 50", "Sensex", "Bank Nifty", "Midcap", "Smallcap"], default="Nifty 50", key="corr_pills")

            

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

                            

                        st.dataframe(result.style.applymap(color_action, subset=['action'])

                                     .format({

                                         'current_weight': '{:.1%}', 

                                         'target_weight': '{:.1%}', 

                                         'volatility': '{:.1%}',

                                         'return': '{:.1%}'

                                     }), width='stretch')

                                     

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

    sub_tab1, sub_tab2 = st.tabs(["📊 Report Generator", "🧪 Analytics Lab"])

    

    with sub_tab1:
        # We need run_analysis passed or imported.
        # For now, let's call render_upload_section and assume run_analysis is available via import if we move it to a util.
        # But we haven't moved it yet.
        # Let's import handle_upload_section_logic which we will define
        render_upload_section_logic(max_parallel)

    with sub_tab2:

        render_analytics_section()

def render_upload_section_logic(max_parallel):
    st.header("📊 Portfolio Operations")

    from rover_tools.ticker_resources import get_common_tickers
    
    pm = PortfolioManager(st.session_state.get('username'))
    saved_names = pm.get_portfolio_names()
    
    # State management for input mode
    if 'pf_input_mode' not in st.session_state:
        # Default to 'Manage' if portfolios exist, else 'Upload'
        st.session_state.pf_input_mode = "Manage Portfolios" if saved_names else "Create / Upload"

    # Input Mode Toggle (Small, Cleaner)
    # st.write("---")
    c_mode_1, c_mode_2 = st.columns([1, 4])
    with c_mode_1:
         pass # Spacing
         
    # Logic to switch mode
    # If we have saved names, we show the loaded portfolio by default
    
    df = None
    filename = None
    
    # --- AUTO-LOAD LOGIC ---
    if saved_names and st.session_state.pf_input_mode == "Manage Portfolios":
        
        # Load most recent or selected
        if 'loaded_portfolio_name' not in st.session_state:
            st.session_state.loaded_portfolio_name = saved_names[0] # Default to first
            
        # Dropdown to switch
        col_sel, col_opt = st.columns([3, 1])
        with col_sel:
            selected_load = st.selectbox("📂 Active Portfolio", saved_names, 
                                       index=saved_names.index(st.session_state.loaded_portfolio_name) if st.session_state.loaded_portfolio_name in saved_names else 0,
                                       key="load_portfolio_select_main")
            
            if selected_load != st.session_state.loaded_portfolio_name:
                 st.session_state.loaded_portfolio_name = selected_load
                 # Force reload state
                 st.session_state.manual_portfolio_df = None
                 st.rerun()
        
        with col_opt:
            st.write("")
            st.write("")
            if st.button("➕ New / Import", help="Switch to creation mode"):
                 st.session_state.pf_input_mode = "Create / Upload"
                 st.session_state.manual_portfolio_df = None
                 st.rerun()

        # Get Data (Condition: Only if not already loaded in session to allow edits)
        if 'manual_portfolio_df' not in st.session_state or st.session_state.manual_portfolio_df is None:
             loaded_df = pm.get_portfolio(st.session_state.loaded_portfolio_name)
             if loaded_df is not None:
                  st.session_state.manual_portfolio_df = loaded_df
                  df = loaded_df
                  filename = f"portfolio_{st.session_state.loaded_portfolio_name}.csv"
                  st.info(f"Loaded **{len(df)}** assets from *{st.session_state.loaded_portfolio_name}*")
             else:
                  df = None
        else:
             df = st.session_state.manual_portfolio_df
             filename = f"portfolio_{st.session_state.loaded_portfolio_name}.csv"
             
    else:
        # --- CREATION MODE ---
        st.subheader("📝 Create or Import Portfolio")
        
        if saved_names:
            if st.button("🔙 Back to Saved Portfolios"):
                st.session_state.pf_input_mode = "Manage Portfolios"
                st.rerun()

        tab_create, tab_upload = st.tabs(["Manual Entry", "Upload CSV"])
        
        with tab_upload:
            uploaded_file = st.file_uploader("Upload CSV", type=['csv'], help="Required columns: Symbol, Company Name")
            if uploaded_file is not None:
                try:
                    file_bytes = uploaded_file.read()
                    df = load_portfolio_file(file_bytes, uploaded_file.name)
                    filename = uploaded_file.name
                    st.success(f"✅ Loaded {len(df)} stocks")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        with tab_create:
            # Initialize Data (5 Empty Rows) only for NEW creation
            if 'manual_portfolio_df' not in st.session_state or st.session_state.manual_portfolio_df is None:
                st.session_state.manual_portfolio_df = pd.DataFrame(
                    [{"Symbol": "", "Company Name": "", "Quantity": 0, "Average Price": 0.0}] * 5
                )

            # We use the common editor below for Manual Entry too.
            df = st.session_state.manual_portfolio_df # Provisional
            
    # --- COMMON EDITOR & ANALYSIS AREA ---
    
    # Ensure DF exists in state
    if 'manual_portfolio_df' not in st.session_state or st.session_state.manual_portfolio_df is None:
         # Fallback empty structure
         st.session_state.manual_portfolio_df = pd.DataFrame([{"Symbol": "", "Company Name": "", "Quantity": 0, "Average Price": 0.0}])

    # Editor is shown ONLY if we are in Manual Creation OR if we want to allow editing matches.
    # To keep it simple: "View/Edit Portfolio" expander
    
    with st.expander("📝 View / Edit Holdings", expanded=(st.session_state.pf_input_mode == "Create / Upload")):
        
        work_df = st.session_state.manual_portfolio_df.copy()
        
        # 1. Enforce Types (Robustness)
        if "Quantity" in work_df.columns:
            work_df["Quantity"] = pd.to_numeric(work_df["Quantity"], errors='coerce').fillna(0).astype(int)
        if "Average Price" in work_df.columns:
            work_df["Average Price"] = pd.to_numeric(work_df["Average Price"], errors='coerce').fillna(0.0).astype(float)
        
        # 2. Config toggle
        # Default to Custom (Text) View to prevent 'Blank' issues with Unknown symbols
        # Unless user explicitly wants Dropdown
        is_custom = st.session_state.get('allow_custom_view', True)
        
        if st.toggle("Enable Text Entry (Custom Symbols)", value=is_custom, key='allow_custom_view'):
             symbol_col_view = st.column_config.TextColumn("Symbol", required=True)
        else:
             from rover_tools.ticker_resources import get_common_tickers
             symbol_col_view = st.column_config.SelectboxColumn(options=get_common_tickers(), required=True)

        edited_df = st.data_editor(
            work_df,
            num_rows="dynamic",
            width='stretch',
            column_config={
                "Symbol": symbol_col_view,
                "Company Name": st.column_config.TextColumn("Company Name"),
                "Quantity": st.column_config.NumberColumn("Quantity", min_value=0, step=1),
                "Average Price": st.column_config.NumberColumn("Avg Price", min_value=0.0, format="₹ %.2f")
            },
            key="portfolio_editor_main"
        )
        
        # Validation Logic
        if edited_df is not None:
             valid_df = edited_df[edited_df["Symbol"].astype(str).str.strip() != ""].copy()
             
             # Post-process (Split ' - ')
             def parse_row(row):
                 val = str(row['Symbol'])
                 if " - " in val:
                     parts = val.split(" - ")
                     row['Symbol'] = parts[0]
                     if not row['Company Name']: row['Company Name'] = parts[1]
                 return row
             
             if not valid_df.empty:
                 valid_df = valid_df.apply(parse_row, axis=1)
                 df = valid_df # Update the main DF reference
                 st.session_state.manual_portfolio_df = valid_df # Persist changes

    # --- ACTION BAR (Analyze & Save) ---
    if df is not None and not df.empty:
        
        # Save Controls
        col_act_save, col_act_analyze = st.columns([1, 1], gap="large")
        
        with col_act_save:
             if st.button("💾 Save Changes", use_container_width=True):
                 name = st.text_input("Confirm Name", value=st.session_state.get('loaded_portfolio_name', 'My Portfolio'))
                 if name:
                     pm.save_portfolio(name, df)
                     st.success("Saved!")
                     st.session_state.loaded_portfolio_name = name
                     st.session_state.pf_input_mode = "Manage Portfolios"
                     time.sleep(1)
                     st.rerun()
        
        with col_act_analyze:
             # Primary Action
             if st.button("🚀 Analyze Portfolio", type="primary", use_container_width=True):
                 
                 # VALIDATION: Check for empty data before sending
                 clean_tickers = [str(x).strip() for x in df['Symbol'].tolist() if str(x).strip()] if 'Symbol' in df else []
                 
                 if not clean_tickers:
                     st.error("⚠️ Portfolio is empty! Please add valid symbols before analyzing.")
                 elif len(clean_tickers) < 1:
                     st.error("⚠️ Please add at least one valid stock symbol.")
                 else:
                     allowed, message = st.session_state.portfolio_limiter.is_allowed()
                     if not allowed:
                         st.error(f"⏱️ {message}")
                     else:
                         from utils.analysis_runner import run_analysis
                         run_analysis(df, filename or "portfolio_analysis", max_parallel)




    
    # End of active function logic. 
    pass

    # --- ANALYSIS CLEANUP ---
    # The Analysis Button and logic are now inside render_upload_section_logic
    # We remove the old duplicated blocks below this line.
    pass
