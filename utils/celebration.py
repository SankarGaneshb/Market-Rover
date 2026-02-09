import streamlit as st
from utils.metrics import track_engagement

def trigger_celebration(event_type: str, description: str, metadata: dict = None):
    """
    Triggers Streamlit balloons and logs engagement metrics.
    """
    # 1. Set global balloon flag for app.py to trigger
    st.session_state.show_balloons = True
    
    # 2. Log Engagement Metric
    current_user = st.session_state.get('username', 'guest')
    track_engagement(current_user, event_type, description, metadata)

def report_failure(event_type: str, error_msg: str, metadata: dict = None):
    """
    Logs an engagement failure.
    """
    current_user = st.session_state.get('username', 'guest')
    from utils.metrics import track_engagement_failure
    track_engagement_failure(current_user, event_type, error_msg, metadata)
