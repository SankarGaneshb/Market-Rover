import streamlit as st
import pandas as pd
import base64
import html
from rover_tools.analytics.investor_profiler import InvestorProfiler, InvestorPersona
from rover_tools.ticker_resources import NIFTY_50_SECTOR_MAP, NIFTY_50_BRAND_META
from utils.user_manager import UserProfileManager
from utils.security import sanitize_ticker

def show_profiler_tab():
    st.header("👤 Investor Profiler")
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
    if "profiler_scores" not in st.session_state: # Initialize for scores persistence
        st.session_state.profiler_scores = None
    
    # --- Persistence: Load Profile if exists ---
    user_mgr = UserProfileManager()
    current_user = st.session_state.get('username', 'guest')
    
    if st.session_state.persona is None:
        saved_profile = user_mgr.get_user_profile(current_user)
        if saved_profile and 'persona' in saved_profile:
            try:
                # Rehydrate Enum from string value
                # We need to find the Enum member by value
                for p in InvestorPersona:
                    if p.value == saved_profile['persona']:
                        st.session_state.persona = p
                        break
                
                # Rehydrate brands if available
                if 'brands' in saved_profile:
                     st.session_state.user_brands = saved_profile['brands']
                     
                # Rehydrate scores (optional, but good for UI consistency if we showed them)
                if 'scores' in saved_profile:
                    st.session_state.profiler_scores = saved_profile['scores']
                    
            except Exception as e:
                st.error(f"Error loading profile: {e}")

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

                # Set Persona
                new_persona = profiler.get_profile(s1, s2, s3)
                st.session_state.persona = new_persona
                
                # Save to Disk
                scores = {'q1': s1, 'q2': s2, 'q3': s3}
                st.session_state.profiler_scores = scores # Keep in session
                
                user_mgr.save_user_profile(
                    username=current_user,
                    persona_val=new_persona.value,
                    scores=scores,
                    brands=[] 
                )
                
                st.success(f"Profile Saved: {new_persona.value}")
                st.rerun()

    if "user_growth_brands" not in st.session_state:
        st.session_state.user_growth_brands = []

    # --- 2. THE BRAND SHOP (USER PARTICIPATION) ---
    if st.session_state.persona:
        p = st.session_state.persona
        
        # Robustness: Handle if p is String instead of Enum (Streamlit State quirk)
        persona_val = p.value if hasattr(p, 'value') else str(p)
        
        # Re-verify Enum membership to be safe
        real_persona_enum = None
        for member in InvestorPersona:
            if member.value == persona_val:
                real_persona_enum = member
                break
        
        if real_persona_enum:
             p = real_persona_enum # Fix it
             strategy = profiler.get_allocation_strategy(p)
             
             st.divider()
             st.subheader(f"🎉 Persona: {p.value}")
             if strategy:
                 st.info(f"**Strategy: {strategy.get('description', 'Custom')}**")
             
             # --- Primary Selection (Nifty 50) ---
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
                             import html
                             tick_short = getattr(html, 'escape', lambda s: s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))(ticker.replace('.NS', '')[:4])
                             color = meta['color']
                             text_color = "#000000" if color in ["#FFD200", "#FFF200"] else "#ffffff"
                             
                             svg_raw = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="{color}"/><text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" fill="{text_color}" font-family="Arial" font-weight="bold" font-size="9">{tick_short}</text></svg>'
                             b64_svg = base64.b64encode(svg_raw.encode('utf-8')).decode('utf-8')
                             icon_src = f"data:image/svg+xml;base64,{b64_svg}"
                             
                             # Display Card
                             with col:
                                 # Visual Card
                                 # Ensure HTML safety for text
                                 safe_name = getattr(html, 'escape', lambda s: s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))(meta['name'])
                                 
                                 st.markdown(f'<div style="background: white; border-radius: 8px; padding: 10px; border: 1px solid #eee; display: flex; align-items: center; margin-bottom: 5px;"><img src="{icon_src}" style="width: 35px; height: 35px; margin-right: 10px; border-radius: 6px;"><div style="line-height: 1.2;"><div style="font-weight: bold; font-size: 14px; color: #333;">{tick_short}</div><div style="font-size: 11px; color: #666;">{safe_name}</div></div></div>', unsafe_allow_html=True)
                                 
                                 # Interaction (Checkbox)
                                 is_checked = ticker in selected_brands
                                 if st.checkbox("Select", value=is_checked, key=f"btn_{ticker}", label_visibility="collapsed"):
                                     new_selection.append(ticker)
                                     
                     except Exception as e:
                          st.error(f"Error loading sector {sector}: {e}")

        cnt = len(new_selection)
        st.write(f"**Selected Main Brands: {cnt}/3**")

        if new_selection:
            # Simple icon visualization code omitted for brevity as it's purely visual
            pass
        
        if cnt > 3:
            st.warning("⚠️ You picked more than 3 brands. We will only use the first 3.")
            new_selection = new_selection[:3]
            
        st.session_state.user_brands = new_selection

        # --- Secondary Selection (Midcap/Next50) for Compounder/Hunter ---
        is_growth_persona = (p == InvestorPersona.COMPOUNDER or p == InvestorPersona.HUNTER)
        
        if is_growth_persona:
            from rover_tools.ticker_resources import NIFTY_NEXT_50_SECTOR_MAP, NIFTY_MIDCAP_SECTOR_MAP, NIFTY_NEXT_50, NIFTY_MIDCAP
            
            # Configure based on Persona
            if p == InvestorPersona.COMPOUNDER:
                sec_title = "🚀 Step 2.5: Growth Accelerators (Nifty Next 50)"
                sec_limit = 2
                target_map = NIFTY_NEXT_50_SECTOR_MAP
                # We need a meta map. For now we mock it or infer from Nifty 50 if overlap
                # Or just use raw list
            else: # Hunter
                sec_title = "🏹 Step 2.5: Alpha Hunters (Nifty Midcap)"
                sec_limit = 2
                target_map = NIFTY_MIDCAP_SECTOR_MAP
            
            st.markdown(f"### {sec_title}")
            st.markdown(f"Select up to **{sec_limit} Brands** from this high-growth segment.")
            
            # 1. Get Sectors
            growth_sectors = sorted(list(set(target_map.values())))
            growth_selected = st.session_state.user_growth_brands
            
            # 2. Tabs
            g_tabs = st.tabs(growth_sectors)
            
            growth_new_selection = []
            
            for i, sector in enumerate(growth_sectors):
                with g_tabs[i]:
                    try:
                        # Filter tickers
                        g_tickers = [t for t, s in target_map.items() if s == sector]
                        
                        g_cols = st.columns(3)
                        for j, ticker in enumerate(g_tickers):
                            col = g_cols[j % 3]
                            
                            # Fallback Meta
                            # We check if it exists in primary map, else generic
                            meta = NIFTY_50_BRAND_META.get(ticker, {"name": ticker.replace('.NS',''), "color": "#5b21b6"}) # Purple default
                            
                            import html
                            tick_short = getattr(html, 'escape', lambda s: s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))(ticker.replace('.NS', '')[:4])
                            color = meta['color']
                            # Check specific known colors for common Next50
                            if ticker == "ZOMATO.NS": color = "#E23744"
                            if ticker == "BEL.NS": color = "#0054A6"
                            if ticker == "TRENT.NS": color = "#2D2926"
                            if ticker == "DLF.NS": color = "#0054A6"
                            
                            text_color = "#000000" if color in ["#FFD200", "#FFF200"] else "#ffffff"

                            svg_raw = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="{color}"/><text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" fill="{text_color}" font-family="Arial" font-weight="bold" font-size="9">{tick_short}</text></svg>'
                            b64_svg = base64.b64encode(svg_raw.encode('utf-8')).decode('utf-8')
                            icon_src = f"data:image/svg+xml;base64,{b64_svg}"

                            with col:
                                st.markdown(f'<div style="background: white; border-radius: 8px; padding: 10px; border: 1px solid #eee; display: flex; align-items: center; margin-bottom: 5px;"><img src="{icon_src}" style="width: 35px; height: 35px; margin-right: 10px; border-radius: 6px;"><div style="line-height: 1.2;"><div style="font-weight: bold; font-size: 14px; color: #333;">{ticker.replace(".NS", "")}</div></div></div>', unsafe_allow_html=True)
                                
                                is_checked = ticker in growth_selected
                                if st.checkbox("Select", value=is_checked, key=f"btn_g_{ticker}", label_visibility="collapsed"):
                                    growth_new_selection.append(ticker)

                    except Exception as e:
                        st.error(f"Error: {e}")
            
            cnt_growth = len(growth_new_selection)
            st.write(f"**Selected: {cnt_growth}/{sec_limit}**")
            
            if cnt_growth > sec_limit:
                st.warning(f"⚠️ Max {sec_limit} allowed. Using first {sec_limit}.")
                growth_new_selection = growth_new_selection[:sec_limit]
            
            st.session_state.user_growth_brands = growth_new_selection
            
        st.divider()
        
        # --- 3. GENERATION (AUTOMATIC) ---
        st.markdown("### 🤖 Step 3: AI Smart Portfolio")
        
        # Check conditions
        ready_to_gen = st.session_state.persona is not None and len(st.session_state.user_brands) >= 1
        if is_growth_persona and len(st.session_state.user_growth_brands) < 1:
             st.info("💡 You can proceed, but selecting at least 1 Growth Brand matches your persona better.")
        
        if ready_to_gen:
             # Save User Brands Choice
             if st.session_state.profiler_scores:
                 pass 

             with st.spinner(f"Running {strategy.get('description','')} Engine..."):
                # 1. Generate
                raw_holdings = profiler.generate_smart_portfolio(
                    p, 
                    st.session_state.user_brands, 
                    user_growth_brands=st.session_state.user_growth_brands if is_growth_persona else []
                )
                
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
             edited = st.data_editor(
                 df_show, 
                 num_rows="dynamic", 
                 use_container_width=True, 
                 key="res_editor",
                 column_config={
                     "Weight (%)": st.column_config.NumberColumn(
                        "Weight (%)",
                        help="Target Allocation (Must sum to 100% ideally)",
                        min_value=0,
                        max_value=100,
                        step=0.1,
                        format="%.1f %%"
                    ),
                 }
             )
             
             # Calculate total weight
             total_weight = edited['Weight (%)'].sum()
             
             # Show weight meter
             if abs(total_weight - 100.0) > 0.1:
                 st.warning(f"⚠️ Total Weight is {total_weight:.1f}%. Recommended: 100%. (You can still save, but simulation might be skewed)")
             else:
                 st.success("✅ Total Allocation: 100%")

             # Action Buttons
             if st.button("💾 Save Portfolio & Initialize"):
                  from utils.portfolio_manager import PortfolioManager
                  # Ensure we get the correct username
                  current_user = st.session_state.get('username', 'guest')
                  pm = PortfolioManager(current_user)
                  
                  # Conversion to save format
                  save_df = edited.copy()
                  
                  # Handle Quantity Logic
                  if 'Weight (%)' in save_df.columns:
                      # Mock quantity based on 100k notional
                      save_df['Quantity'] = (100000 * save_df['Weight (%)'] / 100).astype(int)
                  else:
                      save_df['Quantity'] = 10
                      
                  save_df['Average Price'] = 100.0 # Mock price for initial setup
                  
                  # Save Profile + Portfolio
                  # 1. Save Profile Data
                  if st.session_state.profiler_scores:
                      user_mgr.save_user_profile(
                        username=current_user,
                        persona_val=p.value,
                        scores=st.session_state.profiler_scores,
                        brands=st.session_state.user_brands
                    )
                  
                  # 2. Save Portfolio
                  success, msg = pm.save_portfolio(f"Smart {p.value} Portfolio", save_df)
                  
                  if success:
                      st.success("✅ Saved Successfully!")
                      
                      # CRITICAL: Mark profile as updated to unlock other tabs
                      user_profile_mgr = UserProfileManager() # local instance
                      user_profile_mgr.update_profile_timestamp(current_user)
                      
                      # Trigger Simulation Immediately
                      st.session_state.show_sim = True
                      
                      # Force Rerun to update Sidebar (allow small delay for user to read success)
                      st.rerun() 
                      
                  else:
                      st.error(f"Save failed: {msg}")
                  
             # --- SIMULATION SECTION (Auto-Shows after Save) ---
             # We check if profile is valid (saved) OR if user clicked Sim previously (legacy)
             # But prompt says "Once save portfolio is clicked... see Historical performance"
             # So we check if 'show_sim' is set or if we just saved.
             # Actually, since we do st.rerun() on save, we might lose 'show_sim' unless persisted.
             
             # Better check: If profile !needs_update, we show simulation.
             # Because 'needs_update' is false only after save.
             
             current_status = user_profile_mgr.get_profile_status(current_user)
             show_simulation = (not current_status['needs_update']) or st.session_state.get('show_sim', False)
             
             if show_simulation:
                  st.divider()
                  st.subheader("📈 Historical Performance Simulation")
                  with st.spinner("Running Historical Simulation (1 Year) vs Nifty 50..."):
                      try:
                          import yfinance as yf
                          import plotly.graph_objects as go
                          import pandas as pd
                          
                          # 1. Prepare Portfolio Tickers & Weights - Aggregate Duplicates
                          sim_df = edited.copy()
                          if sim_df.empty:
                               st.warning("Portfolio is empty.")
                          else:
                               # Aggregate weights by ticker to handle duplicates
                               raw_tickers = [t if t.endswith('.NS') else f"{t}.NS" for t in sim_df['Symbol'].tolist()]
                               raw_weights = sim_df['Weight (%)'].values / 100.0
                               
                               ticker_weights = {}
                               for t, w in zip(raw_tickers, raw_weights):
                                   ticker_weights[t] = ticker_weights.get(t, 0.0) + w
                               
                               unique_tickers = list(ticker_weights.keys())
                               
                               # 2. Fetch Data (Portfolio + Benchmark)
                               data = yf.download(unique_tickers + ['^NSEI'], period="1y", progress=False)['Close']
                               
                               if data.empty:
                                   st.error("No data available for simulation.")
                               else:
                                   # Benchmark
                                   if '^NSEI' in data.columns:
                                       bench = data['^NSEI'].pct_change().fillna(0)
                                   else:
                                       bench = pd.Series(0, index=data.index)

                                   bench_cum = (1 + bench).cumprod()
                                   
                                   # Portfolio
                                   valid_tickers = [t for t in unique_tickers if t in data.columns and t != '^NSEI']
                                   
                                   if not valid_tickers:
                                       st.error("Could not fetch data for selected stocks.")
                                   else:
                                       stock_data = data[valid_tickers]
                                       
                                       # Handle MultiIndex if necessary (yf.download can be tricky)
                                       if isinstance(stock_data.columns, pd.MultiIndex):
                                           stock_data.columns = stock_data.columns.droplevel(0)
                                           
                                       stock_returns = stock_data.pct_change().fillna(0)
                                       
                                       port_ret = pd.Series(0.0, index=stock_returns.index)
                                       total_w = 0.0
                                       
                                       for t in valid_tickers:
                                           w = ticker_weights.get(t, 0.0)
                                           total_w += w
                                           if t in stock_returns:
                                                port_ret += stock_returns[t] * w
                                           
                                       if total_w > 0:
                                           port_ret = port_ret / total_w 
                                           
                                       port_cum = (1 + port_ret).cumprod()
                                       
                                       # 3. Plot
                                       fig_sim = go.Figure()
                                       fig_sim.add_trace(go.Scatter(x=port_cum.index, y=port_cum, mode='lines', name='Smart Portfolio', line=dict(color='#00ff00', width=2)))
                                       fig_sim.add_trace(go.Scatter(x=bench_cum.index, y=bench_cum, mode='lines', name='Nifty 50', line=dict(color='gray', dash='dot')))
                                       
                                       fig_sim.update_layout(title="Historical Performance Simulation (1 Year)", yaxis_title="Growth (1 = Base)", height=400)
                                       st.plotly_chart(fig_sim, use_container_width=True)
                                       
                                       p_ret = (port_cum.iloc[-1] - 1) * 100
                                       b_ret = (bench_cum.iloc[-1] - 1) * 100
                                       
                                       m1, m2 = st.columns(2)
                                       m1.metric("Portfolio Return", f"{p_ret:.1f}%", delta=f"{p_ret-b_ret:.1f}% vs Index")
                                       m2.metric("Benchmark Return", f"{b_ret:.1f}%")
                                       
                      except Exception as e:
                          # st.error(f"Simulation Error: {str(e)}") # Suppress noise if transient
                          st.warning(f"Could not run simulation: {str(e)}")
