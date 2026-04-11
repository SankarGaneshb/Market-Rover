"""
SRE Sentinel Task: Simulates a system audit.
If latency > threshold, the agent will propose an infrastructure fix.
"""
from agents import create_sre_support_agent
from rover_tools.sre_tools import propose_system_remediation

def run_sre_sentinel():
    # Simulate a system check
    # In production, this would read from Cloud Run Metrics / performance.log
    print("SRE SENTINEL: Auditing System Health...")

    mock_latency = 3.2  # Seconds (Simulating a bottleneck)

    if mock_latency > 2.0:
        print("BOTTLENECK DETECTED: Latency > 2.0s")
        remediation = propose_system_remediation(
            issue_description=f"Persistent latency spike of {mock_latency}s detected in 'News Scraper' module.",
            suggested_fix="Enable Parallel Scrape Mode and Scale Cloud Run minimum instances from 0 to 1.",
            risk_level="High / Stability Critical"
        )
        print(f"ACTION: {remediation}")
    else:
        print("SYSTEM OPTIMAL: No healing required.")

if __name__ == "__main__":
    run_sre_sentinel()
