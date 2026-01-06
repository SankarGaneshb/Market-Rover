import streamlit as st
import pandas as pd
from rover_tools.analytics.investor_profiler import InvestorProfiler, InvestorPersona
from utils.user_manager import UserProfileManager
from utils.security import sanitize_ticker

def show_profiler_tab():
    st.header("👤 Investor Profiler")
    st.markdown("""
    **Discover your Institutional Investor Persona.**
    Take the 'Sleep Test' to generate a scientific Asset Allocation plan with strict risk controls.
    """)
    
    profiler = InvestorProfiler()
    
    # Init Session State
    if "persona" not in st.session_state:
        st.session_state.persona = None
        
    # Quiz Section
    with st.expander("📝 The 'Sleep Test' (3 Questions)", expanded=(st.session_state.persona is None)):
        with st.form("profiler_form"):
            st.subheader("1. The Panic Test 📉")
            q1 = st.radio(
                "If your portfolio drops 20% tomorrow, what do you do?",
                [
                    "A) Sell everything to stop the pain. (Conservative)",
                    "B) Do nothing / Wait. (Moderate)",
                    "C) Buy more. (Aggressive)"
                ],
                key="q1"
            )
            
            st.subheader("2. The Deadline Test ⏳")
            q2 = st.radio(
                "When do you need this money back?",
                [
                    "A) < 3 Years (Short Term - Compounding won't work)",
                    "B) 3-7 Years (Medium Term)",
                    "C) 7+ Years (Long Term)"
                ],
                key="q2"
            )
            
            st.subheader("3. The Cushion Test 🛏️")
            q3 = st.radio(
                "If you lose this money, does your lifestyle change?",
                [
                    "A) Yes, I can't pay bills. (Low Capacity)",
                    "B) It hurts, but I'm okay. (Medium Capacity)",
                    "C) No impact, I have other assets. (High Capacity)"
                ],
                key="q3"
            )
            
            submitted = st.form_submit_button("Analyze Profile 🧠")
            
            if submitted:
                # Scoring Logic
                s1 = 1 if "A)" in q1 else (2 if "B)" in q1 else 3)
                s2 = 1 if "A)" in q2 else (2 if "B)" in q2 else 3)
                s3 = 1 if "A)" in q3 else (2 if "B)" in q3 else 3)
                
                persona = profiler.get_profile(s1, s2, s3)
                st.session_state.persona = persona
                
                # Update Profile Timestamp
                upm = UserProfileManager()
                current_user = st.session_state.get('username', 'guest')
                upm.update_profile_timestamp(current_user)
                
                st.rerun()

    # Result Section
    if st.session_state.persona:
        p = st.session_state.persona
        strategy = profiler.get_allocation_strategy(p)
        
        st.divider()
        st.subheader(f"🎉 Your Persona: {p.value}")
        st.info(f"**{strategy['description']}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Asset Allocation")
            alloc = strategy['allocation']
            df_alloc = pd.DataFrame(list(alloc.items()), columns=["Asset Class", "Weight (%)"])
            st.dataframe(df_alloc, hide_index=True, use_container_width=True)
            
            # Pie Chart
            import plotly.express as px
            fig = px.pie(df_alloc, values='Weight (%)', names='Asset Class', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("### 🎯 Portfolio Structure")
            st.warning(f"**Strict Ticker Limit: {strategy['max_tickers']} Stocks**")
            
            struct = strategy['structure']
            for k, v in struct.items():
                st.write(f"- **{k}**: {v} Slots")
                
        
        st.divider()
        st.subheader("🤖 AI Model Portfolio Generator")
        
        if st.button("Generate Model Portfolio"):
            with st.spinner("Selecting high-quality assets based on your profile..."):
                model_holdings = profiler.generate_model_portfolio(p)
                st.session_state.model_portfolio = pd.DataFrame(model_holdings)
                
        if "model_portfolio" in st.session_state:
            df_model = st.session_state.model_portfolio
            
            # Editable Editor
            st.markdown("#### Proposed Holdings")
            edited_df = st.data_editor(df_model, num_rows="dynamic", use_container_width=True, key="model_editor")
            
            col_a, col_b = st.columns(2)
            
            # SAVE FEATURE
            with col_a:
                st.write("###### Save to Portfolios")
                pf_name = st.text_input("Portfolio Name", value=f"My {p.value} Model")
                if st.button("💾 Save Portfolio"):
                     from utils.portfolio_manager import PortfolioManager
                     pm = PortfolioManager(st.session_state.get('username'))
                     # Prepare dataframe for saving (needs Quantity, Average Price columns usually)
                     # For model, we assume a nominal investment amount, e.g. 10 Lakhs
                     save_df = edited_df.copy()
                     save_df['Quantity'] = (100000 * save_df['Weight (%)'] / 100).astype(int) # Dummy allocation logic
                     save_df['Average Price'] = 1000 # Dummy price
                     
                     success, msg = pm.save_portfolio(pf_name, save_df)
                     if success: st.success(msg)
                     else: st.error(msg)

            # SIMULATION FEATURE
            with col_b:
                st.write("###### Performance Check")
                if st.button("🚀 Simulate vs Benchmark"):
                    with st.spinner("Calculating Composite Benchmark..."):
                        import yfinance as yf
                        import plotly.graph_objects as go
                        import datetime
                        
                        # 1. Fetch Data
                        tickers = edited_df['Symbol'].tolist()
                        proxies_map = profiler.get_benchmark_proxies()
                        
                        # Get unique proxies needed
                        needed_proxies = list(set([proxies_map.get(row['Asset Class'], '^NSEI') for _, row in edited_df.iterrows()]))
                        
                        # Download all data
                        all_tickers_raw = list(set(tickers + needed_proxies))
                        all_tickers = []
                        for t in all_tickers_raw:
                             clean = sanitize_ticker(t)
                             if clean: all_tickers.append(clean)
                        # Validating tickers before download (basic check)
                        
                        try:
                            data = yf.download(all_tickers, period="1y", progress=False)['Close']
                            
                            # Normalize to 100
                            if not data.empty:
                                rebased = data / data.iloc[0] * 100
                                
                                # 2. Calculate Portfolio Curve
                                # This is a simplified daily rebalance assumption for visualization
                                portfolio_curve = pd.Series(0, index=data.index)
                                
                                for _, row in edited_df.iterrows():
                                    sym = row['Symbol']
                                    w = row['Weight (%)'] / 100.0
                                    if sym in rebased.columns:
                                        portfolio_curve += rebased[sym] * w
                                        
                                # 3. Calculate COMPOSITE BENCHMARK Curve
                                # Sum (Weight_i * Proxy_Index_i)
                                benchmark_curve = pd.Series(0, index=data.index)
                                used_benchmarks = {} # For pie chart
                                
                                # Group by asset class to get total weight per class
                                asset_weights = edited_df.groupby('Asset Class')['Weight (%)'].sum()
                                
                                for asset_class, total_weight in asset_weights.items():
                                    proxy = proxies_map.get(asset_class, '^NSEI')
                                    w = total_weight / 100.0
                                    
                                    if proxy in rebased.columns:
                                        # Handle missing data in proxy (ffill)
                                        proxy_series = rebased[proxy].ffill()
                                        benchmark_curve += proxy_series * w
                                        used_benchmarks[proxy] = used_benchmarks.get(proxy, 0) + total_weight

                                # 4. Plot
                                fig_perf = go.Figure()
                                fig_perf.add_trace(go.Scatter(x=portfolio_curve.index, y=portfolio_curve, name=f"{p.value} Portfolio", line=dict(color='green', width=2)))
                                fig_perf.add_trace(go.Scatter(x=benchmark_curve.index, y=benchmark_curve, name="Composite Benchmark", line=dict(color='gray', dash='dash')))
                                
                                fig_perf.update_layout(title="1-Year Performance Simulation (Rebased to 100)", xaxis_title="Date", yaxis_title="Value")
                                st.plotly_chart(fig_perf, use_container_width=True)
                                
                                # Composition Pie
                                df_bench = pd.DataFrame(list(used_benchmarks.items()), columns=['Proxy Index', 'Weight (%)'])
                                fig_pie = px.pie(df_bench, values='Weight (%)', names='Proxy Index', title="Benchmark Composition")
                                st.plotly_chart(fig_pie, use_container_width=True)
                                
                                final_ret = portfolio_curve.iloc[-1] - 100
                                bench_ret = benchmark_curve.iloc[-1] - 100
                                st.metric("Portfolio Alpha", f"{final_ret - bench_ret:.2f}%", delta=f"{final_ret:.2f}% vs {bench_ret:.2f}%")
                                
                            else:
                                st.error("No data returned from Yahoo Finance.")
                                
                        except Exception as e:
                            st.error(f"Simulation Error: {e}")

        st.divider()
        st.success("✅ **Next Step:** customize the generated portfolio in the editor above, then Save it for detailed analysis in the main dashboard.")
