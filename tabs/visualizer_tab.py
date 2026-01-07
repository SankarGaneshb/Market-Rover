import streamlit as st
from utils.security import sanitize_ticker
from utils.visualizer_interface import generate_market_snapshot
from utils.metrics import track_error_detail

def show_visualizer_tab():
    """Show the Market Visualizer tab - Generates comprehensive market snapshot image"""
    st.header("📈 Market Visualizer")
    st.markdown("Generate **comprehensive market snapshot** with Price Chart and Scenario Targets.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info("⚠️ **Disclaimer:** Automated analysis. Not financial advice.")
        ticker_raw = st.text_input("Enter Stock Ticker (e.g., SBIN, TCS)", value="SBIN", key="viz_ticker")
        
        if st.button("Generate Snapshot", type="primary", width="stretch", key="btn_viz"):
            # Sanitize input
            ticker = sanitize_ticker(ticker_raw)
            if not ticker:
                st.error("Please enter a ticker symbol.")
                return

            # Check rate limit
            allowed, message = st.session_state.visualizer_limiter.is_allowed()
            if not allowed:
                 st.warning(f"⏱️ {message}")
                 return

            with st.spinner(f"🎨 Generating snapshot for {ticker}... This may take a minute."):
                try:
                    result = generate_market_snapshot(ticker)
                    
                    if result['success']:
                        st.success("✅ Snapshot generated successfully!")
                        
                        # Display Image
                        if result['image_path']:
                            st.image(result['image_path'], caption=f"Market Snapshot: {ticker}", width="stretch")
                        
                        # Display Summary
                        st.markdown("### 📝 Analysis Summary")
                        st.markdown(result['message'])
                        
                    else:
                        st.error("❌ Generation Failed")
                        st.error(result['message'])
                        
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
                    try:
                        track_error_detail(type(e).__name__, str(e), context={"location": "show_visualizer_tab", "ticker": ticker})
                    except Exception:
                        pass
    
        st.markdown("""
        **Dashboard Features:**
        - 📊 **Price Chart**: With volatility bands and time-adjusted targets.
        - 🌡️ **Monthly Heatmap**: Historical performance from IPO to date.
        - 🔮 **2026 Forecast**: Long-term trend projection.
        """)
