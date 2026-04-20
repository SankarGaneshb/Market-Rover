import os
import yfinance as yf
from src.state import AgentState
from rover_tools.analytics.forensic_engine import ForensicAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def forensic_node(state: AgentState) -> dict:
    """
    Node: Forensic Guardrail (Parallel)
    Scans for accounting red flags, debt issues, and promoter pledging.
    """
    logger.info("Executing Forensic Node...")
    tickers = state.get("tickers", [])

    forensic_reports = []
    red_flags_detected = False
    critical_tickers = []

    for ticker in tickers:
        try:
            # Use the official Forensic Engine from legacy analytics
            analyzer = ForensicAnalyzer(ticker)
            report = analyzer.generate_forensic_report()

            # overall_status 'CRITICAL', 'CAUTION', or 'HEALTHY'
            status = report.get('overall_status', 'HEALTHY')

            if status == "CRITICAL":
                red_flags_detected = True
                critical_tickers.append(ticker)

            forensic_reports.append({
                "ticker": ticker,
                "status": status,
                "red_flags": report.get('red_flags', 0),
                "summary": report.get('summary', "No major accounting red flags.")
            })
        except Exception as e:
            logger.error(f"Forensic scan failed for {ticker}: {e}")
            forensic_reports.append({"ticker": ticker, "status": "Error", "summary": "Forensic data unavailable."})

    celebrations = []
    feedback_prompts = []

    if red_flags_detected:
        celebrations.append({
            "type": "FORENSIC_ALERT_FLARE",
            "message": f"DANGER: Critical Forensic issues detected in {', '.join(critical_tickers)}! Check debt and pledging levels before proceeding.",
            "context": "forensic_red_flag"
        })

        feedback_prompts.append({
            "type": "RISK_MITIGATION_CHOICE",
            "message": "Critical flags detected. Should I run a 'Contagion Analysis' on the promoter group or proceed with technicals?",
            "choices": ["Run Contagion Scan", "Proceed with Technicals"]
        })

    return {
        "forensic_reports": forensic_reports,
        "celebrations": celebrations,
        "feedback_prompts": feedback_prompts,
        "current_node": "forensic_analyst"
    }
