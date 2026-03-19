import os
from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel, Field

# Define Output Schema for The Council
class CouncilOutput(BaseModel):
    promoter_symbol: str = Field(description="The BSE/NSE symbol of the promoter or holding company")
    governance_score: float = Field(description="A score from 1.0 to 10.0 indicating pledging safety")
    final_sentiment: str = Field(description="One of: 'Growth', 'Survival', 'High Contagion Risk'")
    debate_summary: str = Field(description="A 2-3 sentence summary of the Skeptic vs Actuary debate")

def create_council_crew(filing_text: str, computed_metrics: dict = None):
    """
    Creates and runs the CrewAI 'Council of Experts' for a given SAST/LODR filing.
    Ingests mathematical scoring (Skin in Game %, Survival Score) to ground the debate.
    """
    
    # Format the mathematical context if provided
    quant_context = ""
    if computed_metrics:
        quant_context = (
            f"\n\n--- DETERMINISTIC QUANTITATIVE METRICS ---\n"
            f"Skin in the Game (SEBI 75% normalized): {computed_metrics.get('skin_in_the_game', 'N/A')}%\n"
            f"Survival Score (8-Quarter Time Series): {computed_metrics.get('survival_score', 'N/A')}/100 "
            f"({computed_metrics.get('intent_label', 'Unknown')} Pattern)\n"
            f"Release vs Create Trust Ratio: {computed_metrics.get('release_create_ratio', 'N/A')}x\n"
        )

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
        goal='Synthesize the deterministic Survival Score (0-100) and Skin in the Game % into a risk thesis.',
        backstory='You rely on hard math. You see the provided time-series Survival Score and 75%-normalized Skin in the Game metric. You explain *what the math means* regarding margin call proximity and contagion risk.',
        verbose=True,
        allow_delegation=False
    )

    # 4. The Skeptic
    skeptic = Agent(
        role='The Skeptic',
        goal='Analyze the true intent behind the pledge by weighing The Actuary\'s math against the context.',
        backstory='You never trust the surface data. You debate The Actuary. If the math says "Survival Pledging", you explain the dire reality. You finalize the ultimate governance score.',
        verbose=True,
        allow_delegation=False
    )

    # Define Tasks
    extract_task = Task(
        description=f"Extract the core facts from this filing data: {filing_text}\n\nYou must strictly incorporate these pre-computed historical metrics into your context: {quant_context}",
        expected_output="A structured summary of the core pledging facts, combined with the deterministic metrics.",
        agent=harvester
    )

    trace_task = Task(
        description="Take Harvester's output. Analyze the Pledgee. Determine the pledgee quality and how it impacts the provided Skin in the Game percentage.",
        expected_output="A risk assessment of the Pledgee and its impact on the promoter's true economic interest.",
        agent=genealogist
    )

    quantify_task = Task(
        description="Take the Genealogist's output and the deterministic metrics. The Survival Score determines historical intent (Growth vs Survival). Explain the severity of the contagion risk.",
        expected_output="Contagion risk assessment anchored entirely on the mathematical Survival Score and Skin %.",
        agent=actuary
    )

    debate_task = Task(
        description="Take the Actuary's output. Debate the sentiment. Validate the 'Growth' or 'Survival' label. Synthesize the final Governance Score (1-10) and summary.",
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

async def run_council(filing_text: str, computed_metrics: dict = None):
    crew = create_council_crew(filing_text, computed_metrics)
    result = crew.kickoff()
    return result
