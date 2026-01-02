import streamlit as st
import pandas as pd
import json
import plotly.express as px
from pathlib import Path
from datetime import datetime

# Define metrics directory
METRICS_DIR = Path("metrics")

def load_data():
    """Load workflow events and session logs"""
    data = []
    # Load all workflow_events jsonl files
    files = list(METRICS_DIR.glob("workflow_events_*.jsonl"))
    if not files:
        return pd.DataFrame()
        
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except:
                    continue
    
    if not data:
        return pd.DataFrame()
        
    return pd.DataFrame(data)

def show_system_health_tab():
    st.header("⚙️ System Health & Process Metrics")
    st.markdown("Monitor the efficiency, stability, and speed of your development workflows.")
    
    # 1. Load Data
    df = load_data()
    
    if df.empty:
        st.info("No process metrics found yet. Start using the new workflows to populate this dashboard!")
        return

    # 2. Process Data
    # Convert timestamp
    df['ts'] = pd.to_datetime(df['ts'])
    
    # Separate types
    df_starts = df[df['type'] == 'start'].set_index('session_id')
    df_ends = df[df['type'] == 'end'].set_index('session_id')
    df_events = df[df['type'] == 'event']
    
    # Calculate Cycle Times
    cycle_times = []
    if not df_starts.empty and not df_ends.empty:
        df_sessions = df_starts.join(df_ends, lsuffix='_start', rsuffix='_end')
        df_completed = df_sessions.dropna(subset=['ts_end'])
        
        if not df_completed.empty:
            df_completed['duration_minutes'] = (df_completed['ts_end'] - df_completed['ts_start']).dt.total_seconds() / 60
            cycle_times = df_completed
            
    # KPI Calculations
    total_sessions = len(df_starts)
    completed_sessions = len(df_ends)
    success_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    avg_cycle_time = 0
    if isinstance(cycle_times, pd.DataFrame) and not cycle_times.empty:
        avg_cycle_time = cycle_times['duration_minutes'].mean()
        
    # Count Emergency Overrides
    overrides = 0
    if not df_events.empty:
        overrides = len(df_events[df_events['event_name'] == 'emergency_override'])
        
    stability_score = max(0, 100 - (overrides * 10)) # Simple penalty logic
    
    # --- UI Layout ---
    
    # 3. KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Success Rate", f"{success_rate:.1f}%", help="Completed Sessions / Started Sessions")
    with col2:
        st.metric("Avg Cycle Time", f"{avg_cycle_time:.2f} min", help="Average duration of completed workflows")
    with col3:
        st.metric("Stability Score", f"{stability_score}%", delta=f"-{overrides} Overrides" if overrides > 0 else "Stable", delta_color="inverse")
    with col4:
        st.metric("Total Activities", total_sessions)
        
    st.markdown("---")
    
    # 4. Charts
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("⏱️ Speed Trend")
        if isinstance(cycle_times, pd.DataFrame) and not cycle_times.empty:
            # Sort by start time
            viz_df = cycle_times.sort_values('ts_start')
            fig = px.bar(
                viz_df, 
                x='ts_start', 
                y='duration_minutes',
                color='workflow_start',
                title="Workflow Duration History",
                labels={'duration_minutes': 'Duration (min)', 'ts_start': 'Date', 'workflow_start': 'Workflow'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No cycle time data available.")

    with col_right:
        st.subheader("🛡️ Protocol Usage")
        if not df_events.empty:
            event_counts = df_events['event_name'].value_counts().reset_index()
            event_counts.columns = ['Event Type', 'Count']
            
            fig2 = px.pie(
                event_counts, 
                names='Event Type', 
                values='Count', 
                title="Event Distribution",
                hole=0.4
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.caption("No protocol events (exceptions/overrides) logged.")

    # 5. Detailed Tables
    st.markdown("### 📝 Recent Event Log")
    
    tab1, tab2 = st.tabs(["Exceptions & Overrides", "Session History"])
    
    with tab1:
        if not df_events.empty:
            display_cols = ['ts', 'event_name', 'description']
            st.dataframe(
                df_events[display_cols].sort_values('ts', ascending=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No exceptions logged.")
            
    with tab2:
        if isinstance(cycle_times, pd.DataFrame) and not cycle_times.empty:
            session_cols = ['ts_start', 'workflow_start', 'status', 'duration_minutes']
            st.dataframe(
                cycle_times[session_cols].sort_values('ts_start', ascending=False),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No sessions completed.")
