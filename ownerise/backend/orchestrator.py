import os
from crewai import Crew, Process
from .agents import create_analyst_agent, create_strategist_agent, create_tax_consultant_agent
from .tasks import create_ownerise_tasks

def run_ownerise_audit(filing_text: str):
    """
    Orchestrates the OwneRise AI analysis for a given Rights Issue document.
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
        verbose=True
    )

    # 4. Execute
    result = crew.kickoff()
    return result

if __name__ == "__main__":
    # Test sample
    sample_text = "Reliance Industries Rights Issue... Objects: Repayment of debt... Promoters intend to subscribe to full entitlement..."
    # result = run_ownerise_audit(sample_text)
    # print(result)
    pass
