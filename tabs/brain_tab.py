import streamlit as st
import pandas as pd
from rover_tools.memory_tool import read_memory
from utils.autonomy_logger import read_autonomy_events

def show_brain_tab():
    """
    Displays the 'Agent Brain' Dashboard.
    Visualizes Memory (Knowledge) and Autonomy Events (Behavior).
    """
    st.title("🧠 Agent Brain & Autonomy Monitor")
    
    st.markdown("""
    This dashboard reveals the **internal thought processes** of the Autonomous Agents.
    Track how they **Learn** from history and **Adapt** to market regimes.
    """)
    
    col1, col2 = st.columns(2)
    
    # --- 1. MEMORY VIEWER ---
    with col1:
        st.subheader("📚 Active Memory (Stateful Learning)")
        memories = read_memory()
        
        if not memories:
            st.info("No memories stored yet. Agents will learn after the first run.")
        else:
            # Convert to DataFrame
            df_mem = pd.DataFrame(memories)
            # Reorder columns if possible
            if not df_mem.empty:
                cols = ['date', 'ticker', 'signal', 'confidence', 'outcome']
                # Filter strictly for columns that exist
                existing_cols = [c for c in cols if c in df_mem.columns]
                df_mem = df_mem[existing_cols]
                
            st.dataframe(df_mem, use_container_width=True, hide_index=True)
            st.caption(f"Total Knowledge Nodes: {len(memories)}")

    # --- 2. AUTONOMY STREAM ---
    with col2:
        st.subheader("⚡ Autonomy Activity Stream")
        events = read_autonomy_events() # Returns list of dicts
        
        if not events:
            st.info("No autonomy events logged yet.")
        else:
            # Sort by timestamp descending
            events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            for evt in events[:10]: # Show last 10
                role = evt.get('role', 'Agent')
                e_type = evt.get('type', 'INFO')
                detail = evt.get('details', '')
                ticker = evt.get('ticker', '')
                time = evt.get('timestamp', '').split('T')[-1][:5] # HH:MM
                
                # Dynamic Icon
                if "REGIME" in e_type:
                    icon = "🛡️" if "DEFENSIVE" in detail else "🚀"
                elif "MEMORY" in e_type:
                    icon = "🧠"
                elif "PIVOT" in e_type:
                    icon = "🔀"
                else:
                    icon = "🤖"
                    
                st.markdown(f"""
                **{time}** {icon} **{e_type}** ({role})  
                _{detail}_  
                `{ticker}`
                <hr style="margin: 5px 0">
                """, unsafe_allow_html=True)
                
    st.divider()
    
    # --- 3. LOGIC INSPECTOR (Static for now, dynamic later) ---
    st.subheader("🔍 Current Logic Matrix")
    with st.expander("View Active Decision Rules"):
        st.markdown("""
        **Regime Router (Strategist)**:
        - `DEFENSIVE` if **VIX > 22** OR **Crude > $95** OR **USD/INR > 84.5**
        - `GROWTH` otherwise.
        
        **Shadow Learning (Shadow Analyst)**:
        - If `Last Prediction` == `False` -> **Confidence Penalty -20%**
        """)
