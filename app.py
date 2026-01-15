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
from tabs.portfolio_tab import show_portfolio_analysis_tab
from tabs.market_analysis_tab import show_market_analysis_tab
from tabs.forecast_tab import show_forecast_tracker_tab
from tabs.shadow_tab import show_shadow_tracker_tab
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
        /* Global Spacing Reductions */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 5rem !important;
        }

        [data-testid="stVerticalBlock"] > div {
            gap: 0.5rem !important;
        }

        h1 {
            margin-top: -1rem !important;
            margin-bottom: 0.5rem !important;
        }

        h2, h3 {
            margin-top: 0.5rem !important;
            margin-bottom: 0.25rem !important;
        }

        .stMetric {
            margin-bottom: -1rem !important;
        }

        hr {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }

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
            "🎯 Forecast Tracker",
            "---",
            "🔍 Market Analysis",
            "🕵️ Shadow Tracker",
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
    # Default settings after UI removal
    st.session_state.test_mode = False
    max_parallel = 5

    # Main content area - Render based on selection
    
    if selection.startswith("👤 Investor Profile"):
        show_profiler_tab()

    if selection.startswith("📤 Portfolio Analysis"):
        show_portfolio_analysis_tab(max_parallel)
    
    elif selection.startswith("🔍 Market Analysis"):
        show_market_analysis_tab()

    elif selection.startswith("🎯 Forecast Tracker"):
        show_forecast_tracker_tab()
    
    elif selection.startswith("🕵️ Shadow Tracker"):
        show_shadow_tracker_tab()

    
    elif selection.startswith("🧠 Agent Brain"):
        show_brain_tab()
        
    elif selection.startswith("⚙️ System Health"):
        show_system_health_tab()


if __name__ == "__main__":
    main()
