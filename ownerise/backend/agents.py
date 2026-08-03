import os
from crewai import Agent, Process
from langchain_google_genai import ChatGoogleGenerativeAI

def get_gemini_llm():
    """Helper to initialize the Gemini LLM for OwneRise agents."""
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", # Consistent with other satellite modules
        verbose=True,
        temperature=0.2,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

def create_analyst_agent():
    return Agent(
        role='Rights Issue Analyst',
        goal='Determine the fundamental purpose of the rights issue and its impact on company value.',
        backstory='You are a seasoned investment analyst. You read Draft Letter of Offer (DLOF) documents to distinguish between "Desperation Rights" (debt reduction, survival) and "Growth Rights" (CapEx, expansion).',
        verbose=True,
        allow_delegation=False,
        llm=get_gemini_llm()
    )

def create_strategist_agent():
    return Agent(
        role='Promoter Intent Strategist',
        goal='Analyze promoter behavior and renunciation signals to determine retail allocation probability.',
        backstory='You focus on the "Skin in the Game". You look for signals in the filing about whether promoters are subscribing to their full entitlement or renouncing them, which is a major signal for retail investors.',
        verbose=True,
        allow_delegation=False,
        llm=get_gemini_llm()
    )

def create_tax_consultant_agent():
    return Agent(
        role='Retail Tax Consultant',
        goal='Identify tax implications and fractional entitlement rules for retail investors.',
        backstory='You are an expert in Indian securities taxation. You warn users about STCG on RE sales and explain how fractional shares will be handled (consolidated vs refunded).',
        verbose=True,
        allow_delegation=False,
        llm=get_gemini_llm()
    )
