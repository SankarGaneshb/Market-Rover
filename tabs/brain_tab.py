import streamlit as st
import pandas as pd
from rover_tools.memory_tool import read_memory
from utils.autonomy_logger import read_autonomy_events

# ============================================================
# Agent Manifests (Static definitions – no live import needed)
# ============================================================

MARKET_ROVER_AGENTS = [
    {
        "id": "A",
        "role": "Portfolio Manager",
        "emoji": "📁",
        "platform": "Market-Rover",
        "model": "gemini-2.0-flash",
        "goal": "Read and process user's stock portfolio from CSV.",
        "tools": ["read_portfolio", "calculate_portfolio_risk_tool"],
        "status": "Active",
    },
    {
        "id": "B",
        "role": "Market Impact Strategist",
        "emoji": "🌐",
        "platform": "Market-Rover",
        "model": "gemini-2.0-flash",
        "goal": "Monitor macro events, global cues (Crude/Gold), corporate actions & news.",
        "tools": ["search_market_news", "get_global_cues", "get_corporate_actions",
                  "announce_regime_tool", "log_pivot_tool", "check_accounting_fraud",
                  "fetch_economic_calendar_tool"],
        "status": "Active",
    },
    {
        "id": "C",
        "role": "Sentiment Analysis Expert",
        "emoji": "🎭",
        "platform": "Market-Rover",
        "model": "gemini-2.0-flash",
        "goal": "Classify news sentiment (Fear/Greed) and detect contrarian traps.",
        "tools": ["analyze_retail_sentiment_tool"],
        "status": "Active",
    },
    {
        "id": "D",
        "role": "Technical Market Analyst",
        "emoji": "📊",
        "platform": "Market-Rover",
        "model": "gemini-2.0-flash",
        "goal": "Analyze Nifty/BankNifty price action, trends, and support/resistance levels.",
        "tools": ["analyze_market_context", "batch_get_stock_data", "detect_technical_patterns_tool"],
        "status": "Active",
    },
    {
        "id": "E",
        "role": "Intelligence Report Writer",
        "emoji": "📝",
        "platform": "Market-Rover",
        "model": "gemini-2.0-flash",
        "goal": "Generate comprehensive weekly stock intelligence report with risk highlights.",
        "tools": ["fetch_historical_context_tool"],
        "status": "Active",
    },
    {
        "id": "F",
        "role": "Market Data Visualizer",
        "emoji": "🎨",
        "platform": "Market-Rover",
        "model": "gemini-2.0-flash",
        "goal": "Generate premium visual dashboards with derivative analysis.",
        "tools": ["generate_market_snapshot", "generate_sector_heatmap_tool"],
        "status": "Active",
    },
    {
        "id": "G",
        "role": "Institutional Shadow Analyst",
        "emoji": "🕵️",
        "platform": "Market-Rover",
        "model": "gemini-2.0-flash",
        "goal": "Detect market traps (Accumulation/Distribution) by comparing Sentiment vs Flow.",
        "tools": ["analyze_sector_flow_tool", "fetch_block_deals_tool", "batch_detect_accumulation",
                  "get_trap_indicator_tool", "read_past_predictions_tool", "save_prediction_tool",
                  "fetch_fii_dii_flow_tool"],
        "status": "Active",
    },
    {
        "id": "H",
        "role": "Traditional Timing Analyst",
        "emoji": "🪔",
        "platform": "Market-Rover",
        "model": "gemini-2.0-flash",
        "goal": "Identify culturally significant investing windows via Indian calendars & astrology.",
        "tools": ["fetch_subha_muhurtham_tool", "analyze_traditional_calendar_tool"],
        "status": "Active",
    },
]

INVESTBRAND_AGENTS = [
    {
        "id": "IB-1",
        "role": "Game Master",
        "emoji": "🎮",
        "platform": "InvestBrand",
        "model": "gemini-2.0-flash",
        "goal": "Orchestrate daily brand puzzle challenges and track player streaks.",
        "tools": ["daily_puzzle_scheduler", "streak_tracker"],
        "status": "Active",
    },
    {
        "id": "IB-2",
        "role": "Brand Profiler",
        "emoji": "🏷️",
        "platform": "InvestBrand",
        "model": "gemini-2.0-flash",
        "goal": "Build rich brand profiles linking NSE tickers to logos, sectors & trivia.",
        "tools": ["brand_data_fetcher", "ticker_mapper"],
        "status": "Active",
    },
    {
        "id": "IB-3",
        "role": "Teacher Agent",
        "emoji": "🎓",
        "platform": "InvestBrand",
        "model": "gemini-2.0-flash",
        "goal": "Explain brand-to-stock connections using simplified financial concepts.",
        "tools": ["explainer_tool", "quiz_generator"],
        "status": "Active",
    },
    {
        "id": "IB-4",
        "role": "QC Agent",
        "emoji": "✅",
        "platform": "InvestBrand",
        "model": "gemini-2.0-flash",
        "goal": "Validate logo assets and brand data quality before publishing puzzles.",
        "tools": ["logo_validator", "data_quality_checker"],
        "status": "Active",
    },
    {
        "id": "IB-5",
        "role": "Ops Support Agent",
        "emoji": "🛠️",
        "platform": "InvestBrand",
        "model": "gemini-2.0-flash",
        "goal": "Monitor game infrastructure and diagnose runtime errors automatically.",
        "tools": ["log_analyzer", "error_classifier", "alert_dispatcher"],
        "status": "Active",
    },
]

PLEDGE_ROVER_AGENTS = [
    {
        "id": "PR-1",
        "role": "Pledge Council",
        "emoji": "🛡️",
        "platform": "Pledge Rover",
        "model": "gemini-2.0-flash",
        "goal": "Analyze promoter pledging data and score contagion risk across companies.",
        "tools": ["bse_pledge_fetcher", "nse_pledge_fetcher", "contagion_scorer"],
        "status": "Active",
    },
    {
        "id": "PR-2",
        "role": "Data Harvester",
        "emoji": "🌾",
        "platform": "Pledge Rover",
        "model": "gemini-2.0-flash",
        "goal": "Collect and normalize raw shareholding & pledging data from BSE/NSE sources.",
        "tools": ["bse_scraper", "nse_scraper", "data_normalizer"],
        "status": "Active",
    },
]

PLATFORM_COLORS = {
    "Market-Rover": "#1e6f50",
    "InvestBrand":  "#4a3fa0",
    "Pledge Rover": "#9b2335",
}

PLATFORM_ICONS = {
    "Market-Rover": "🔍",
    "InvestBrand":  "🧩",
    "Pledge Rover": "🛡️",
}


def _render_agent_card(agent: dict):
    platform = agent["platform"]
    color = PLATFORM_COLORS.get(platform, "#555")
    st.markdown(
        f"""
        <div style="border-left: 4px solid {color}; padding: 10px 14px; background: #1e1e2e;
                    border-radius: 6px; margin-bottom: 8px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:1.05em; font-weight:600; color:#f0f0f0;">
                    {agent['emoji']} {agent['role']}
                </span>
                <span style="font-size:0.7em; background:{color}33; color:{color};
                             border:1px solid {color}55; border-radius:20px; padding:2px 9px;">
                    {agent['id']}
                </span>
            </div>
            <div style="font-size:0.82em; color:#aaa; margin-top:4px;">{agent['goal']}</div>
            <div style="font-size:0.75em; color:#666; margin-top:4px;">
                🤖 <code>{agent['model']}</code> &nbsp;|&nbsp;
                🔧 {len(agent['tools'])} tool(s)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_brain_tab():
    """
    Displays the 'Agent Brain' Dashboard.
    Visualizes Memory (Knowledge) and Autonomy Events (Behavior).
    Shows all agents across Market-Rover, InvestBrand, and Pledge Rover ecosystems.
    """
    st.title("🧠 Agent Brain & Autonomy Monitor")

    st.markdown("""
    This dashboard reveals the **internal thought processes** of the Autonomous Agents across
    the entire **Market-Rover ecosystem** —
    📈 Market-Rover · 🧩 InvestBrand · 🛡️ Pledge Rover.
    """)

    # ─── PLATFORM AGENT ROSTER ───────────────────────────────────────────────
    st.subheader("🤖 Agent Roster — Full Ecosystem")

    all_agents = MARKET_ROVER_AGENTS + INVESTBRAND_AGENTS + PLEDGE_ROVER_AGENTS

    # Platform filter
    platforms = ["All", "Market-Rover", "InvestBrand", "Pledge Rover"]
    selected_platform = st.pills(
        "Filter by Platform", platforms, default="All", key="brain_platform_filter"
    )

    if selected_platform == "All":
        filtered = all_agents
    else:
        filtered = [a for a in all_agents if a["platform"] == selected_platform]

    # Group by platform
    for platform_name, platform_emoji in PLATFORM_ICONS.items():
        platform_agents = [a for a in filtered if a["platform"] == platform_name]
        if not platform_agents:
            continue

        with st.expander(
            f"{platform_emoji} **{platform_name}** — {len(platform_agents)} Agents",
            expanded=True,
        ):
            cols = st.columns(2)
            for i, agent in enumerate(platform_agents):
                with cols[i % 2]:
                    _render_agent_card(agent)

    # Summary metrics
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Agents", len(all_agents))
    m2.metric("Market-Rover", len(MARKET_ROVER_AGENTS))
    m3.metric("InvestBrand", len(INVESTBRAND_AGENTS))
    m4.metric("Pledge Rover", len(PLEDGE_ROVER_AGENTS))

    st.divider()

    col1, col2 = st.columns(2)

    # --- 1. MEMORY VIEWER ---
    with col1:
        st.subheader("📚 Active Memory (Stateful Learning)")
        memories = read_memory()

        if not memories:
            st.info("No memories stored yet. Agents will learn after the first run.")
        else:
            df_mem = pd.DataFrame(memories)
            if not df_mem.empty:
                cols_order = ['date', 'ticker', 'signal', 'confidence', 'outcome']
                existing_cols = [c for c in cols_order if c in df_mem.columns]
                df_mem = df_mem[existing_cols]

            st.dataframe(df_mem, use_container_width=True, hide_index=True)

            if not df_mem.empty and 'outcome' in df_mem.columns:
                completed = df_mem[df_mem['outcome'] != 'Pending']
                total_completed = len(completed)

                if total_completed > 0:
                    wins = len(completed[completed['outcome'].str.contains('Success')])
                    win_rate = (wins / total_completed) * 100

                    m1c, m2c, m3c = st.columns(3)
                    m1c.metric("Total Predictions", len(df_mem))
                    m2c.metric("Validated Outcomes", total_completed)
                    m3c.metric("🎯 Win Rate", f"{win_rate:.1f}%")

    # --- 2. AUTONOMY STREAM ---
    with col2:
        st.subheader("⚡ Autonomy Activity Stream")
        events = read_autonomy_events()

        if not events:
            st.info("No autonomy events logged yet.")
        else:
            events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            for evt in events[:10]:
                role = evt.get('role', 'Agent')
                e_type = evt.get('type', 'INFO')
                detail = evt.get('details', '')
                ticker = evt.get('ticker', '')
                time_str = evt.get('timestamp', '').split('T')[-1][:5]

                if "REGIME" in e_type:
                    icon = "🛡️" if "DEFENSIVE" in detail else "🚀"
                elif "MEMORY" in e_type:
                    icon = "🧠"
                elif "PIVOT" in e_type:
                    icon = "🔀"
                else:
                    icon = "🤖"

                st.markdown(f"""
                **{time_str}** {icon} **{e_type}** ({role})  
                _{detail}_  
                `{ticker}`
                <hr style="margin: 5px 0">
                """, unsafe_allow_html=True)

    st.divider()

    # --- 3. LOGIC INSPECTOR ---
    st.subheader("🔍 Current Logic Matrix")
    with st.expander("View Active Decision Rules"):
        st.markdown("""
        **Regime Router (Strategist)**:
        - `DEFENSIVE` if **VIX > 22** OR **Crude > $95** OR **USD/INR > 84.5**
        - `GROWTH` otherwise.
        
        **Shadow Learning (Shadow Analyst)**:
        - If `Last Prediction` == `False` → **Confidence Penalty -20%**
        
        **InvestBrand QC Gate**:
        - Logo validated → Puzzle published. Failed QC → flagged for manual review.
        
        **Pledge Rover Council**:
        - Contagion Risk Score ≥ 70 → 🔴 High Risk alert raised.
        """)
