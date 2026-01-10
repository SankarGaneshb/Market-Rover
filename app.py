"""
Market-Rover - Streamlit Web Application

Interactive portfolio analysis with real-time progress tracking, visualizers, and forecasts.
"""

import os
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

import warnings
warnings.filterwarnings('ignore')
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime
import time

# Ensure root is in path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    import plotly
    import rover_tools
except ImportError as e:
    st.error(f"Critical Dependency Error: {e}")

from config import UPLOAD_DIR, REPORT_DIR
from utils.job_manager import JobManager
from utils.metrics import (get_api_usage, get_performance_stats, get_cache_stats, 
                           get_error_stats)
from utils.security import RateLimiter
from utils.auth import AuthManager
from utils.user_manager import UserProfileManager
from utils.logger import get_logger

# Import Tabs
from tabs.portfolio_tab import show_portfolio_analysis_tab, show_recent_reports
from tabs.visualizer_tab import show_visualizer_tab
from tabs.market_analysis_tab import show_market_analysis_tab
from tabs.forecast_tab import show_forecast_tracker_tab
from tabs.shadow_tab import show_shadow_tracker_tab
from tabs.forensic_tab import show_forensic_tab
from tabs.profiler_tab import show_profiler_tab
from tabs.system_health import show_system_health_tab
from tabs.brain_tab import show_brain_tab

# Initialize logger
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Market-Rover",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="auto"
)

# Initialize session state
if 'job_manager' not in st.session_state:
    st.session_state.job_manager = JobManager()

if 'current_job_id' not in st.session_state:
    st.session_state.current_job_id = None

if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

if 'test_mode' not in st.session_state:
    st.session_state.test_mode = False

# Rate limiters for API protection
if 'visualizer_limiter' not in st.session_state:
    st.session_state.visualizer_limiter = RateLimiter(max_requests=30, time_window_seconds=60)

if 'heatmap_limiter' not in st.session_state:
    st.session_state.heatmap_limiter = RateLimiter(max_requests=20, time_window_seconds=60)

if 'portfolio_limiter' not in st.session_state:
    st.session_state.portfolio_limiter = RateLimiter(max_requests=5, time_window_seconds=300) # 5 per 5 mins


def main():
    """Main application entry point"""
    
    # Initialize Authentication
    auth_manager = AuthManager()
    
    # Check if user is authenticated
    if not auth_manager.check_authentication():
        # Stop execution if not authenticated 
        # (check_authentication handles the login widget display)
        st.stop()
        
    # Show logout button in sidebar
    auth_manager.logout_widget()
    
    # CSS for Fixed Footer and Layout Adjustments
    st.markdown(
        """
        <style>
        /* Fixed Footer styling */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #262730; /* Streamlit dark theme secondary bg */
            color: white;
            text-align: center;
            padding: 12px;
            font-size: 14px;
            border-top: 1px solid #4e4e4e;
            z-index: 999999; /* Ensure it sits on top of everything */
            box-shadow: 0px -2px 10px rgba(0,0,0,0.2);
        }
        .footer p {
            margin: 0;
        }
        
        /* Adjust main content to not be hidden by footer */
        .block-container {
            padding-bottom: 100px; /* Increased padding */
        }
        
        /* Adjust Sidebar to not be hidden by footer */
        section[data-testid="stSidebar"] > div > div:nth-child(2) {
            padding-bottom: 100px;
        }
        
        /* Hide default Streamlit footer */
        footer {visibility: hidden;}
        </style>
        <div class="footer">
            <p>⚠️ <b>Disclaimer:</b> Market-Rover is for informational purposes only. Not financial advice. Past performance ≠ future results. Consult a qualified advisor. No liability for losses. By using this app, you accept these terms.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Header
    st.title("🔍 Market-Rover")
    st.markdown("**AI-Powered Stock Intelligence System**")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("🚀 About")
        st.markdown("""
        **AI Stock Intelligence**        
        Your personal quant researcher.
        """)        
        st.markdown("---")
        st.header("📍 Navigation") # NAVIGATION        
        
        # User Profile Status Check
        user_profile_mgr = UserProfileManager()
        current_user = st.session_state.get('username', 'guest')
        
        profile_status = user_profile_mgr.get_profile_status(current_user)
        force_profile = not profile_status['exists'] or profile_status['needs_update']
        
        # Complete Options List
        all_options = [
            "📤 Portfolio Analysis",
            "📈 Market Visualizer",
            "🎯 Forecast Tracker",
            "---",
            "🔍 Market Analysis",
            "🕵️ Shadow Tracker",
            "🛡️ Integrity Shield",
            "---",
            "🧠 Agent Brain",
             "---",
            "👤 Investor Profile",
            "⚙️ System Health"
        ]
        
        # Filter separators for actual selection
        valid_options = [o for o in all_options if o != "---"]
        
        if "nav_selection" not in st.session_state:
            st.session_state.nav_selection = valid_options[0]
            
        # Hook for forced redirect
        if force_profile and st.session_state.nav_selection != "👤 Investor Profile":
             st.session_state.nav_selection = "👤 Investor Profile"
             
        selection = st.radio(
            "Navigate", 
            valid_options, 
            index=valid_options.index(st.session_state.nav_selection) if st.session_state.nav_selection in valid_options else 0,
            key="nav_radio",
            label_visibility="hidden"
        )
        
        # Sync selection back to state
        st.session_state.nav_selection = selection

        # Enforce Profile Check (Double Check)
        if force_profile and selection != "👤 Investor Profile":
             st.warning("🔒 Features Locked")
             st.info("You must complete your Investor Profile first.")
             selection = "👤 Investor Profile" # Override locally for rendering logic
        
        st.markdown("---")        
        st.markdown("### ⚙️ Settings")
        max_parallel = st.slider(
            "Concurrent Stocks",
            min_value=1,
            max_value=10,
            value=5,
            help="Number of stocks to analyze simultaneously"
        )        
        # Test mode toggle (compact)
        test_mode = st.checkbox(
            "🧪 Test Mode",
            value=st.session_state.test_mode,
            help="Use mock data without API calls"
        )
        st.session_state.test_mode = test_mode
        if test_mode:
            st.info("🧪 Test mode enabled - using mock data")

        # Observability metrics
        st.markdown("---")
        with st.expander("📊 Observability", expanded=False):
            st.markdown("### Real-Time Metrics")
            # API Usage
            api_usage = get_api_usage()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("API Calls Today", f"{api_usage['today']}/{api_usage['limit']}")
            with col2:
                st.metric("Remaining", api_usage['remaining'])
            # Progress bar for API quota
            quota_pct = api_usage['today'] / api_usage['limit']
            st.progress(quota_pct, text=f"Quota: {quota_pct*100:.0f}%")
            st.markdown("---")
            # Performance Stats
            perf_stats = get_performance_stats()
            if perf_stats['total_analyses'] > 0:
                st.markdown("**Performance**")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Total Analyses",
                        perf_stats['total_analyses']
                    )
                with col2:
                    st.metric(
                        "Avg Duration",
                        f"{perf_stats['avg_duration']:.1f}s"
                    )
                st.markdown("---")
            
            # Cache Stats
            cache_stats = get_cache_stats()
            total_cache = cache_stats['hits'] + cache_stats['misses']
            if total_cache > 0:
                st.markdown("**Cache Performance**")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Hit Rate", f"{cache_stats['hit_rate']:.0f}%")
                with col2:
                    st.metric("Total Ops", total_cache)
                st.markdown("---")
            
            # Error Stats
            error_stats = get_error_stats()
            if error_stats['total'] > 0:
                st.markdown("**Errors**")
                st.metric("Total Errors", error_stats['total'])
                if error_stats['by_type']:
                    st.json(error_stats['by_type'], expanded=False)
            
            # Refresh button (note: refreshes entire app)
            if st.button("🔄 Refresh App", width="stretch", help="Refreshes the entire app to update all metrics"):
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📚 Recent Reports")
        show_recent_reports()


    
    # Main content area - Render based on selection
    
    if selection.startswith("📤 Portfolio Analysis"):
        show_portfolio_analysis_tab(max_parallel)
    
    elif selection.startswith("📈 Market Visualizer"):
        show_visualizer_tab()

    elif selection.startswith("🔍 Market Analysis"):
        show_market_analysis_tab()

    elif selection.startswith("🎯 Forecast Tracker"):
        show_forecast_tracker_tab()
    
    elif selection.startswith("🕵️ Shadow Tracker"):
        show_shadow_tracker_tab()

    elif selection.startswith("🛡️ Integrity Shield"):
        show_forensic_tab()
    
    elif selection.startswith("🧠 Agent Brain"):
        show_brain_tab()
        
    elif selection.startswith("👤 Investor Profile"):
        show_profiler_tab()

    elif selection.startswith("⚙️ System Health"):
        show_system_health_tab()


if __name__ == "__main__":
    main()
