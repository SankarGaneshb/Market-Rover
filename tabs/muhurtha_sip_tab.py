import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from rover_tools.sip_planner import MuhurthaSIPPlanner, PORTFOLIO_STYLES
from rover_tools.calendar_adapter import CalendarSyncAdapter
from rover_tools.broker_adapters import ZerodhaKiteAdapter, GrowwAdapter, ICICIDirectAdapter


def show_muhurtha_sip_tab():
    """
    Dedicated 1-Click Muhurtha-SIP Planner Tab.
    Provides systematic investment planning around auspicious Vedic windows with active market hours (09:15 - 15:30 IST) & holiday filters.
    Includes user choice for Next Session Live Execution vs Off-Market / AMO with full pros/cons transparency, score breakdown pie chart,
    and deep-dive Quant Safety Shield indicator analysis.
    """
    st.header("🪔 1-Click Muhurtha-SIP Planner")
    st.markdown("Plan and schedule your monthly systematic investments around high-probability Vedic Nakshatras & Shubh Muhurats with **active trading hours (09:15 - 15:30 IST)**, quant safety filters, and zero-OAuth broker execution.")

    # 1. User Inputs Row
    col_budget, col_style, col_exec = st.columns([1, 1.3, 1.3])

    with col_budget:
        budget_tier = st.selectbox(
            "1. Monthly Investment Budget",
            ["₹10,000", "₹25,000", "₹50,000", "₹1,00,000", "Custom"],
            index=1
        )
        if budget_tier == "Custom":
            budget_amount = st.number_input("Enter Budget (₹)", min_value=1000, value=25000, step=1000)
        else:
            budget_amount = float(budget_tier.replace("₹", "").replace(",", ""))

    with col_style:
        style_choice = st.selectbox(
            "2. Portfolio Strategy",
            list(PORTFOLIO_STYLES.keys()),
            index=0
        )

    with col_exec:
        exec_choice = st.radio(
            "3. Execution Mode",
            ["⚡ Next Session Live (Recommended)", "🌙 Off-Market / AMO Order"],
            index=0,
            help="Choose between live execution during the auspicious daytime window or an advance After Market Order (AMO)."
        )
        is_amo = "AMO" in exec_choice
        exec_mode = "AMO" if is_amo else "LIVE"

    # 2. Comprehensive Educational Comparison Card (Pros & Cons)
    with st.expander("ℹ️ **Understanding Execution Modes: Next Session Live vs. Off-Market AMO (Pros & Cons)**", expanded=False):
        c_live, c_amo = st.columns(2)

        with c_live:
            st.markdown("""
            #### ⚡ Next Session Live Execution *(Recommended)*
            **How it works:**
            You execute your order live during the active market session on the designated trading day, specifically inside the daytime auspicious window (e.g., *Abhijit Muhurat* `11:45 AM – 12:35 PM IST`).

            **✅ Pros:**
            - **Best Price Discovery**: Trades during the liquid mid-day session with tightest bid-ask spreads and minimal slippage.
            - **Active Quant Safety Shield**: Live 50-EMA support, RSI levels, and Institutional Anti-Trap radar are checked against real-time quotes before executing.
            - **No Opening Spikes**: Avoids the volatile 09:15 – 09:25 AM opening gap-up/gap-down price distortions.
            - **Calendar Notification**: 1-Click Google Calendar event with a **15-minute advance alarm** alerts you right before the auspicious window opens.

            **⚠️ Cons:**
            - Requires you to be online or trigger your trade during active trading hours (09:15 AM – 03:30 PM IST).
            """)

        with c_amo:
            st.markdown("""
            #### 🌙 Off-Market / AMO (After Market Order)
            **How it works:**
            You place the order outside trading hours (on weekends, holidays, or weekday evenings after 3:45 PM). Your broker queues the order and automatically routes it to NSE at **09:15 AM Market Open** on the next trading session.

            **✅ Pros:**
            - **100% Set-and-Forget Convenience**: Place your order anytime from the comfort of your home without worrying about weekday market timings.
            - **Instant Auspicious Intent**: Formally book your investment during weekend planetary yogas (e.g., Ravi Pushya on a Sunday).
            - **Automated Routing**: Broker automatically pushes your basket to the exchange at 09:15 AM without manual intervention.

            **⚠️ Cons:**
            - **Opening Volatility Risk**: Market orders at 09:15 AM execute against the opening auction/pre-open price which can have wider spreads for initial minutes.
            - **Static Safety Checks**: Pre-market quotes cannot dynamically account for unexpected morning global gap-down events.
            """)

    # 3. Calculate Plan
    planner = MuhurthaSIPPlanner()
    plan = planner.calculate_plan(
        budget=budget_amount,
        portfolio_style=style_choice,
        market_days_only=True,
        execution_mode=exec_mode
    )
    primary = plan["primary_window"]
    safety = plan.get("safety_status", {})

    # 4. Auspicious Window & Calendar Action Row
    st.markdown("---")
    col_card, col_action = st.columns([1.3, 1])

    with col_card:
        yogas_str = ", ".join(primary["special_yogas"]) if primary["special_yogas"] else "Auspicious Nakshatra Alignment"
        total_score = primary.get("score", 50)
        safety_score = safety.get("score", 75)
        safety_rating = safety.get("rating", "STRONG")
        badge_col = safety.get("badge_color", "green")
        badge_hex = "#22c55e" if badge_col == "green" else ("#f59e0b" if badge_col == "orange" else "#ef4444")

        if is_amo:
            badge_text = "🌙 AMO QUEUED (09:15 AM MARKET OPEN)"
            badge_bg = "#6366f1" # Indigo
            time_display = f"09:15 AM IST on {primary.get('next_trading_day', primary['date'])} (Place anytime before 08:59 AM IST)"
        else:
            badge_text = "🟢 MARKET ACTIVE (09:15 - 15:30 IST)" if primary.get("is_trading_day") else "⚠️ EXCHANGE CLOSED"
            badge_bg = "#15803d" if primary.get("is_trading_day") else "#b91c1c"
            time_display = primary['auspicious_time']

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 12px; padding: 18px; border: 1px solid #334155; color: #f8fafc; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 1.1em; font-weight: bold; color: #f59e0b;">✨ {'AMO EXECUTION WINDOW' if is_amo else 'OPTIMAL AUSPICIOUS WINDOW'}</span>
                <div>
                    <span style="background: #f59e0b; color: #0f172a; font-size: 0.75em; font-weight: bold; padding: 3px 8px; border-radius: 12px; margin-right: 6px;">⭐ SCORE: {total_score} PTS</span>
                    <span style="background: {badge_bg}; color: #ffffff; font-size: 0.72em; font-weight: bold; padding: 3px 8px; border-radius: 12px;">{badge_text}</span>
                </div>
            </div>
            <div style="font-size: 1.35em; font-weight: bold; color: #ffffff; margin-bottom: 4px;">
                📅 {'Execution Day: ' + primary.get('next_trading_day', primary['date']) if is_amo else primary['date'] + ' (' + primary['weekday'] + ')'}
            </div>
            <div style="font-size: 1.0em; color: #38bdf8; margin-bottom: 8px;">
                ⏰ Window: {time_display}
            </div>
            <div style="font-size: 0.88em; color: #cbd5e1; line-height: 1.4;">
                • <b>Nakshatra</b>: {primary['nakshatra']} &nbsp;|&nbsp; <b>Tithi</b>: {primary['tithi']}<br>
                • <b>Alignments</b>: {yogas_str}<br>
                • <b>Rahu Kaalam</b>: <span style="color: #f87171;">{primary['rahu_kaalam']}</span> (Avoided)<br>
                • <b>Quant Safety</b>: <span style="color: {badge_hex}; font-weight: bold;">🛡️ {safety_score}/100 {safety_rating} SAFETY</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_action:
        st.markdown(f"#### 📅 {'AMO Execution Reminders' if is_amo else 'Live Calendar Reminders'}")
        if is_amo:
            st.caption("Sets a reminder for 09:00 AM IST on next market open to verify your AMO order execution status.")
        else:
            st.caption("Never miss the Muhurat window. Automatically sets a reminder alert 15 minutes before inside active market hours.")

        # Calendar Sync Links with execution_mode
        google_cal_url = CalendarSyncAdapter.generate_google_calendar_url(plan, broker_name="Mutual Funds & Stocks", execution_mode=exec_mode)
        ics_content = CalendarSyncAdapter.generate_ics_content(plan, broker_name="Mutual Funds & Stocks", execution_mode=exec_mode)

        st.link_button(f"📅 Add to Google Calendar ({exec_mode})", google_cal_url, type="primary", use_container_width=True)
        st.download_button(
            f"📥 Download .ics ({exec_mode})",
            data=ics_content,
            file_name=f"muhurtha_sip_{primary['date']}_{exec_mode.lower()}.ics",
            mime="text/calendar",
            use_container_width=True
        )

    # 5. Score Breakdown & Factor Analysis with Interactive Pie Chart
    st.markdown("---")
    st.subheader("📊 Auspicious Score & Factor Breakdown")
    st.markdown(f"How the **{total_score} Points** composite score is derived across Vedic astronomical alignments and quantitative market mechanics:")

    score_breakdown = primary.get("score_breakdown", {})
    if not score_breakdown:
        score_breakdown = {
            "Auspicious Nakshatra": 30,
            "Active Market Hours (NSE/BSE)": 25,
            "Shukla Paksha (Growth)": 15
        }

    col_pie, col_table = st.columns([1.2, 1.2])

    with col_pie:
        labels = list(score_breakdown.keys())
        values = [max(0, v) for v in score_breakdown.values()]
        custom_colors = ['#f59e0b', '#06b6d4', '#10b981', '#8b5cf6', '#ec4899', '#3b82f6']

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.48,
            textinfo='label+percent',
            insidetextorientation='radial',
            marker=dict(colors=custom_colors[:len(labels)]),
            hovertemplate='<b>%{label}</b><br>Points: %{value} pts<br>Contribution: %{percent}<extra></extra>'
        )])

        fig.update_layout(
            title_text=f"Score Factor Weightage (Total: {total_score} pts)",
            title_font=dict(size=14, color="#f8fafc"),
            template='plotly_dark',
            paper_bgcolor='rgba(15, 23, 42, 0.6)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=40, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=10)),
            height=320
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("##### 🧮 Factor Scoring Breakdown Table")

        breakdown_rows = []
        for factor_name, pts in score_breakdown.items():
            if "Yoga" in factor_name:
                rationale = "Supreme astronomical alignment between weekday & Moon constellation"
                category = "✨ Planetary Yoga"
            elif "Nakshatra" in factor_name:
                rationale = "High-probability wealth accumulation star (e.g. Pushya, Anuradha, Rohini)"
                category = "⭐ Lunar Star"
            elif "Shukla" in factor_name:
                rationale = "Waxing moon phase symbolizing expansion and compounding growth"
                category = "🌙 Lunar Phase"
            elif "Market" in factor_name:
                rationale = "Active daytime exchange liquidity (09:15 - 15:30 IST) with tight spreads"
                category = "📈 Market Liquidity"
            else:
                rationale = "Astronomical baseline multiplier"
                category = "🎯 General Factor"

            breakdown_rows.append({
                "Factor": factor_name,
                "Category": category,
                "Points": f"+{pts} pts" if pts > 0 else f"{pts} pts",
                "Weight": f"{round((pts / max(1, total_score)) * 100, 1)}%",
                "Vedic / Market Rationale": rationale
            })

        df_breakdown = pd.DataFrame(breakdown_rows)
        st.dataframe(df_breakdown, use_container_width=True, hide_index=True)

    # 6. Quant Safety Shield Deep-Dive Section
    st.markdown("---")
    st.subheader("🛡️ Quant Safety Shield: Downside Risk & Technical Health")

    as_of = safety.get("as_of_date", "Today")
    bench = safety.get("benchmark_name", "NIFTY 50")
    b_ltp = safety.get("ltp", 0.0)
    b_chg = safety.get("change_1d_pct", 0.0)
    safety_factors = safety.get("factors", [])

    st.caption(f"⚡ **Live Real-Time Market Telemetry as of {as_of}** | Benchmark ({bench}): **₹{b_ltp:,.2f}** ({b_chg:+.2f}% Today)")

    # 4 Indicator Gauges / Metric Cards with LIVE values
    q1, q2, q3, q4 = st.columns(4)
    p1_val = safety_factors[0]["value"] if safety_factors else f"{safety.get('ema_dist_pct', 0.0):+.2f}% vs 50-EMA"
    p1_stat = safety_factors[0]["status"] if safety_factors else "50-EMA"
    q1.metric("50-Day EMA Trend", p1_val, p1_stat)

    p2_val = f"RSI {safety.get('rsi_14', 50.0)}"
    p2_stat = safety_factors[1]["status"] if len(safety_factors) > 1 else "Momentum"
    q2.metric("RSI (14) Momentum", p2_val, p2_stat)

    p3_val = safety_factors[2]["value"] if len(safety_factors) > 2 else "Clean Orderflow"
    p3_stat = safety_factors[2]["status"] if len(safety_factors) > 2 else "Orderflow"
    q3.metric("Anti-Trap Radar", p3_val, p3_stat)

    q4.metric("1-Day Market Delta", f"{b_chg:+.2f}%", f"₹{b_ltp:,.2f}")

    safety_score = safety.get("score", 75)
    badge_col = safety.get("badge_color", "green")
    badge_hex = "#22c55e" if badge_col == "green" else ("#f59e0b" if badge_col == "orange" else "#ef4444")

    with st.expander("🔍 **Detailed Quant Safety Pillars & Scoring Formula**", expanded=True if safety_score < 70 else False):
        st.markdown(f"""
        **Composite Safety Score**: `{safety_score} / 100` &nbsp;|&nbsp; **Rating**: <span style="color: {badge_hex}; font-weight: bold;">🛡️ {safety.get('rating', 'STRONG')} SAFETY</span>
        <br><span style="color: #cbd5e1; font-size: 0.92em; line-height: 1.5;">{safety.get('summary', 'Market structure is resilient.')}</span>
        """, unsafe_allow_html=True)

        st.progress(safety_score / 100)

        # Factor table
        if safety_factors:
            df_safety = pd.DataFrame([
                {
                    "Pillar": f["pillar"],
                    "Status": f["status"],
                    "Live Indicator Value": f["value"],
                    "Points Awarded": f"{f['points']} / {f['max_points']} pts",
                    "Safety Rationale": f["rationale"]
                }
                for f in safety_factors
            ])
            st.dataframe(df_safety, use_container_width=True, hide_index=True)

        st.markdown("""
        > **💡 Why Quant Safety Matters:**
        > Even on the most auspicious celestial yoga (*Guru Pushya*), investing into a stock or index that is collapsing below its 200-day moving average or experiencing an institutional bull trap exposes capital to severe drawdown. **The Quant Safety Shield ensures you only deploy capital when both the stars AND the market structure align.**
        """)

    # 7. Allocated Basket Table
    st.markdown("---")
    st.markdown("##### 📦 Allocated Investment Basket")
    basket_df = pd.DataFrame([
        {
            "Symbol": item["clean_symbol"],
            "Asset Name": item["name"],
            "Class": item["asset_class"],
            "LTP (₹)": f"₹{item['ltp']:,.2f}",
            "Quantity": f"{item['quantity']} Units",
            "Est. Cost (₹)": f"₹{item['estimated_cost']:,.2f}",
            "Weight": f"{item['weight_pct']}%"
        }
        for item in plan["order_basket"]
    ])
    st.dataframe(basket_df, use_container_width=True, hide_index=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Budget", f"₹{plan['budget']:,.2f}")
    c1.caption("Allocated Capital")
    c2.metric("Estimated Spend", f"₹{plan['total_estimated_spend']:,.2f}")
    c2.caption("Deployed in Orders")
    c3.metric("Remaining Balance", f"₹{plan['remaining_cash']:,.2f}")
    c3.caption("Cash Buffer")

    # 8. Candidate Dates Comparison
    if len(plan.get("candidate_windows", [])) > 1:
        with st.expander("🗓️ Other Auspicious Trading Days This Month", expanded=False):
            cand_rows = []
            for c in plan["candidate_windows"]:
                cand_rows.append({
                    "Date": f"{c['date']} ({c['weekday']})",
                    "Score": f"{c.get('score', 0)} pts",
                    "Trading Status": "🟢 Open" if c.get("is_trading_day", True) else "⚠️ Closed",
                    "Nakshatra": c.get("nakshatra"),
                    "Muhurat Window": c.get("auspicious_window"),
                    "Key Alignment": ", ".join(c.get("special_yogas", [])) or "Auspicious Nakshatra"
                })
            st.dataframe(pd.DataFrame(cand_rows), use_container_width=True, hide_index=True)

    # 9. Multi-Broker Copyable Order Payloads
    with st.expander(f"📋 Copyable Broker Baskets ({'AMO Order' if is_amo else 'Live Market Order'})", expanded=True):
        tab_zerodha, tab_groww, tab_icici = st.tabs(["Zerodha Kite", "Groww", "ICICI Direct"])

        with tab_zerodha:
            variety_tag = "amo" if is_amo else "regular"
            zk_payload = ZerodhaKiteAdapter.generate_basket_payload(plan["order_basket"], variety=variety_tag)
            st.markdown(f"**Zerodha Kite Basket Schema (`variety: {variety_tag}`)**")
            if is_amo:
                st.caption("ℹ️ In Zerodha Kite, paste this into Basket Orders or place each with Order Variety = **AMO**.")
            st.json(zk_payload)

        with tab_groww:
            groww_summary = GrowwAdapter.generate_copyable_summary(plan["order_basket"], execution_mode=exec_mode)
            st.code(groww_summary, language="text")
            st.markdown("**Quick Asset Direct Links:**")
            asset_links = GrowwAdapter.generate_asset_links(plan["order_basket"])
            link_cols = st.columns(len(asset_links))
            for i, al in enumerate(asset_links):
                with link_cols[i]:
                    st.link_button(f"🔍 {al['symbol']} on Groww", al["groww_url"], use_container_width=True)

        with tab_icici:
            icici_payload = ICICIDirectAdapter.generate_breeze_payload(plan["order_basket"], execution_mode=exec_mode)
            st.markdown(f"**ICICI Direct Breeze Parameters (`validity: {'amo' if is_amo else 'day'}`)**")
            st.json(icici_payload)
