import os
from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel, Field

# Define Output Schema for The Council
class CouncilOutput(BaseModel):
    promoter_symbol: str = Field(description="The BSE/NSE symbol of the promoter or holding company")
    governance_score: float = Field(description="A score from 1.0 to 10.0 indicating pledging safety")
    final_sentiment: str = Field(description="One of: 'Growth', 'Survival', 'High Contagion Risk'")
    debate_summary: str = Field(description="A 2-3 sentence summary of the Skeptic vs Actuary debate")

def create_council_crew(filing_text: str):
    """
    Creates and runs the CrewAI 'Council of Experts' for a given SAST/LODR filing.
    """
    
    # 1. The Harvester
    harvester = Agent(
        role='The Harvester',
        goal='Extract exact pledging data from raw SAST & LODR disclosures.',
        backstory='An expert in reading XBRL and PDF tables. You find the Pledgor, the Pledgee, and the exact percentage encumbered without hallucinating.',
        verbose=True,
        allow_delegation=False
    )

    # 2. The Genealogist
    genealogist = Agent(
        role='The Genealogist',
        goal='Map the entity network and identify shell companies or obscure NBFCs.',
        backstory='You maintain the Shadow Tracker. You look at the Pledgee (the lender) and determine if it is a Tier-1 Bank (safe) or a related party/obscure NBFC (red flag).',
        verbose=True,
        allow_delegation=False
    )

    # 3. The Actuary
    actuary = Agent(
        role='The Actuary',
        goal='Calculate the margin-call proximity and volatility impact (Contagion Risk).',
        backstory='You calculate numbers. You look at LTV ratios and the current price vs the trigger price. If it is within 15%, you panic.',
        verbose=True,
        allow_delegation=False
    )

    # 4. The Skeptic
    skeptic = Agent(
        role='The Skeptic',
        goal='Analyze the true intent behind the pledge by reading Notes to Accounts and debating The Actuary.',
        backstory='You never trust the surface data. You look for "Survival Pledging" vs "Growth Pledging". You challenge the numbers with context.',
        verbose=True,
        allow_delegation=False
    )

    # Define Tasks
    extract_task = Task(
        description=f"Extract the Pledgor, Pledgee, % pledged, and purpose from this filing data: {filing_text}",
        expected_output="A structured summary of the core pledging facts.",
        agent=harvester
    )

    trace_task = Task(
        description="Take Harvester's output. Analyze the Pledgee. Are they a Tier-1 Bank or an obscure NBFC? Determine the net-effective holding of the promoter.",
        expected_output="A risk assessment of the Pledgee and the promoter's true economic interest.",
        agent=genealogist
    )

    quantify_task = Task(
        description="Take the Genealogist's output. Estimate the margin call trigger price. Is it a high contagion risk?",
        expected_output="Contagion risk assessment and estimated trigger price.",
        agent=actuary
    )

    debate_task = Task(
        description="Take the Actuary's output. Debate the sentiment. Is this 'Survival' or 'Growth'? Synthesize the final Governance Score (1-10) and summary.",
        expected_output="The final JSON determining the governance score and sentiment.",
        agent=skeptic,
        output_json=CouncilOutput
    )

    crew = Crew(
        agents=[harvester, genealogist, actuary, skeptic],
        tasks=[extract_task, trace_task, quantify_task, debate_task],
        process=Process.sequential,
        verbose=True
    )

    return crew

async def run_council(filing_text: str):
    crew = create_council_crew(filing_text)
    result = crew.kickoff()
    return result
