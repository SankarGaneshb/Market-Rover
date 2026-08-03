from crewai import Task
from pydantic import BaseModel, Field
from typing import List, Optional

class OwneRiseAnalysisOutput(BaseModel):
    purpose_of_issue: str = Field(description="Summary of why the company is raising money.")
    growth_vs_survival: str = Field(description="'Growth' or 'Survival' label with justification.")
    promoter_intent: str = Field(description="Analysis of promoter subscription plans.")
    additional_allotment_probability: str = Field(description="Likelihood of getting extra shares if applied.")
    tax_implications: str = Field(description="Summary of tax rules for REs and installments.")
    fractional_rules: str = Field(description="How fractions are handled.")

def create_ownerise_tasks(filing_text: str, analyst, strategist, tax_consultant):
    """Creates the sequence of tasks for OwneRise analysis."""

    analysis_task = Task(
        description=(
            f"Analyze the following Rights Issue filing: {filing_text}\n\n"
            "Identify the 'Objects of the Issue'. Is the money going to pay off high-interest debt or into a new factory?"
        ),
        expected_output="A report on the issue's purpose and its 'Growth vs Survival' classification.",
        agent=analyst
    )

    strategy_task = Task(
        description=(
            "Based on the filing and analyst report, look for 'Promoter Intention to Subscribe'. "
            "Are they renouncing? Are they subscribing to the full extent? "
            "Calculate the likelihood of a retail investor getting more than their ratio if they apply for extra."
        ),
        expected_output="An analysis of promoter skin-in-the-game and retail allocation probabilities.",
        agent=strategist
    )

    tax_task = Task(
        description=(
            "Summarize the tax implications of this issue. Mention Short-Term Capital Gains (STCG) for RE sales. "
            "Also, find the section on 'Fractional Entitlements' and explain the refund/consolidation process."
        ),
        expected_output="A clear summary of tax rules and fractional share handling.",
        agent=tax_consultant,
        output_json=OwneRiseAnalysisOutput
    )

    return [analysis_task, strategy_task, tax_task]
