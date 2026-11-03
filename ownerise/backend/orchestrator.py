import os
import logging
from crewai import Crew, Process
from .agents import create_analyst_agent, create_strategist_agent, create_tax_consultant_agent
from .tasks import create_ownerise_tasks

logger = logging.getLogger("ownerise.orchestrator")

def run_ownerise_audit(filing_text: str):
    """
    Orchestrates the OwneRise AI analysis for a given Rights Issue document.
    Includes a deterministic safe floor fallback if LLM or network execution fails.
    """
    # 1. Initialize Agents
    analyst = create_analyst_agent()
    strategist = create_strategist_agent()
    tax_consultant = create_tax_consultant_agent()

    # 2. Create Tasks
    tasks = create_ownerise_tasks(filing_text, analyst, strategist, tax_consultant)

    # 3. Form the Crew
    crew = Crew(
        agents=[analyst, strategist, tax_consultant],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        max_rpm=15
    )

    # 4. Execute with Deterministic Safe Floor Fallback
    try:
        result = crew.kickoff()
        return result
    except Exception as e:
        logger.warning(
            f"OwneRise AI Crew interrupted ({type(e).__name__}: {e}). "
            "Returning deterministic rights issue baseline."
        )
        return (
            "### OwneRise Rights Issue Audit (Deterministic Safe Floor)\n\n"
            f"> **System Notice:** AI reasoning engine encountered a transient interruption ({type(e).__name__}). "
            "Displaying deterministic baseline safety audit.\n\n"
            "#### 1. Fundamental Classification\n"
            "- **Status:** Baseline Analysis Generated\n"
            "- **Action:** Check DLOF objects (repayment of debt / survival vs capex growth expansion).\n\n"
            "#### 2. Promoter Intent Baseline\n"
            "- **Observation:** Promoters holding $\\ge 50\\%$ typically subscribe in full to retain control.\n"
            "- **Caution:** If promoters renounce entitlements, retail allocation probability increases but indicates lack of conviction.\n\n"
            "#### 3. Retail Tax & Fractional Warning\n"
            "- Short-Term Capital Gains (STCG) apply on market sales of Rights Entitlements (RE).\n"
            "- Fractional entitlements are typically consolidated and liquidated by the registrar for cash credit."
        )

if __name__ == "__main__":
    # Test sample
    sample_text = "Reliance Industries Rights Issue... Objects: Repayment of debt... Promoters intend to subscribe to full entitlement..."
    # result = run_ownerise_audit(sample_text)
    # print(result)
    pass
