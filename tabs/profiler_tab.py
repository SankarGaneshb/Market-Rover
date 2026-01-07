import streamlit as st
import pandas as pd
from rover_tools.analytics.investor_profiler import InvestorProfiler, InvestorPersona
from rover_tools.ticker_resources import NIFTY_50_SECTOR_MAP, NIFTY_50_BRAND_META
from utils.user_manager import UserProfileManager
from utils.security import sanitize_ticker

def show_profiler_tab():
    st.header("👤 Institutional Investor Profiler")
    st.markdown("""
    **Discover your Persona & Build a 'Smart' Portfolio.**
    Combine your favorite Brands with AI-driven Forensic & Shadow Strategies.
    """)
    
    profiler = InvestorProfiler()
    
    # Init Session State
    if "persona" not in st.session_state:
        st.session_state.persona = None
    if "user_brands" not in st.session_state:
        st.session_state.user_brands = []
    if "model_portfolio" not in st.session_state:
        st.session_state.model_portfolio = None
        
    # --- 1. SLEEP TEST (QUIZ) ---
    with st.expander("📝 Step 1: The 'Sleep Test' (Define Persona)", expanded=(st.session_state.persona is None)):
        st.info("""
        **What is an Investor Persona?**
        Your persona is your "financial personality." It balances three key forces:
        1.  **Risk Tolerance:** How much market volatility can you handle without panic?
        2.  **Time Horizon:** How long can you leave the money untouched?
        3.  **Loss Capacity:** Can your lifestyle survive a temporary loss?
        
        *Answer honestly to get a mathematically suitable strategy.*
        """)
        
        with st.form("profiler_form"):
            col_q1, col_q2, col_q3 = st.columns(3)
            with col_q1:
                st.markdown("**1. The Panic Test 📉**")
                st.caption("The market crashes 20% tomorrow. What is your immediate reaction?")
                q1 = st.radio("Behavior:", ["Sell everything immediately", "Wait and watch / Do nothing", "Buy more at lower prices"], key="q1")
            with col_q2:
                st.markdown("**2. The Deadline Test ⏳**")
                st.caption("When do you absolutely need to access this specific capital?")
                q2 = st.radio("Timeframe:", ["Less than 3 Years", "3 to 7 Years", "More than 7 Years"], key="q2")
            with col_q3:
                st.markdown("**3. The Cushion Test 🛏️**")
                st.caption("If this portfolio drops 50% temporarily, does your lifestyle change?")
                q3 = st.radio("Impact:", ["My lifestyle would be significantly affected", "I'd have to cut back on some luxuries", "No impact, my lifestyle is secure"], key="q3")
            
            submitted = st.form_submit_button("Analyze Profile 🧠")
            
            if submitted:
                # Mapping user answers to scores (1=Conservative, 2=Moderate, 3=Aggressive)
                # Q1: Sell=1, Wait=2, Buy=3
                if "Sell" in q1: s1=1
                elif "Wait" in q1: s1=2
                else: s1=3
                
                # Q2: <3yr = 1, 3-7yr = 2, >7yr = 3
                if "Less" in q2: s2=1
                elif "3 to 7" in q2: s2=2
                else: s2=3
                
                # Q3: Significant=1, Cut back=2, No impact=3
                if "significantly" in q3: s3=1
                elif "luxury" in q3 or "cut back" in q3: s3=2
                else: s3=3

                st.session_state.persona = profiler.get_profile(s1, s2, s3)
                st.rerun()

    # --- 2. THE BRAND SHOP (USER PARTICIPATION) ---
    if st.session_state.persona:
        p = st.session_state.persona
        strategy = profiler.get_allocation_strategy(p)
        
        st.divider()
        st.subheader(f"🎉 Persona: {p.value}")
        st.info(f"**Strategy: {strategy['description']}**")
        
        st.markdown("### 🛍️ Step 2: The 'Brand Shop' (Buy What You Know)")
        st.markdown(f"Select up to **3 Nifty 50 Brands** you use/trust daily. We will use these as your **Core Equity Portfolio**.")
        
        # Organize Nifty 50 by Sector for easier selection
        sectors = sorted(list(set(NIFTY_50_SECTOR_MAP.values())))
        selected_brands = st.session_state.user_brands
        
        # Tabs for Sectors
        tabs = st.tabs(sectors)
        
        new_selection = []
        
        for i, sector in enumerate(sectors):
            with tabs[i]:
                # Filter tickers for this sector
                try:
                    sector_tickers = [t for t, s in NIFTY_50_SECTOR_MAP.items() if s == sector]
                    
                    # Create a grid
                    cols = st.columns(3)
                    
                    for j, ticker in enumerate(sector_tickers):
                        col = cols[j % 3]
                        
                        # Get Metadata
                        meta = NIFTY_50_BRAND_META.get(ticker, {"name": ticker, "color": "#333333"})
                        
                        # Generate SVG Logo
                        import base64
                        tick_short = ticker.replace('.NS', '')[:4]
                        color = meta['color']
                        text_color = "#000000" if color in ["#FFD200", "#FFF200"] else "#ffffff"
                        
                        svg_raw = f"""
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
                            <rect width="32" height="32" rx="8" fill="{color}"/>
                            <text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" fill="{text_color}" font-family="Arial" font-weight="bold" font-size="9">{tick_short}</text>
                        </svg>
                        """
                        b64_svg = base64.b64encode(svg_raw.encode('utf-8')).decode('utf-8')
                        icon_src = f"data:image/svg+xml;base64,{b64_svg}"
                        
                        # Display Card
                        with col:
                            # Visual Card
                            st.markdown(f"""
                            <div style="background: white; border-radius: 8px; padding: 10px; border: 1px solid #eee; display: flex; align-items: center; margin-bottom: 5px;">
                                <img src="{icon_src}" style="width: 35px; height: 35px; margin-right: 10px; border-radius: 6px;">
                                <div style="line-height: 1.2;">
                                    <div style="font-weight: bold; font-size: 14px;">{tick_short}</div>
                                    <div style="font-size: 11px; color: #666;">{meta['name']}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Interaction (Checkbox)
                            is_checked = ticker in selected_brands
                            if st.checkbox("Select", value=is_checked, key=f"btn_{ticker}", label_visibility="collapsed"):
                                new_selection.append(ticker)
                                
                except Exception as e:
                     st.error(f"Error loading sector {sector}: {e}")

        # Update Session State with new/removed items logic if needed, 
        # but Streamlit reruns script on interaction, so we need to capture efficient state
        # Actually standard checkbox 'key' persistence works but 'new_selection' is transient.
        # Let's enforce the limit and warning here.
        
        cnt = len(new_selection)
        st.write(f"**Selected: {cnt}/3**")
        
        if cnt > 3:
            st.warning("⚠️ You picked more than 3 brands. We will only use the first 3 or most safe ones.")
            new_selection = new_selection[:3]
            
        st.session_state.user_brands = new_selection

        # Sector Constraint Warning
        # Check duplicates in sectors
        sel_sectors = [NIFTY_50_SECTOR_MAP.get(t, "Unknown") for t in new_selection]
        if len(sel_sectors) != len(set(sel_sectors)) and cnt > 1:
            st.warning("💡 **Diversification Tip:** You have multiple stocks from the same sector. Consider diversifying.")

        st.divider()
        
        # --- 3. GENERATION ---
        st.markdown("### 🤖 Step 3: AI Generation")
        
        if st.button("Generate Smart Portfolio 🚀"):
            with st.spinner(f"Running {strategy['description']} Engine..."):
                # 1. Generate
                raw_holdings = profiler.generate_smart_portfolio(p, st.session_state.user_brands)
                
                # 2. Validate (Forensic + Shadow + Correlation)
                flags = profiler.validator.validate_holdings(raw_holdings)
                
                # 3. Enrich Data
                final_data = []
                for h in raw_holdings:
                    sym = h['Symbol']
                    status = "✅ Clean"
                    note = h.get('Strategy', '')
                    
                    if sym in flags:
                        f = flags[sym]
                        if f['status'] == 'RED': status = "🔴 RISK"
                        elif f['status'] == 'AMBER': status = "⚠️ Warning"
                        note += f" | {f['reason']}"
                    
                    row = h.copy()
                    row['Health Status'] = status
                    row['AI Reasoning'] = note
                    final_data.append(row)
                    
                st.session_state.model_portfolio = pd.DataFrame(final_data)

        # --- 4. RESULTS ---
        if st.session_state.model_portfolio is not None:
             df_res = st.session_state.model_portfolio
             
             st.subheader("Your Custom Smart Portfolio")
             
             # Styling columns
             # Reorder
             cols = ['Symbol', 'Asset Class', 'Weight (%)', 'Health Status', 'AI Reasoning']
             df_show = df_res[cols]
             
             # Color highlight logic (using pandas styler is hard in st.data_editor, so we rely on status text)
             edited = st.data_editor(df_show, num_rows="dynamic", use_container_width=True, key="res_editor")
             
             # Action Buttons
             c1, c2 = st.columns(2)
             if c1.button("💾 Save Portfolio"):
                  from utils.portfolio_manager import PortfolioManager
                  # Ensure we get the correct username
                  current_user = st.session_state.get('username', 'guest')
                  pm = PortfolioManager(current_user)
                  
                  # Conversion to save format
                  save_df = edited.copy()
                  # Remove textual columns for saving if needed, or keep for notes
                  # Usually PM expects Quantity/AvgPrice. We mimic defaults.
                  if 'Weight (%)' in save_df.columns:
                      save_df['Quantity'] = (100000 * save_df['Weight (%)'] / 100).astype(int)
                  else:
                      save_df['Quantity'] = 10
                      
                  save_df['Average Price'] = 100.0
                  
                  success, msg = pm.save_portfolio(f"Smart {p.value} Portfolio", save_df)
                  if success:
                      st.success("✅ Saved Successfully!")
                      # CRITICAL: Mark profile as updated to unlock other tabs
                      user_profile_mgr = UserProfileManager()
                      user_profile_mgr.update_profile_timestamp(current_user)
                      st.balloons()
                  else:
                      st.error(f"Save failed: {msg}")
                  
             if c2.button("Run Simulation 🎢"):
                  with st.spinner("Running Historical Simulation (1 Year) vs Nifty 50..."):
                      try:
                          import yfinance as yf
                          import plotly.graph_objects as go
                          import pandas as pd
                          
                          # 1. Prepare Portfolio Tickers & Weights
                          sim_df = edited.copy()
                          if sim_df.empty:
                              st.warning("Portfolio is empty.")
                          else:
                              tickers = [t if t.endswith('.NS') else f"{t}.NS" for t in sim_df['Symbol'].tolist()]
                              weights = sim_df['Weight (%)'].values / 100.0
                              
                              # 2. Fetch Data (Portfolio + Benchmark)
                              data = yf.download(tickers + ['^NSEI'], period="1y", progress=False)['Close']
                              
                              if data.empty:
                                  st.error("No data available for simulation.")
                              else:
                                  # Benchmark
                                  bench = data['^NSEI'].pct_change().fillna(0)
                                  bench_cum = (1 + bench).cumprod()
                                  
                                  # Portfolio
                                  # Filter only stock columns
                                  stock_data = data[tickers]
                                  # Calculate weighted returns
                                  # Align weights to columns found
                                  valid_tickers = [t for t in tickers if t in stock_data.columns]
                                  
                                  if not valid_tickers:
                                      st.error("Could not fetch data for selected stocks.")
                                  else:
                                      # Re-normalize weights for valid data
                                      # This is a simplification; ideally we use exact weights mapping
                                      stock_returns = stock_data[valid_tickers].pct_change().fillna(0)
                                      
                                      # Simple equal weight fallback if mapping is complex, OR map correctly
                                      # Let's assume order is preserved or use map
                                      # Better: Construct daily portfolio value
                                      
                                      # We map symbol to weight
                                      w_map = dict(zip([t if t.endswith('.NS') else f"{t}.NS" for t in sim_df['Symbol']], weights))
                                      
                                      # Calculate daily weighted return
                                      port_ret = pd.Series(0.0, index=stock_returns.index)
                                      total_w = 0.0
                                      for t in valid_tickers:
                                          w = w_map.get(t, 0)
                                          total_w += w
                                          port_ret += stock_returns[t] * w
                                          
                                      if total_w > 0:
                                          port_ret = port_ret / total_w # Re-normalize to 100% of captured stocks
                                          
                                      port_cum = (1 + port_ret).cumprod()
                                      
                                      # 3. Plot
                                      fig_sim = go.Figure()
                                      fig_sim.add_trace(go.Scatter(x=port_cum.index, y=port_cum, mode='lines', name='Smart Portfolio', line=dict(color='#00ff00', width=2)))
                                      fig_sim.add_trace(go.Scatter(x=bench_cum.index, y=bench_cum, mode='lines', name='Nifty 50', line=dict(color='gray', dash='dot')))
                                      
                                      fig_sim.update_layout(title="Historical Performance Simulation (1 Year)", yaxis_title="Growth (1 = Base)", height=400)
                                      st.plotly_chart(fig_sim, use_container_width=True)
                                      
                                      # Metrics
                                      p_ret = (port_cum.iloc[-1] - 1) * 100
                                      b_ret = (bench_cum.iloc[-1] - 1) * 100
                                      
                                      m1, m2 = st.columns(2)
                                      m1.metric("Portfolio Return", f"{p_ret:.1f}%", delta=f"{p_ret-b_ret:.1f}% vs Index")
                                      m2.metric("Benchmark Return", f"{b_ret:.1f}%")
                                      
                                      st.success("Simulation Complete! This strategy would have performed as shown above.")
                                      
                      except Exception as e:
                          st.error(f"Simulation Error: {str(e)}")


