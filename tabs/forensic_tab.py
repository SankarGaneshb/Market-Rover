import streamlit as st
import pandas as pd
from rover_tools.analytics.forensic_engine import ForensicAnalyzer
from utils.security import sanitize_ticker

def show_forensic_tab():
    st.header("🛡️ Forensic Integrity Shield")
    st.markdown("""
    **Institutional-Grade Fraud Detection Engine.**
    This tool scans financial statements for accounting red flags commonly used to manipulate stock prices.
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("### 🕵️ Scan Target")
        ticker = st.text_input("Enter Ticker Symbol:", value="RELIANCE", help="e.g. TCS, TATAMOTORS")
        
        if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
            ticker += ".NS"
            
        if st.button("Run Forensic Audit 🔍", type="primary"):
            clean_ticker = sanitize_ticker(ticker)
            if clean_ticker:
                st.session_state.forensic_ticker = clean_ticker
                st.rerun()
            else:
                st.error("Invalid Ticker Symbol. Please use alphanumeric characters (e.g. TCS.NS)")

    with col2:
        if "forensic_ticker" in st.session_state:
            target = st.session_state.forensic_ticker
            
            with st.spinner(f"Auditing {target} Balance Sheet & Cash Flows..."):
                analyzer = ForensicAnalyzer(target)
                report = analyzer.generate_forensic_report()
                
                st.subheader(f"Audit Report: {target}")
                
                # Overall Badge
                status = report.get("overall_status", "UNKNOWN")
                if status == "CLEAN":
                    st.success("✅ **CLEAN STATUS**: No major red flags detected.")
                elif status == "CAUTION":
                    st.warning("⚠️ **CAUTION**: Multiple amber flags detected.")
                else:
                    st.error("🚨 **CRITICAL RISK**: Serious accounting irregularities detected.")
                
                st.divider()
                
                # Checks Display
                checks = report.get("checks", [])
                
                for check in checks:
                    # Visual Card for each check
                    c_status = check.get("status")
                    c_flag = check.get("flag", "GREEN")
                    
                    if c_status == "SKIPPED":
                        st.caption(f"⚪ **{check['metric']}**: Skipped ({check.get('reason')})")
                        continue
                        
                    icon = "✅"
                    if c_flag == "RED": icon = "🚨"
                    elif c_flag == "AMBER": icon = "⚠️"
                    
                    with st.expander(f"{icon} {check['metric']}: {check['value']}%", expanded=(c_flag=="RED")):
                        st.write(f"**Details:** {check['details']}")
                        st.caption(f"**Threshold:** {check['threshold']}")
                        if c_flag == "RED":
                            st.error("This is a significant red flag used by institutions to identify fraud.")
                            
    st.markdown("---")
    st.info("ℹ️ **Note:** This tool uses raw data from public filings. Always verify with official Annual Reports.")
