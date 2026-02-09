import streamlit as st
import pandas as pd
import json
import plotly.express as px
from pathlib import Path
from datetime import datetime

# Define metrics directory
METRICS_DIR = Path("metrics")

def load_data(prefix="workflow_events"):
    """Load jsonl metrics from METRICS_DIR based on prefix"""
    data = []
    files = list(METRICS_DIR.glob(f"{prefix}_*.jsonl"))
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
    st.header("⚙️ System Health & Performance")
    st.markdown("Monitor system stability, development workflows, and user engagement metrics.")
    
    # 1. Load Data
    df_workflow = load_data("workflow_events")
    df_engagement = load_data("engagement")
    
    # Define Tabs
    tab_overview, tab_workflows, tab_engagement = st.tabs([
        "🏠 Overview", 
        "🔄 Workflows", 
        "🎯 User Engagement"
    ])

    with tab_overview:
        if df_workflow.empty:
            st.info("No workflow metrics found yet.")
        else:
            # KPI Row for System
            df_workflow['ts'] = pd.to_datetime(df_workflow['ts'])
            df_starts = df_workflow[df_workflow['type'] == 'start']
            df_ends = df_workflow[df_workflow['type'] == 'end']
            
            total_sessions = len(df_starts)
            completed_sessions = len(df_ends)
            success_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("System Success Rate", f"{success_rate:.1f}%")
            col2.metric("Total Workflow Activities", total_sessions)
            
            if not df_engagement.empty:
                df_engagement['ts'] = pd.to_datetime(df_engagement['ts'])
                successes = len(df_engagement[df_engagement.get('status') != 'failed'])
                failures = len(df_engagement[df_engagement.get('status') == 'failed'])
                col3.metric("Engagement Success", successes, delta=f"-{failures} Failures" if failures > 0 else "0 Errors", delta_color="inverse")

        st.divider()
        st.subheader("🛡️ Recent Error Log (Last 10)")
        df_errors = load_data("errors")
        if not df_errors.empty:
            df_errors['timestamp'] = pd.to_datetime(df_errors['timestamp'])
            st.dataframe(df_errors.sort_values('timestamp', ascending=False).head(10), use_container_width=True)
        else:
            st.success("No system errors recorded today! 🎉")

    with tab_workflows:
        if df_workflow.empty:
            st.info("No workflow data.")
        else:
            # (Previously existing workflow logic moved here)
            df_workflow['ts'] = pd.to_datetime(df_workflow['ts'])
            df_starts = df_workflow[df_workflow['type'] == 'start'].set_index('session_id')
            df_ends = df_workflow[df_workflow['type'] == 'end'].set_index('session_id')
            df_events = df_workflow[df_workflow['type'] == 'event']
            
            # Use columns logic
            col_left, col_right = st.columns(2)
            with col_left:
                st.subheader("⏱️ Speed Trend")
                if not df_starts.empty and not df_ends.empty:
                    df_sessions = df_starts.join(df_ends, lsuffix='_start', rsuffix='_end')
                    df_completed = df_sessions.dropna(subset=['ts_end'])
                    if not df_completed.empty:
                        df_completed['duration_minutes'] = (df_completed['ts_end'] - df_completed['ts_start']).dt.total_seconds() / 60
                        viz_df = df_completed.sort_values('ts_start')
                        fig = px.bar(viz_df, x='ts_start', y='duration_minutes', color='workflow_start', title="Cycle Time")
                        st.plotly_chart(fig, use_container_width=True)
            
            with col_right:
                st.subheader("📊 Event Distribution")
                if not df_events.empty:
                    event_counts = df_events['event_name'].value_counts().reset_index()
                    event_counts.columns = ['Event', 'Count']
                    fig2 = px.pie(event_counts, names='Event', values='Count', hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)

    with tab_engagement:
        st.subheader("🎯 High-Value User Actions")
        if df_engagement.empty:
            st.info("No engagement metrics recorded yet. Perform actions like saving a portfolio to see data!")
        else:
            df_engagement['ts'] = pd.to_datetime(df_engagement['ts'])
            
            # Action Distribution
            action_counts = df_engagement['event'].value_counts().reset_index()
            action_counts.columns = ['Action', 'Count']
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.dataframe(action_counts, hide_index=True, use_container_width=True)
            with c2:
                fig3 = px.bar(action_counts, x='Count', y='Action', orientation='h', title="Top Engagements", color='Action')
                st.plotly_chart(fig3, use_container_width=True)
            
            st.divider()
            st.subheader("📝 Engagement History")
            st.dataframe(
                df_engagement[['ts', 'user', 'event', 'desc', 'status']].sort_values('ts', ascending=False),
                use_container_width=True,
                hide_index=True
            )
