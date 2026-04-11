import streamlit as st
import pandas as pd
from datetime import datetime
from utils.hil_manager import get_requests, process_request, get_kpi_summary

def show_hil_tab():
    st.title("⚖️ HIL Management Dashboard")
    st.markdown("""
    **Human-In-The-Loop (HIL) Governance Hub**
    Review, audit, and approve autonomous agent decisions. Ensure alignment with risk parameters.
    """)

    # --- KPI OVERVIEW ---
    kpis = get_kpi_summary()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Requests", kpis["total"])
    m2.metric("Approval Rate", f"{kpis['approval_rate']:.1f}%")
    m3.metric("Pending Approval", kpis["pending"])

    # SLA Warning
    sla_color = "normal" if kpis["sla_breaches"] == 0 else "inverse"
    m4.metric("SLA Breaches (>24h)", kpis["sla_breaches"], delta=f"-{kpis['sla_breaches']}" if kpis["sla_breaches"] > 0 else "0", delta_color=sla_color)

    st.divider()

    tabs = st.tabs(["📥 Pending Review", "✅ History & Audit"])

    # --- PENDING REVIEW ---
    with tabs[0]:
        pending = get_requests(status="PENDING")
        if not pending:
            st.success("🎉 All clear! No pending agent actions require approval.")
            # Mock button to seed a request for demo if empty (commented out in prod)
            if st.button("🔧 Seed Test Request (Debug)"):
                from utils.hil_manager import create_hil_request
                create_hil_request(
                    "Shadow Analyst",
                    "Confirm Accumulation Pattern",
                    {"ticker": "RELIANCE.NS", "signal": "BULLISH", "confidence": 0.92},
                    "The Shadow Analyst has detected a Bull Trap divergence. Confirm if this risk should be published to the dashboard."
                )
                st.rerun()
        else:
            for req in pending:
                with st.expander(f"🔴 Request [{req['id']}] - {req['agent_name']}: {req['task_name']}", expanded=True):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"**Instructions for HIL:**")
                        st.info(req['instructions'])
                        st.markdown(f"**Agent Data Payload:**")
                        st.json(req['data'])

                    with c2:
                        st.markdown("**Governance Actions**")
                        created_time = datetime.fromisoformat(req['created_at']).strftime("%Y-%m-%d %H:%M")
                        st.caption(f"Received: {created_time}")

                        comments = st.text_area("Review Comments", key=f"comm_{req['id']}", placeholder="Optional rationale...")

                        b1, b2 = st.columns(2)
                        if b1.button("✅ Approve", key=f"app_{req['id']}", use_container_width=True):
                            process_request(req['id'], "APPROVED", comments)
                            st.toast(f"Request {req['id']} Approved!")
                            st.rerun()

                        if b2.button("❌ Reject", key=f"rej_{req['id']}", use_container_width=True):
                            process_request(req['id'], "REJECTED", comments)
                            st.toast(f"Request {req['id']} Rejected.", icon="⚠️")
                            st.rerun()

    # --- HISTORY ---
    with tabs[1]:
        history = [r for r in get_requests() if r["status"] != "PENDING"]
        if not history:
            st.info("No approval history found.")
        else:
            df = pd.DataFrame(history)
            # Cleanup for display
            df = df[['id', 'agent_name', 'task_name', 'status', 'processed_at', 'comments']]
            st.dataframe(df, use_container_width=True, hide_index=True)

    # --- HIL INSTRUCTIONS ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📖 HIL Guidelines")
    st.sidebar.markdown("""
    1. **SLA Compliance**: All requests must be processed within **24 hours**.
    2. **Review Integrity**: Verify the 'Agent Data Payload' against current market charts if confidence is < 85%.
    3. **Rejection Rationale**: Always provide comments when rejecting an action to help the Agent learn from the feedback loop.
    4. **Critical Risk**: Any flag marked as 'Survival' or 'Critical' in the data requires double verification.
    """)
